use pyo3::prelude::*;
// PyCell import removed as it's not used in this file
use crate::auth::extract_auth;
use crate::config::ClientConfig;
use crate::core::{build_and_send_request, send_request};
use crate::error::RequestError;
use crate::request::HttpRequest;
use crate::response::HttpResponse;
use crate::runtime::get_global_runtime;
use crate::utils::build_url;
use reqwest::Client;
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

// Synchronous HTTP client
#[pyclass]
pub struct HttpClient {
    client: Client,
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
        params: Option<HashMap<String, String>>,
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
        let client = config.build_client(None)?;

        Ok(HttpClient {
            client,
            config,
            is_closed: AtomicBool::new(false),
        })
    }

    // Build request object - delegate URL processing to reqwest
    #[allow(clippy::too_many_arguments)]
    pub fn build_request(
        &self,
        method: &str,
        url: &str,
        params: Option<HashMap<String, String>>,
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
        let final_url = build_url(url, self.config.base_url.as_ref(), Some(&final_params))
            .map_err(RequestError::new_err)?;

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

    // Send pre-built request
    pub fn send(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        self.check_not_closed()?;
        let rt = get_global_runtime();
        rt.block_on(send_request(&self.client, request, &self.config))
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

    // Expose event_hooks for httpx compatibility
    #[getter]
    pub fn event_hooks(&self) -> PyResult<crate::hooks::EventHooksProxy> {
        Ok(crate::hooks::EventHooksProxy::new(
            self.config.event_hooks.clone(),
        ))
    }

    // Generic request method to reduce code duplication
    #[allow(clippy::too_many_arguments)]
    fn _request(
        &self,
        method: &str,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
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

        // Simple cookie merging - delegate actual cookie handling to reqwest
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

        // Note: Event hooks are now handled in Python layer to avoid GIL conflicts

        // Execute the actual request
        let rt = get_global_runtime();
        let response = rt.block_on(build_and_send_request(
            &self.config,
            method,
            url,
            content,
            data,
            json,
            files,
            merged_params,
            headers,
            timeout,
            &self.config.base_url,
            &self.config.default_headers,
            self.config.default_timeout,
            auth_option,
            follow_redirects,
            merged_cookies,
        ))?;

        // Note: Event hooks are now handled in Python layer to avoid GIL conflicts

        Ok(response)
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
        params: Option<HashMap<String, String>>,
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
        params: Option<HashMap<String, String>>,
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
        params: Option<HashMap<String, String>>,
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
        params: Option<HashMap<String, String>>,
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
        params: Option<HashMap<String, String>>,
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
        params: Option<HashMap<String, String>>,
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
        params: Option<HashMap<String, String>>,
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
        params: Option<HashMap<String, String>>,
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
        method: &str,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<crate::streaming::StreamingHttpResponse> {
        use crate::core::build_and_send_streaming_request;

        self.check_not_closed()?;
        let rt = get_global_runtime();

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

        rt.block_on(build_and_send_streaming_request(
            &self.config,
            method,
            url,
            content,
            data,
            json,
            files,
            params,
            headers,
            timeout,
            &self.config.base_url,
            &self.config.default_headers,
            self.config.default_timeout,
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
    pub fn params(&self) -> HashMap<String, String> {
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
