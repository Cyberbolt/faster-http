// Synchronous HTTP client implementation using hyper with tokio runtime
use pyo3::prelude::*;
use std::collections::HashMap;
use crate::config::ClientConfig;
use crate::response::HttpResponse;
use crate::hyper_client::{HyperHttpClient, HyperClientConfig};
use crate::core::{build_and_send_request, send_request_direct};
use std::sync::OnceLock;
use tokio::runtime::Runtime;
use std::time::Duration;
use pyo3_asyncio;

/// Safe runtime management for synchronous operations
/// Returns a reference to the shared runtime when safe, or creates a temporary one
fn get_shared_runtime() -> PyResult<&'static Runtime> {
    use crate::error::RuntimeInitFailed;
    
    static SHARED_RUNTIME: OnceLock<Result<Runtime, String>> = OnceLock::new();
    
    let result = SHARED_RUNTIME.get_or_init(|| {
        tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .thread_name("faster-http-shared")
            .worker_threads(2) // Limit threads to avoid resource conflicts
            .build()
            .map_err(|e| format!("Failed to create shared runtime: {}", e))
    });
    
    match result {
        Ok(runtime) => Ok(runtime),
        Err(msg) => Err(RuntimeInitFailed::new_err(msg.clone()))
    }
}

/// Execute async operation in a runtime-safe manner with simplified logic
/// Uses the global shared runtime to avoid context issues
pub fn execute_in_runtime<F, T>(future: F) -> PyResult<T>
where
    F: std::future::Future<Output = PyResult<T>> + Send + 'static,
    T: Send + 'static,
{
    // Use the global shared runtime to maintain connection pool state
    // This ensures the same runtime context as the connection pool
    let runtime = get_shared_runtime()?;
    runtime.block_on(future)
}

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
        // Convert ClientConfig to HyperClientConfig
        let hyper_config = HyperClientConfig {
            follow_redirects: config.follow_redirects,
            max_redirects: config.max_redirects as usize,
            timeout: config.default_timeout,
            http1_only: config.http1,
            http2_only: config.http2,
        };

        // Create the hyper client
        let client = HyperHttpClient::new(hyper_config)?;

        Ok(Self { client, config })
    }

    /// Send a request using the synchronous client (blocking wrapper around async client)
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
        // Create a clone of the config to move into the async block
        let config = self.config.clone();

        // Convert timeout to Duration if provided
        let timeout_duration = timeout.map(Duration::from_secs_f64);

        // Convert borrowed strings to owned strings for async block
        let method_owned = method.to_string();
        let url_owned = url.to_string();
        
        // Execute the async operation in a runtime-safe manner
        execute_in_runtime(async move {
            build_and_send_request(
                &config,
                &method_owned,
                &url_owned,
                content,
                data.and_then(|obj| {
                    Python::with_gil(|py| {
                        // Convert PyObject to HashMap for data parameter
                        obj.extract::<HashMap<String, PyObject>>(py).ok()
                    })
                }),
                json.and_then(|obj| {
                    Python::with_gil(|py| {
                        // Convert PyObject to HashMap for json parameter  
                        obj.extract::<HashMap<String, PyObject>>(py).ok()
                    })
                }),
                files.and_then(|obj| {
                    Python::with_gil(|py| {
                        // Convert PyObject to HashMap for files parameter
                        obj.extract::<HashMap<String, PyObject>>(py).ok()
                    })
                }),
                params,
                headers,
                timeout,
                &config.base_url,
                &config.default_headers,
                config.default_timeout.or(timeout_duration),
                auth,
                follow_redirects.unwrap_or(config.follow_redirects),
                cookies,
            ).await
        })
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
        
        // Execute the async operation in a runtime-safe manner
        execute_in_runtime(async move {
            send_request_direct(&client, &method_owned, &url_owned, &headers, content.as_deref(), &config).await
        })
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
    /// Create a new SyncHttpClient with the provided config (internal use)
    pub fn new_with_config(config: ClientConfig) -> PyResult<Self> {
        // Convert ClientConfig to HyperClientConfig
        let hyper_config = HyperClientConfig {
            follow_redirects: config.follow_redirects,
            max_redirects: config.max_redirects as usize,
            timeout: config.default_timeout,
            http1_only: config.http1,
            http2_only: config.http2,
        };

        // Create the hyper client
        let client = HyperHttpClient::new(hyper_config)?;

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