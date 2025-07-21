use pyo3::prelude::*;
use pyo3::types::IntoPyDict;
use std::collections::HashMap;

/// Simple Headers wrapper - minimal interface for httpx compatibility
/// Core logic handled by reqwest in HTTP requests
#[pyclass(name = "Headers")]
#[derive(Debug, Clone)]
pub struct HttpHeaders {
    inner: HashMap<String, String>,
}

#[pymethods]
impl HttpHeaders {
    #[new]
    #[pyo3(signature = (headers = None))]
    pub fn new(headers: Option<HashMap<String, String>>) -> Self {
        Self { inner: headers.unwrap_or_default() }
    }
    
    fn __getitem__(&self, key: &str) -> PyResult<String> {
        // Simple case-insensitive lookup for httpx compatibility
        for (k, v) in &self.inner {
            if k.to_lowercase() == key.to_lowercase() {
                return Ok(v.clone());
            }
        }
        Err(pyo3::exceptions::PyKeyError::new_err(key.to_string()))
    }
    
    fn __setitem__(&mut self, key: String, value: String) {
        // Remove existing key (case-insensitive) then add new one
        let key_lower = key.to_lowercase();
        self.inner.retain(|k, _| k.to_lowercase() != key_lower);
        self.inner.insert(key, value);
    }
    
    fn get(&self, key: &str, default: Option<String>) -> Option<String> {
        for (k, v) in &self.inner {
            if k.to_lowercase() == key.to_lowercase() {
                return Some(v.clone());
            }
        }
        default
    }
    
    fn update(&mut self, other: HashMap<String, String>) {
        self.inner.extend(other);
    }
    
    fn items(&self) -> Vec<(String, String)> {
        self.inner.iter().map(|(k, v)| (k.clone(), v.clone())).collect()
    }
    
    fn keys(&self) -> Vec<String> {
        self.inner.keys().cloned().collect()
    }
    
    fn values(&self) -> Vec<String> {
        self.inner.values().cloned().collect()
    }
    
    fn __len__(&self) -> usize {
        self.inner.len()
    }
    
    fn __iter__(&self) -> Vec<String> {
        self.inner.keys().cloned().collect()
    }
    
    fn __contains__(&self, key: &str) -> bool {
        // 支持不区分大小写的查找
        for k in self.inner.keys() {
            if k.to_lowercase() == key.to_lowercase() {
                return true;
            }
        }
        false
    }
}

impl HttpHeaders {
    pub fn to_hashmap(&self) -> HashMap<String, String> {
        self.inner.clone()
    }
}

/// Simple QueryParams wrapper - string parsing delegated to reqwest
#[pyclass(name = "QueryParams")]
#[derive(Debug, Clone)]
pub struct HttpQueryParams {
    inner: HashMap<String, String>,
    raw_string: Option<String>,
}

#[pymethods]
impl HttpQueryParams {
    #[new]
    #[pyo3(signature = (params = None))]
    pub fn new(params: Option<PyObject>) -> PyResult<Self> {
        Python::with_gil(|py| {
            if let Some(p) = params {
                if let Ok(string_params) = p.extract::<String>(py) {
                    // Let reqwest handle parsing when actually used
                    // For now, provide basic interface compatibility
                    let mut inner = HashMap::new();
                    
                    // Use reqwest's URL parsing - this is the correct approach
                    if let Ok(parsed_url) = reqwest::Url::parse(&format!("http://example.com?{}", string_params.trim_start_matches('?'))) {
                        for (key, value) in parsed_url.query_pairs() {
                            inner.insert(key.to_string(), value.to_string());
                        }
                    }
                    
                    Ok(Self {
                        inner,
                        raw_string: Some(string_params),
                    })
                } else if let Ok(dict_params) = p.extract::<HashMap<String, String>>(py) {
                    Ok(Self {
                        inner: dict_params,
                        raw_string: None,
                    })
                } else {
                    Ok(Self {
                        inner: HashMap::new(),
                        raw_string: None,
                    })
                }
            } else {
                Ok(Self {
                    inner: HashMap::new(),
                    raw_string: None,
                })
            }
        })
    }
    
