use crate::config::ClientConfig;
use crate::error::{map_ureq_error, create_request_error, map_json_error};
use crate::response::HttpResponse;
use pyo3::prelude::*;
use std::collections::HashMap;
use ureq::{Agent, AgentBuilder, Response};
use std::time::Duration;
use std::io::Read;
use base64;
use bytes::Bytes;

/// Synchronous HTTP client implementation using ureq
/// This avoids any use of tokio runtime and block_on calls
pub struct SyncHttpClient {
    agent: Agent,
    config: ClientConfig,
}

impl SyncHttpClient {
    /// Create a new synchronous HTTP client from config
    pub fn new(config: ClientConfig) -> PyResult<Self> {
        let agent = build_ureq_agent(&config)?;
        Ok(SyncHttpClient { agent, config })
    }

    /// Execute a synchronous HTTP request
    #[allow(clippy::too_many_arguments)]
    pub fn send_request(
        &self,
        method: &str,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        json: Option<PyObject>,
        files: Option<PyObject>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        // Build final URL with params
        let final_url = self.build_final_url(url, params.as_ref())?;
        
        // Merge headers
        let final_headers = self.merge_headers(headers);
        
        // Merge cookies
        let final_cookies = self.merge_cookies(cookies);
        
        // Create ureq request
        let mut request = self.agent.request(method, &final_url);
        
        // Add headers
        for (key, value) in final_headers {
            request = request.set(&key, &value);
        }
        
        // Add cookies
        if let Some(cookies) = final_cookies {
            for (key, value) in cookies {
                request = request.set("Cookie", &format!("{}={}", key, value));
            }
        }
        
        // Add authentication
        if let Some((username, password)) = auth {
            use base64::Engine;
            let auth_value = base64::engine::general_purpose::STANDARD.encode(format!("{}:{}", username, password));
            request = request.set("Authorization", &format!("Basic {}", auth_value));
        }
        
        // Set timeout
        if let Some(timeout_secs) = timeout {
            // ureq uses timeout per operation, not total request timeout
            let timeout_duration = Duration::from_secs_f64(timeout_secs);
            request = request.timeout(timeout_duration);
        } else if let Some(default_timeout) = self.config.default_timeout {
            request = request.timeout(default_timeout);
        }
        
        // Execute request based on content type
        let response = if let Some(content) = content {
            // Raw bytes content
            request.send_bytes(&content)
        } else if let Some(json_data) = json {
            // JSON content
            let json_value = python_object_to_json_value(json_data)?;
            request.send_json(json_value)
        } else if let Some(form_data) = data {
            // Form data - convert to URL encoded string
            let form_string = encode_python_object_as_form(form_data)?;
            request
                .set("Content-Type", "application/x-www-form-urlencoded")
                .send_string(&form_string)
        } else if files.is_some() {
            // Multipart file upload - not supported in ureq directly
            return Err(create_request_error(
                "File uploads are not supported in synchronous mode. Use async client instead."
            ));
        } else {
            // No body
            request.call()
        };
        
        // Handle response or error
        match response {
            Ok(resp) => convert_ureq_response_to_http_response(resp),
            Err(ureq::Error::Status(code, resp)) => {
                // HTTP error responses (4xx, 5xx) - still convert to HttpResponse
                convert_ureq_response_to_http_response(resp)
            }
            Err(ureq_error) => {
                Err(map_ureq_error(ureq_error))
            }
        }
    }

    /// Build final URL with base_url and params
    fn build_final_url(&self, url: &str, params: Option<&HashMap<String, String>>) -> PyResult<String> {
        use crate::utils::build_url;
        
        // Merge default params with request params
        let merged_params = match params {
            Some(request_params) => {
                let mut merged = self.config.default_params.clone();
                merged.extend(request_params.clone());
                if merged.is_empty() { None } else { Some(merged) }
            }
            None if !self.config.default_params.is_empty() => {
                Some(self.config.default_params.clone())
            }
            _ => None,
        };

        build_url(url, self.config.base_url.as_ref(), merged_params.as_ref())
            .map_err(|e| create_request_error(&e.to_string()))
    }

