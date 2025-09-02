use crate::core::sync_core::SyncHttpClient;
use crate::models::HttpResponse;
use crate::stubs::streaming_stub::StreamingClient;
use pyo3::prelude::*;
use std::collections::HashMap;

// Request parameters structure to eliminate too many arguments issue
#[derive(Default)]
pub struct RequestParams {
    pub content: Option<Vec<u8>>,
    pub data: Option<PyObject>,
    pub json: Option<HashMap<String, PyObject>>,
    pub files: Option<HashMap<String, PyObject>>,
    pub params: Option<HashMap<String, PyObject>>,
    pub headers: Option<PyObject>,
    pub cookies: Option<HashMap<String, String>>,
    pub auth: Option<PyObject>,
    pub follow_redirects: bool,
    pub verify: bool,
    pub timeout: f64,
}

// Configuration parameters grouped to reduce function argument count
#[derive(Clone)]
struct RequestConfig {
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
}

struct RequestData {
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
}

struct RequestMeta {
    params: Option<HashMap<String, PyObject>>,
    headers: Option<PyObject>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
}

// Removed helper methods to avoid too many arguments issue

// Simplified internal functions with reduced parameter counts
fn execute_simple_request(
    method: &str,
    url: &str,
    data: RequestData,
    meta: RequestMeta,
    config: RequestConfig,
) -> PyResult<HttpResponse> {
    let params = RequestParams {
        content: data.content,
        data: data.data,
        json: data.json,
        files: data.files,
        params: meta.params,
        headers: meta.headers,
        cookies: meta.cookies,
        auth: meta.auth,
        follow_redirects: config.follow_redirects,
        verify: config.verify,
        timeout: config.timeout,
    };
    execute_core_request(method, url, params)
}

// Core request executor with minimal parameters - eliminates complexity
fn execute_core_request(method: &str, url: &str, params: RequestParams) -> PyResult<HttpResponse> {
    let mut builder = HttpRequestBuilder::new()
        .with_follow_redirects(params.follow_redirects)
        .with_verify(params.verify)
        .with_timeout(params.timeout);

    if let Some(c) = params.content {
        builder = builder.with_content(c);
    }
    if let Some(d) = params.data {
        builder = builder.with_data(d);
    }
    if let Some(j) = params.json {
        builder = builder.with_json(j);
    }
    if let Some(f) = params.files {
        builder = builder.with_files(f);
    }
    if let Some(p) = params.params {
        builder = builder.with_params(p);
    }
    if let Some(h) = params.headers {
        builder = builder.with_headers(h);
    }
    if let Some(c) = params.cookies {
        builder = builder.with_cookies(c);
    }
    if let Some(a) = params.auth {
        builder = builder.with_auth(a);
    }

    builder.execute(method, url)
}

// Production-grade Builder pattern for HTTP requests - eliminates parameter complexity
#[derive(Default, Clone)]
pub struct HttpRequestBuilder {
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<PyObject>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
}

impl HttpRequestBuilder {
    // Create new builder with defaults
    pub fn new() -> Self {
        Self {
            content: None,
            data: None,
            json: None,
            files: None,
            params: None,
            headers: None,
            cookies: None,
            auth: None,
            follow_redirects: false,
            verify: true,
            timeout: 5.0,
        }
    }

    // Builder methods for setting parameters
    pub fn with_content(mut self, content: Vec<u8>) -> Self {
        self.content = Some(content);
        self
    }

    pub fn with_data(mut self, data: PyObject) -> Self {
        self.data = Some(data);
        self
    }

    pub fn with_json(mut self, json: HashMap<String, PyObject>) -> Self {
        self.json = Some(json);
        self
    }

    pub fn with_files(mut self, files: HashMap<String, PyObject>) -> Self {
        self.files = Some(files);
        self
    }

    pub fn with_params(mut self, params: HashMap<String, PyObject>) -> Self {
        self.params = Some(params);
        self
    }

    pub fn with_headers(mut self, headers: PyObject) -> Self {
        self.headers = Some(headers);
        self
    }

    pub fn with_cookies(mut self, cookies: HashMap<String, String>) -> Self {
        self.cookies = Some(cookies);
        self
    }

    pub fn with_auth(mut self, auth: PyObject) -> Self {
        self.auth = Some(auth);
        self
    }

