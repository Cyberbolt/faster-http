use crate::config::ClientConfig;
use crate::hyper_client::HyperHttpClient;
use crate::request::HttpRequest;
use pyo3::prelude::*;
use pyo3_asyncio::tokio::future_into_py;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use crate::auth::extract_auth;
use crate::core::{build_and_send_request, send_request_direct};
use crate::error::RequestError;
use crate::utils::{build_url, build_url_with_python_params};

// Asynchronous HTTP client
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
        timeout: Option<PyObject>, // Accept either f64 or Timeout object
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
        let client = config.build_client(None)?;

        Ok(AsyncHttpClient {
            client,
            config,
            is_closed: Arc::new(AtomicBool::new(false)),
        })
    }

    #[allow(clippy::too_many_arguments)]
    pub fn build_request(
        &self,
        py: Python,
        method: &str,
        url: &str,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        files: Option<PyObject>,
        json: Option<PyObject>,
        stream: Option<bool>,
    ) -> PyResult<HttpRequest> {
        // Merge default params with request params (same pattern as headers)
        let mut final_params = self.config.default_params.clone();
        if let Some(request_params) = params {
            final_params.extend(request_params);
        }

        // Use centralized URL building with merged params
        let final_url = crate::utils::build_url_with_python_params(
            url, 
            self.config.base_url.as_ref(), 
            Some(&final_params)
        )?;

        // Simple header merging
        let mut final_headers = self.config.default_headers.clone();
        if let Some(headers) = headers {
            final_headers.extend(headers);
        }

        // Merge cookies
        let final_cookies = self.config.default_cookies.clone();
        // Note: Individual request cookies would be handled at higher level

        let headers_dict: HashMap<String, String> = final_headers;
        HttpRequest::new(
            method.to_string(),
            final_url,
            Some(headers_dict.into_py(py)),
            content,
            Some(final_params),
            Some(final_cookies),
            data,
            files,
            json,
            stream,
        )
    }

    pub fn send<'py>(&self, py: Python<'py>, request: &HttpRequest) -> PyResult<&'py PyAny> {
        self.check_not_closed()?;

        let client = self.client.clone();
        let config = self.config.clone();
        // Extract minimal data needed, avoid unnecessary cloning
        let method = request.method_str().to_string();
        let url = request.url_str().to_string();
        let headers = request.headers_map().clone();
        let content_bytes = request.content_bytes().map(|b| b.to_vec());

        future_into_py(py, async move {
            send_request_direct(
                &client,
                &method,
                &url,
                &headers,
                content_bytes.as_deref(),
                &config,
            )
            .await
        })
    }

    fn __aenter__<'py>(&self, py: Python<'py>) -> PyResult<&'py PyAny> {
        // Return self in async context manager
        let self_ref = self.clone();
        future_into_py(py, async move { Ok(self_ref) })
    }

    fn __aexit__<'py>(
        &self,
        py: Python<'py>,
        _exc_type: Option<PyObject>,
        _exc_val: Option<PyObject>,
        _exc_tb: Option<PyObject>,
    ) -> PyResult<&'py PyAny> {
        future_into_py(py, async move { Ok(false) })
    }

    // Async close client connection pool
    pub fn aclose<'py>(&self, py: Python<'py>) -> PyResult<&'py PyAny> {
        self.is_closed.store(true, Ordering::Relaxed);
        future_into_py(py, async move { Ok(()) })
    }

    // Public request method for httpx compatibility
    #[allow(clippy::too_many_arguments)]
    pub fn request<'py>(
        &self,
        py: Python<'py>,
        method: String,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.async_request(
            py,
            &method,
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

    #[allow(clippy::too_many_arguments)]
    pub fn get<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.async_request(
            py,
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

    #[allow(clippy::too_many_arguments)]
    pub fn post<'py>(
        &self,
        py: Python<'py>,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.async_request(
            py,
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

    #[allow(clippy::too_many_arguments)]
    pub fn put<'py>(
        &self,
        py: Python<'py>,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.async_request(
            py,
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

    #[allow(clippy::too_many_arguments)]
    pub fn patch<'py>(
        &self,
        py: Python<'py>,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.async_request(
            py,
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

    #[allow(clippy::too_many_arguments)]
    pub fn delete<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.async_request(
            py,
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

    #[allow(clippy::too_many_arguments)]
    pub fn head<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.async_request(
            py,
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

    #[allow(clippy::too_many_arguments)]
    pub fn options<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.async_request(
            py,
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

    #[allow(clippy::too_many_arguments)]
    pub fn stream(
        &self,
        method: String,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<crate::streaming_stub::StreamingClient> {
        use crate::streaming_stub::StreamingClient;

        self.check_not_closed()?;

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
        let auth_option = auth.or_else(|| extract_auth(&self.config.auth));
        let follow_redirects = follow_redirects.unwrap_or(self.config.follow_redirects);

        // Create StreamingClient that can be used as async context manager
        Ok(StreamingClient::new(
            self.config.clone(),
            method,
            url,
            content,
            data,
            json,
            files,
            params,
            headers,
            timeout,
            auth_option,
            follow_redirects,
            merged_cookies,
        ))
    }

    // httpx compatibility attributes
    #[getter]
    pub fn base_url(&self) -> Option<String> {
        self.config.base_url.clone()
    }

    #[getter]
    pub fn headers(&self) -> HashMap<String, String> {
        self.config.default_headers.clone()
    }

    #[getter]
    pub fn cookies(&self) -> HashMap<String, String> {
        self.config.default_cookies.clone()
    }

    #[getter]
    pub fn params(&self) -> HashMap<String, PyObject> {
        self.config.default_params.clone()
    }

    #[getter]
    pub fn auth(&self) -> Option<PyObject> {
        self.config.auth_object.clone()
    }

    #[getter]
    pub fn event_hooks(&self) -> PyResult<crate::hooks::EventHooksProxy> {
        Ok(crate::hooks::EventHooksProxy::new(
            self.config.event_hooks.clone(),
        ))
    }
}

impl AsyncHttpClient {
    // Private internal methods not exposed to Python
    fn check_not_closed(&self) -> PyResult<()> {
        if self.is_closed.load(Ordering::Relaxed) {
            return Err(RequestError::new_err("AsyncClient has been closed"));
        }
        Ok(())
    }

    // Create AsyncClient from existing config (for internal use by sync client)
    pub fn new_from_config(config: &ClientConfig) -> PyResult<Self> {
        let client = config.build_client(None)?;
        Ok(AsyncHttpClient {
            client,
            config: config.clone(),
            is_closed: Arc::new(AtomicBool::new(false)),
        })
    }

    #[allow(clippy::too_many_arguments)]
    fn async_request<'py>(
        &self,
        py: Python<'py>,
        method: &str,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.check_not_closed()?;

        // Merge default params with request params (same pattern as cookies)
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

        // Simple cookie merging - delegate actual cookie handling to hyper
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
        let auth_option = auth.or_else(|| extract_auth(&self.config.auth));
        let follow_redirects = follow_redirects.unwrap_or(self.config.follow_redirects);

        let config = self.config.clone();
        let method = method.to_string();

        future_into_py(py, async move {
            build_and_send_request(
                &config,
                &method,
                &url,
                content,
                data,
                json,
                files,
                merged_params,
                headers,
                timeout,
                &config.base_url,
                &config.default_headers,
                config.default_timeout,
                auth_option,
                follow_redirects,
                merged_cookies,
            )
            .await
        })
    }
}
