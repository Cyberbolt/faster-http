use crate::error::{map_hyper_util_error, create_timeout_error, ReadTimeout, RequestError};
use crate::response::HttpResponse;
use hyper::body::Incoming;
use hyper::{Method, Request, Response, Uri, Version};
use hyper_util::client::legacy::Client;
use hyper_util::rt::TokioExecutor;
use http_body_util::{BodyExt, Empty, Full};
use std::collections::HashMap;
use std::time::Duration;
use pyo3::prelude::*;
use bytes::Bytes;
use std::str::FromStr;
use std::sync::Once;

/// Configuration for the Hyper-based HTTP client
#[derive(Clone, Debug)]
pub struct HyperClientConfig {
    pub follow_redirects: bool,
    pub max_redirects: usize,
    pub timeout: Option<Duration>,
    pub http1_only: bool,
    pub http2_only: bool,
}

impl Default for HyperClientConfig {
    fn default() -> Self {
        Self {
            follow_redirects: true,
            max_redirects: 20,
            timeout: Some(Duration::from_secs(30)),
            http1_only: false,
            http2_only: false,
        }
    }
}

/// A wrapper around hyper client that provides httpx-compatible functionality
#[derive(Clone)]
pub struct HyperHttpClient {
    client: Client<hyper_rustls::HttpsConnector<hyper_util::client::legacy::connect::HttpConnector>, http_body_util::Full<bytes::Bytes>>,
    config: HyperClientConfig,
}

impl HyperHttpClient {
    /// Create a new HyperHttpClient with the given configuration
    pub fn new(config: HyperClientConfig) -> PyResult<Self> {
        // Initialize the default crypto provider for rustls
        static INIT: Once = Once::new();
        INIT.call_once(|| {
            rustls::crypto::ring::default_provider()
                .install_default()
                .expect("Failed to install default crypto provider");
        });

        // Create HTTPS connector with rustls
        let https = hyper_rustls::HttpsConnectorBuilder::new()
            .with_webpki_roots()
            .https_or_http()
            .enable_http1()
            .enable_http2()
            .build();

        // Create the hyper client
        let client = hyper_util::client::legacy::Client::builder(TokioExecutor::new())
            .build(https);

        Ok(Self { client, config })
    }

    /// Create a simple HTTP request
    pub async fn request(
        &self,
        method: Method,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
    ) -> PyResult<HttpResponse> {
        let start_time = std::time::Instant::now();
        self.request_internal(method, uri, headers, body, start_time).await
    }

    /// Internal request method that preserves start_time for redirect handling
    async fn request_internal(
        &self,
        method: Method,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
        start_time: std::time::Instant,
    ) -> PyResult<HttpResponse> {
        let url = uri.to_string();
        
        // Build the request
        // Clone needed values before moving them
        let method_clone = method.clone();
        let headers_clone = headers.clone();
        let body_clone = body.clone();
        let uri_clone = uri.clone(); // Clone URI before moving it
        
        let mut request_builder = Request::builder()
            .method(method)
            .uri(uri);

        // Add headers
        if let Some(ref headers_map) = headers {
            for (key, value) in headers_map {
                request_builder = request_builder.header(key, value);
            }
        }

        // Build request with body - use Full for both cases to maintain type consistency
        let body_data = body.clone().unwrap_or_default();
        let request = request_builder
            .body(Full::new(body_data))
            .map_err(|e| RequestError::new_err(format!("Failed to build request: {}", e)))?;

        // Send the request with timeout if configured
        let response = if let Some(timeout) = self.config.timeout {
            match tokio::time::timeout(timeout, self.client.request(request)).await {
                Ok(result) => result.map_err(map_hyper_util_error)?,
                Err(_) => return Err(create_timeout_error("read", "Request timeout")),
            }
        } else {
            self.client.request(request).await.map_err(map_hyper_util_error)?
        };

        let elapsed = start_time.elapsed().as_secs_f64();

        // Handle redirects if enabled
        if self.config.follow_redirects && self.is_redirect_status(response.status().as_u16()) {
            self.handle_redirects(response, &method_clone, headers_clone.as_ref(), body_clone.as_ref(), 0, start_time, &uri_clone).await
        } else {
            self.process_response(response, url, elapsed).await
        }
    }

    /// Handle GET request
    pub async fn get(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self.request(Method::GET, uri, headers, None).await
    }

    /// Handle POST request
    pub async fn post(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
    ) -> PyResult<HttpResponse> {
        self.request(Method::POST, uri, headers, body).await
    }

    /// Handle PUT request  
    pub async fn put(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
    ) -> PyResult<HttpResponse> {
        self.request(Method::PUT, uri, headers, body).await
    }

    /// Handle PATCH request
    pub async fn patch(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
    ) -> PyResult<HttpResponse> {
        self.request(Method::PATCH, uri, headers, body).await
    }

    /// Handle DELETE request
    pub async fn delete(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self.request(Method::DELETE, uri, headers, None).await
    }

    /// Handle HEAD request
    pub async fn head(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self.request(Method::HEAD, uri, headers, None).await
    }

    /// Handle OPTIONS request
    pub async fn options(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self.request(Method::OPTIONS, uri, headers, None).await
    }

