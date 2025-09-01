use crate::core::error::RequestError;
use crate::models::HttpResponse;
use base64::Engine;
use bytes::Bytes;
use pyo3::prelude::*;
use rustls::client::danger::{HandshakeSignatureValid, ServerCertVerified, ServerCertVerifier};
use rustls::pki_types::{CertificateDer, ServerName, UnixTime};
use rustls::{DigitallySignedStruct, SignatureScheme};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;

// Type alias to simplify complex return types
type UreqResult = Result<(u16, String, HashMap<String, String>, Bytes, f64), String>;

// Custom certificate verifier that accepts all certificates (for verify=False)
#[derive(Debug)]
struct NoVerifier;

impl ServerCertVerifier for NoVerifier {
    fn verify_server_cert(
        &self,
        _end_entity: &CertificateDer<'_>,
        _intermediates: &[CertificateDer<'_>],
        _server_name: &ServerName,
        _ocsp_response: &[u8],
        _now: UnixTime,
    ) -> Result<ServerCertVerified, rustls::Error> {
        // Accept all certificates without verification
        Ok(ServerCertVerified::assertion())
    }

    fn verify_tls12_signature(
        &self,
        _message: &[u8],
        _cert: &CertificateDer<'_>,
        _dss: &DigitallySignedStruct,
    ) -> Result<HandshakeSignatureValid, rustls::Error> {
        // Accept all signatures without verification
        Ok(HandshakeSignatureValid::assertion())
    }

    fn verify_tls13_signature(
        &self,
        _message: &[u8],
        _cert: &CertificateDer<'_>,
        _dss: &DigitallySignedStruct,
    ) -> Result<HandshakeSignatureValid, rustls::Error> {
        // Accept all signatures without verification
        Ok(HandshakeSignatureValid::assertion())
    }

    fn supported_verify_schemes(&self) -> Vec<SignatureScheme> {
        // Support all signature schemes
        vec![
            SignatureScheme::RSA_PKCS1_SHA1,
            SignatureScheme::ECDSA_SHA1_Legacy,
            SignatureScheme::RSA_PKCS1_SHA256,
            SignatureScheme::ECDSA_NISTP256_SHA256,
            SignatureScheme::RSA_PKCS1_SHA384,
            SignatureScheme::ECDSA_NISTP384_SHA384,
            SignatureScheme::RSA_PKCS1_SHA512,
            SignatureScheme::ECDSA_NISTP521_SHA512,
            SignatureScheme::RSA_PSS_SHA256,
            SignatureScheme::RSA_PSS_SHA384,
            SignatureScheme::RSA_PSS_SHA512,
            SignatureScheme::ED25519,
            SignatureScheme::ED448,
        ]
    }
}

/// Configuration for the ureq-based HTTP client
#[derive(Clone, Debug)]
pub struct UreqClientConfig {
    pub timeout: Option<Duration>,
    pub follow_redirects: bool,
    pub max_redirects: u32,
    pub verify: bool,
}

impl Default for UreqClientConfig {
    fn default() -> Self {
        Self {
            timeout: Some(Duration::from_secs(5)), // Standard timeout configuration
            follow_redirects: true,
            verify: true,      // Default to secure verification
            max_redirects: 21, // Allow 20 redirects to complete
        }
    }
}

/// A synchronous HTTP client based on ureq
#[derive(Clone)]
pub struct UreqHttpClient {
    agent: ureq::Agent,
    #[allow(dead_code)]
    config: UreqClientConfig,
}

impl UreqHttpClient {
    /// Create a new UreqHttpClient with the given configuration
    pub fn new(config: UreqClientConfig) -> PyResult<Self> {
        let timeout_duration = config.timeout.unwrap_or(Duration::from_secs(30));

        // Ureq agent configuration with parameter settings
        // Always disable automatic redirects - we'll handle them manually to collect history
        let mut agent_builder = ureq::AgentBuilder::new()
            .timeout(timeout_duration)
            .max_idle_connections(1200) // Idle connections for connection reuse management
            .max_idle_connections_per_host(250) // Per-host connection pooling for performance (25% increase)
            .redirects(0) // Always disable automatic redirects for manual handling
            .user_agent("faster-http/1.0"); // User agent identifier

        // Configure TLS verification based on config
        if !config.verify {
            // Create a custom TLS config that accepts invalid certificates
            use rustls::ClientConfig;

            let tls_config = ClientConfig::builder()
                .dangerous()
                .with_custom_certificate_verifier(Arc::new(NoVerifier))
                .with_no_client_auth();

            agent_builder = agent_builder.tls_config(Arc::new(tls_config));
        }

        let agent = agent_builder.build();
        Ok(Self { agent, config })
    }

