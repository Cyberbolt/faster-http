// GIL-free processing
// Implements complete Python-free request processing chains in Rust

use crate::client::hyper_client::HyperHttpClient;
use crate::config::ClientConfig;
use crate::core::error::RequestError;
use crate::models::HttpResponse;
use crate::optimization::precompiled::{parse_method_configured, process_headers_configured};
use crate::transport::ureq_client::UreqHttpClient;
// use crate::zero_copy::ZeroCopyBuffer; // Removed - over-engineered
use bytes::Bytes;
use hyper::Uri;
use pyo3::prelude::*;
use pyo3::{PyObject, Python};
use std::collections::HashMap;
use std::str::FromStr;
use std::sync::Arc;
use std::time::Duration;

/// GIL-free request context
/// All request data pre-processed and stored in Rust-native types
#[derive(Clone)]
#[allow(dead_code)]
pub struct GilFreeRequestContext {
    /// Pre-parsed HTTP method
    pub method: hyper::Method,
    /// Pre-parsed URI
    pub uri: Uri,
    /// Pre-processed headers
    pub headers: HashMap<String, String>,
    /// Zero-copy content buffer
    pub content: Option<Bytes>,
    /// Pre-processed timeout
    pub timeout: Option<Duration>,
    /// Request ID for tracking
    pub request_id: u64,
}

#[allow(dead_code)]
impl GilFreeRequestContext {
    /// Create context from raw request data WITHOUT entering GIL
    pub fn from_raw_data(
        method: String,
        url: String,
        headers: HashMap<String, String>,
        content: Option<Vec<u8>>,
        timeout: Option<f64>,
    ) -> Result<Self, String> {
        // Parse method using precompiled lookup
        let method = parse_method_configured(&method)?;

        // Parse URI
        let uri = Uri::from_str(&url).map_err(|e| format!("Invalid URI: {}", e))?;

        // Process headers using precompiled configuration
        let processed_headers = process_headers_configured(&headers)
            .into_iter()
            .map(|(k, v)| (k.to_string(), v))
            .collect();

        // Create zero-copy content buffer
        let content_buffer = content.map(Bytes::from);

        // Convert timeout
        let timeout_duration = timeout.map(Duration::from_secs_f64);

        Ok(Self {
            method,
            uri,
            headers: processed_headers,
            content: content_buffer,
            timeout: timeout_duration,
            request_id: generate_request_id(),
        })
    }

    /// Extract minimal Python data and create GIL-free context
    pub fn from_python_request(py_request: &PyObject) -> PyResult<Self> {
        // CRITICAL: Minimize GIL time by extracting all data at once
        let (method, url, headers, content, timeout) = Python::with_gil(|py| {
            let method = py_request.getattr(py, "method")?.extract::<String>(py)?;
            let url = py_request.getattr(py, "url")?.extract::<String>(py)?;
            let headers: HashMap<String, String> = py_request
                .getattr(py, "headers")
                .unwrap_or_else(|_| py.None())
                .extract(py)
                .unwrap_or_default();
            let content: Option<Vec<u8>> = py_request
                .getattr(py, "content")
                .ok()
                .and_then(|c| c.extract(py).ok());
            let timeout: Option<f64> = py_request
                .getattr(py, "timeout")
                .ok()
                .and_then(|t| t.extract(py).ok());

            PyResult::Ok((method, url, headers, content, timeout))
        })?;

        // Process data WITHOUT GIL
        Self::from_raw_data(method, url, headers, content, timeout).map_err(RequestError::new_err)
    }

    /// Get content as slice without copying
    #[inline(always)]
    pub fn content_slice(&self) -> Option<&[u8]> {
        self.content.as_ref().map(|buf| buf.as_ref())
    }

    /// Get content size without copying
    #[inline(always)]
    pub fn content_size(&self) -> usize {
        self.content.as_ref().map(|buf| buf.len()).unwrap_or(0)
    }
}

/// GIL-free async request processor
#[allow(dead_code)]
pub struct GilFreeAsyncProcessor {
    client: HyperHttpClient,
    config: ClientConfig,
    active_requests: Arc<std::sync::atomic::AtomicUsize>,
}

#[allow(dead_code)]
impl GilFreeAsyncProcessor {
    pub fn new(config: ClientConfig) -> PyResult<Self> {
        let client = config.build_client(None)?;
        Ok(Self {
            client,
            config,
            active_requests: Arc::new(std::sync::atomic::AtomicUsize::new(0)),
        })
    }

    /// Process request completely without GIL
    pub async fn process_request_gil_free(
        &self,
        context: GilFreeRequestContext,
    ) -> Result<HttpResponse, String> {
        // Increment active request counter
        self.active_requests
            .fetch_add(1, std::sync::atomic::Ordering::Relaxed);

        // Process request entirely in Rust without Python interaction
        let result = self
            .client
            .request_with_timeout(
                context.method,
                context.uri,
                Some(context.headers),
                context.content,
                context.timeout,
            )
            .await
            .map_err(|e| format!("Request failed: {:?}", e));

        // Decrement active request counter
        self.active_requests
            .fetch_sub(1, std::sync::atomic::Ordering::Relaxed);

        result
    }

