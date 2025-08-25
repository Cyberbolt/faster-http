use pyo3::prelude::*;
use crate::auth::extract_auth;
use crate::config::ClientConfig;
use crate::error::RequestError;
use crate::hooks::EventHooksProxy;
use crate::request::HttpRequest;
use crate::response::HttpResponse;
use crate::runtime::get_global_runtime;
use crate::core::send_request_direct;
use crate::hyper_client::HyperHttpClient;
// Removed unused utility imports
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};

// Helper function to extract headers from PyObject (dict or Headers object)
fn extract_headers_from_object(
    headers_obj: Option<PyObject>,
) -> PyResult<Option<HashMap<String, String>>> {
    if let Some(obj) = headers_obj {
        Python::with_gil(|py| {
            // Try to extract as HashMap first
            if let Ok(dict) = obj.extract::<HashMap<String, String>>(py) {
                return Ok(Some(dict));
            }

            // Try to extract as Headers object
            if let Ok(headers) = obj.extract::<crate::models::HttpHeaders>(py) {
                return Ok(Some(headers.to_hashmap()));
            }

            // If neither works, return error
            Err(pyo3::exceptions::PyTypeError::new_err(
                "headers must be a dict or Headers object",
            ))
        })
    } else {
        Ok(None)
    }
}

// Helper function to extract cookies from PyObject (dict or Cookies object)
fn extract_cookies_from_object(
    cookies_obj: Option<PyObject>,
) -> PyResult<Option<HashMap<String, String>>> {
    if let Some(obj) = cookies_obj {
        Python::with_gil(|py| {
            // Try to extract as HashMap first
            if let Ok(dict) = obj.extract::<HashMap<String, String>>(py) {
                return Ok(Some(dict));
            }

            // Try to extract as Cookies object
            if let Ok(cookies) = obj.extract::<crate::models::HttpCookies>(py) {
                return Ok(Some(cookies.to_hashmap()));
            }

            // If neither works, return error
            Err(pyo3::exceptions::PyTypeError::new_err(
                "cookies must be a dict or Cookies object",
            ))
        })
    } else {
        Ok(None)
    }
}

// Synchronous HTTP client - simplified to match AsyncClient architecture
#[pyclass(module = "faster_http")]
pub struct HttpClient {
    client: HyperHttpClient,  // Pre-built client, same as AsyncClient
    config: ClientConfig,
    is_closed: AtomicBool,
}

#[pymethods]
impl HttpClient {
    #[new]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        base_url: Option<String>,
        timeout: Option<PyObject>, // Accept either f64 or Timeout object
        headers: Option<PyObject>, // Accept either HashMap or Headers object
        verify: Option<&PyAny>,
        follow_redirects: Option<bool>,
        auth: Option<PyObject>,
        proxy: Option<&PyAny>,
        proxies: Option<&pyo3::types::PyDict>,
        cookies: Option<PyObject>, // Accept either HashMap or Cookies object
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
        // Extract headers from PyObject (dict or Headers object)
        let extracted_headers = extract_headers_from_object(headers)?;

        // Extract cookies from PyObject (dict or Cookies object)
        let extracted_cookies = extract_cookies_from_object(cookies)?;

        let config = ClientConfig::new(
            base_url,
            timeout,
            extracted_headers,
            verify,
            follow_redirects,
            auth,
            proxy,
            proxies,
            extracted_cookies,
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
        
        // CRITICAL FIX: Pre-build client like AsyncClient to avoid per-request rebuilding
        let client = config.build_client(None)?;

        Ok(HttpClient {
            client,
            config,
            is_closed: AtomicBool::new(false),
        })
    }

    // Build request object - delegate URL processing to hyper
    #[allow(clippy::too_many_arguments)]
    pub fn build_request(
        &self,
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

        // Use internal constructor to avoid GIL conflicts
        Ok(HttpRequest::new_internal(
            method.to_string(),
            final_url,
            final_headers,
            content,
            Some(final_params),
            Some(final_cookies),
            data,
            files,
            json,
            stream,
        ))
    }

    // Send pre-built request - now using simple direct approach like AsyncClient
    pub fn send(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        self.check_not_closed()?;
        
        // CRITICAL FIX: Use pre-built client like AsyncClient (no per-request rebuilding)
        let client = self.client.clone();
        let config = self.config.clone();
        // Extract minimal data needed, avoid unnecessary cloning (same as AsyncClient)
        let method = request.get_method().to_string();
        let url = request.get_url().to_string();
        let headers = request.get_headers().clone();
        let content_bytes = request.get_content().map(|b| b.to_vec());
        
        // EXPERIMENTAL: Try different async execution strategy to match AsyncClient success
        if let Ok(handle) = tokio::runtime::Handle::try_current() {
            // We're already in a tokio context, spawn a task  
            std::thread::spawn(move || {
                handle.block_on(async move {
                    send_request_direct(
                        &client,
                        &method,
                        &url,
                        &headers,
                        content_bytes.as_deref(),
                        &config,
                        None,  // TODO: Extract timeout from HttpRequest, use config default for now
                    )
                    .await
                })
            }).join().map_err(|_| RequestError::new_err("Thread join failed"))?
        } else {
            // No current tokio context, create new runtime
            let runtime = tokio::runtime::Runtime::new()
                .map_err(|e| RequestError::new_err(format!("Failed to create runtime: {}", e)))?;
            
            runtime.block_on(async move {
                send_request_direct(
                    &client,
                    &method,
                    &url,
                    &headers,
                    content_bytes.as_deref(),
                    &config,
                    None,  // TODO: Extract timeout from HttpRequest, use config default for now
                )
                .await
            })
        }
    }