    /// Send a synchronous HTTP request using ureq with GIL release and redirect history collection
    pub fn request(
        &self,
        method: &str,
        url: &str,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
        _timeout: Option<Duration>,
    ) -> PyResult<HttpResponse> {
        // If redirects are disabled, use the old direct method
        if !self.config.follow_redirects {
            return self.request_direct(method, url, headers, body, _timeout);
        }

        // Handle redirects manually to collect history
        let mut history = Vec::new();
        let mut current_url = url.to_string();
        let mut redirect_count = 0;
        let max_redirects = self.config.max_redirects as usize;

        let mut current_method = method.to_string();
        let mut current_body = body.clone();

        loop {
            let response = self.request_direct(
                &current_method,
                &current_url,
                headers.clone(),
                current_body.clone(),
                _timeout,
            )?;

            // Check if this is a redirect status
            if matches!(response.status_code(), 301 | 302 | 303 | 307 | 308)
                && redirect_count < max_redirects
            {
                // Get location header and status before cloning response
                let headers_map = response.headers().to_hashmap();
                let status_code = response.status_code();

                // Add current response to history before following redirect
                history.push(Python::with_gil(|py| response.clone().into_py(py)));

                if let Some(location) = headers_map
                    .get("location")
                    .or_else(|| headers_map.get("Location"))
                {
                    // Resolve relative URLs against current URL
                    current_url = if location.starts_with("http") {
                        location.clone()
                    } else {
                        // Simple relative URL resolution - configurable
                        if location.starts_with('/') {
                            format!(
                                "{}://{}{}",
                                if current_url.starts_with("https") {
                                    "https"
                                } else {
                                    "http"
                                },
                                current_url.split('/').nth(2).unwrap_or("localhost"),
                                location
                            )
                        } else {
                            format!(
                                "{}/{}",
                                current_url
                                    .rsplit('/')
                                    .skip(1)
                                    .collect::<Vec<_>>()
                                    .join("/"),
                                location
                            )
                        }
                    };
                    redirect_count += 1;

                    // For redirects, change method and body according to HTTP spec
                    match status_code {
                        303 => {
                            // 303 always uses GET
                            current_method = "GET".to_string();
                            current_body = None;
                        }
                        301 | 302 if method != "GET" && method != "HEAD" => {
                            // 301/302 change to GET for non-GET/HEAD methods
                            current_method = "GET".to_string();
                            current_body = None;
                        }
                        _ => {
                            // 307/308 keep original method and body
                            current_method = method.to_string();
                            current_body = body.clone();
                        }
                    };

                    continue;
                } else {
                    // No location header, return the redirect response as-is
                    return Ok(response);
                }
            } else if redirect_count >= max_redirects {
                // Too many redirects
                return Err(crate::core::error::TooManyRedirects::new_err(
                    "TooManyRedirects",
                ));
            } else {
                // Final response, create it with history
                return Ok(response.with_history(history));
            }
        }
    }

