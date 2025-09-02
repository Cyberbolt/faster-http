// Complete streaming HTTP client implementation for hyper - httpx compatible
use crate::client::hyper_client::{HyperClientConfig, HyperHttpClient};
use crate::config::ClientConfig;
use crate::core::error::RequestError;
use crate::models::HttpResponse;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex, OnceLock};
use tokio::runtime::Runtime;

/// Simplified runtime management for streaming operations
/// Uses the same runtime as sync_core for consistency and simplicity
#[allow(dead_code)]
fn execute_streaming_async<F, T>(future: F) -> PyResult<T>
where
    F: std::future::Future<Output = PyResult<T>> + Send + 'static,
    T: Send + 'static,
{
    use crate::core::error::RuntimeInitFailed;

    // Use shared streaming runtime for all operations
    // This avoids complex nested runtime detection
    static STREAMING_RUNTIME: OnceLock<Result<Runtime, String>> = OnceLock::new();

    let result = STREAMING_RUNTIME.get_or_init(|| {
        tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .thread_name("faster-http-streaming")
            .build() // Use default configuration for optimal performance
            .map_err(|e| format!("Failed to create streaming runtime: {}", e))
    });

    let runtime = match result {
        Ok(runtime) => runtime,
        Err(msg) => return Err(RuntimeInitFailed::new_err(msg.clone())),
    };

    runtime.block_on(future)
}

/// Global streaming client pool for reusing connections - safe implementation
#[allow(dead_code)]
static STREAMING_CLIENT_POOL: OnceLock<Result<Arc<Mutex<HyperHttpClient>>, String>> =
    OnceLock::new();

/// Get or create the global shared streaming client for efficiency
/// Uses safe OnceLock pattern without unsafe code
#[allow(dead_code)]
fn get_shared_streaming_client() -> PyResult<Arc<Mutex<HyperHttpClient>>> {
    let result = STREAMING_CLIENT_POOL.get_or_init(|| {
        let config = HyperClientConfig {
            follow_redirects: true,
            max_redirects: 20,
            timeout: None,
            http1_only: false,
            http2_only: false,
        };

        // Try primary config first, then fallback to default
        match HyperHttpClient::new(config)
            .or_else(|_| HyperHttpClient::new(HyperClientConfig::default()))
        {
            Ok(client) => Ok(Arc::new(Mutex::new(client))),
            Err(e) => Err(format!("Failed to create streaming client: {}", e)),
        }
    });

    match result {
        Ok(client) => Ok(client.clone()),
        Err(msg) => Err(RequestError::new_err(msg.clone())),
    }
}

#[pyclass(module = "faster_http")]
pub struct StreamingClient {
    config: ClientConfig,
    method: String,
    url: String,
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: bool,
    cookies: Option<HashMap<String, String>>,
    // Streaming state
    response: Option<HttpResponse>,
    _is_closed: bool,
    _content_consumed: bool,
}

impl StreamingClient {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        config: ClientConfig,
        method: String,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<PyObject>,
        json: Option<HashMap<String, PyObject>>,
        files: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, PyObject>>,
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
            response: None,
            _is_closed: false,
            _content_consumed: false,
        }
    }
}