    pub fn with_follow_redirects(mut self, follow_redirects: bool) -> Self {
        self.follow_redirects = follow_redirects;
        self
    }

    pub fn with_verify(mut self, verify: bool) -> Self {
        self.verify = verify;
        self
    }

    pub fn with_timeout(mut self, timeout: f64) -> Self {
        self.timeout = timeout;
        self
    }

    // Execute the HTTP request
    pub fn execute(self, method: &str, url: &str) -> PyResult<HttpResponse> {
        // Extract auth parameter - unified processing
        let auth_tuple = extract_auth_parameter(self.auth)?;

        // Extract headers - unified processing
        let extracted_headers = extract_headers(self.headers)?;

        // Create ephemeral config - unified processing
        let client_config = create_ephemeral_config_with_verify(
            self.cookies.clone(),
            Some(self.timeout),
            self.follow_redirects,
            Some(&Python::with_gil(|py| self.verify.to_object(py))),
        )?;

        // Use the config to create a client
        let sync_client = SyncHttpClient::new_with_config(client_config)?;

        // Convert HashMap types to PyObject for sync_client
        let json_obj = self
            .json
            .as_ref()
            .map(|j| Python::with_gil(|py| j.to_object(py)));
        let files_obj = self
            .files
            .as_ref()
            .map(|f| Python::with_gil(|py| f.to_object(py)));

        // Execute request using client - all common logic centralized
        sync_client.send_request(
            method,
            url,
            self.content,
            self.data,
            json_obj,
            files_obj,
            self.params,
            extracted_headers,
            Some(self.timeout),
            auth_tuple,
            Some(self.follow_redirects),
            self.cookies,
        )
    }

    // Execute streaming request
    pub fn execute_stream(self, method: &str, url: &str) -> PyResult<StreamingClient> {
        // Extract auth parameter for streaming
        let auth_tuple = extract_auth_parameter(self.auth)?;
        let config = create_ephemeral_config_with_verify(
            self.cookies.clone(),
            Some(self.timeout),
            self.follow_redirects,
            Some(&Python::with_gil(|py| self.verify.to_object(py))),
        )?;

        // Convert headers for streaming client
        let headers_hashmap = match self.headers {
            Some(h) => Python::with_gil(|py| h.extract::<HashMap<String, String>>(py).ok()),
            None => None,
        };

        Ok(StreamingClient::new(
            config,
            method.to_string(),
            url.to_string(),
            self.content,
            self.data,
            self.json,
            self.files,
            self.params,
            headers_hashmap,
            Some(self.timeout),
            auth_tuple,
            self.follow_redirects,
            self.cookies,
        ))
    }
}

// Removed - RequestConfig no longer needed with Builder pattern

// Legacy function for backward compatibility - uses reduced parameter set
pub fn execute_request_with_sync_client(
    config: &ClientConfig,
    method: &str,
    url: &str,
    builder: HttpRequestBuilder,
) -> PyResult<HttpResponse> {
    // Use the provided config to create a client with proper timeout settings
    let sync_client = SyncHttpClient::new_with_config(config.clone())?;

    // Extract auth parameter
    let auth_tuple = extract_auth_parameter(builder.auth)?;

    // Extract headers
    let extracted_headers = extract_headers(builder.headers)?;

    // Convert HashMap types to PyObject for sync_client
    let json_obj = builder
        .json
        .as_ref()
        .map(|j| Python::with_gil(|py| j.to_object(py)));
    let files_obj = builder
        .files
        .as_ref()
        .map(|f| Python::with_gil(|py| f.to_object(py)));

    // Execute request using client with proper timeout configuration
    sync_client.send_request(
        method,
        url,
        builder.content,
        builder.data,
        json_obj,
        files_obj,
        builder.params,
        extracted_headers,
        Some(builder.timeout),
        auth_tuple,
        Some(builder.follow_redirects),
        builder.cookies,
    )
}
use crate::auth::{extract_auth, extract_auth_from_object};
use crate::config::ClientConfig;
use crate::models::HttpHeaders;

