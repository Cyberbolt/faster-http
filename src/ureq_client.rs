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
        let mut builder = ureq::AgentBuilder::new();
        
        if let Some(timeout) = config.timeout {
            builder = builder.timeout(timeout);
        }
        
        if config.follow_redirects {
            builder = builder.max_idle_connections(10);
        } else {
            builder = builder.redirects(0);
        }

        let agent = builder.build();

        Ok(Self { agent, config })
    }

    /// Send a synchronous HTTP request using ureq
    pub fn request(
        &self,
        method: &str,
        url: &str,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
        timeout: Option<Duration>,
    ) -> PyResult<HttpResponse> {
        let start_time = Instant::now();
        
        // Create request
        let mut req = match method.to_uppercase().as_str() {
            "GET" => self.agent.get(url),
            "POST" => self.agent.post(url),
            "PUT" => self.agent.put(url),
            "PATCH" => self.agent.request("PATCH", url),
            "DELETE" => self.agent.delete(url),
            "HEAD" => self.agent.head(url),
            "OPTIONS" => self.agent.request("OPTIONS", url),
            _ => return Err(RequestError::new_err(format!("Unsupported method: {}", method))),
        };

        // Set timeout
        if let Some(timeout) = timeout.or(self.config.timeout) {
            req = req.timeout(timeout);
        }

        // Add headers
        if let Some(headers_map) = headers {
            for (key, value) in headers_map {
                req = req.set(&key, &value);
            }
        }

        // Send request
        let response = if let Some(body_bytes) = body {
            req.send_bytes(&body_bytes)
        } else {
            req.call()
        };

        // Handle response or error
        let response = match response {
            Ok(resp) => resp,
            Err(ureq::Error::Status(code, resp)) => {
                // Handle HTTP error status codes - still return a response
                resp
            },
            Err(e) => {
                return Err(RequestError::new_err(format!("Request failed: {}", e)));
            }
        };

        // Extract response data
        let status_code = response.status();
        let url_str = response.get_url().to_string();
        let elapsed = start_time.elapsed().as_secs_f64();
        
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
            return Err(RequestError::new_err(format!("Failed to read response body: {}", e)));
        }
        
        let body = Bytes::from(body_bytes);
        let num_bytes_downloaded = body.len();

        // Extract cookies (simple implementation)
        let mut cookies = HashMap::new();
        if let Some(cookie_header) = headers_map.get("set-cookie") {
            // Parse cookies (simplified - just get the first key=value pair)
            for cookie_str in cookie_header.split(',') {
                let cookie_str = cookie_str.trim();
                if let Some(eq_pos) = cookie_str.find('=') {
                    let key = cookie_str[..eq_pos].trim();
                    let value_part = &cookie_str[eq_pos + 1..];
                    // Extract value before any semicolon
                    let value = value_part.split(';').next().unwrap_or("").trim();
                    cookies.insert(key.to_string(), value.to_string());
                }
            }
        }

        // Determine HTTP version (ureq doesn't expose this directly)
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