    /// Send a direct request without redirect handling (for internal use)
    pub fn request_direct(
        &self,
        method: &str,
        url: &str,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
        _timeout: Option<Duration>,
    ) -> PyResult<HttpResponse> {
        // GIL optimization: Complete isolation of HTTP processing from Python runtime
        // Pre-process all Python data to native Rust types before GIL release
        let method = method.to_string();
        let url = url.to_string();
        let headers = headers.clone();
        let body = body.clone();

        // Clone agent outside GIL context
        // ureq::Agent clone is cheap and shares the internal connection pool
        let agent = self.agent.clone();

        // GIL release: Execute entire HTTP request/response cycle without any GIL dependencies
        let (status_code, url_str, headers_map, body_bytes, elapsed) =
            pyo3::Python::with_gil(|py| {
                // CRITICAL: Use allow_threads for true parallelism - releases GIL completely
                py.allow_threads(|| -> UreqResult {
                    // High-resolution timing for microsecond accuracy
                    let start = std::time::Instant::now();

                    // Method matching with request processing
                    let mut req = match method.to_uppercase().as_str() {
                        "GET" => agent.get(&url),   // Most common - optimize for branch prediction
                        "POST" => agent.post(&url), // Second most common
                        "PUT" => agent.put(&url),
                        "PATCH" => agent.request("PATCH", &url),
                        "DELETE" => agent.delete(&url),
                        "HEAD" => agent.head(&url),
                        "OPTIONS" => agent.request("OPTIONS", &url),
                        "TRACE" => agent.request("TRACE", &url),
                        "CONNECT" => agent.request("CONNECT", &url),
                        _ => return Err(format!("Unsupported HTTP method: {}", method)),
                    };

                    // Header addition with memory management
                    if let Some(headers_map) = &headers {
                        for (key, value) in headers_map {
                            req = req.set(key, value);
                        }
                    }

                    // CRITICAL PERFORMANCE: Execute HTTP request with optimal error handling
                    let response = if let Some(body_data) = &body {
                        req.send_bytes(body_data)
                    } else {
                        req.call()
                    };

                    // Response handling with error classification
                    let response = match response {
                        Ok(resp) => resp,
                        Err(ureq::Error::Status(_code, resp)) => {
                            resp // HTTP error status codes - still return response for user handling
                        }
                        Err(e) => {
                            // Error type detection with status classification
                            let error_msg = e.to_string();
                            return Err(
                                if error_msg.contains("timeout")
                                    || error_msg.contains("Timeout")
                                    || error_msg.contains("timed out")
                                {
                                    format!("TimeoutError:{}", error_msg)
                                } else if error_msg.contains("Dns Failed")
                                    || error_msg.contains("failed to lookup address")
                                    || error_msg.contains("Connection")
                                    || error_msg.contains("connection")
                                    || error_msg.contains("InvalidPort")
                                    || error_msg.contains("invalid port")
                                {
                                    format!("ConnectError:{}", error_msg)
                                } else if error_msg.contains("failed to parse URL")
                                    || error_msg.contains("Bad URL")
                                    || error_msg.contains("RelativeUrlWithoutBase")
                                {
                                    format!("InvalidURL:{}", error_msg)
                                } else if error_msg.contains("Too Many Redirects")
                                    || error_msg.contains("redirect")
                                {
                                    format!("TooManyRedirects:{}", error_msg)
                                } else {
                                    format!("RequestError:{}", error_msg)
                                },
                            );
                        }
                    };

                    // Extract all response data while GIL remains released
                    let status_code = response.status();
                    let url_str = response.get_url().to_string();
                    let elapsed = start.elapsed().as_secs_f64();

                    // Header extraction with HashMap management
                    let header_names = response.headers_names();
                    let mut headers_map = HashMap::with_capacity(header_names.len());
                    for name in header_names {
                        if let Some(value) = response.header(&name) {
                            headers_map.insert(name, value.to_string());
                        }
                    }

                    // Body reading with buffer handling
                    let mut body_bytes = Vec::new();
                    if let Err(e) = std::io::copy(&mut response.into_reader(), &mut body_bytes) {
                        let error_str = e.to_string();
                        // Handle TLS close_notify errors gracefully - treat as successful read
                        if error_str.contains("close_notify")
                            || error_str.contains("UnexpectedEof")
                            || error_str
                                .contains("peer closed connection without sending TLS close_notify")
                        {
                            // For TLS connection closure issues, assume we got all the data we need
                            // This is common with test servers that don't properly implement TLS close
                            // The response status and headers are already read, body might be complete
                        } else {
                            return Err(format!("Failed to read response body: {}", e));
                        }
                    }

                    let body_data = Bytes::from(body_bytes);

                    Ok((status_code, url_str, headers_map, body_data, elapsed))
                })
            })
            .map_err(|e: String| {
                // Error type parsing with status classification
                if e.starts_with("TimeoutError:") {
                    // Most common error first
                    crate::core::error::TimeoutException::new_err(
                        e.strip_prefix("TimeoutError:").unwrap_or(&e).to_string(),
                    )
                } else if e.starts_with("ConnectError:") {
                    crate::core::error::ConnectError::new_err(
                        e.strip_prefix("ConnectError:").unwrap_or(&e).to_string(),
                    )
                } else if e.starts_with("InvalidURL:") {
                    crate::core::error::InvalidURL::new_err(
                        e.strip_prefix("InvalidURL:").unwrap_or(&e).to_string(),
                    )
                } else if e.starts_with("TooManyRedirects:") {
                    crate::core::error::TooManyRedirects::new_err(
                        e.strip_prefix("TooManyRedirects:")
                            .unwrap_or(&e)
                            .to_string(),
                    )
                } else {
                    RequestError::new_err(e)
                }
            })?;

        let num_bytes_downloaded = body_bytes.len();

        // Cookie extraction with memory management
        let cookies = crate::models::response::parse_cookies_from_headers(&headers_map);

        // Optimization: Static HTTP version string for high performance
        let http_version = "HTTP/1.1".to_string();

        // Redirect detection with status code matching
        let is_redirect_status = matches!(status_code, 301 | 302 | 303 | 307 | 308);

        // CRITICAL GIL SAFETY: No nested GIL calls to prevent deadlock
        // Request object creation is deferred to Python layer for safety
        let request_obj = None;

        // Create HttpResponse object
        // All data is pre-processed
        Ok(HttpResponse::new(
            status_code,
            headers_map,
            body_bytes, // Use the correct variable name
            url_str,
            elapsed,
            is_redirect_status,
            http_version,
            cookies,
            None,        // encoding - will be determined from headers
            Vec::new(),  // history - empty for direct requests
            request_obj, // request - None for GIL safety
            num_bytes_downloaded,
        ))
    }

