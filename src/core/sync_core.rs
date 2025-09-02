// Synchronous HTTP client implementation using ureq
use crate::config::ClientConfig;
use crate::models::HttpResponse;
use crate::transport::ureq_client::{UreqClientConfig, UreqHttpClient};
use pyo3::prelude::*;
use std::collections::HashMap;

#[pyclass(module = "faster_http")]
pub struct SyncHttpClient {
    client: UreqHttpClient,
    config: ClientConfig,
}

#[pymethods]
impl SyncHttpClient {
    #[new]
    pub fn new() -> PyResult<Self> {
        // Create default config for direct Python usage
        let config = ClientConfig::new(
            None, // base_url
            None, // timeout
            None, // headers
            None, // verify
            None, // follow_redirects
            None, // auth
            None, // proxy
            None, // proxies
            None, // cookies
            None, // http1
            None, // http2
            None, // event_hooks
            None, // cert
            None, // trust_env
            None, // transport
            None, // mounts
            None, // limits
            None, // max_redirects
            None, // default_encoding
            None, // params
        )?;

        // Create ureq client configuration from ClientConfig
        let ureq_config = UreqClientConfig {
            timeout: config.default_timeout,
            follow_redirects: config.follow_redirects,
            max_redirects: config.max_redirects as u32,
            verify: config.ssl_config.verify,
        };

        let client = UreqHttpClient::new(ureq_config)?;

        Ok(Self { client, config })
    }

    /// Use ureq for synchronous requests
    #[allow(clippy::too_many_arguments)]
    pub fn send_request(
        &self,
        method: &str,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        json: Option<PyObject>,
        files: Option<PyObject>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        // Merge default params with request params
        let merged_params = match params {
            Some(request_params) => {
                let mut merged = self.config.default_params.clone();
                merged.extend(request_params);
                Some(merged)
            }
            None if !self.config.default_params.is_empty() => {
                Some(self.config.default_params.clone())
            }
            _ => None,
        };

        // Merge default cookies with request cookies
        let merged_cookies = match cookies {
            Some(request_cookies) => {
                let mut merged = self.config.default_cookies.clone();
                merged.extend(request_cookies);
                Some(merged)
            }
            None if !self.config.default_cookies.is_empty() => {
                Some(self.config.default_cookies.clone())
            }
            _ => None,
        };

        let auth_option = auth.or_else(|| crate::auth::extract_auth(&self.config.auth));

        // Merge default headers with request headers
        let merged_headers = match headers {
            Some(request_headers) => {
                let mut merged = self.config.default_headers.clone();
                merged.extend(request_headers);
                Some(merged)
            }
            None if !self.config.default_headers.is_empty() => {
                Some(self.config.default_headers.clone())
            }
            _ => headers,
        };

        // Handle data parameter - can be string, bytes, or dict
        let (data_content, _data_dict) = if let Some(ref data_obj) = data {
            Python::with_gil(|py| {
                // Try string first
                if let Ok(s) = data_obj.extract::<String>(py) {
                    (Some(s.into_bytes()), None)
                }
                // Try bytes
                else if let Ok(b) = data_obj.extract::<Vec<u8>>(py) {
                    (Some(b), None)
                }
                // Try dict
                else if let Ok(dict) = data_obj.extract::<HashMap<String, PyObject>>(py) {
                    (None, Some(dict))
                } else {
                    // Fallback: convert to string
                    match data_obj
                        .call_method0(py, "__str__")
                        .and_then(|s| s.extract::<String>(py))
                    {
                        Ok(s) => (Some(s.into_bytes()), None),
                        Err(_) => {
                            // If string conversion fails, use empty bytes as fallback
                            (Some(Vec::new()), None)
                        }
                    }
                }
            })
        } else {
            (None, None)
        };

        let json_dict = json.and_then(|obj| {
            Python::with_gil(|py| obj.extract::<HashMap<String, PyObject>>(py).ok())
        });
        let files_dict = files.and_then(|obj| {
            Python::with_gil(|py| obj.extract::<HashMap<String, PyObject>>(py).ok())
        });

        // Build final URL
        let final_url = if let Some(base) = &self.config.base_url {
            if url.starts_with("http://") || url.starts_with("https://") {
                url.to_string()
            } else {
                format!(
                    "{}/{}",
                    base.trim_end_matches('/'),
                    url.trim_start_matches('/')
                )
            }
        } else {
            url.to_string()
        };

        // Use ureq client for synchronous request
        // If we have raw data content (string/bytes), prefer that over existing content
        let final_content = data_content.or(content);

        self.client.send_request_full(
            method,
            &final_url,
            final_content,
            data,
            json_dict,
            files_dict,
            merged_params,
            merged_headers,
            timeout,
            auth_option,
            merged_cookies,
            follow_redirects,
        )
    }