    fn __getitem__(&self, key: &str) -> PyResult<String> {
        self.inner.get(key)
            .cloned()
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err(key.to_string()))
    }
    
    fn __setitem__(&mut self, key: String, value: String) {
        self.inner.insert(key, value);
        self.raw_string = None; // Invalidate raw string
    }
    
    fn get(&self, key: &str, default: Option<String>) -> Option<String> {
        self.inner.get(key).cloned().or(default)
    }
    
    fn update(&mut self, other: HashMap<String, String>) {
        self.inner.extend(other);
        self.raw_string = None;
    }
    
    fn items(&self) -> Vec<(String, String)> {
        self.inner.iter().map(|(k, v)| (k.clone(), v.clone())).collect()
    }
    
    fn keys(&self) -> Vec<String> {
        self.inner.keys().cloned().collect()
    }
    
    fn values(&self) -> Vec<String> {
        self.inner.values().cloned().collect()
    }
    
    fn __len__(&self) -> usize {
        self.inner.len()
    }
    
    fn __iter__(&self) -> Vec<String> {
        self.inner.keys().cloned().collect()
    }
    
    fn __contains__(&self, key: &str) -> bool {
        self.inner.contains_key(key)
    }
}

impl HttpQueryParams {
    pub fn to_hashmap(&self) -> HashMap<String, String> {
        self.inner.clone()
    }
    
    pub fn get_raw_string(&self) -> Option<&String> {
        self.raw_string.as_ref()
    }
}

/// Simple Cookies wrapper - processing delegated to reqwest
#[pyclass(name = "Cookies")]
#[derive(Debug, Clone)]
pub struct HttpCookies {
    inner: HashMap<String, String>,
}

#[pymethods]
impl HttpCookies {
    #[new]
    #[pyo3(signature = (cookies = None))]
    pub fn new(cookies: Option<HashMap<String, String>>) -> Self {
        Self { inner: cookies.unwrap_or_default() }
    }
    
    fn __getitem__(&self, key: &str) -> PyResult<String> {
        self.inner.get(key)
            .cloned()
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err(key.to_string()))
    }
    
    fn __setitem__(&mut self, key: String, value: String) {
        self.inner.insert(key, value);
    }
    
    fn get(&self, key: &str, default: Option<String>) -> Option<String> {
        self.inner.get(key).cloned().or(default)
    }
    
    #[pyo3(signature = (name, value, domain = None))]
    fn set(&mut self, name: String, value: String, domain: Option<String>) {
        // Note: domain parameter ignored for now, reqwest handles cookie domains
        let _ = domain; // Suppress unused parameter warning
        self.inner.insert(name, value);
    }
    
    fn update(&mut self, other: HashMap<String, String>) {
        self.inner.extend(other);
    }
    
    fn items(&self) -> Vec<(String, String)> {
        self.inner.iter().map(|(k, v)| (k.clone(), v.clone())).collect()
    }
    
    fn keys(&self) -> Vec<String> {
        self.inner.keys().cloned().collect()
    }
    
    fn values(&self) -> Vec<String> {
        self.inner.values().cloned().collect()
    }
    
    fn __len__(&self) -> usize {
        self.inner.len()
    }
    
    fn __iter__(&self) -> Vec<String> {
        self.inner.keys().cloned().collect()
    }
    
    fn __contains__(&self, key: &str) -> bool {
        self.inner.contains_key(key)
    }
}

impl HttpCookies {
    pub fn to_hashmap(&self) -> HashMap<String, String> {
        self.inner.clone()
    }
}

/// Simple URL wrapper - parsing handled by reqwest
#[pyclass(name = "URL")]
#[derive(Debug, Clone)]
pub struct HttpUrl {
    url: String,
}

#[pymethods]
impl HttpUrl {
    #[new]
    pub fn new(url: String) -> Self {
        Self { url }
    }
    
    fn __str__(&self) -> String {
        self.url.clone()
    }
}

impl HttpUrl {
    pub fn as_str(&self) -> &str {
        &self.url
    }
}

/// Timeout configuration - minimal wrapper for reqwest
#[pyclass(name = "Timeout")]
#[derive(Debug, Clone)]
pub struct HttpTimeout {
    connect: Option<f64>,
    read: Option<f64>,
    write: Option<f64>,
    pool: Option<f64>,
}

#[pymethods]
impl HttpTimeout {
    #[new]
    #[pyo3(signature = (connect = None, read = None, write = None, pool = None))]
    pub fn new(
        connect: Option<f64>,
        read: Option<f64>,
        write: Option<f64>,
        pool: Option<f64>,
    ) -> Self {
        Self { connect, read, write, pool }
    }
    
    #[getter]
    pub fn connect(&self) -> Option<f64> {
        self.connect
    }
    
    #[getter]
    pub fn read(&self) -> Option<f64> {
        self.read
    }
    
    #[getter]
    pub fn write(&self) -> Option<f64> {
        self.write
    }
    
    #[getter]
    pub fn pool(&self) -> Option<f64> {
        self.pool
    }
}

impl HttpTimeout {
    pub fn get_read_timeout(&self) -> f64 {
        self.read.unwrap_or(30.0)
    }
}