// Helper function to extract headers from either HashMap or Headers object
fn extract_headers(headers: Option<PyObject>) -> PyResult<Option<HashMap<String, String>>> {
    if let Some(h) = headers {
        Python::with_gil(|py| {
            // Try to extract as HashMap first
            if let Ok(hashmap) = h.extract::<HashMap<String, String>>(py) {
                return Ok(Some(hashmap));
            }

            // Try to extract as Headers object
            if let Ok(headers_obj) = h.extract::<PyRef<HttpHeaders>>(py) {
                return Ok(Some(headers_obj.to_hashmap()));
            }

            // If neither works, return an error
            Err(pyo3::exceptions::PyTypeError::new_err(
                "headers must be a dict or Headers object",
            ))
        })
    } else {
        Ok(None)
    }
}

// Helper function to extract timeout from either f64 or Timeout object
fn extract_timeout_parameter(timeout: Option<f64>) -> Option<PyObject> {
    timeout.map(|t| Python::with_gil(|py| t.to_object(py)))
}

// Helper function to extract auth from either tuple or Auth object
fn extract_auth_parameter(auth: Option<PyObject>) -> PyResult<Option<(String, String)>> {
    if let Some(auth_obj) = auth {
        Python::with_gil(|py| {
            // Try to extract as tuple first (for backward compatibility)
            if let Ok(tuple) = auth_obj.extract::<(String, String)>(py) {
                return Ok(Some(tuple));
            }

            // Try to extract as Auth object
            if let Ok(auth_type) = extract_auth_from_object(&auth_obj) {
                if let Some(auth_data) = extract_auth(&auth_type) {
                    return Ok(Some(auth_data));
                }
            }

            // If neither works, return an error
            Err(pyo3::exceptions::PyTypeError::new_err(
                "auth must be a tuple (username, password) or Auth object",
            ))
        })
    } else {
        Ok(None)
    }
}

// Removed dead code - ephemeral config creation without verify parameter

// Ephemeral config creation with parameter handling
fn create_ephemeral_config_with_verify(
    cookies: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    follow_redirects: bool,
    verify: Option<&PyObject>,
) -> PyResult<ClientConfig> {
    Python::with_gil(|py| {
        ClientConfig::new(
            None,                               // base_url
            extract_timeout_parameter(timeout), // timeout - convert f64 to PyObject
            None,                               // headers
            verify.map(|v| v.as_ref(py)),       // verify - convert to &PyAny
            Some(follow_redirects),             // follow_redirects
            None,                               // auth
            None,                               // proxy
            None,                               // proxies
            cookies,                            // cookies
            None,                               // http1
            None,                               // http2
            None,                               // event_hooks
            None,                               // cert
            None,                               // trust_env
            None,                               // transport
            None,                               // mounts
            None,                               // limits
            None,                               // max_redirects
            None,                               // default_encoding
            None,                               // params
        )
    })
}

// Python GET wrapper - delegates to core executor with proper parameter management
// Note: Function signature must match httpx API for compatibility
#[allow(clippy::too_many_arguments)] // Required for httpx API compatibility
#[pyfunction]
#[pyo3(signature = (url, *, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=false, verify=true, timeout=5.0, trust_env=true))]
pub fn get(
    url: &str,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
    proxy: Option<PyObject>, // Accepted for compatibility but not implemented
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
    trust_env: bool, // Accepted for compatibility but not implemented
) -> PyResult<HttpResponse> {
    // Handle compatibility parameters (accepted for httpx compatibility)
    let _ = (proxy, trust_env);

    let data = RequestData {
        content: None,
        data: None,
        json: None,
        files: None,
    };
    let meta = RequestMeta {
        params,
        headers: headers.map(|h| Python::with_gil(|py| h.to_object(py))),
        cookies,
        auth,
    };
    let config = RequestConfig {
        follow_redirects,
        verify,
        timeout,
    };

    execute_simple_request("GET", url, data, meta, config)
}

// Python POST wrapper - delegates to core executor with proper parameter management
// Note: Function signature must match httpx API for compatibility
#[allow(clippy::too_many_arguments)] // Required for httpx API compatibility
#[pyfunction]
#[pyo3(signature = (url, *, content=None, data=None, json=None, files=None, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=false, verify=true, timeout=5.0, trust_env=true))]
pub fn post(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<PyObject>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
    proxy: Option<PyObject>,
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
    trust_env: bool,
) -> PyResult<HttpResponse> {
    // Handle compatibility parameters (accepted for httpx compatibility)
    let _ = (proxy, trust_env);

    let request_data = RequestData {
        content,
        data,
        json,
        files,
    };
    let meta = RequestMeta {
        params,
        headers,
        cookies,
        auth,
    };
    let config = RequestConfig {
        follow_redirects,
        verify,
        timeout,
    };

    execute_simple_request("POST", url, request_data, meta, config)
}