    /// Send a simple request directly using ureq
    pub fn send_request_direct(
        &self,
        method: &str,
        url: &str,
        headers: HashMap<String, String>,
        content: Option<Vec<u8>>,
    ) -> PyResult<HttpResponse> {
        use bytes::Bytes;

        let body = content.map(Bytes::from);
        self.client.request(method, url, Some(headers), body, None)
    }

    /// Send a GET request
    #[allow(clippy::too_many_arguments)]
    pub fn get(
        &self,
        url: &str,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.send_request(
            "GET",
            url,
            None,
            None,
            None,
            None,
            params,
            headers,
            timeout,
            auth,
            follow_redirects,
            cookies,
        )
    }

    /// Send a POST request
    #[allow(clippy::too_many_arguments)]
    pub fn post(
        &self,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        json: Option<PyObject>,
        files: Option<PyObject>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.send_request(
            "POST",
            url,
            content,
            data,
            json,
            files,
            params,
            headers,
            timeout,
            auth,
            follow_redirects,
            cookies,
        )
    }

    /// Send a PUT request
    #[allow(clippy::too_many_arguments)]
    pub fn put(
        &self,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        json: Option<PyObject>,
        files: Option<PyObject>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.send_request(
            "PUT",
            url,
            content,
            data,
            json,
            files,
            params,
            headers,
            timeout,
            auth,
            follow_redirects,
            cookies,
        )
    }

    /// Send a PATCH request
    #[allow(clippy::too_many_arguments)]
    pub fn patch(
        &self,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        json: Option<PyObject>,
        files: Option<PyObject>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.send_request(
            "PATCH",
            url,
            content,
            data,
            json,
            files,
            params,
            headers,
            timeout,
            auth,
            follow_redirects,
            cookies,
        )
    }

    /// Send a DELETE request
    #[allow(clippy::too_many_arguments)]
    pub fn delete(
        &self,
        url: &str,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.send_request(
            "DELETE",
            url,
            None,
            None,
            None,
            None,
            params,
            headers,
            timeout,
            auth,
            follow_redirects,
            cookies,
        )
    }

    /// Send a HEAD request
    #[allow(clippy::too_many_arguments)]
    pub fn head(
        &self,
        url: &str,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.send_request(
            "HEAD",
            url,
            None,
            None,
            None,
            None,
            params,
            headers,
            timeout,
            auth,
            follow_redirects,
            cookies,
        )
    }

    /// Send an OPTIONS request
    #[allow(clippy::too_many_arguments)]
    pub fn options(
        &self,
        url: &str,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.send_request(
            "OPTIONS",
            url,
            None,
            None,
            None,
            None,
            params,
            headers,
            timeout,
            auth,
            follow_redirects,
            cookies,
        )
    }
}

impl SyncHttpClient {
    /// Get access to the underlying UreqHttpClient
    pub fn get_client(&self) -> &UreqHttpClient {
        &self.client
    }

    // Removed complex localhost handling - now using unified simple approach

    /// Create a new SyncHttpClient with the provided config (internal use)
    pub fn new_with_config(config: ClientConfig) -> PyResult<Self> {
        // Create ureq client configuration from ClientConfig
        let ureq_config = UreqClientConfig {
            timeout: config.default_timeout,
            follow_redirects: config.follow_redirects,
            max_redirects: config.max_redirects as u32,
            verify: config.ssl_config.verify,
        };

        let client = UreqHttpClient::new(ureq_config)?;

        Ok(Self { client, config })
    }
}

impl Clone for SyncHttpClient {
    fn clone(&self) -> Self {
        Self {
            client: self.client.clone(),
            config: self.config.clone(),
        }
    }
}

// Removed complex localhost optimization - now using unified simple approach
