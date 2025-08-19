use crate::error::RequestError;
use crate::request::HttpRequest;
use crate::response::HttpResponse;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use pyo3::PyCell;
use crate::hyper_client::HyperHttpClient;
use std::collections::HashMap;

/// Transport configuration structure - corresponding to httpx's Transport system
#[derive(Clone, Default)]
pub struct TransportConfig {
    /// Default transport (for unmatched requests)
    pub default_transport: Option<PyObject>,
    /// Mounted transport mapping (scheme/domain -> transport)
    pub mounts: HashMap<String, PyObject>,
    /// Whether to enable custom transport
    pub enable_custom_transport: bool,
}

impl TransportConfig {
    /// Create Transport configuration from Python parameters
    pub fn from_python_params(
        transport: Option<PyObject>,
        mounts: Option<&PyDict>,
    ) -> PyResult<Self> {
        let mut config = TransportConfig::default();

        // Set default transport
        if let Some(transport_obj) = transport {
            config.default_transport = Some(transport_obj);
            config.enable_custom_transport = true;
        }

        // Set mounted transport
        if let Some(mounts_dict) = mounts {
            for (key, value) in mounts_dict.iter() {
                let key_str = key.downcast::<PyString>()?.to_str()?.to_string();
                config
                    .mounts
                    .insert(key_str, value.to_object(mounts_dict.py()));
            }
            if !config.mounts.is_empty() {
                config.enable_custom_transport = true;
            }
        }

        Ok(config)
    }

    /// Select appropriate transport for the given URL
    pub fn select_transport_for_url(&self, url: &str) -> Option<&PyObject> {
        // Parse URL to get scheme and host
        if let Ok(parsed_url) = url::Url::parse(url) {
            let scheme = parsed_url.scheme();
            let host = parsed_url.host_str().unwrap_or("");

            // 1. First check complete URL matching
            if let Some(transport) = self.mounts.get(url) {
                return Some(transport);
            }

            // 2. Check scheme + host matching (e.g.: "https://example.com")
            let scheme_host = format!("{}://{}", scheme, host);
            if let Some(transport) = self.mounts.get(&scheme_host) {
                return Some(transport);
            }

            // 3. Check host matching (e.g.: "example.com")
            if let Some(transport) = self.mounts.get(host) {
                return Some(transport);
            }

            // 4. Check scheme matching (e.g.: "https://")
            let scheme_pattern = format!("{}://", scheme);
            if let Some(transport) = self.mounts.get(&scheme_pattern) {
                return Some(transport);
            }
        }

        // 5. Return default transport
        self.default_transport.as_ref()
    }

    /// Check if custom transport should be used to handle the request
    pub fn should_use_custom_transport(&self, url: &str) -> bool {
        self.enable_custom_transport
            && (self.default_transport.is_some() || self.select_transport_for_url(url).is_some())
    }

    /// Send request using custom transport
    pub fn send_request_via_custom_transport(
        &self,
        transport: &PyObject,
        request: &HttpRequest,
    ) -> PyResult<HttpResponse> {
        Python::with_gil(|py| {
            // Convert HttpRequest to Python object
            let py_request = PyCell::new(py, request.clone())?;

            // Call the handle_request method of transport
            let result = transport.call_method1(py, "handle_request", (py_request,))?;

            // Expect to return HttpResponse object
            result.extract::<HttpResponse>(py)
        })
    }
}

/// Default faster-http Transport implementation
/// This class wraps the hyper client, providing an interface compatible with httpx.BaseTransport
#[pyclass]
pub struct FasterhttpTransport {
    #[allow(dead_code)]
    client: HyperHttpClient,
}

#[pymethods]
impl FasterhttpTransport {
    #[new]
    pub fn new() -> PyResult<Self> {
        let client = HyperHttpClient::new(crate::hyper_client::HyperClientConfig::default())
            .map_err(|e| RequestError::new_err(format!("Failed to create client: {}", e)))?;

        Ok(FasterhttpTransport { client })
    }

    /// Handle request - implement httpx.BaseTransport interface
    pub fn handle_request(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        // Create default configuration and headers to call build_and_send_request
        let empty_headers: HashMap<String, String> = HashMap::new();
        let config = crate::config::ClientConfig::new(
            None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None,
        )?;

        // Use sync client to avoid block_on
        let sync_client = crate::sync_core::SyncHttpClient::new(config)?;
        let response = sync_client.send_request(
            request.get_method(),
            request.get_url(),
            request.get_content(),
            request.get_data().clone(),
            request.get_json().clone(),
            request.get_files().clone(),
            Some(request.get_params().clone()),
            Some(request.get_headers().clone()), // headers
            None,                                // timeout
            None,                                // auth
            Some(true),                          // follow_redirects
            Some(request.get_cookies().clone()), // cookies
        )?;

        Ok(response)
    }