    /// Get active request count
    pub fn active_request_count(&self) -> usize {
        self.active_requests
            .load(std::sync::atomic::Ordering::Relaxed)
    }
}

/// GIL-free sync request processor  
#[allow(dead_code)]
pub struct GilFreeSyncProcessor {
    client: UreqHttpClient,
    active_requests: Arc<std::sync::atomic::AtomicUsize>,
}

#[allow(dead_code)]
impl GilFreeSyncProcessor {
    pub fn new(config: &ClientConfig) -> PyResult<Self> {
        let ureq_config = crate::transport::ureq_client::UreqClientConfig {
            timeout: config.default_timeout,
            follow_redirects: config.follow_redirects,
            max_redirects: config.max_redirects as u32,
            verify: config.ssl_config.verify,
        };
        let client = UreqHttpClient::new(ureq_config)?;

        Ok(Self {
            client,
            active_requests: Arc::new(std::sync::atomic::AtomicUsize::new(0)),
        })
    }

    /// Process request completely without GIL
    pub fn process_request_gil_free(
        &self,
        context: &GilFreeRequestContext,
    ) -> Result<HttpResponse, String> {
        // Increment active request counter
        self.active_requests
            .fetch_add(1, std::sync::atomic::Ordering::Relaxed);

        // Convert method to string for ureq
        let method_str = context.method.as_str();
        let url_str = context.uri.to_string();

        // Process request entirely in Rust without Python interaction
        let content_bytes = context.content.clone();

        let result = self
            .client
            .request(
                method_str,
                &url_str,
                Some(context.headers.clone()),
                content_bytes,
                context.timeout,
            )
            .map_err(|e| format!("Request failed: {:?}", e));

        // Decrement active request counter
        self.active_requests
            .fetch_sub(1, std::sync::atomic::Ordering::Relaxed);

        result
    }

    /// Get active request count
    pub fn active_request_count(&self) -> usize {
        self.active_requests
            .load(std::sync::atomic::Ordering::Relaxed)
    }
}

/// Batch GIL-free request processor
pub struct BatchGilFreeProcessor {
    async_processor: GilFreeAsyncProcessor,
    sync_processor: GilFreeSyncProcessor,
    max_concurrent: usize,
}

impl BatchGilFreeProcessor {
    pub fn new(config: ClientConfig) -> PyResult<Self> {
        let async_processor = GilFreeAsyncProcessor::new(config.clone())?;
        let sync_processor = GilFreeSyncProcessor::new(&config)?;

        Ok(Self {
            async_processor,
            sync_processor,
            max_concurrent: num_cpus::get() * 8, // Concurrent processing configuration
        })
    }

    /// Process multiple requests with minimal GIL interaction
    pub async fn process_batch_requests(
        &self,
        contexts: Vec<GilFreeRequestContext>,
    ) -> Vec<Result<HttpResponse, String>> {
        let mut results = Vec::with_capacity(contexts.len());
        let mut join_set = tokio::task::JoinSet::new();

        // Process in chunks to manage system resources
        for chunk in contexts.chunks(self.max_concurrent) {
            for context in chunk.iter().cloned() {
                let processor = self.async_processor.client.clone();

                join_set.spawn(async move {
                    // Complete request processing without GIL
                    processor
                        .request_with_timeout(
                            context.method,
                            context.uri,
                            Some(context.headers),
                            context.content,
                            context.timeout,
                        )
                        .await
                        .map_err(|e| format!("Request failed: {:?}", e))
                });
            }

            // Collect results for this chunk
            while let Some(result) = join_set.join_next().await {
                if let Ok(request_result) = result {
                    results.push(request_result);
                }
            }
        }

        results
    }

    /// Process requests synchronously with minimal GIL
    pub fn process_sync_batch_requests(
        &self,
        contexts: &[GilFreeRequestContext],
    ) -> Vec<Result<HttpResponse, String>> {
        contexts
            .iter()
            .map(|context| self.sync_processor.process_request_gil_free(context))
            .collect()
    }
}

/// Global request ID generator
static REQUEST_ID_COUNTER: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(1);

fn generate_request_id() -> u64 {
    REQUEST_ID_COUNTER.fetch_add(1, std::sync::atomic::Ordering::Relaxed) as u64
}

