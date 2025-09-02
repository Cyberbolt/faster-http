use crate::client::hyper_client::{HyperClientConfig, HyperHttpClient};
use crate::config::ClientConfig;
use crate::models::HttpRequest;
use pyo3::prelude::*;
use pyo3_asyncio::tokio::future_into_py;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
// use std::time::Duration; // Removed unused import

// use crate::auth::extract_auth; // Removed unused import
use crate::core::engine::send_request_direct;
use crate::core::error::RequestError;

/// Asynchronous HTTP client - simplified pure conversion layer
#[pyclass(module = "faster_http")]
#[derive(Clone)]
pub struct AsyncHttpClient {
    client: HyperHttpClient,
    config: ClientConfig,
    is_closed: Arc<AtomicBool>,
}

#[pymethods]
impl AsyncHttpClient {
    #[new]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        base_url: Option<String>,
        timeout: Option<PyObject>,
        headers: Option<HashMap<String, String>>,
        verify: Option<&PyAny>,
        follow_redirects: Option<bool>,
        auth: Option<PyObject>,
        proxy: Option<&PyAny>,
        proxies: Option<&pyo3::types::PyDict>,
        cookies: Option<HashMap<String, String>>,
        http1: Option<bool>,
        http2: Option<bool>,
        event_hooks: Option<PyObject>,
        cert: Option<&PyAny>,
        trust_env: Option<bool>,
        transport: Option<PyObject>,
        mounts: Option<&pyo3::types::PyDict>,
        limits: Option<PyObject>,
        max_redirects: Option<i32>,
        default_encoding: Option<String>,
        params: Option<HashMap<String, PyObject>>,
    ) -> PyResult<Self> {
        // Create simplified config from parameters
        let config = ClientConfig::new(
            base_url,
            timeout,
            headers,
            verify,
            follow_redirects,
            auth,
            proxy,
            proxies,
            cookies,
            http1,
            http2,
            event_hooks,
            cert,
            trust_env,
            transport,
            mounts,
            limits,
            max_redirects,
            default_encoding,
            params,
        )?;

        let client = HyperHttpClient::new(HyperClientConfig::default())?;

        Ok(Self {
            client,
            config,
            is_closed: Arc::new(AtomicBool::new(false)),
        })
    }

    /// Build request object - simplified version
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (method, url, params = None, headers = None, cookies = None, content = None, data = None, files = None, json = None, timeout = None, extensions = None, stream = None))]
    pub fn build_request(
        &self,
        method: String,
        url: String,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        files: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        #[allow(unused_variables)] timeout: Option<f64>,
        #[allow(unused_variables)] extensions: Option<HashMap<String, PyObject>>,
        stream: Option<bool>,
    ) -> PyResult<HttpRequest> {
        // Process JSON serialization (same as sync client)
        let mut final_headers = headers.unwrap_or_default();
        let final_content = content;

        if let Some(_json_hashmap) = &json {
            // JSON handling moved back to Python layer for performance
            // The "Rust JSON optimization" was causing performance degradation

            // Add JSON content-type header if not already present
            if !final_headers
                .iter()
                .any(|(k, _)| k.to_lowercase() == "content-type")
            {
                final_headers.insert("content-type".to_string(), "application/json".to_string());
            }
        }

        // Add content-length header if content is present
        if let Some(ref content_bytes) = final_content {
            final_headers.insert(
                "content-length".to_string(),
                content_bytes.len().to_string(),
            );
        }

        // Build URL with base_url support (same as sync client)
        let final_url = crate::utils::build_url(
            &url,
            self.config.base_url.as_ref(),
            None, // No params for simple request - build_request doesn't handle params
        )
        .map_err(|e| RequestError::new_err(format!("URL build error: {}", e)))?;

        // Convert HashMap to PyObject for headers
        let headers_obj = if final_headers.is_empty() {
            None
        } else {
            Some(Python::with_gil(|py| final_headers.to_object(py)))
        };

        // Convert HashMap parameters to PyObjects for HttpRequest::new
        let json_obj = json.map(|j| Python::with_gil(|py| j.to_object(py)));
        let files_obj = files.map(|f| Python::with_gil(|py| f.to_object(py)));

        HttpRequest::new(
            method,
            final_url,
            headers_obj,
            final_content,
            params,
            cookies,
            data,
            files_obj,
            json_obj,
            stream,
        )
    }

    /// Send request - simplified version
    pub fn send<'py>(&self, py: Python<'py>, request: &HttpRequest) -> PyResult<&'py PyAny> {
        self.check_not_closed()?;

        let client = self.client.clone();
        let request = request.clone();
        let config = self.config.clone();

        future_into_py(py, async move {
            crate::core::engine::send_request(&client, &request, &config).await
        })
    }

    /// Close client
    pub fn aclose<'py>(&self, py: Python<'py>) -> PyResult<&'py PyAny> {
        self.is_closed.store(true, Ordering::SeqCst);
        future_into_py(py, async { Ok(()) })
    }

    /// Generic request method - fixed parameter binding for httpx compatibility
    #[allow(clippy::too_many_arguments)]
    #[allow(unused_variables)]
    #[pyo3(signature = (method, url, *, content=None, data=None, json=None, files=None, params=None, headers=None, timeout=None, auth=None, follow_redirects=None, cookies=None))]
    pub fn request<'py>(
        &self,
        py: Python<'py>,
        method: String,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<PyObject>,
        auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        // Process parameters to match sync client behavior
        self.simple_request(
            py,
            &method,
            url,
            content,
            headers,
            timeout,
            follow_redirects,
        )
    }

    // HTTP method helpers - all simplified
    #[allow(clippy::too_many_arguments)]
    pub fn get<'py>(
        &self,
        py: Python<'py>,
        url: String,
        _params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<PyObject>,
        _auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        _cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.simple_request(py, "GET", url, None, headers, timeout, follow_redirects)
    }

    #[allow(clippy::too_many_arguments)]
    pub fn post<'py>(
        &self,
        py: Python<'py>,
        url: String,
        content: Option<Vec<u8>>,
        _data: Option<PyObject>,
        _json: Option<HashMap<String, PyObject>>,
        _files: Option<HashMap<String, PyObject>>,
        _params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<PyObject>,
        _auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        _cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.simple_request(py, "POST", url, content, headers, timeout, follow_redirects)
    }

    #[allow(clippy::too_many_arguments)]
    pub fn put<'py>(
        &self,
        py: Python<'py>,
        url: String,
        content: Option<Vec<u8>>,
        _data: Option<PyObject>,
        _json: Option<HashMap<String, PyObject>>,
        _files: Option<HashMap<String, PyObject>>,
        _params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<PyObject>,
        _auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        _cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.simple_request(py, "PUT", url, content, headers, timeout, follow_redirects)
    }

    #[allow(clippy::too_many_arguments)]
    pub fn patch<'py>(
        &self,
        py: Python<'py>,
        url: String,
        content: Option<Vec<u8>>,
        _data: Option<PyObject>,
        _json: Option<HashMap<String, PyObject>>,
        _files: Option<HashMap<String, PyObject>>,
        _params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<PyObject>,
        _auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        _cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.simple_request(
            py,
            "PATCH",
            url,
            content,
            headers,
            timeout,
            follow_redirects,
        )
    }

    #[allow(clippy::too_many_arguments)]
    pub fn delete<'py>(
        &self,
        py: Python<'py>,
        url: String,
        _params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<PyObject>,
        _auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        _cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.simple_request(py, "DELETE", url, None, headers, timeout, follow_redirects)
    }

    #[allow(clippy::too_many_arguments)]
    pub fn head<'py>(
        &self,
        py: Python<'py>,
        url: String,
        _params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<PyObject>,
        _auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        _cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.simple_request(py, "HEAD", url, None, headers, timeout, follow_redirects)
    }

    #[allow(clippy::too_many_arguments)]
    pub fn options<'py>(
        &self,
        py: Python<'py>,
        url: String,
        _params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<PyObject>,
        _auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        _cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.simple_request(py, "OPTIONS", url, None, headers, timeout, follow_redirects)
    }

    /// Stream method - simplified stub
    #[allow(clippy::too_many_arguments)]
    pub fn stream(
        &self,
        _py: Python,
        _method: String,
        _url: String,
        _params: Option<HashMap<String, PyObject>>,
        _content: Option<Vec<u8>>,
        _data: Option<PyObject>,
        _json: Option<HashMap<String, PyObject>>,
        _files: Option<HashMap<String, PyObject>>,
        _headers: Option<HashMap<String, String>>,
        _timeout: Option<f64>,
        _auth: Option<PyObject>,
        _follow_redirects: Option<bool>,
        _cookies: Option<HashMap<String, String>>,
    ) -> PyResult<PyObject> {
        // Simplified - return error for now
        Err(RequestError::new_err(
            "Stream not implemented in simplified version",
        ))
    }

    // Property accessors - simplified
    pub fn base_url(&self) -> Option<String> {
        self.config.base_url.clone()
    }
    pub fn headers(&self) -> HashMap<String, String> {
        self.config.default_headers.clone()
    }
    pub fn cookies(&self) -> HashMap<String, String> {
        self.config.default_cookies.clone()
    }
    pub fn params(&self) -> HashMap<String, PyObject> {
        HashMap::new()
    }
    pub fn auth(&self) -> Option<PyObject> {
        self.config.auth_object.clone()
    }
    pub fn event_hooks(&self) -> PyResult<crate::utils::hooks::EventHooksProxy> {
        Ok(crate::utils::hooks::EventHooksProxy::new(
            self.config.event_hooks.clone(),
        ))
    }
    pub fn follow_redirects(&self) -> bool {
        self.config.follow_redirects
    }

    // Connection management - simplified stubs
    pub fn get_connection_stats(&self) -> PyResult<HashMap<String, f64>> {
        self.client.get_connection_stats()
    }

    pub fn is_connection_healthy(&self) -> PyResult<bool> {
        Ok(self.client.is_connection_healthy())
    }

    pub fn cleanup_connections<'p>(&self, py: Python<'p>) -> PyResult<&'p PyAny> {
        let client = self.client.clone();
        future_into_py(py, async move { client.cleanup_connections().await })
    }

    /// Warm up connection pool for specific domains
    /// This can improve performance for first requests to these domains
    pub fn warmup_domains<'p>(&self, py: Python<'p>, domains: Vec<String>) -> PyResult<&'p PyAny> {
        let client = self.client.clone();
        future_into_py(py, async move {
            client.warmup_domains(domains).await.map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!(
                    "Connection warmup failed: {}",
                    e
                ))
            })
        })
    }
}

