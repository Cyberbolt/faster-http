use crate::client::hyper_client::HyperHttpClient;
use crate::config::ClientConfig;
use crate::models::HttpRequest;
use pyo3::prelude::*;
use pyo3_asyncio::tokio::future_into_py;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

use crate::auth::extract_auth;
use crate::core::core::{build_and_send_request, send_request_direct};
use crate::core::error::RequestError;
// Removed unused import build_url_with_python_params

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

        // Handle cookies - convert to Cookie header like httpx does
        if !final_cookies.is_empty() {
            let cookie_header = final_cookies
                .iter()
                .map(|(k, v)| format!("{}={}", k, v))
                .collect::<Vec<_>>()
                .join("; ");
            final_headers.insert("Cookie".to_string(), cookie_header);
        }

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

        // Optimization: Minimize cloning by extracting only what we need
        let client = self.client.clone();
        let config = self.config.clone();

        // Pre-extract data with minimal cloning
        let method = request.method_str().to_string();
        let url = request.url_str().to_string();
        let headers = request.headers_map().clone();

        // Use move for content to avoid cloning if possible
        let content_bytes = request.content_bytes().map(|b| b.to_vec());

        future_into_py(py, async move {
            send_request_direct(
                &client,
                &method,
                &url,
                &headers,
                content_bytes.as_deref(),
                &config,
                None, // Use config default timeout for performance
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
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
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
        auth: Option<PyObject>,
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
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
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
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
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
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
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
        auth: Option<PyObject>,
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
        auth: Option<PyObject>,
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
        auth: Option<PyObject>,
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
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<crate::stubs::streaming_stub::StreamingClient> {
        use crate::stubs::streaming_stub::StreamingClient;

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
        // Handle both client-level auth and request-level auth
        let final_auth = if let Some(auth_obj) = auth {
            // Request-level auth takes priority
            crate::auth::extract_auth_from_object(&auth_obj)?
        } else {
            // Use client-level auth as fallback
            self.config.auth.clone()
        };

        // Convert auth to tuple format for StreamingClient
        let auth_option = extract_auth(&final_auth);
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
    pub fn event_hooks(&self) -> PyResult<crate::utils::hooks::EventHooksProxy> {
        Ok(crate::utils::hooks::EventHooksProxy::new(
            self.config.event_hooks.clone(),
        ))
    }

    #[getter]
    pub fn follow_redirects(&self) -> bool {
        self.config.follow_redirects
    }

    // Connection pool monitoring methods
    pub fn get_connection_stats(&self) -> PyResult<std::collections::HashMap<String, f64>> {
        self.check_not_closed()?;

        // Get statistics from the underlying hyper client's connection pool
        match self.client.get_connection_stats() {
            Ok(stats) => Ok(stats),
            Err(_) => {
                // Fallback: provide basic stats if pool stats aren't available
                let mut fallback_stats = std::collections::HashMap::new();
                fallback_stats.insert("client_type".to_string(), 1.0); // 1 = async
                fallback_stats.insert("health_score".to_string(), 1.0);
                fallback_stats.insert("total_requests".to_string(), 0.0);
                fallback_stats.insert("failed_requests".to_string(), 0.0);
                fallback_stats.insert("success_rate".to_string(), 1.0);
                Ok(fallback_stats)
            }
        }
    }

    pub fn is_connection_healthy(&self) -> PyResult<bool> {
        self.check_not_closed()?;

        // Check health from the underlying hyper client's connection pool
        match self.client.is_connection_healthy() {
            Ok(healthy) => Ok(healthy),
            Err(_) => Ok(true), // Fallback: assume healthy if can't check
        }
    }

    pub fn cleanup_connections<'p>(&self, py: Python<'p>) -> PyResult<&'p PyAny> {
        self.check_not_closed()?;

        // Use pyo3_asyncio to wrap the async function
        let client = self.client.clone();
        future_into_py(py, async move {
            // Force cleanup of idle connections in the connection pool
            match client.cleanup_connections().await {
                Ok(_) => Ok(()),
                Err(e) => Err(RequestError::new_err(format!(
                    "Failed to cleanup connections: {}",
                    e
                ))),
            }
        })
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

    /// Header merging for request processing
    fn merge_headers_standard(
        &self,
        request_headers: Option<HashMap<String, String>>,
    ) -> HashMap<String, String> {
        match request_headers {
            Some(req_headers) if !self.config.default_headers.is_empty() => {
                let mut merged =
                    HashMap::with_capacity(self.config.default_headers.len() + req_headers.len());
                merged.extend(
                    self.config
                        .default_headers
                        .iter()
                        .map(|(k, v)| (k.clone(), v.clone())),
                );
                merged.extend(req_headers);
                merged
            }
            Some(req_headers) => req_headers,
            None => self.config.default_headers.clone(),
        }
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
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<PyObject>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self.check_not_closed()?;

        // Try direct send path first for simple requests
        if data.is_none()
            && json.is_none()
            && files.is_none()
            && auth.is_none()
            && follow_redirects.is_none()
        {
            // Direct path: Send request with standard processing
            let client = self.client.clone();
            let method_owned = method.to_string();
            let headers_merged = self.merge_headers_standard(headers);
            let effective_timeout = timeout
                .map(Duration::from_secs_f64)
                .or(self.config.default_timeout);

            // Build full URL with base_url if needed
            let full_url = if let Some(base) = &self.config.base_url {
                if url.starts_with("http://") || url.starts_with("https://") {
                    url
                } else {
                    format!(
                        "{}/{}",
                        base.trim_end_matches('/'),
                        url.trim_start_matches('/')
                    )
                }
            } else {
                url
            };

            let config = self.config.clone();
            return future_into_py(py, async move {
                crate::core::core::send_request_direct(
                    &client,
                    &method_owned,
                    &full_url,
                    &headers_merged,
                    content.as_deref(),
                    &config,
                    effective_timeout.map(|d| d.as_secs_f64()),
                )
                .await
            });
        }

        // FALLBACK: Full processing path

        // Optimization: Pre-extract needed config values to minimize cloning
        let base_url = self.config.base_url.clone();
        let default_headers = self.config.default_headers.clone();
        let default_timeout = self.config.default_timeout;
        let config_follow_redirects = self.config.follow_redirects;

        // Merge default params with request params (optimize with capacity pre-allocation)
        let merged_params = if let Some(request_params) = params {
            let mut merged =
                HashMap::with_capacity(self.config.default_params.len() + request_params.len());
            merged.extend(
                self.config
                    .default_params
                    .iter()
                    .map(|(k, v)| (k.clone(), v.clone())),
            );
            merged.extend(request_params);
            Some(merged)
        } else if !self.config.default_params.is_empty() {
            Some(self.config.default_params.clone())
        } else {
            None
        };

        // Cookie merge with memory management
        let merged_cookies = {
            let default_cookies = &self.config.default_cookies;
            let jar_cookies_opt = self.config.cookie_jar.lock().ok().map(|jar| jar.clone());

            match (default_cookies.is_empty(), jar_cookies_opt, cookies) {
                (true, None, None) => None,
                (true, None, Some(req_cookies)) => Some(req_cookies),
                (false, jar_opt, cookies_opt) => {
                    let total_capacity = default_cookies.len()
                        + jar_opt.as_ref().map_or(0, |j| j.len())
                        + cookies_opt.as_ref().map_or(0, |c| c.len());
                    let mut merged = HashMap::with_capacity(total_capacity);

                    // Add in priority order: default -> jar -> request
                    merged.extend(default_cookies.iter().map(|(k, v)| (k.clone(), v.clone())));
                    if let Some(jar_cookies) = jar_opt {
                        merged.extend(jar_cookies);
                    }
                    if let Some(request_cookies) = cookies_opt {
                        merged.extend(request_cookies);
                    }
                    Some(merged)
                }
                (true, Some(jar_cookies), cookies_opt) => {
                    if let Some(request_cookies) = cookies_opt {
                        let mut merged =
                            HashMap::with_capacity(jar_cookies.len() + request_cookies.len());
                        merged.extend(jar_cookies);
                        merged.extend(request_cookies);
                        Some(merged)
                    } else {
                        Some(jar_cookies)
                    }
                }
            }
        };

        // Handle both client-level auth and request-level auth
        let final_auth = if let Some(auth_obj) = auth {
            // Request-level auth takes priority
            crate::auth::extract_auth_from_object(&auth_obj)?
        } else {
            // Use client-level auth as fallback
            self.config.auth.clone()
        };

        // Convert auth to tuple format for hyper client
        let auth_option = extract_auth(&final_auth);
        let follow_redirects = follow_redirects.unwrap_or(config_follow_redirects);

        // Optimization: Clone only essential config data instead of entire config
        let method_owned = method.to_string();
        let config = self.config.clone(); // Still need full config for build_and_send_request

        future_into_py(py, async move {
            // Don't pass base_url if URL is already absolute (prevents double URL building)
            let base_url_param = if url.starts_with("http://") || url.starts_with("https://") {
                &None
            } else {
                &base_url
            };

            build_and_send_request(
                &config,
                &method_owned,
                &url,
                content,
                data,
                json,
                files,
                merged_params,
                headers,
                timeout,
                base_url_param,
                &default_headers,
                default_timeout,
                auth_option,
                follow_redirects,
                merged_cookies,
            )
            .await
        })
    }
}