    /// Process hyper response into our HttpResponse format
    async fn process_response(&self, response: Response<Incoming>, url: String, elapsed: f64) -> PyResult<HttpResponse> {
        let status_code = response.status().as_u16();
        let version = match response.version() {
            Version::HTTP_09 => "HTTP/0.9".to_string(),
            Version::HTTP_10 => "HTTP/1.0".to_string(),
            Version::HTTP_11 => "HTTP/1.1".to_string(),
            Version::HTTP_2 => "HTTP/2".to_string(),
            Version::HTTP_3 => "HTTP/3".to_string(),
            _ => "Unknown".to_string(),
        };

        // Extract headers
        let headers: HashMap<String, String> = response
            .headers()
            .iter()
            .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
            .collect();

        // Extract cookies from Set-Cookie headers
        let cookies = self.extract_cookies_from_headers(&headers);

        // Read the body
        let body_bytes = response
            .into_body()
            .collect()
            .await
            .map_err(|e| ReadTimeout::new_err(format!("Failed to read response body: {}", e)))?
            .to_bytes();

        // Create HttpResponse using the proper constructor from response.rs
        Ok(HttpResponse::new(
            status_code,
            headers.clone(),
            body_bytes.clone(),
            url,
            elapsed,
            self.is_redirect_status(status_code),
            version,
            cookies,
            Some(self.detect_encoding_from_headers(&headers)),
            Vec::new(), // history
            None,       // request
            body_bytes.len(),
        ))
    }

    /// Handle redirect responses manually (since hyper doesn't handle redirects automatically)
    async fn handle_redirects(
        &self,
        response: Response<Incoming>,
        original_method: &Method,
        original_headers: Option<&HashMap<String, String>>,
        original_body: Option<&Bytes>,
        redirect_count: usize,
        start_time: std::time::Instant,
        original_uri: &Uri,
    ) -> PyResult<HttpResponse> {
        if redirect_count >= self.config.max_redirects {
            return Err(crate::error::TooManyRedirects::new_err(
                format!("Too many redirects (max: {})", self.config.max_redirects)
            ));
        }

        // Extract the Location header
        let location = response
            .headers()
            .get("location")
            .and_then(|v| v.to_str().ok())
            .ok_or_else(|| RequestError::new_err("Redirect response missing Location header"))?;

        // Parse the new URI - handle relative URIs by making them absolute
        let new_uri = if location.starts_with("http://") || location.starts_with("https://") {
            // Already absolute
            Uri::from_str(location)
                .map_err(|e| RequestError::new_err(format!("Invalid redirect URI: {}", e)))?
        } else {
            // Relative URL - need to make it absolute using the original request's base
            let current_scheme = original_uri.scheme().map(|s| s.as_str()).unwrap_or("https");
            let current_host = original_uri.host().ok_or_else(|| {
                RequestError::new_err("Cannot resolve relative redirect URL: original request missing host")
            })?;
            let current_port = original_uri.port().map(|p| format!(":{}", p.as_u16())).unwrap_or_default();
            
            let absolute_location = if location.starts_with("/") {
                // Absolute path
                format!("{}://{}{}{}", current_scheme, current_host, current_port, location)
            } else {
                // Relative path
                let current_path = original_uri.path();
                let base_path = if current_path.ends_with("/") {
                    current_path.to_string()
                } else {
                    let mut path_parts: Vec<&str> = current_path.split('/').collect();
                    path_parts.pop(); // Remove the last segment
                    if path_parts.is_empty() || (path_parts.len() == 1 && path_parts[0].is_empty()) {
                        "/".to_string()
                    } else {
                        format!("{}/", path_parts.join("/"))
                    }
                };
                format!("{}://{}{}{}{}", current_scheme, current_host, current_port, base_path, location)
            };
            
            Uri::from_str(&absolute_location)
                .map_err(|e| RequestError::new_err(format!("Invalid absolute redirect URI '{}': {}", absolute_location, e)))?
        };

        // Determine the method for the redirect
        let redirect_method = match response.status().as_u16() {
            301 | 302 | 303 => Method::GET, // Change to GET for these status codes
            307 | 308 => original_method.clone(),   // Keep original method
            _ => Method::GET,
        };

        // For GET/HEAD requests, don't send body in redirect
        let redirect_body = if redirect_method == Method::GET || redirect_method == Method::HEAD {
            None
        } else {
            original_body.cloned()
        };

        // Follow the redirect using internal request method that preserves original timing
        Box::pin(self.request_internal(redirect_method, new_uri, original_headers.cloned(), redirect_body, start_time)).await
    }

    /// Check if a status code indicates a redirect
    fn is_redirect_status(&self, status: u16) -> bool {
        matches!(status, 301 | 302 | 303 | 307 | 308)
    }

    /// Extract cookies from headers
    fn extract_cookies_from_headers(&self, headers: &HashMap<String, String>) -> HashMap<String, String> {
        let mut cookies = HashMap::new();
        
        // Look for Set-Cookie headers (case-insensitive)
        for (key, value) in headers {
            if key.to_lowercase() == "set-cookie" {
                // Parse the Set-Cookie header
                if let Some(cookie_pair) = value.split(';').next() {
                    if let Some((name, val)) = cookie_pair.split_once('=') {
                        cookies.insert(
                            name.trim().to_string(),
                            val.trim().trim_matches('"').to_string(),
                        );
                    }
                }
            }
        }
        
        cookies
    }

    /// Detect encoding from headers
    fn detect_encoding_from_headers(&self, headers: &HashMap<String, String>) -> String {
        // Look for Content-Type header and extract charset
        for (key, value) in headers {
            if key.to_lowercase() == "content-type" {
                if let Some(charset_pos) = value.to_lowercase().find("charset=") {
                    let charset = &value[charset_pos + 8..];
                    if let Some(end_pos) = charset.find(';') {
                        return charset[..end_pos].trim().to_string();
                    } else {
                        return charset.trim().to_string();
                    }
                }
            }
        }
        "utf-8".to_string() // Default encoding
    }
}