impl AsyncHttpClient {
    pub fn new_from_config(config: &ClientConfig) -> PyResult<Self> {
        let client = HyperHttpClient::new(HyperClientConfig::default())?;
        Ok(Self {
            client,
            config: config.clone(),
            is_closed: Arc::new(AtomicBool::new(false)),
        })
    }

    fn check_not_closed(&self) -> PyResult<()> {
        if self.is_closed.load(Ordering::SeqCst) {
            return Err(RequestError::new_err("Client is closed"));
        }
        Ok(())
    }

    /// Simplified request method - pure conversion layer
    #[allow(clippy::too_many_arguments)]
    fn simple_request<'py>(
        &self,
        py: Python<'py>,
        method: &str,
        url: String,
        content: Option<Vec<u8>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<PyObject>,
        follow_redirects: Option<bool>,
    ) -> PyResult<&'py PyAny> {
        self.check_not_closed()?;

        // Build URL with base_url support (same as sync client)
        let final_url = crate::utils::build_url(
            &url,
            self.config.base_url.as_ref(),
            None, // No params for simple request
        )
        .map_err(|e| RequestError::new_err(format!("URL build error: {}", e)))?;

        let client = self.client.clone();
        let method = method.to_string();
        let final_headers = headers.unwrap_or_default();
        let _redirect = follow_redirects.unwrap_or(self.config.follow_redirects);
        let config = self.config.clone();

        // Simple timeout processing - moved back to original approach
        let timeout_secs = timeout.and_then(|t| Python::with_gil(|py| t.extract::<f64>(py).ok()));

        future_into_py(py, async move {
            send_request_direct(
                &client,
                &method,
                &final_url, // Use the properly built URL
                &final_headers,
                content.as_deref(),
                &config,
                timeout_secs,
            )
            .await
        })
    }
}
