// Streaming HTTP client implementation for hyper
use pyo3::prelude::*;
use std::collections::HashMap;
use crate::config::ClientConfig;
use crate::hyper_client::{HyperHttpClient, HyperClientConfig};
use crate::response::HttpResponse;
use crate::error::RequestError;
use crate::core::build_and_send_request;
use std::sync::OnceLock;
use tokio::runtime::Runtime;

/// Global tokio runtime for streaming operations
static STREAMING_RUNTIME: OnceLock<Runtime> = OnceLock::new();

/// Get or create the global tokio runtime for streaming operations
fn get_streaming_runtime() -> &'static Runtime {
    STREAMING_RUNTIME.get_or_init(|| {
        tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .thread_name("faster-http-streaming")
            .build()
            .expect("Failed to create tokio runtime for streaming operations")
    })
}

#[pyclass(module = "faster_http")]
pub struct StreamingClient {
    config: ClientConfig,
    method: String,
    url: String,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: bool,
    cookies: Option<HashMap<String, String>>,
    client: Option<HyperHttpClient>,
}

impl StreamingClient {
    pub fn new(
        config: ClientConfig,
        method: String,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: bool,
        cookies: Option<HashMap<String, String>>,
    ) -> Self {
        Self {
            config,
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
            client: None,
        }
    }
}

#[pymethods]
impl StreamingClient {
    /// Context manager protocol - enter
    fn __enter__(mut slf: PyRefMut<'_, Self>) -> PyResult<PyRefMut<'_, Self>> {
        // Initialize the hyper client when entering context
        let hyper_config = HyperClientConfig {
            follow_redirects: slf.config.follow_redirects,
            max_redirects: slf.config.max_redirects as usize,
            timeout: slf.config.default_timeout,
            http1_only: slf.config.http1,
            http2_only: slf.config.http2,
        };

        let client = HyperHttpClient::new(hyper_config)?;
        slf.client = Some(client);
        
        Ok(slf)
    }

    /// Context manager protocol - exit
    fn __exit__(
        &mut self,
        _exc_type: Option<PyObject>,
        _exc_val: Option<PyObject>,
        _exc_tb: Option<PyObject>,
    ) -> PyResult<bool> {
        // Clean up the client when exiting context
        self.client = None;
        Ok(false)
    }

    /// Execute the streaming request and return response
    pub fn send(&self) -> PyResult<HttpResponse> {
        if self.client.is_none() {
            return Err(RequestError::new_err(
                "StreamingClient must be used as a context manager (use 'with' statement)"
            ));
        }

        let runtime = get_streaming_runtime();
        
        // Clone necessary data for the async block
        let config = self.config.clone();
        let method = self.method.clone();
        let url = self.url.clone();
        let content = self.content.clone();
        let data = self.data.clone();
        let json = self.json.clone();
        let files = self.files.clone();
        let params = self.params.clone();
        let headers = self.headers.clone();
        let timeout = self.timeout;
        let auth = self.auth.clone();
        let follow_redirects = self.follow_redirects;
        let cookies = self.cookies.clone();

        // Execute the async operation synchronously
        runtime.block_on(async move {
            build_and_send_request(
                &config,
                &method,
                &url,
                content,
                data,
                json,
                files,
                params,
                headers,
                timeout,
                &config.base_url,
                &config.default_headers,
                config.default_timeout,
                auth,
                follow_redirects,
                cookies,
            ).await
        })
    }

    /// Get the configured method
    #[getter]
    pub fn method(&self) -> String {
        self.method.clone()
    }

    /// Get the configured URL
    #[getter]
    pub fn url(&self) -> String {
        self.url.clone()
    }

    /// Check if client is ready (has been entered)
    #[getter]
    pub fn is_ready(&self) -> bool {
        self.client.is_some()
    }
}

#[pyclass(module = "faster_http")]
pub struct StreamingHttpResponse {
    // For future implementation of actual streaming response
    response: HttpResponse,
}

#[pymethods]
impl StreamingHttpResponse {
    #[new]
    pub fn new(response: HttpResponse) -> Self {
        Self { response }
    }

    /// Delegate common response properties to the underlying response
    #[getter]
    pub fn status_code(&self) -> u16 {
        self.response.status_code()
    }

    #[getter]
    pub fn headers(&self) -> PyResult<HashMap<String, String>> {
        Ok(self.response.headers().to_hashmap())
    }

    #[getter]
    pub fn text(&self) -> PyResult<String> {
        self.response.text()
    }

    #[getter]
    pub fn content(&self) -> PyResult<Vec<u8>> {
        Python::with_gil(|py| {
            let content_obj = self.response.content(py)?;
            content_obj.extract::<Vec<u8>>(py)
        })
    }
}