/// Connection pool limits - minimal wrapper for reqwest
#[pyclass(name = "Limits")]
#[derive(Debug, Clone)]
pub struct HttpLimits {
    max_keepalive_connections: i32,
    max_connections: i32,
    keepalive_expiry: f64,
}

#[pymethods]
impl HttpLimits {
    #[new]
    #[pyo3(signature = (max_keepalive_connections = 20, max_connections = 100, keepalive_expiry = 5.0))]
    pub fn new(
        max_keepalive_connections: i32,
        max_connections: i32,
        keepalive_expiry: f64,
    ) -> Self {
        Self {
            max_keepalive_connections,
            max_connections,
            keepalive_expiry,
        }
    }
    
    #[getter]
    pub fn max_keepalive_connections(&self) -> i32 {
        self.max_keepalive_connections
    }
    
    #[getter]
    pub fn max_connections(&self) -> i32 {
        self.max_connections
    }
    
    #[getter]
    pub fn keepalive_expiry(&self) -> f64 {
        self.keepalive_expiry
    }
}

/// Basic authentication - minimal interface wrapper for reqwest
#[pyclass(name = "BasicAuth")]
#[derive(Debug, Clone)]
pub struct HttpBasicAuth {
    username: String,
    password: String,
}

#[pymethods]
impl HttpBasicAuth {
    #[new]
    pub fn new(username: String, password: String) -> Self {
        Self { username, password }
    }
    
    #[getter]
    pub fn username(&self) -> String {
        self.username.clone()
    }
    
    #[getter]
    pub fn password(&self) -> String {
        self.password.clone()
    }
    
    // Minimal auth_flow method for httpx compatibility 
    // Actual authentication is handled by reqwest during request sending
    fn auth_flow(&self, request: PyObject) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            // Simple placeholder implementation for httpx compatibility
            // The real auth logic happens in the Rust request sending code using reqwest
            let iter = py.eval("iter([request])", Some([("request", &request)].into_py_dict(py)), None)?;
            Ok(iter.to_object(py))
        })
    }
    
    fn __repr__(&self) -> String {
        format!("<BasicAuth [username={:?}]>", self.username)
    }
}

impl HttpBasicAuth {
    pub fn to_tuple(&self) -> (String, String) {
        (self.username.clone(), self.password.clone())
    }
}

/// Digest authentication - minimal interface wrapper for reqwest
#[pyclass(name = "DigestAuth")]
#[derive(Debug, Clone)]
pub struct HttpDigestAuth {
    username: String,
    password: String,
}

#[pymethods]
impl HttpDigestAuth {
    #[new]
    pub fn new(username: String, password: String) -> Self {
        Self { username, password }
    }
    
    #[getter]
    pub fn username(&self) -> String {
        self.username.clone()
    }
    
    #[getter]
    pub fn password(&self) -> String {
        self.password.clone()
    }
    
    // Minimal auth_flow method for httpx compatibility
    // Actual digest authentication is handled by reqwest during request sending
    fn auth_flow(&self, request: PyObject) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            // Simple placeholder implementation for httpx compatibility
            // The real digest auth logic happens in the Rust request sending code using reqwest
            let iter = py.eval("iter([request])", Some([("request", &request)].into_py_dict(py)), None)?;
            Ok(iter.to_object(py))
        })
    }
    
    fn __repr__(&self) -> String {
        format!("<DigestAuth [username={:?}]>", self.username)
    }
}

impl HttpDigestAuth {
    pub fn to_tuple(&self) -> (String, String) {
        (self.username.clone(), self.password.clone())
    }
}

/// NetRC authentication - minimal interface wrapper for reqwest
#[pyclass(name = "NetRCAuth")]
#[derive(Debug, Clone)]
pub struct HttpNetRCAuth {
    file: Option<String>,
}

#[pymethods]
impl HttpNetRCAuth {
    #[new]
    #[pyo3(signature = (file = None))]
    pub fn new(file: Option<String>) -> Self {
        let file_path = file.or_else(|| {
            // Default to ~/.netrc like httpx
            std::env::var("HOME").ok().map(|home| format!("{}/.netrc", home))
        });
        Self { file: file_path }
    }
    
    #[getter]
    pub fn file(&self) -> String {
        self.file.clone().unwrap_or_else(|| "~/.netrc".to_string())
    }
    
    // Minimal auth_flow method for httpx compatibility
    // Actual netrc parsing would be handled during request sending
    fn auth_flow(&self, request: PyObject) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            // Simple placeholder implementation for httpx compatibility
            // The real netrc logic would happen in the Rust request sending code
            let iter = py.eval("iter([request])", Some([("request", &request)].into_py_dict(py)), None)?;
            Ok(iter.to_object(py))
        })
    }
    
    fn __repr__(&self) -> String {
        "<NetRCAuth>".to_string()
    }
}