    /// Close transport
    pub fn close(&self) -> PyResult<()> {
        // hyper client has no explicit close method
        Ok(())
    }

    /// Asynchronously close transport
    pub fn aclose(&self) -> PyResult<()> {
        // hyper client has no explicit close method
        Ok(())
    }
}

/// Create a mock transport for testing
#[pyclass]
pub struct MockTransport {
    /// Predefined response mapping (URL -> Response)
    responses: HashMap<String, HttpResponse>,
    /// Default response
    default_response: Option<HttpResponse>,
}

#[pymethods]
impl MockTransport {
    #[new]
    pub fn new(
        responses: Option<HashMap<String, HttpResponse>>,
        default_response: Option<HttpResponse>,
    ) -> Self {
        MockTransport {
            responses: responses.unwrap_or_default(),
            default_response,
        }
    }

    /// Add mock response
    pub fn add_response(&mut self, url: String, response: HttpResponse) {
        self.responses.insert(url, response);
    }

    /// Set default response
    pub fn set_default_response(&mut self, response: HttpResponse) {
        self.default_response = Some(response);
    }

    /// Handle request - return predefined mock response
    pub fn handle_request(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        let url = request.url_str();

        // Check if there is a response for the specific URL
        if let Some(response) = self.responses.get(url) {
            return Ok(response.clone());
        }

        // Check if there is a default response
        if let Some(response) = &self.default_response {
            return Ok(response.clone());
        }

        // If no response is configured, return 404
        Err(RequestError::new_err(format!(
            "No mock response configured for URL: {}",
            url
        )))
    }

    pub fn close(&self) -> PyResult<()> {
        Ok(())
    }

    pub fn aclose(&self) -> PyResult<()> {
        Ok(())
    }
}

/// Redirect Transport - redirect HTTP requests to HTTPS
#[pyclass]
pub struct HTTPSRedirectTransport {
    /// Underlying transport
    transport: FasterhttpTransport,
}

#[pymethods]
impl HTTPSRedirectTransport {
    #[new]
    pub fn new() -> PyResult<Self> {
        Ok(HTTPSRedirectTransport {
            transport: FasterhttpTransport::new()?,
        })
    }

    /// Handle request - redirect HTTP to HTTPS
    pub fn handle_request(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        let original_url = request.url_str();

        // Check if it's an HTTP URL
        if original_url.starts_with("http://") {
            // Create HTTPS version of the request
            let https_url = original_url.replacen("http://", "https://", 1);
            let https_request = Python::with_gil(|py| {
                HttpRequest::new(
                    request.method_str().to_string(),
                    https_url,
                    Some(request.headers_map().clone().into_py(py)),
                    request.content_bytes().map(|c| c.to_vec()),
                    Some(request.params_internal().clone()),
                    Some(request.cookies_internal().clone()),
                    request.data_internal().clone(),
                    request.files_internal().clone(),
                    request.json_internal().clone(),
                    Some(request.stream_internal()),
                )
            })?;

            // Use underlying transport to send HTTPS request
            self.transport.handle_request(&https_request)
        } else {
            // Send original request directly
            self.transport.handle_request(request)
        }
    }

    pub fn close(&self) -> PyResult<()> {
        self.transport.close()
    }

    pub fn aclose(&self) -> PyResult<()> {
        self.transport.aclose()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_transport_config_default() {
        let config = TransportConfig::default();
        assert!(!config.enable_custom_transport);
        assert!(config.default_transport.is_none());
        assert!(config.mounts.is_empty());
    }

    #[test]
    fn test_transport_url_selection() {
        let config = TransportConfig::default();

        // This test requires Python objects, skip for now
        // In actual use, there will be Python objects
        assert!(!config.should_use_custom_transport("https://example.com"));
    }

    #[tokio::test]
    async fn test_mock_transport() {
        // Create mock transport
        let mock_transport = MockTransport::new(None, None);

        // Test the case where no response is configured
        let request = Python::with_gil(|_py| {
            HttpRequest::new(
                "GET".to_string(),
                "https://example.com".to_string(),
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )
        })
        .unwrap();

        let result = mock_transport.handle_request(&request);
        assert!(result.is_err());
    }
}
