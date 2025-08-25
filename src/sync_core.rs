// Synchronous HTTP client implementation using hyper with tokio runtime
use pyo3::prelude::*;
use std::collections::HashMap;
use crate::config::ClientConfig;
use crate::response::HttpResponse;
use crate::hyper_client::HyperHttpClient;
use crate::core::{build_and_send_request, send_request_direct};
use crate::runtime::get_global_runtime;
// Removed unused Duration import

// Removed complex runtime management - now using simple approach in client.rs

#[pyclass(module = "faster_http")]
pub struct SyncHttpClient {
    client: HyperHttpClient,
    config: ClientConfig,
}

#[pymethods]
impl SyncHttpClient {
    #[new]
    pub fn new() -> PyResult<Self> {
        // Create default config for direct Python usage
        let config = ClientConfig::new(
            None,    // base_url
            None,    // timeout
            None,    // headers
            None,    // verify
            None,    // follow_redirects
            None,    // auth
            None,    // proxy
            None,    // proxies
            None,    // cookies
            None,    // http1
            None,    // http2
            None,    // event_hooks
            None,    // cert
            None,    // trust_env
            None,    // transport
            None,    // mounts
            None,    // limits
            None,    // max_redirects
            None,    // default_encoding
            None,    // params
        )?;
        // Use dynamic client build for consistency with AsyncClient
        let client = config.build_client(None)?;

        Ok(Self { client, config })
    }

    /// Use build_and_send_request for ALL requests (same as AsyncHttpClient)
    /// This ensures consistent behavior and fixes localhost timeout issues
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
        
        // Merge default params with request params (same pattern as AsyncClient)
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

        // Merge default cookies with request cookies (same pattern as AsyncClient)
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
        let follow_redirects = follow_redirects.unwrap_or(self.config.follow_redirects);
        
        let config = self.config.clone();
        let method_owned = method.to_string();
        let url_owned = url.to_string();
        
        // Convert Python objects to HashMap 
        let data_dict = data.and_then(|obj| {
            Python::with_gil(|py| {
                obj.extract::<HashMap<String, PyObject>>(py).ok()
            })
        });
        let json_dict = json.and_then(|obj| {
            Python::with_gil(|py| {
                obj.extract::<HashMap<String, PyObject>>(py).ok()
            })
        });
        let files_dict = files.and_then(|obj| {
            Python::with_gil(|py| {
                obj.extract::<HashMap<String, PyObject>>(py).ok()
            })
        });
        
        // Use global runtime for better performance and consistency
        if let Some(runtime) = get_global_runtime() {
            runtime.block_on(async move {
                build_and_send_request(
                    &config,
                    &method_owned,
                    &url_owned,
                    content,
                    data_dict,
                    json_dict,
                    files_dict,
                    merged_params,
                    headers,
                    timeout,
                    &config.base_url,
                    &config.default_headers,
                    config.default_timeout,
                    auth_option,
                    follow_redirects,
                    merged_cookies,
                ).await
            })
        } else {
            // Fallback: create temporary runtime if global one fails
            let runtime = tokio::runtime::Runtime::new()
                .map_err(|e| crate::error::RequestError::new_err(format!("Failed to create runtime: {}", e)))?;
            
            runtime.block_on(async move {
                build_and_send_request(
                    &config,
                    &method_owned,
                    &url_owned,
                    content,
                    data_dict,
                    json_dict,
                    files_dict,
                    merged_params,
                    headers,
                    timeout,
                    &config.base_url,
                    &config.default_headers,
                    config.default_timeout,
                    auth_option,
                    follow_redirects,
                    merged_cookies,
                ).await
            })
        }
    }

    /// Send a simple request directly (optimized version)
    pub fn send_request_direct(
        &self,
        method: &str,
        url: &str,
        headers: HashMap<String, String>,
        content: Option<Vec<u8>>,
    ) -> PyResult<HttpResponse> {
        // Create a clone of the client to move into the async block
        let client = self.client.clone();
        let config = self.config.clone();

        // Convert borrowed strings to owned strings for async block
        let method_owned = method.to_string();
        let url_owned = url.to_string();
        
        // Use global runtime for better performance and consistency
        if let Some(runtime) = get_global_runtime() {
            runtime.block_on(async move {
                send_request_direct(&client, &method_owned, &url_owned, &headers, content.as_deref(), &config, None).await
            })
        } else {
            // Fallback: create temporary runtime if global one fails
            let runtime = tokio::runtime::Runtime::new()
                .map_err(|e| crate::error::RequestError::new_err(format!("Failed to create runtime: {}", e)))?;
            
            runtime.block_on(async move {
                send_request_direct(&client, &method_owned, &url_owned, &headers, content.as_deref(), &config, None).await
            })
        }
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
    /// Get access to the underlying HyperHttpClient
    pub fn get_client(&self) -> &HyperHttpClient {
        &self.client
    }

    // Removed complex localhost handling - now using unified simple approach

    /// Create a new SyncHttpClient with the provided config (internal use)
    pub fn new_with_config(config: ClientConfig) -> PyResult<Self> {
        // Use dynamic client build for consistency with AsyncClient
        let client = config.build_client(None)?;

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