    /// Merge client default headers with request headers
    fn merge_headers(&self, request_headers: Option<HashMap<String, String>>) -> HashMap<String, String> {
        let mut final_headers = self.config.default_headers.clone();
        if let Some(headers) = request_headers {
            final_headers.extend(headers);
        }
        final_headers
    }

    /// Merge client default cookies with request cookies
    fn merge_cookies(&self, request_cookies: Option<HashMap<String, String>>) -> Option<HashMap<String, String>> {
        match request_cookies {
            Some(request_cookies) => {
                let mut merged = self.config.default_cookies.clone();
                merged.extend(request_cookies);
                if merged.is_empty() { None } else { Some(merged) }
            }
            None if !self.config.default_cookies.is_empty() => {
                Some(self.config.default_cookies.clone())
            }
            _ => None,
        }
    }
}

/// Build ureq Agent from ClientConfig
fn build_ureq_agent(config: &ClientConfig) -> PyResult<Agent> {
    let mut agent_builder = AgentBuilder::new();
    
    // Set redirects
    if config.follow_redirects {
        let max_redirects = config.max_redirects as u32;
        agent_builder = agent_builder.redirects(max_redirects);
    } else {
        agent_builder = agent_builder.redirects(0);
    }
    
    // Note: ureq has limited TLS configuration options compared to reqwest
    // Some advanced features like custom CA certificates are not supported
    
    Ok(agent_builder.build())
}

/// Convert Python object to serde_json::Value for JSON requests
fn python_object_to_json_value(obj: PyObject) -> PyResult<serde_json::Value> {
    Python::with_gil(|py| {
        let json_str = py
            .import("json")?
            .getattr("dumps")?
            .call1((obj,))?
            .extract::<String>()?;
        
        serde_json::from_str(&json_str)
            .map_err(map_json_error)
    })
}

/// Encode Python object as URL-encoded form string
fn encode_python_object_as_form(obj: PyObject) -> PyResult<String> {
    Python::with_gil(|py| -> PyResult<String> {
        // Try to extract as dict first
        if let Ok(dict) = obj.extract::<HashMap<String, PyObject>>(py) {
            let mut pairs = Vec::new();
            for (key, value) in dict {
                let value_str = value.extract::<String>(py)
                    .or_else(|_| {
                        // Try to convert to string
                        value.call_method0(py, "__str__")?.extract::<String>(py)
                    })?;
                
                pairs.push(format!("{}={}", 
                    urlencoding::encode(&key), 
                    urlencoding::encode(&value_str)
                ));
            }
            Ok(pairs.join("&"))
        } else {
            // Try to convert to string directly
            let form_str = obj.extract::<String>(py)
                .or_else(|_| {
                    obj.call_method0(py, "__str__")?.extract::<String>(py)
                })?;
            Ok(form_str)
        }
    })
}

/// Convert ureq Response to our HttpResponse
fn convert_ureq_response_to_http_response(resp: Response) -> PyResult<HttpResponse> {
    // Get status code
    let status_code = resp.status();
    
    // Get headers
    let mut headers = HashMap::new();
    for name in resp.headers_names() {
        if let Some(value) = resp.header(&name) {
            headers.insert(name.to_lowercase(), value.to_string());
        }
    }
    
    // Read response body
    let mut body = Vec::new();
    resp.into_reader()
        .read_to_end(&mut body)
        .map_err(|e| create_request_error(&format!("Failed to read response body: {}", e)))?;
    
    // Store body length before moving body
    let body_len = body.len();
    
    // Create HttpResponse with all required parameters
    Ok(HttpResponse::new(
        status_code as u16,
        headers,
        Bytes::from(body),
        "".to_string(), // URL not easily available from ureq response
        0.0, // elapsed time not tracked in this simple implementation
        false, // is_redirect_status - simplified for now
        "HTTP/1.1".to_string(), // default HTTP version
        HashMap::new(), // cookies - not extracted from response for now
        None, // encoding - not determined here
        Vec::new(), // history - empty for sync implementation
        None, // request - not stored for sync implementation
        body_len, // num_bytes_downloaded
    ))
}