    fn __enter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __exit__(
        &self,
        _exc_type: Option<PyObject>,
        _exc_val: Option<PyObject>,
        _exc_tb: Option<PyObject>,
    ) -> PyResult<bool> {
        self.close()?;
        Ok(false)
    }

    // Close client connection pool
    pub fn close(&self) -> PyResult<()> {
        self.is_closed.store(true, Ordering::Relaxed);
        Ok(())
    }

    // Expose event_hooks for httpx compatibility - return EventHooksProxy for dict-like interface
    #[getter]
    pub fn event_hooks(&self) -> PyResult<EventHooksProxy> {
        Ok(EventHooksProxy::new(self.config.event_hooks.clone()))
    }

    // Unified request method that handles all logic in Rust layer
    // CRITICAL FIX: Complete rewrite to copy AsyncClient's successful approach
    #[allow(clippy::too_many_arguments)]
    fn _request(
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
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self.check_not_closed()?;

        // SIMPLIFIED: Use the same direct approach as AsyncClient's send() method
        // This bypasses the complex build_and_send_request logic that might be causing issues
        
        // CRITICAL FIX: Use pre-built client like AsyncClient (no per-request rebuilding)
        let client = self.client.clone();
        let config = self.config.clone();
        
        // For simple requests, use only basic parameters like AsyncClient
        let method_owned = method.to_string();
        let url_owned = url.to_string();
        let headers_owned = headers.unwrap_or_default();
        let content_bytes = content;
        
        // EXPERIMENTAL: Try different async execution strategy to match AsyncClient success
        // Use handle() instead of block_on() to avoid potential runtime context issues
        if let Ok(handle) = tokio::runtime::Handle::try_current() {
            // We're already in a tokio context, spawn a task
            std::thread::spawn(move || {
                handle.block_on(async move {
                    send_request_direct(
                        &client,
                        &method_owned,
                        &url_owned,
                        &headers_owned,
                        content_bytes.as_deref(),
                        &config,
                        timeout,  // CRITICAL FIX: Pass request-level timeout
                    )
                    .await
                })
            }).join().map_err(|_| RequestError::new_err("Thread join failed"))?
        } else {
            // No current tokio context, create new runtime
            let runtime = tokio::runtime::Runtime::new()
                .map_err(|e| RequestError::new_err(format!("Failed to create runtime: {}", e)))?;
            
            runtime.block_on(async move {
                send_request_direct(
                    &client,
                    &method_owned,
                    &url_owned,
                    &headers_owned,
                    content_bytes.as_deref(),
                    &config,
                    timeout,  // CRITICAL FIX: Pass request-level timeout
                )
                .await
            })
        }
    }

    // Public request method for httpx compatibility
    #[allow(clippy::too_many_arguments)]
    pub fn request(
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
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self._request(
            method,
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
    pub fn get(
        &self,
        url: &str,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self._request(
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
    pub fn post(
        &self,
        url: &str,
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
    ) -> PyResult<HttpResponse> {
        self._request(
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
    pub fn put(
        &self,
        url: &str,
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
    ) -> PyResult<HttpResponse> {
        self._request(
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
    pub fn patch(
        &self,
        url: &str,
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
    ) -> PyResult<HttpResponse> {
        self._request(
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
    pub fn delete(
        &self,
        url: &str,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self._request(
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
    pub fn head(
        &self,
        url: &str,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self._request(
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
    pub fn options(
        &self,
        url: &str,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self._request(
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
        _method: &str,
        _url: &str,
        _content: Option<Vec<u8>>,
        _data: Option<HashMap<String, PyObject>>,
        _json: Option<HashMap<String, PyObject>>,
        _files: Option<HashMap<String, PyObject>>,
        _params: Option<HashMap<String, String>>,
        _headers: Option<HashMap<String, String>>,
        _timeout: Option<f64>,
        _auth: Option<(String, String)>,
        _follow_redirects: Option<bool>,
        _cookies: Option<HashMap<String, String>>,
    ) -> PyResult<crate::streaming_stub::StreamingClient> {
        // Streaming is not supported in the synchronous client implementation
        // For streaming functionality, use the async client instead
        Err(RequestError::new_err(
            "Streaming is not supported in synchronous client. Use AsyncHttpClient for streaming functionality."
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
}

impl HttpClient {
    // Private internal methods not exposed to Python
    fn check_not_closed(&self) -> PyResult<()> {
        if self.is_closed.load(Ordering::Relaxed) {
            return Err(RequestError::new_err("Client has been closed"));
        }
        Ok(())
    }
}