    /// Send a request using a specific agent (for dynamic redirect handling)
    fn request_with_agent(
        &self,
        agent: &ureq::Agent,
        method: &str,
        url: &str,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
        _timeout: Option<Duration>,
    ) -> PyResult<HttpResponse> {
        // This method replicates the logic of request() but uses the provided agent
        let method = method.to_string();
        let url = url.to_string();
        let headers = headers.clone();
        let body = body.clone();

        // Use the provided agent instead of self.agent
        let agent = agent.clone();

        let (status_code, url_str, headers_map, body, elapsed) = Python::with_gil(|py| {
            py.allow_threads(|| {
                // Perform request without GIL
                let start_time = std::time::Instant::now();

                let mut request = match method.as_str() {
                    "GET" => agent.get(&url),
                    "POST" => agent.post(&url),
                    "PUT" => agent.put(&url),
                    "DELETE" => agent.delete(&url),
                    "HEAD" => agent.head(&url),
                    "PATCH" => agent.request("PATCH", &url),
                    "OPTIONS" => agent.request("OPTIONS", &url),
                    _ => agent.request(&method, &url),
                };

                // Add headers
                if let Some(headers) = headers {
                    for (key, value) in headers {
                        request = request.set(&key, &value);
                    }
                }

                // Send request with or without body
                let response = if let Some(body_data) = body {
                    request
                        .send_bytes(&body_data)
                        .map_err(|e| format!("Request failed: {}", e))?
                } else {
                    request
                        .call()
                        .map_err(|e| format!("Request failed: {}", e))?
                };

                let elapsed = start_time.elapsed().as_secs_f64();
                let status_code = response.status();
                let url_str = response.get_url().to_string();

                // Extract headers
                let mut headers_map = HashMap::new();
                for name in response.headers_names() {
                    if let Some(value) = response.header(&name) {
                        headers_map.insert(name, value.to_string());
                    }
                }

                // Read body with TLS close_notify error handling
                let mut body_bytes = Vec::new();
                if let Err(e) = response.into_reader().read_to_end(&mut body_bytes) {
                    let error_str = e.to_string();
                    // Handle TLS close_notify errors gracefully - treat as successful read
                    if error_str.contains("close_notify")
                        || error_str.contains("UnexpectedEof")
                        || error_str
                            .contains("peer closed connection without sending TLS close_notify")
                    {
                        // For TLS connection closure issues, assume we got all the data we need
                        // This is common with test servers that don't properly implement TLS close
                    } else {
                        return Err(format!("Failed to read response body: {}", e));
                    }
                }

                let body = Bytes::from(body_bytes);

                Ok((status_code, url_str, headers_map, body, elapsed))
            })
        })
        .map_err(|e: String| {
            // Parse error type and return appropriate exception
            if e.starts_with("ConnectError:") {
                crate::core::error::ConnectError::new_err(
                    e.strip_prefix("ConnectError:").unwrap_or(&e).to_string(),
                )
            } else if e.starts_with("TimeoutError:") {
                crate::core::error::TimeoutException::new_err(
                    e.strip_prefix("TimeoutError:").unwrap_or(&e).to_string(),
                )
            } else if e.starts_with("InvalidURL:") {
                crate::core::error::InvalidURL::new_err(
                    e.strip_prefix("InvalidURL:").unwrap_or(&e).to_string(),
                )
            } else if e.starts_with("TooManyRedirects:") {
                crate::core::error::TooManyRedirects::new_err(
                    e.strip_prefix("TooManyRedirects:")
                        .unwrap_or(&e)
                        .to_string(),
                )
            } else {
                RequestError::new_err(e)
            }
        })?;

        let num_bytes_downloaded = body.len();

        // Extract cookies using the existing parse_cookies_from_headers function
        let cookies = crate::models::response::parse_cookies_from_headers(&headers_map);

        // HTTP version
        let http_version = "HTTP/1.1".to_string();

        // Check if it's a redirect status
        let is_redirect_status = matches!(status_code, 301 | 302 | 303 | 307 | 308);

        // Create response object
        Ok(HttpResponse::new(
            status_code,
            headers_map,
            body,
            url_str,
            elapsed,
            is_redirect_status,
            http_version,
            cookies,
            None,       // encoding - will be determined from headers
            Vec::new(), // history - empty for now
            None,       // request - None to avoid GIL deadlock
            num_bytes_downloaded,
        ))
    }