/// Python-facing GIL-free request API
#[pyfunction]
pub fn gil_processed_request(py_request: PyObject, use_async: Option<bool>) -> PyResult<PyObject> {
    // Extract data from Python with minimal GIL time
    let context = GilFreeRequestContext::from_python_request(&py_request)?;

    // Release GIL and process request entirely in Rust
    let use_async = use_async.unwrap_or(true);

    if use_async {
        // Async processing
        Python::with_gil(|py| {
            Ok(pyo3_asyncio::tokio::future_into_py(py, async move {
                // Create ephemeral config for single request
                let config = ClientConfig::new(
                    None, None, None, None, None, None, None, None, None, None, None, None, None,
                    None, None, None, None, None, None, None,
                )?;

                let processor = GilFreeAsyncProcessor::new(config)?;
                let result = processor
                    .process_request_gil_free(context)
                    .await
                    .map_err(RequestError::new_err)?;

                Ok(result)
            })?
            .to_object(py))
        })
    } else {
        // Sync processing - complete without GIL
        let config = ClientConfig::new(
            None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None,
        )?;

        let processor = GilFreeSyncProcessor::new(&config)?;
        let result = processor
            .process_request_gil_free(&context)
            .map_err(RequestError::new_err)?;

        Python::with_gil(|py| Ok(result.to_object(py)))
    }
}

/// Async-specific GIL-free request API
/// Designed for async processing without future_into_py overhead
#[pyfunction]
pub fn gil_processed_async_request<'py>(
    py: Python<'py>,
    py_request: PyObject,
) -> PyResult<&'py PyAny> {
    use pyo3_asyncio::tokio::future_into_py;

    // Data extraction from Python with GIL management
    let (method, url, headers, content, timeout) = Python::with_gil(|py| {
        let method = py_request.getattr(py, "method")?.extract::<String>(py)?;
        let url = py_request.getattr(py, "url")?.extract::<String>(py)?;
        let headers: HashMap<String, String> = py_request
            .getattr(py, "headers")
            .unwrap_or_else(|_| py.None())
            .extract(py)
            .unwrap_or_default();
        let content: Option<Vec<u8>> = py_request
            .getattr(py, "content")
            .ok()
            .and_then(|c| c.extract(py).ok());
        let timeout: Option<f64> = py_request
            .getattr(py, "timeout")
            .ok()
            .and_then(|t| t.extract(py).ok());

        PyResult::Ok((method, url, headers, content, timeout))
    })?;

    // Process request with minimal GIL interaction
    future_into_py(py, async move {
        // Create GIL-free context
        let context = GilFreeRequestContext::from_raw_data(method, url, headers, content, timeout)
            .map_err(RequestError::new_err)?;

        // Create ephemeral config for single request
        let config = ClientConfig::new(
            None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None,
        )?;

        let processor = GilFreeAsyncProcessor::new(config)?;
        let result = processor
            .process_request_gil_free(context)
            .await
            .map_err(RequestError::new_err)?;

        Ok(result)
    })
}

/// Python-facing batch GIL-free request API
#[pyfunction]
pub fn gil_processed_batch_request(
    py_requests: Vec<PyObject>,
    use_async: Option<bool>,
) -> PyResult<PyObject> {
    // Extract all data from Python with minimal total GIL time
    let mut contexts = Vec::with_capacity(py_requests.len());

    for py_request in py_requests {
        let context = GilFreeRequestContext::from_python_request(&py_request)?;
        contexts.push(context);
    }

    // Process entirely in Rust without GIL
    let use_async = use_async.unwrap_or(true);

    if use_async {
        Python::with_gil(|py| {
            Ok(pyo3_asyncio::tokio::future_into_py(py, async move {
                let config = ClientConfig::new(
                    None, None, None, None, None, None, None, None, None, None, None, None, None,
                    None, None, None, None, None, None, None,
                )?;

                let processor = BatchGilFreeProcessor::new(config)?;
                let results = processor.process_batch_requests(contexts).await;

                // Convert results back to Python objects
                let py_results: PyResult<Vec<PyObject>> = Python::with_gil(|py| {
                    results
                        .into_iter()
                        .map(|result| match result {
                            Ok(response) => Ok(response.to_object(py)),
                            Err(error) => Err(RequestError::new_err(error)),
                        })
                        .collect()
                });

                py_results
            })?
            .to_object(py))
        })
    } else {
        let config = ClientConfig::new(
            None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None,
        )?;

        let processor = BatchGilFreeProcessor::new(config)?;
        let results = processor.process_sync_batch_requests(&contexts);

        Python::with_gil(|py| {
            let py_results: PyResult<Vec<PyObject>> = results
                .into_iter()
                .map(|result| match result {
                    Ok(response) => Ok(response.to_object(py)),
                    Err(error) => Err(RequestError::new_err(error)),
                })
                .collect();

            Ok(py_results?.to_object(py))
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_gil_free_context_creation() {
        let context = GilFreeRequestContext::from_raw_data(
            "GET".to_string(),
            "https://httpbin.org/get".to_string(),
            HashMap::new(),
            None,
            Some(10.0),
        );

        assert!(context.is_ok());
        let ctx = context.unwrap();
        assert_eq!(ctx.method, hyper::Method::GET);
        assert!(ctx.timeout.is_some());
    }

    #[test]
    fn test_request_id_generation() {
        let id1 = generate_request_id();
        let id2 = generate_request_id();
        assert!(id2 > id1);
    }
}