// Python PUT wrapper - delegates to core executor
// Note: Function signature must match httpx API for compatibility
#[allow(clippy::too_many_arguments)] // Required for httpx API compatibility
#[pyfunction]
#[pyo3(signature = (url, *, content=None, data=None, json=None, files=None, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=false, verify=true, timeout=5.0, trust_env=true))]
pub fn put(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
    proxy: Option<PyObject>,
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
    trust_env: bool,
) -> PyResult<HttpResponse> {
    // Handle compatibility parameters (accepted for httpx compatibility)
    let _ = (proxy, trust_env);

    let request_data = RequestData {
        content,
        data,
        json,
        files,
    };
    let meta = RequestMeta {
        params,
        headers: headers.map(|h| Python::with_gil(|py| h.to_object(py))),
        cookies,
        auth,
    };
    let config = RequestConfig {
        follow_redirects,
        verify,
        timeout,
    };

    execute_simple_request("PUT", url, request_data, meta, config)
}

// Python PATCH wrapper - delegates to core executor
// Note: Function signature must match httpx API for compatibility
#[allow(clippy::too_many_arguments)] // Required for httpx API compatibility
#[pyfunction]
#[pyo3(signature = (url, *, content=None, data=None, json=None, files=None, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=false, verify=true, timeout=5.0, trust_env=true))]
pub fn patch(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
    proxy: Option<PyObject>,
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
    trust_env: bool,
) -> PyResult<HttpResponse> {
    // Handle compatibility parameters (accepted for httpx compatibility)
    let _ = (proxy, trust_env);

    let request_data = RequestData {
        content,
        data,
        json,
        files,
    };
    let meta = RequestMeta {
        params,
        headers: headers.map(|h| Python::with_gil(|py| h.to_object(py))),
        cookies,
        auth,
    };
    let config = RequestConfig {
        follow_redirects,
        verify,
        timeout,
    };

    execute_simple_request("PATCH", url, request_data, meta, config)
}

// Python DELETE wrapper - delegates to core executor
// Note: Function signature must match httpx API for compatibility
#[allow(clippy::too_many_arguments)] // Required for httpx API compatibility
#[pyfunction]
#[pyo3(signature = (url, *, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=false, verify=true, timeout=5.0, trust_env=true))]
pub fn delete(
    url: &str,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
    proxy: Option<PyObject>,
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
    trust_env: bool,
) -> PyResult<HttpResponse> {
    // Handle compatibility parameters (accepted for httpx compatibility)
    let _ = (proxy, trust_env);

    let data = RequestData {
        content: None,
        data: None,
        json: None,
        files: None,
    };
    let meta = RequestMeta {
        params,
        headers: headers.map(|h| Python::with_gil(|py| h.to_object(py))),
        cookies,
        auth,
    };
    let config = RequestConfig {
        follow_redirects,
        verify,
        timeout,
    };

    execute_simple_request("DELETE", url, data, meta, config)
}

// Python HEAD wrapper - delegates to core executor
// Note: Function signature must match httpx API for compatibility
#[allow(clippy::too_many_arguments)] // Required for httpx API compatibility
#[pyfunction]
#[pyo3(signature = (url, *, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=false, verify=true, timeout=5.0, trust_env=true))]
pub fn head(
    url: &str,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
    proxy: Option<PyObject>,
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
    trust_env: bool,
) -> PyResult<HttpResponse> {
    // Handle compatibility parameters (accepted for httpx compatibility)
    let _ = (proxy, trust_env);

    let data = RequestData {
        content: None,
        data: None,
        json: None,
        files: None,
    };
    let meta = RequestMeta {
        params,
        headers: headers.map(|h| Python::with_gil(|py| h.to_object(py))),
        cookies,
        auth,
    };
    let config = RequestConfig {
        follow_redirects,
        verify,
        timeout,
    };

    execute_simple_request("HEAD", url, data, meta, config)
}