#[pymethods]
impl StreamingClient {
    /// Context manager protocol - enter
    fn __enter__(mut slf: PyRefMut<'_, Self>) -> PyResult<PyRefMut<'_, Self>> {
        // Execute request immediately when entering context using synchronous execution
        // This avoids async runtime conflicts and timeout issues

        // Prepare data for synchronous execution
        let config = slf.config.clone();
        let method = slf.method.clone();
        let url = slf.url.clone();
        let content = slf.content.clone();
        let json = slf.json.clone();
        let files = slf.files.clone();
        let params = slf.params.clone();
        let headers = slf.headers.clone();
        let timeout = slf.timeout;
        let auth = slf.auth.clone();
        let follow_redirects = slf.follow_redirects;
        let cookies = slf.cookies.clone();

        // Data is already Option<PyObject>, no conversion needed
        let data_obj = slf.data.clone();

        // Build request using Builder pattern to eliminate parameter complexity
        let mut builder = crate::core::api::HttpRequestBuilder::new()
            .with_follow_redirects(follow_redirects)
            .with_verify(true) // Default verify value
            .with_timeout(timeout.unwrap_or(5.0));

        if let Some(c) = content {
            builder = builder.with_content(c);
        }
        if let Some(d) = data_obj {
            builder = builder.with_data(d);
        }
        if let Some(j) = json {
            builder = builder.with_json(j);
        }
        if let Some(f) = files {
            builder = builder.with_files(f);
        }
        if let Some(p) = params {
            builder = builder.with_params(p);
        }
        if let Some(h) = headers {
            builder = builder.with_headers(Python::with_gil(|py| h.to_object(py)));
        }
        if let Some(c) = cookies {
            builder = builder.with_cookies(c);
        }
        if let Some(a) = auth {
            builder = builder.with_auth(Python::with_gil(|py| a.to_object(py)));
        }

        // Execute request using synchronous client to avoid async runtime issues
        let response =
            crate::core::api::execute_request_with_sync_client(&config, &method, &url, builder)?;

        slf.response = Some(response);
        slf._is_closed = false;
        slf._content_consumed = false;

        Ok(slf)
    }

    /// Context manager protocol - exit
    fn __exit__(
        &mut self,
        _exc_type: Option<PyObject>,
        _exc_val: Option<PyObject>,
        _exc_tb: Option<PyObject>,
    ) -> PyResult<bool> {
        // Clean up when exiting context
        self.close()?;
        Ok(false)
    }

    /// Close the streaming response
    fn close(&mut self) -> PyResult<()> {
        self._is_closed = true;
        self.response = None;
        Ok(())
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

    /// Check if response is ready and not closed
    #[getter]
    pub fn is_ready(&self) -> bool {
        self.response.is_some() && !self._is_closed
    }

    /// Check if streaming client is closed - httpx compatible
    #[getter]
    pub fn is_closed(&self) -> bool {
        self._is_closed
    }

    /// Get status code - httpx compatible
    #[getter]
    pub fn status_code(&self) -> PyResult<u16> {
        match &self.response {
            Some(resp) => Ok(resp.status_code()),
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Get headers - httpx compatible
    #[getter]
    pub fn headers(&self) -> PyResult<crate::models::HttpHeaders> {
        match &self.response {
            Some(resp) => Ok(resp.headers()),
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Get URL object - httpx compatible
    #[getter]
    pub fn url_obj(&self) -> PyResult<crate::models::HttpUrl> {
        match &self.response {
            Some(resp) => resp.url(),
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Get elapsed time - httpx compatible
    #[getter]
    pub fn elapsed(&self) -> PyResult<PyObject> {
        match &self.response {
            Some(resp) => resp.elapsed(),
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Check if response is successful (2xx status code) - httpx compatible
    #[getter]
    pub fn is_success(&self) -> PyResult<bool> {
        match &self.response {
            Some(resp) => Ok(resp.is_success()),
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Conditionally read the full response body - httpx stream compatible
    fn read(&mut self) -> PyResult<Vec<u8>> {
        if self._is_closed {
            return Err(RequestError::new_err("Cannot read from closed stream"));
        }

        match &self.response {
            Some(resp) => {
                self._content_consumed = true;
                Python::with_gil(|py| {
                    let content_obj = resp.content(py)?;
                    content_obj.extract::<Vec<u8>>(py)
                })
            }
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Get text content (only after read() has been called) - httpx compatible
    #[getter]
    fn text(&self) -> PyResult<String> {
        if !self._content_consumed {
            return Err(RequestError::new_err(
                "Response content not loaded. Call read() first to access text.",
            ));
        }

        match &self.response {
            Some(resp) => resp.text(),
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Get binary content (only after read() has been called) - httpx compatible
    #[getter]
    fn content(&self) -> PyResult<Vec<u8>> {
        if !self._content_consumed {
            return Err(RequestError::new_err(
                "Response content not loaded. Call read() first to access content.",
            ));
        }

        match &self.response {
            Some(resp) => Python::with_gil(|py| {
                let content_obj = resp.content(py)?;
                content_obj.extract::<Vec<u8>>(py)
            }),
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Stream response content as bytes - httpx iter_bytes() compatible
    fn iter_bytes(&self, chunk_size: Option<usize>) -> PyResult<StreamingIterator> {
        if self._is_closed {
            return Err(crate::core::error::StreamError::new_err(
                "Cannot iterate over closed stream",
            ));
        }

        match &self.response {
            Some(resp) => {
                let content = Python::with_gil(|py| {
                    let content_obj = resp.content(py)?;
                    content_obj.extract::<Vec<u8>>(py)
                })?;

                Ok(StreamingIterator::new(
                    content,
                    chunk_size.unwrap_or(8192),
                    StreamingMode::Bytes,
                ))
            }
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Stream response content as text - httpx iter_text() compatible
    fn iter_text(&self, chunk_size: Option<usize>) -> PyResult<StreamingIterator> {
        if self._is_closed {
            return Err(crate::core::error::StreamError::new_err(
                "Cannot iterate over closed stream",
            ));
        }

        match &self.response {
            Some(resp) => {
                let text_content = resp.text()?;
                let content = text_content.into_bytes();

                Ok(StreamingIterator::new(
                    content,
                    chunk_size.unwrap_or(8192),
                    StreamingMode::Text,
                ))
            }
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Stream response content line by line - httpx iter_lines() compatible
    fn iter_lines(&self) -> PyResult<StreamingIterator> {
        if self._is_closed {
            return Err(crate::core::error::StreamError::new_err(
                "Cannot iterate over closed stream",
            ));
        }

        match &self.response {
            Some(resp) => {
                let text_content = resp.text()?;
                let content = text_content.into_bytes();

                Ok(StreamingIterator::new(
                    content,
                    0, // Not used for lines mode
                    StreamingMode::Lines,
                ))
            }
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Stream raw response bytes - httpx iter_raw() compatible
    fn iter_raw(&self, chunk_size: Option<usize>) -> PyResult<StreamingIterator> {
        if self._is_closed {
            return Err(crate::core::error::StreamError::new_err(
                "Cannot iterate over closed stream",
            ));
        }

        match &self.response {
            Some(resp) => {
                let content = Python::with_gil(|py| {
                    let content_obj = resp.content(py)?;
                    content_obj.extract::<Vec<u8>>(py)
                })?;

                Ok(StreamingIterator::new(
                    content,
                    chunk_size.unwrap_or(8192),
                    StreamingMode::Raw,
                ))
            }
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// JSON parsing support - httpx compatible
    fn json(&self) -> PyResult<PyObject> {
        if !self._content_consumed {
            return Err(RequestError::new_err(
                "Response content not loaded. Call read() first to access json.",
            ));
        }

        match &self.response {
            Some(resp) => Python::with_gil(|py| resp.json(py)),
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }

    /// Raise for HTTP status errors - httpx compatible
    fn raise_for_status(&self) -> PyResult<()> {
        match &self.response {
            Some(resp) => resp.raise_for_status(),
            None => Err(RequestError::new_err(
                "Response not available - use within 'with' statement",
            )),
        }
    }
}

#[derive(Clone)]
enum StreamingMode {
    Bytes,
    Text,
    Lines,
    Raw,
}

#[pyclass(module = "faster_http")]
pub struct StreamingIterator {
    content: Vec<u8>,
    chunk_size: usize,
    position: usize,
    mode: StreamingMode,
    lines: Option<Vec<String>>,
    line_position: usize,
}

impl StreamingIterator {
    fn new(content: Vec<u8>, chunk_size: usize, mode: StreamingMode) -> Self {
        let lines = if matches!(mode, StreamingMode::Lines) {
            let text = String::from_utf8_lossy(&content);
            Some(text.lines().map(|s| s.to_string()).collect())
        } else {
            None
        };

        Self {
            content,
            chunk_size,
            position: 0,
            mode,
            lines,
            line_position: 0,
        }
    }
}

#[pymethods]
impl StreamingIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self) -> PyResult<Option<PyObject>> {
        match &self.mode {
            StreamingMode::Lines => {
                if let Some(lines) = &self.lines {
                    if self.line_position < lines.len() {
                        let line = lines[self.line_position].clone();
                        self.line_position += 1;
                        return Python::with_gil(|py| Ok(Some(line.to_object(py))));
                    }
                }
                Ok(None)
            }
            StreamingMode::Bytes | StreamingMode::Text | StreamingMode::Raw => {
                if self.position >= self.content.len() {
                    return Ok(None);
                }

                let end = std::cmp::min(self.position + self.chunk_size, self.content.len());
                let chunk = &self.content[self.position..end];
                self.position = end;

                Python::with_gil(|py| {
                    match &self.mode {
                        StreamingMode::Text => {
                            let text = String::from_utf8_lossy(chunk);
                            Ok(Some(text.to_string().to_object(py)))
                        }
                        StreamingMode::Bytes | StreamingMode::Raw => {
                            // Create proper Python bytes object instead of list
                            Ok(Some(pyo3::types::PyBytes::new(py, chunk).to_object(py)))
                        }
                        StreamingMode::Lines => {
                            // This should not happen in this branch, but handle gracefully
                            Ok(None)
                        }
                    }
                })
            }
        }
    }
}
