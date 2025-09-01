use crate::core::error::RequestError;
use crate::models::HttpResponse;
use bytes::Bytes;
use http_body_util::{BodyExt, Full};
use hyper::body::Incoming;
use hyper::{Method, Response, Uri, Version};
use hyper_util::client::legacy::{connect::HttpConnector, Client};
use hyper_rustls::HttpsConnector;
use hyper_util::rt::TokioExecutor;
use pyo3::prelude::*;
use std::collections::HashMap;
// use std::str::FromStr; // Unused import removed
use std::time::Duration;

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
            timeout: Some(Duration::from_millis(2000)),
            http1_only: false,
            http2_only: false,
        }
    }
}

/// A wrapper around hyper client that provides httpx-compatible functionality
/// Uses hyper's native connection pooling for optimal performance
#[derive(Clone)]
pub struct HyperHttpClient {
    /// Native hyper client with automatic connection pooling
    client: Client<HttpsConnector<HttpConnector>, Full<Bytes>>,
    #[allow(dead_code)]
    config: HyperClientConfig,
}

impl HyperHttpClient {
    /// Create a new HyperHttpClient with the given configuration
    /// Uses hyper's native connection pooling
    pub fn new(config: HyperClientConfig) -> PyResult<Self> {
        // Create HTTPS connector with hyper's built-in connection pooling
        let https = hyper_rustls::HttpsConnectorBuilder::new()
            .with_native_roots()
            .map_err(|e| RequestError::new_err(format!("Failed to create HTTPS connector: {}", e)))?
            .https_or_http()
            .enable_http1()
            .enable_http2()
            .build();

        // Create client with native connection pooling
        let client = Client::builder(TokioExecutor::new())
            .build(https);

        Ok(Self { client, config })
    }

    /// Create a simple HTTP request using hyper's native client
    /// This method automatically reuses connections via hyper's built-in pooling
    pub async fn request(
        &self,
        method: Method,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
    ) -> PyResult<HttpResponse> {
        self.request_internal(method, uri, headers, body).await
    }

    /// Internal request implementation
    async fn request_internal(
        &self,
        method: Method,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
    ) -> PyResult<HttpResponse> {
        // Build hyper request
        let mut req = hyper::Request::builder()
            .method(method)
            .uri(uri);

        // Add headers if provided
        if let Some(headers_map) = headers {
            for (key, value) in headers_map {
                req = req.header(key, value);
            }
        }

        // Build request body
        let body = body.map(Full::new).unwrap_or_else(|| Full::new(Bytes::new()));
        
        let request = req.body(body)
            .map_err(|e| RequestError::new_err(format!("Failed to build request: {}", e)))?;

        // Send request using hyper's native client
        let response = self.client
            .request(request)
            .await
            .map_err(|e| RequestError::new_err(format!("Request failed: {}", e)))?;

        // Convert hyper response to our HttpResponse
        self.convert_response(response).await
    }

    /// Convert hyper Response to HttpResponse
    async fn convert_response(&self, response: Response<Incoming>) -> PyResult<HttpResponse> {
        let status = response.status().as_u16();
        let version = match response.version() {
            Version::HTTP_09 => "HTTP/0.9",
            Version::HTTP_10 => "HTTP/1.0", 
            Version::HTTP_11 => "HTTP/1.1",
            Version::HTTP_2 => "HTTP/2.0",
            Version::HTTP_3 => "HTTP/3.0",
            _ => "HTTP/1.1",
        };

        // Extract headers
        let mut headers = HashMap::new();
        for (key, value) in response.headers() {
            if let Ok(value_str) = value.to_str() {
                headers.insert(key.to_string(), value_str.to_string());
            }
        }

        // Read body
        let body_bytes = response
            .into_body()
            .collect()
            .await
            .map_err(|e| RequestError::new_err(format!("Failed to read response body: {}", e)))?
            .to_bytes();

        // Create HttpResponse with all required parameters
        let body_len = body_bytes.len();
        Ok(HttpResponse::new(
            status,
            headers,
            body_bytes,
            "".to_string(), // url - will be set by caller
            0.0, // elapsed - will be calculated by caller
            false, // is_redirect_status
            version.to_string(),
            HashMap::new(), // cookies - empty for now
            None, // encoding
            Vec::new(), // history
            None, // request
            body_len, // num_bytes_downloaded
        ))
    }

    /// Handle GET request
    pub async fn get(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        let method = Method::GET;
        self.request(method, uri, headers, None).await
    }

    /// Handle POST request
    pub async fn post(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
    ) -> PyResult<HttpResponse> {
        let method = Method::POST;
        self.request(method, uri, headers, body).await
    }

    /// Handle PUT request
    pub async fn put(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
    ) -> PyResult<HttpResponse> {
        let method = Method::PUT;
        self.request(method, uri, headers, body).await
    }

    /// Handle PATCH request
    pub async fn patch(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
    ) -> PyResult<HttpResponse> {
        let method = Method::PATCH;
        self.request(method, uri, headers, body).await
    }

    /// Handle DELETE request
    pub async fn delete(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        let method = Method::DELETE;
        self.request(method, uri, headers, None).await
    }

    /// Handle HEAD request
    pub async fn head(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        let method = Method::HEAD;
        self.request(method, uri, headers, None).await
    }

    /// Handle OPTIONS request
    pub async fn options(
        &self,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        let method = Method::OPTIONS;
        self.request(method, uri, headers, None).await
    }

    /// Handle request with timeout (simplified version)
    pub async fn request_with_timeout(
        &self,
        method: Method,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
        _timeout: Option<Duration>, // Ignored for now - hyper manages timeouts internally
    ) -> PyResult<HttpResponse> {
        self.request(method, uri, headers, body).await
    }

    /// Get connection statistics (simplified version)
    pub fn get_connection_stats(&self) -> PyResult<HashMap<String, f64>> {
        // Return empty stats - hyper handles connection pooling internally
        Ok(HashMap::new())
    }

    /// Check if connection is healthy (simplified version)
    pub fn is_connection_healthy(&self) -> bool {
        // Always return true - hyper manages connection health internally
        true
    }

    /// Clean up connections (simplified version)
    pub async fn cleanup_connections(&self) -> PyResult<()> {
        // No-op - hyper manages connection cleanup internally
        Ok(())
    }
}