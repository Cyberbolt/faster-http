use crate::error::RequestError;
use crate::response::HttpResponse;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::time::{Duration, Instant};
use bytes::Bytes;
use base64::Engine;

/// Configuration for the ureq-based HTTP client
#[derive(Clone, Debug)]
pub struct UreqClientConfig {
    pub timeout: Option<Duration>,
    pub follow_redirects: bool,
    pub max_redirects: u32,
}

impl Default for UreqClientConfig {
    fn default() -> Self {
        Self {
            timeout: Some(Duration::from_secs(30)),
            follow_redirects: true,
            max_redirects: 20,
        }
    }
}

/// A synchronous HTTP client based on ureq
#[derive(Clone)]
pub struct UreqHttpClient {
    agent: ureq::Agent,
    config: UreqClientConfig,
}

impl UreqHttpClient {
    /// Create a new UreqHttpClient with the given configuration
    pub fn new(config: UreqClientConfig) -> PyResult<Self> {
        let timeout_duration = config.timeout.unwrap_or(Duration::from_secs(30));
        
        // Configure ureq agent with connection pooling and keep-alive
        let agent = ureq::AgentBuilder::new()
            .timeout(timeout_duration)
            .max_idle_connections(100)  // Allow more idle connections for reuse
            .max_idle_connections_per_host(20)  // Per-host connection pooling
            .build();

        Ok(Self { agent, config })
    }

    /// Send a synchronous HTTP request using ureq with GIL release
    pub fn request(
        &self,
        method: &str,
        url: &str,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
        timeout: Option<Duration>,
    ) -> PyResult<HttpResponse> {
        let start_time = Instant::now();
        
        let final_timeout = timeout
            .or(self.config.timeout)
            .unwrap_or(Duration::from_secs(30)); 
        
        // SOLUTION: Release Python GIL and run ureq in isolated environment
        // This fixes the core issue where Python GIL interferes with ureq's network I/O
        let config_timeout = self.config.timeout;
        let method = method.to_string();
        let url = url.to_string();
        let headers = headers.clone();
        let body = body.clone();
        
        // Complete ureq request and response processing with GIL released
        // CRITICAL FIX: Reuse the existing agent instead of creating a new one each time
        let agent = self.agent.clone(); // ureq::Agent clone is cheap and shares connection pool
        let (status_code, url_str, headers_map, body, elapsed) = pyo3::Python::with_gil(|py| {
            py.allow_threads(|| {
                let start = std::time::Instant::now();
                
                // Execute ureq request with GIL released
                let mut req = match method.to_uppercase().as_str() {
                    "GET" => agent.get(&url),
                    "POST" => agent.post(&url),
                    "PUT" => agent.put(&url),
                    "PATCH" => agent.request("PATCH", &url),
                    "DELETE" => agent.delete(&url),
                    "HEAD" => agent.head(&url),
                    "OPTIONS" => agent.request("OPTIONS", &url),
                    _ => return Err(format!("Unsupported method: {}", method)),
                };

                // Add headers
                if let Some(headers_map) = &headers {
                    for (key, value) in headers_map {
                        req = req.set(key, value);
                    }
                }

                // Send request
                let response = if let Some(body_bytes) = &body {
                    req.send_bytes(body_bytes)
                } else {
                    req.call()
                };

                // Handle response
                let response = match response {
                    Ok(resp) => resp,
                    Err(ureq::Error::Status(_code, resp)) => {
                        resp // HTTP error status codes - still return response
                    },
                    Err(e) => return Err(format!("Request failed: {}: {}", url, e)),
                };

                // Extract all response data while GIL is released
                let status_code = response.status();
                let url_str = response.get_url().to_string();
                let elapsed = start.elapsed().as_secs_f64();
                
                // Extract headers
                let mut headers_map = HashMap::new();
                for name in response.headers_names() {
                    if let Some(value) = response.header(&name) {
                        headers_map.insert(name, value.to_string());
                    }
                }

                // Read body
                let mut body_bytes = Vec::new();
                if let Err(e) = std::io::copy(&mut response.into_reader(), &mut body_bytes) {
                    return Err(format!("Failed to read response body: {}", e));
                }
                
                let body = Bytes::from(body_bytes);

                Ok((status_code, url_str, headers_map, body, elapsed))
            })
        }).map_err(|e| RequestError::new_err(e))?;

        let num_bytes_downloaded = body.len();

        // Extract cookies (simple implementation)
        let mut cookies = HashMap::new();
        if let Some(cookie_header) = headers_map.get("set-cookie") {
            // Parse cookies (simplified)
            for cookie_str in cookie_header.split(',') {
                let cookie_str = cookie_str.trim();
                if let Some(eq_pos) = cookie_str.find('=') {
                    let key = cookie_str[..eq_pos].trim();
                    let value_part = &cookie_str[eq_pos + 1..];
                    let value = value_part.split(';').next().unwrap_or("").trim();
                    cookies.insert(key.to_string(), value.to_string());
                }
            }
        }

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
            None, // encoding - will be determined from headers
            Vec::new(), // history - empty for now
            None, // request - will be set later if needed
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
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        
        // Build URL with query parameters
        let mut full_url = url.to_string();
        if let Some(params_map) = &params {
            if !params_map.is_empty() {
                let string_params = crate::utils::convert_params_to_strings(params_map)?;
                let query_string: Vec<String> = string_params
                    .iter()
                    .map(|(key, value)| format!("{}={}", 
                        urlencoding::encode(key), 
                        urlencoding::encode(value)))
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
                if let Some(form_data) = data {
                    let form_string = crate::utils::python_dict_to_form_string(form_data)?;
                    final_headers.insert("Content-Type".to_string(), "application/x-www-form-urlencoded".to_string());
                    Some(Bytes::from(form_string))
                } else {
                    None
                }
            } else {
                // Files is not empty, use multipart
                let (multipart_body, content_type) = crate::utils::build_multipart_body(Some(files_data), data)?;
                final_headers.insert("Content-Type".to_string(), content_type);
                Some(Bytes::from(multipart_body))
            }
        } else if let Some(json_data) = json {
            let json_value = crate::utils::python_dict_to_json_value(json_data)?;
            let json_string = serde_json::to_string(&json_value)
                .map_err(|e| RequestError::new_err(format!("JSON serialization failed: {}", e)))?;
            final_headers.insert("Content-Type".to_string(), "application/json".to_string());
            Some(Bytes::from(json_string))
        } else if let Some(form_data) = data {
            let form_string = crate::utils::python_dict_to_form_string(form_data)?;
            final_headers.insert("Content-Type".to_string(), "application/x-www-form-urlencoded".to_string());
            Some(Bytes::from(form_string))
        } else {
            None
        };

        // Convert timeout
        let timeout_duration = timeout.map(Duration::from_secs_f64);

        // Send request
        self.request(method, &full_url, Some(final_headers), body, timeout_duration)
    }
}