use crate::config::ClientConfig;
use crate::core::error::RequestError;
use crate::models::{HttpRequest, HttpResponse};
use crate::utils::hooks::EventHooksProxy;
use pyo3::prelude::*;
// Removed async-related imports as we use synchronous ureq client
use crate::transport::ureq_client::{UreqClientConfig, UreqHttpClient};
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
    client: UreqHttpClient, // Use ureq for true synchronous operations
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

        // Build ureq-based synchronous client
        let ureq_config = UreqClientConfig {
            timeout: config.default_timeout,
            follow_redirects: config.follow_redirects,
            max_redirects: if config.max_redirects >= 0 {
                config.max_redirects as u32
            } else {
                20
            },
            verify: config.ssl_config.verify,
        };
        let client = UreqHttpClient::new(ureq_config)?;

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
        cookies: Option<HashMap<String, String>>,
        #[allow(unused_variables)] timeout: Option<f64>,
        #[allow(unused_variables)] extensions: Option<HashMap<String, PyObject>>,
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
            Some(&final_params),
        )?;

        // Simple header merging
        let mut final_headers = self.config.default_headers.clone();
        if let Some(headers) = headers {
            final_headers.extend(headers);
        }

        // Merge cookies - same pattern as headers
        let mut final_cookies = self.config.default_cookies.clone();
        if let Some(request_cookies) = cookies {
            final_cookies.extend(request_cookies);
        }

        // Handle JSON serialization and content-type headers like HttpRequest::new does
        let mut final_content = content;
        if let Some(json_obj) = &json {
            Python::with_gil(|py| -> PyResult<()> {
                let json_module = py.import("json")?;
                let json_str = json_module
                    .call_method1("dumps", (json_obj,))?
                    .extract::<String>()?;
                final_content = Some(json_str.into_bytes());

                // Add JSON content-type header if not already present
                if !final_headers
                    .iter()
                    .any(|(k, _)| k.to_lowercase() == "content-type")
                {
                    final_headers
                        .insert("content-type".to_string(), "application/json".to_string());
                }

                Ok(())
            })?;
        }

        // Add content-length header if content is present
        if let Some(ref content_bytes) = final_content {
            final_headers.insert(
                "content-length".to_string(),
                content_bytes.len().to_string(),
            );
        }

        // Handle cookies - convert to Cookie header like httpx does
        if !final_cookies.is_empty() {
            let cookie_header = final_cookies
                .iter()
                .map(|(k, v)| format!("{}={}", k, v))
                .collect::<Vec<_>>()
                .join("; ");
            final_headers.insert("Cookie".to_string(), cookie_header);
        }

        // Use internal constructor but with processed content and headers
        Ok(HttpRequest::new_internal(
            method.to_string(),
            final_url,
            final_headers,
            final_content.map(|bytes| bytes.to_vec()),
            Some(final_params),
            Some(final_cookies),
            data,
            files,
            json,
            stream,
        ))
    }

    // Send pre-built request - using synchronous ureq client directly
    pub fn send(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        self.check_not_closed()?;

        // Extract request data
        let method = request.get_method();
        let url = request.get_url();
        let headers = Some(request.get_headers().clone());
        let content_bytes = request
            .get_content()
            .map(|b| bytes::Bytes::from(b.to_vec()));

        // Use ureq client directly (synchronous operation)
        self.client
            .request(method, url, headers, content_bytes, None)
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
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self.check_not_closed()?;

        // Handle both client-level auth and request-level auth
        let final_auth = if auth.is_some() {
            // Request-level auth takes priority
            crate::auth::extract_auth_from_object(&auth.unwrap())?
        } else {
            // Use client-level auth as fallback
            self.config.auth.clone()
        };

        // Convert auth to tuple format for ureq client
        let auth_tuple = crate::auth::extract_auth(&final_auth);

        // Merge cookies with cookie jar for session management
        let merged_cookies = {
            let mut merged = HashMap::new();

            // Add cookies from cookie jar (session cookies)
            if let Ok(jar) = self.config.cookie_jar.lock() {
                merged.extend(jar.clone());
            }

            // Add request-specific cookies (highest priority)
            if let Some(request_cookies) = cookies {
                merged.extend(request_cookies);
            }

            if !merged.is_empty() {
                Some(merged)
            } else {
                None
            }
        };

        // Use ureq client's full request method (follow_redirects is handled by ureq config)
        let response = self.client.send_request_full(
            method,
            url,
            content,
            data,
            json,
            files,
            params,
            headers,
            timeout,
            auth_tuple,
            merged_cookies,
            follow_redirects,
        )?;

        // Update cookie jar with Set-Cookie headers from response
        self.update_cookie_jar_from_response(&response);

        Ok(response)
    }

    /// Update cookie jar with Set-Cookie headers from response
    fn update_cookie_jar_from_response(&self, response: &crate::models::HttpResponse) {
        let headers_map = response.headers().to_hashmap();

        // Look for Set-Cookie headers (case-insensitive)
        for (key, value) in &headers_map {
            if key.to_lowercase() == "set-cookie" {
                // Parse the Set-Cookie header
                if let Some(cookie_pair) = value.split(';').next() {
                    if let Some((name, val)) = cookie_pair.split_once('=') {
                        let cookie_name = name.trim().to_string();
                        let cookie_value = val.trim().trim_matches('"').to_string();

                        // Update cookie jar
                        if let Ok(mut jar) = self.config.cookie_jar.lock() {
                            jar.insert(cookie_name, cookie_value);
                        }
                    }
                }
            }
        }
    }

    // Public request method for httpx compatibility
    #[allow(clippy::too_many_arguments)]
    pub fn request(
        &self,
        method: &str,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        // CRITICAL FIX: Merge default params with request params and build final URL
        let mut final_params = self.config.default_params.clone();
        if let Some(request_params) = params {
            final_params.extend(request_params);
        }

        // Use centralized URL building with merged params (same as build_request method)
        let final_url = crate::utils::build_url_with_python_params(
            url,
            self.config.base_url.as_ref(),
            Some(&final_params),
        )?;

        // Merge default headers with request headers
        let mut final_headers = self.config.default_headers.clone();
        if let Some(request_headers) = headers {
            final_headers.extend(request_headers);
        }

        // Merge default cookies with request cookies
        let mut final_cookies = self.config.default_cookies.clone();
        if let Some(request_cookies) = cookies {
            final_cookies.extend(request_cookies);
        }

        self._request(
            method,
            &final_url, // Use the properly resolved URL
            content,
            data,
            json,
            files,
            Some(final_params),  // Pass the final params
            Some(final_headers), // Pass the merged headers
            timeout,
            auth,
            follow_redirects,
            Some(final_cookies), // Pass the merged cookies
        )
    }

    #[allow(clippy::too_many_arguments)]
    pub fn get(
        &self,
        url: &str,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
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
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
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
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
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
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
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
        auth: Option<PyObject>,
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
        auth: Option<PyObject>,
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
        auth: Option<PyObject>,
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
        _data: Option<PyObject>,
        _json: Option<HashMap<String, PyObject>>,
        _files: Option<HashMap<String, PyObject>>,
        _params: Option<HashMap<String, String>>,
        _headers: Option<HashMap<String, String>>,
        _timeout: Option<f64>,
        _auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        _cookies: Option<HashMap<String, String>>,
    ) -> PyResult<crate::stubs::streaming_stub::StreamingClient> {
        use crate::stubs::streaming_stub::StreamingClient;

        self.check_not_closed()?;

        // Merge request cookies with client default cookies
        let merged_cookies = match _cookies {
            Some(request_cookies) => {
                let mut combined = self.config.default_cookies.clone();
                combined.extend(request_cookies);
                Some(combined)
            }
            None => {
                if !self.config.default_cookies.is_empty() {
                    Some(self.config.default_cookies.clone())
                } else {
                    None
                }
            }
        };

        // Convert _params from Option<HashMap<String, String>> to Option<HashMap<String, PyObject>>
        let converted_params = _params.map(|params_map| {
            Python::with_gil(|py| {
                params_map
                    .into_iter()
                    .map(|(k, v)| (k, v.to_object(py)))
                    .collect()
            })
        });

        // Use client's configuration and merge with request-specific parameters
        Ok(StreamingClient::new(
            self.config.clone(),
            _method.to_string(),
            _url.to_string(),
            _content,
            _data,
            _json,
            _files,
            converted_params,
            _headers,
            _timeout,
            _auth,
            follow_redirects.unwrap_or(self.config.follow_redirects),
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
    pub fn follow_redirects(&self) -> bool {
        self.config.follow_redirects
    }

    // Connection pool monitoring methods
    pub fn get_connection_stats(&self) -> PyResult<std::collections::HashMap<String, f64>> {
        // Return connection pool statistics for monitoring
        let mut stats = std::collections::HashMap::new();

        // For sync client, we use ureq which doesn't expose detailed pool stats
        // But we can provide basic health information
        stats.insert("client_type".to_string(), 0.0); // 0 = sync
        stats.insert("health_score".to_string(), 1.0); // Assume healthy for sync client
        stats.insert("total_requests".to_string(), 0.0); // ureq doesn't expose this
        stats.insert("failed_requests".to_string(), 0.0);
        stats.insert("success_rate".to_string(), 1.0);

        Ok(stats)
    }

    pub fn is_connection_healthy(&self) -> PyResult<bool> {
        // For sync client, always return true unless client is closed
        Ok(!self.is_closed.load(std::sync::atomic::Ordering::Relaxed))
    }

    pub fn cleanup_connections(&self) -> PyResult<()> {
        // For sync client (ureq), connections are managed automatically
        // This is a no-op but provided for API compatibility
        self.check_not_closed()?;
        Ok(())
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