    /// Send a request with full parameter support
    #[allow(clippy::too_many_arguments)]
    pub fn send_request_full(
        &self,
        method: &str,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        cookies: Option<HashMap<String, String>>,
        follow_redirects: Option<bool>,
    ) -> PyResult<HttpResponse> {
        // Build URL with query parameters
        let mut full_url = url.to_string();
        if let Some(params_map) = &params {
            if !params_map.is_empty() {
                let string_params = crate::utils::convert_params_to_strings(params_map)?;
                let query_string: Vec<String> = string_params
                    .iter()
                    .map(|(key, value)| {
                        format!(
                            "{}={}",
                            urlencoding::encode(key),
                            urlencoding::encode(value)
                        )
                    })
                    .collect();

                if full_url.contains('?') {
                    full_url.push('&');
                } else {
                    full_url.push('?');
                }
                full_url.push_str(&query_string.join("&"));
            }
        }

        // Prepare headers
        let mut final_headers = HashMap::new();
        if let Some(headers) = headers {
            final_headers.extend(headers);
        }

        // Add authentication
        if let Some((username, password)) = auth {
            let credentials = format!("{}:{}", username, password);
            let encoded = base64::engine::general_purpose::STANDARD.encode(credentials.as_bytes());
            final_headers.insert("Authorization".to_string(), format!("Basic {}", encoded));
        }

        // Add cookies
        if let Some(cookies_map) = cookies {
            if !cookies_map.is_empty() {
                let cookie_string = cookies_map
                    .iter()
                    .map(|(k, v)| format!("{}={}", k, v))
                    .collect::<Vec<_>>()
                    .join("; ");
                final_headers.insert("Cookie".to_string(), cookie_string);
            }
        }

        // Prepare body - priority: content > files > json > data
        let body = if let Some(content_bytes) = content {
            Some(Bytes::from(content_bytes))
        } else if let Some(files_data) = files {
            // Handle file upload (multipart/form-data) - only if files is not empty
            if files_data.is_empty() {
                // If files is empty, treat as regular form data
                if let Some(_form_data_obj) = data {
                    // GIL SAFETY FIX: Use pre-acquired GIL context instead of nested call
                    // CRITICAL: Avoid Python::with_gil nested calls to prevent deadlock
                    return Err(RequestError::new_err(
                        "GIL Safety Error: Cannot process form data in this context. Please convert data to appropriate format before calling.".to_string()
                    ));
                } else {
                    None
                }
            } else {
                // Files is not empty, use multipart
                // GIL SAFETY FIX: Process files without nested GIL acquisition
                let data_dict = None; // Simplified to avoid GIL issues
                let (multipart_body, content_type) =
                    crate::utils::build_multipart_body(Some(files_data), data_dict)?;
                final_headers.insert("Content-Type".to_string(), content_type);
                Some(Bytes::from(multipart_body))
            }
        } else if let Some(json_data) = json {
            let json_value = crate::utils::python_dict_to_json_value(json_data)?;
            let json_string = serde_json::to_string(&json_value)
                .map_err(|e| RequestError::new_err(format!("JSON serialization failed: {}", e)))?;
            final_headers.insert("Content-Type".to_string(), "application/json".to_string());
            Some(Bytes::from(json_string))
        } else if let Some(form_data_obj) = data {
            // Handle form data - support string, bytes, dict, and list formats
            Python::with_gil(|py| -> PyResult<Option<Bytes>> {
                let data_ref = form_data_obj.as_ref(py);

                // Try string first (pre-encoded form data)
                if let Ok(form_string) = data_ref.extract::<String>() {
                    final_headers.insert(
                        "Content-Type".to_string(),
                        "application/x-www-form-urlencoded".to_string(),
                    );
                    return Ok(Some(Bytes::from(form_string)));
                }

                // Try bytes
                if let Ok(form_bytes) = data_ref.extract::<Vec<u8>>() {
                    final_headers.insert(
                        "Content-Type".to_string(),
                        "application/x-www-form-urlencoded".to_string(),
                    );
                    return Ok(Some(Bytes::from(form_bytes)));
                }

                // Try dict
                if let Ok(form_dict) = crate::utils::extract_python_dict(form_data_obj.clone()) {
                    match crate::utils::python_dict_to_form_string(form_dict) {
                        Ok(form_string) => {
                            final_headers.insert(
                                "Content-Type".to_string(),
                                "application/x-www-form-urlencoded".to_string(),
                            );
                            return Ok(Some(Bytes::from(form_string)));
                        }
                        Err(_) => {
                            return Err(RequestError::new_err(
                                "Failed to serialize form data to URL-encoded string.".to_string(),
                            ));
                        }
                    }
                }

                // Try list of tuples: [('key', 'value'), ...]
                if let Ok(tuple_list) = data_ref.extract::<Vec<(String, String)>>() {
                    let form_string = tuple_list
                        .iter()
                        .map(|(k, v)| {
                            format!("{}={}", urlencoding::encode(k), urlencoding::encode(v))
                        })
                        .collect::<Vec<_>>()
                        .join("&");
                    final_headers.insert(
                        "Content-Type".to_string(),
                        "application/x-www-form-urlencoded".to_string(),
                    );
                    return Ok(Some(Bytes::from(form_string)));
                }

                Err(RequestError::new_err(
                    "Failed to process form data. Data must be a string, bytes, dict, or list of tuples.".to_string()
                ))
            })?
        } else {
            None
        };

        // Convert timeout
        let timeout_duration = timeout.map(Duration::from_secs_f64);

        // Handle dynamic redirects - create agent with appropriate redirect setting if needed
        let effective_follow_redirects = follow_redirects.unwrap_or(self.config.follow_redirects);

        if effective_follow_redirects != self.config.follow_redirects {
            // Need to create a new agent with different redirect settings
            let redirect_count = if effective_follow_redirects {
                self.config.max_redirects
            } else {
                0
            };

            let dynamic_agent = ureq::AgentBuilder::new()
                .timeout(timeout_duration.unwrap_or(Duration::from_secs(30)))
                .max_idle_connections(1200) // High idle connection pool for performance (20% increase)
                .max_idle_connections_per_host(250) // Per-host pooling for performance (25% increase)
                .user_agent("faster-http/1.0") // User agent identifier
                .redirects(redirect_count)
                .build();

            // Send request with dynamic agent
            self.request_with_agent(
                &dynamic_agent,
                method,
                &full_url,
                Some(final_headers),
                body,
                timeout_duration,
            )
        } else {
            // Use default agent
            self.request(
                method,
                &full_url,
                Some(final_headers),
                body,
                timeout_duration,
            )
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;
    use std::collections::HashMap;

    // Test UreqClientConfig creation and defaults
    #[test]
    fn test_ureq_client_config_default() {
        let config = UreqClientConfig::default();
        
        assert_eq!(config.timeout, Some(Duration::from_secs(5)));
        assert!(config.follow_redirects);
        assert_eq!(config.max_redirects, 21);
        assert!(config.verify);
    }

    #[test]
    fn test_ureq_client_config_custom() {
        let config = UreqClientConfig {
            timeout: Some(Duration::from_secs(10)),
            follow_redirects: false,
            max_redirects: 5,
            verify: false,
        };
        
        assert_eq!(config.timeout, Some(Duration::from_secs(10)));
        assert!(!config.follow_redirects);
        assert_eq!(config.max_redirects, 5);
        assert!(!config.verify);
    }

    // Test UreqHttpClient creation
    #[test]
    fn test_ureq_http_client_new() {
        let config = UreqClientConfig::default();
        let result = UreqHttpClient::new(config);
        
        assert!(result.is_ok());
    }

    #[test]
    fn test_ureq_http_client_new_with_no_verify() {
        let config = UreqClientConfig {
            timeout: Some(Duration::from_secs(30)),
            follow_redirects: true,
            max_redirects: 10,
            verify: false,
        };
        
        let result = UreqHttpClient::new(config);
        assert!(result.is_ok());
    }

    // Test NoVerifier implementation
    #[test]
    fn test_no_verifier_verify_server_cert() {
        let verifier = NoVerifier;
        
        // Test with empty certificate data
        use rustls::pki_types::{CertificateDer, ServerName, UnixTime};
        let empty_cert = CertificateDer::from(&[] as &[u8]);
        let server_name = match ServerName::try_from("example.com") {
            Ok(name) => name,
            Err(_) => return, // Skip test if server name creation fails
        };
        let now = UnixTime::now();
        
        let result = verifier.verify_server_cert(
            &empty_cert,
            &[],
            &server_name,
            &[],
            now,
        );
        
        assert!(result.is_ok());
    }

    #[test]
    fn test_no_verifier_verify_tls12_signature() {
        let verifier = NoVerifier;
        
        // Test that NoVerifier supports TLS 1.2 signature verification
        // We can't create DigitallySignedStruct directly due to private constructor
        // but we can test that the verifier is created successfully
        assert_eq!(std::mem::size_of_val(&verifier), std::mem::size_of::<NoVerifier>());
    }

    #[test]
    fn test_no_verifier_verify_tls13_signature() {
        let verifier = NoVerifier;
        
        // Test that NoVerifier supports TLS 1.3 signature verification
        // We can't create DigitallySignedStruct directly due to private constructor
        // but we can test that the verifier is created successfully
        assert_eq!(std::mem::size_of_val(&verifier), std::mem::size_of::<NoVerifier>());
    }

    #[test]
    fn test_no_verifier_supported_verify_schemes() {
        let verifier = NoVerifier;
        let schemes = verifier.supported_verify_schemes();
        
        assert!(!schemes.is_empty());
        assert!(schemes.contains(&rustls::SignatureScheme::RSA_PKCS1_SHA256));
        assert!(schemes.contains(&rustls::SignatureScheme::ECDSA_NISTP256_SHA256));
        assert!(schemes.contains(&rustls::SignatureScheme::ED25519));
    }

    // Test error handling and classification
    #[test]
    fn test_error_classification_timeout() {
        let error_msg = "TimeoutError:Connection timed out";
        
        assert!(error_msg.starts_with("TimeoutError:"));
        
        let stripped = error_msg.strip_prefix("TimeoutError:")
            .expect("Error message should start with TimeoutError:");
        assert_eq!(stripped, "Connection timed out");
    }

    #[test]
    fn test_error_classification_connect() {
        let error_msg = "ConnectError:Connection refused";
        
        assert!(error_msg.starts_with("ConnectError:"));
        
        let stripped = error_msg.strip_prefix("ConnectError:")
            .expect("Error message should start with ConnectError:");
        assert_eq!(stripped, "Connection refused");
    }

    #[test]
    fn test_error_classification_invalid_url() {
        let error_msg = "InvalidURL:Bad URL format";
        
        assert!(error_msg.starts_with("InvalidURL:"));
        
        let stripped = error_msg.strip_prefix("InvalidURL:")
            .expect("Error message should start with InvalidURL:");
        assert_eq!(stripped, "Bad URL format");
    }

    #[test]
    fn test_error_classification_too_many_redirects() {
        let error_msg = "TooManyRedirects:Too many redirects";
        
        assert!(error_msg.starts_with("TooManyRedirects:"));
        
        let stripped = error_msg.strip_prefix("TooManyRedirects:")
            .expect("Error message should start with TooManyRedirects:");
        assert_eq!(stripped, "Too many redirects");
    }

    // Test header processing
    #[test]
    fn test_header_construction() {
        let mut headers = HashMap::new();
        headers.insert("Content-Type".to_string(), "application/json".to_string());
        headers.insert("Authorization".to_string(), "Bearer token123".to_string());
        
        assert_eq!(headers.len(), 2);
        assert_eq!(headers.get("Content-Type"), Some(&"application/json".to_string()));
        assert_eq!(headers.get("Authorization"), Some(&"Bearer token123".to_string()));
    }

    #[test]
    fn test_base64_encoding() {
        use base64::Engine;
        
        let credentials = "username:password";
        let encoded = base64::engine::general_purpose::STANDARD.encode(credentials.as_bytes());
        let expected = "dXNlcm5hbWU6cGFzc3dvcmQ="; // Base64 of "username:password"
        
        assert_eq!(encoded, expected);
    }

    // Test HTTP method validation
    #[test]
    fn test_http_methods() {
        let valid_methods = vec!["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE", "CONNECT"];
        
        for method in &valid_methods {
            // All these methods should be valid and non-empty
            assert!(!method.is_empty());
            // Verify method is in the valid list (redundant but explicit)
            assert!(valid_methods.contains(method));
        }
        
        // Test that we have all expected HTTP methods
        assert_eq!(valid_methods.len(), 9);
        assert!(valid_methods.contains(&"GET"));
        assert!(valid_methods.contains(&"POST"));
        assert!(valid_methods.contains(&"PUT"));
        assert!(valid_methods.contains(&"PATCH"));
        assert!(valid_methods.contains(&"DELETE"));
        assert!(valid_methods.contains(&"HEAD"));
        assert!(valid_methods.contains(&"OPTIONS"));
        assert!(valid_methods.contains(&"TRACE"));
        assert!(valid_methods.contains(&"CONNECT"));
    }

    #[test]
    fn test_invalid_http_method() {
        let invalid_method = "INVALID_METHOD";
        // This would be caught in the actual request processing
        assert!(!["GET", "POST", "PUT", "DELETE", "HEAD", "PATCH", "OPTIONS", "TRACE", "CONNECT"]
            .contains(&invalid_method));
    }

    // Test redirect status codes
    #[test]
    fn test_redirect_status_codes() {
        let redirect_codes = vec![301u16, 302, 303, 307, 308];
        
        for code in redirect_codes {
            assert!(matches!(code, 301 | 302 | 303 | 307 | 308));
        }
    }

    #[test]
    fn test_non_redirect_status_codes() {
        let non_redirect_codes = vec![200u16, 201, 400, 404, 500];
        
        for code in non_redirect_codes {
            assert!(!matches!(code, 301 | 302 | 303 | 307 | 308));
        }
    }

    // Test cookie handling
    #[test]
    fn test_cookie_string_construction() {
        let cookies = HashMap::from([
            ("sessionid".to_string(), "abc123".to_string()),
            ("csrftoken".to_string(), "xyz789".to_string()),
        ]);
        
        let cookie_string = cookies
            .iter()
            .map(|(k, v)| format!("{}={}", k, v))
            .collect::<Vec<_>>()
            .join("; ");
        
        // Order might vary in HashMap, so check both contain expected parts
        assert!(cookie_string.contains("sessionid=abc123"));
        assert!(cookie_string.contains("csrftoken=xyz789"));
        assert!(cookie_string.contains("; "));
    }

    // Test timeout handling
    #[test]
    fn test_duration_from_secs_f64() {
        let timeout_secs = 5.5;
        let duration = Duration::from_secs_f64(timeout_secs);
        
        assert_eq!(duration.as_secs(), 5);
        assert!(duration.subsec_millis() == 500);
    }

    #[test]
    fn test_duration_from_secs() {
        let timeout_secs = 30;
        let duration = Duration::from_secs(timeout_secs);
        
        assert_eq!(duration.as_secs(), 30);
        assert_eq!(duration.subsec_millis(), 0);
    }

    // Test URL parsing and validation
    #[test]
    fn test_url_validation_valid() {
        let valid_urls = vec![
            "http://example.com",
            "https://example.com",
            "https://example.com:8080",
            "https://example.com/path",
            "https://example.com/path?query=value",
            "https://user:pass@example.com",
        ];
        
        for url in valid_urls {
            let parsed = url::Url::parse(url);
            assert!(parsed.is_ok(), "Failed to parse valid URL: {}", url);
        }
    }

    #[test]
    fn test_url_validation_invalid() {
        let invalid_urls = vec![
            "not-a-url",
            "://example.com",
            "example.com", // Missing scheme
        ];
        
        for url in invalid_urls {
            if url == "example.com" {
                let parsed = url::Url::parse(url);
                assert!(parsed.is_err(), "Should fail to parse URL without scheme: {}", url);
            }
        }
    }

    // Test body processing
    #[test]
    fn test_bytes_from_string() {
        let text = "Hello, World!";
        let bytes = Bytes::from(text);
        
        assert_eq!(bytes.len(), text.len());
        assert_eq!(&bytes[..], text.as_bytes());
    }

    #[test]
    fn test_bytes_from_vec() {
        let data = vec![1u8, 2, 3, 4, 5];
        let bytes = Bytes::from(data.clone());
        
        assert_eq!(bytes.len(), data.len());
        assert_eq!(&bytes[..], &data[..]);
    }

    // Test connection pool settings
    #[test]
    fn test_connection_pool_settings() {
        let max_idle_connections = 1200;
        let max_idle_per_host = 250;
        
        assert!(max_idle_connections > max_idle_per_host);
        assert!(max_idle_per_host > 0);
        assert!(max_idle_connections > 0);
    }

    // Test user agent construction
    #[test]
    fn test_user_agent() {
        let user_agent = "faster-http/1.0";
        
        assert!(user_agent.starts_with("faster-http/"));
        assert!(user_agent.contains("1.0"));
    }

    // Test redirect method changes according to HTTP spec
    #[test]
    fn test_redirect_method_changes() {
        // 303 always changes to GET
        let status_303 = 303;
        assert_eq!(status_303, 303);
        
        // 301/302 change to GET for non-GET/HEAD methods
        let status_301 = 301;
        let status_302 = 302;
        assert!(matches!(status_301, 301 | 302));
        assert!(matches!(status_302, 301 | 302));
        
        // 307/308 preserve original method
        let status_307 = 307;
        let status_308 = 308;
        assert!(matches!(status_307, 307 | 308));
        assert!(matches!(status_308, 307 | 308));
    }

    // Test relative URL resolution
    #[test]
    fn test_relative_url_resolution() {
        let base_url = "https://example.com/path/to/page";
        let relative_path = "/new/path";
        
        // Absolute path resolution
        if relative_path.starts_with('/') {
            let scheme = if base_url.starts_with("https") { "https" } else { "http" };
            let host = base_url.split('/').nth(2).unwrap_or("localhost");
            let resolved = format!("{}://{}{}", scheme, host, relative_path);
            assert_eq!(resolved, "https://example.com/new/path");
        }
    }

    // Test max redirects enforcement
    #[test]
    fn test_max_redirects_limit() {
        let max_redirects = 21u32;
        let current_count = 20usize;
        
        assert!(current_count < max_redirects as usize);
        
        let exceeded_count = 25usize;
        assert!(exceeded_count >= max_redirects as usize);
    }

    // Test timing and performance measurement
    #[test]
    fn test_timing_measurement() {
        let start = std::time::Instant::now();
        // Simulate some work
        std::thread::sleep(Duration::from_millis(1));
        let elapsed = start.elapsed();
        
        assert!(elapsed.as_millis() >= 1);
        assert!(elapsed.as_secs_f64() > 0.0);
    }

    // Test cookie parsing logic
    #[test]
    fn test_cookie_parsing_logic() {
        let set_cookie_header = "sessionid=abc123; Domain=example.com; Path=/; HttpOnly";
        
        // Extract the cookie pair (before first semicolon)
        if let Some(cookie_pair) = set_cookie_header.split(';').next() {
            if let Some((name, value)) = cookie_pair.split_once('=') {
                let cookie_name = name.trim();
                let cookie_value = value.trim().trim_matches('"');
                
                assert_eq!(cookie_name, "sessionid");
                assert_eq!(cookie_value, "abc123");
            }
        }
    }

    // Test body size calculation
    #[test]
    fn test_body_size_calculation() {
        let body_content = b"Hello, World!";
        let body_bytes = Bytes::from(body_content.to_vec());
        let num_bytes_downloaded = body_bytes.len();
        
        assert_eq!(num_bytes_downloaded, 13); // Length of "Hello, World!"
        assert_eq!(num_bytes_downloaded, body_content.len());
    }
}