// Python OPTIONS wrapper - delegates to core executor
// Note: Function signature must match httpx API for compatibility
#[allow(clippy::too_many_arguments)] // Required for httpx API compatibility
#[pyfunction]
#[pyo3(signature = (url, *, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=false, verify=true, timeout=5.0, trust_env=true))]
pub fn options(
    url: &str,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
    proxy: Option<PyObject>,
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
    trust_env: bool,
) -> PyResult<HttpResponse> {
    // Handle compatibility parameters (accepted for httpx compatibility)
    let _ = (proxy, trust_env);

    let data = RequestData {
        content: None,
        data: None,
        json: None,
        files: None,
    };
    let meta = RequestMeta {
        params,
        headers: headers.map(|h| Python::with_gil(|py| h.to_object(py))),
        cookies,
        auth,
    };
    let config = RequestConfig {
        follow_redirects,
        verify,
        timeout,
    };

    execute_simple_request("OPTIONS", url, data, meta, config)
}

// Python request wrapper - delegates to core executor
// Note: Function signature must match httpx API for compatibility
#[allow(clippy::too_many_arguments)] // Required for httpx API compatibility
#[pyfunction]
#[pyo3(signature = (method, url, *, content=None, data=None, json=None, files=None, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=false, verify=true, timeout=5.0, trust_env=true))]
pub fn request(
    method: &str,
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<PyObject>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
    proxy: Option<PyObject>,
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
    trust_env: bool,
) -> PyResult<HttpResponse> {
    // Handle compatibility parameters (accepted for httpx compatibility)
    let _ = (proxy, trust_env);

    let request_data = RequestData {
        content,
        data,
        json,
        files,
    };
    let meta = RequestMeta {
        params,
        headers,
        cookies,
        auth,
    };
    let config = RequestConfig {
        follow_redirects,
        verify,
        timeout,
    };

    execute_simple_request(method, url, request_data, meta, config)
}

// Python streaming wrapper - delegates to builder's streaming executor
// Note: Function signature must match httpx API for compatibility
#[allow(clippy::too_many_arguments)] // Required for httpx API compatibility
#[pyfunction]
#[pyo3(signature = (method, url, *, content=None, data=None, json=None, files=None, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=false, verify=true, timeout=5.0, trust_env=true))]
pub fn stream(
    method: &str,
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    cookies: Option<HashMap<String, String>>,
    auth: Option<PyObject>,
    proxy: Option<PyObject>,
    follow_redirects: bool,
    verify: bool,
    timeout: f64,
    trust_env: bool,
) -> PyResult<StreamingClient> {
    // Handle compatibility parameters (accepted for httpx compatibility)
    let _ = (proxy, trust_env);

    let request_data = RequestData {
        content,
        data,
        json,
        files,
    };
    let meta = RequestMeta {
        params,
        headers: headers.map(|h| Python::with_gil(|py| h.to_object(py))),
        cookies,
        auth,
    };
    let config = RequestConfig {
        follow_redirects,
        verify,
        timeout,
    };

    execute_stream_internal(method, url, request_data, meta, config)
}

// Internal streaming function with reduced parameters
fn execute_stream_internal(
    method: &str,
    url: &str,
    data: RequestData,
    meta: RequestMeta,
    config: RequestConfig,
) -> PyResult<StreamingClient> {
    let mut builder = HttpRequestBuilder::new()
        .with_follow_redirects(config.follow_redirects)
        .with_verify(config.verify)
        .with_timeout(config.timeout);

    if let Some(c) = data.content {
        builder = builder.with_content(c);
    }
    if let Some(d) = data.data {
        builder = builder.with_data(d);
    }
    if let Some(j) = data.json {
        builder = builder.with_json(j);
    }
    if let Some(f) = data.files {
        builder = builder.with_files(f);
    }
    if let Some(p) = meta.params {
        builder = builder.with_params(p);
    }
    if let Some(h) = meta.headers {
        builder = builder.with_headers(h);
    }
    if let Some(c) = meta.cookies {
        builder = builder.with_cookies(c);
    }
    if let Some(a) = meta.auth {
        builder = builder.with_auth(a);
    }

    builder.execute_stream(method, url)
}
