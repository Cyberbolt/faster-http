use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyAny};
use std::collections::HashMap;
use crate::error::{create_validation_error, create_url_error};

/// Iterator for HttpHeaders
#[pyclass]
pub struct HttpHeadersIterator {
    keys: Vec<String>,
    index: usize,
}

#[pymethods]
impl HttpHeadersIterator {
    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<Self>) -> Option<String> {
        if slf.index < slf.keys.len() {
            let key = slf.keys[slf.index].clone();
            slf.index += 1;
            Some(key)
        } else {
            None
        }
    }
}

/// Iterator for HttpCookies
#[pyclass]
pub struct HttpCookiesIterator {
    keys: Vec<String>,
    index: usize,
}

#[pymethods]
impl HttpCookiesIterator {
    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<Self>) -> Option<String> {
        if slf.index < slf.keys.len() {
            let key = slf.keys[slf.index].clone();
            slf.index += 1;
            Some(key)
        } else {
            None
        }
    }
}

/// Simple Headers wrapper - minimal interface for httpx compatibility
/// Core logic handled by hyper in HTTP requests
#[pyclass(name = "Headers", module = "faster_http")]
#[derive(Debug, Clone)]
pub struct HttpHeaders {
    inner: HashMap<String, String>,
}

#[pymethods]
impl HttpHeaders {
    #[new]
    #[pyo3(signature = (headers = None))]
    pub fn new(headers: Option<HashMap<String, String>>) -> Self {
        Self {
            inner: headers.unwrap_or_default(),
        }
    }

    fn __getitem__(&self, key: &str) -> PyResult<String> {
        // Simple case-insensitive lookup for httpx compatibility
        for (k, v) in &self.inner {
            if k.to_lowercase() == key.to_lowercase() {
                return Ok(v.clone());
            }
        }
        Err(create_validation_error(&format!("Header not found: {}", key)))
    }

    fn __setitem__(&mut self, key: String, value: String) {
        // Remove existing key (case-insensitive) then add new one
        let key_lower = key.to_lowercase();
        self.inner.retain(|k, _| k.to_lowercase() != key_lower);
        self.inner.insert(key, value);
    }

    fn __delitem__(&mut self, key: &str) -> PyResult<()> {
        let key_lower = key.to_lowercase();
        let original_len = self.inner.len();
        self.inner.retain(|k, _| k.to_lowercase() != key_lower);
        if self.inner.len() == original_len {
            return Err(create_validation_error(&format!("Header not found: {}", key)));
        }
        Ok(())
    }

    fn get(&self, key: &str, default: Option<String>) -> Option<String> {
        for (k, v) in &self.inner {
            if k.to_lowercase() == key.to_lowercase() {
                return Some(v.clone());
            }
        }
        default
    }

    fn get_list(&self, key: &str, split_commas: Option<bool>) -> Vec<String> {
        // Find all values for this header (case-insensitive)
        let mut values = Vec::new();
        for (k, v) in &self.inner {
            if k.to_lowercase() == key.to_lowercase() {
                if split_commas.unwrap_or(false) {
                    // Split comma-separated values if requested
                    for val in v.split(',') {
                        values.push(val.trim().to_string());
                    }
                } else {
                    values.push(v.clone());
                }
            }
        }
        values
    }

    fn update(&mut self, other: HashMap<String, String>) {
        self.inner.extend(other);
    }

    fn items(&self) -> Vec<(String, String)> {
        self.inner
            .iter()
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect()
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

    fn __iter__(&self) -> HttpHeadersIterator {
        HttpHeadersIterator {
            keys: self.inner.keys().cloned().collect(),
            index: 0,
        }
    }

    fn __contains__(&self, key: &str) -> bool {
        // Support case-insensitive lookup
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

/// Simple QueryParams wrapper - string parsing delegated to hyper
#[pyclass(name = "QueryParams", module = "faster_http")]
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
                    // Let hyper handle parsing when actually used
                    // For now, provide basic interface compatibility
                    let mut inner = HashMap::new();

                    // Use url crate's URL parsing
                    if let Ok(parsed_url) = url::Url::parse(&format!(
                        "http://example.com?{}",
                        string_params.trim_start_matches('?')
                    )) {
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
        self.inner
            .get(key)
            .cloned()
            .ok_or_else(|| create_validation_error(&format!("Query parameter not found: {}", key)))
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
        self.inner
            .iter()
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect()
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

    fn __str__(&self) -> String {
        if let Some(raw) = &self.raw_string {
            raw.clone()
        } else {
            // Convert params to query string format
            self.inner
                .iter()
                .map(|(k, v)| format!("{}={}", urlencoding::encode(k), urlencoding::encode(v)))
                .collect::<Vec<String>>()
                .join("&")
        }
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

/// Simple Cookies wrapper - processing delegated to hyper
#[pyclass(name = "Cookies", module = "faster_http")]
#[derive(Debug, Clone)]
pub struct HttpCookies {
    inner: HashMap<String, String>,
}

#[pymethods]
impl HttpCookies {
    #[new]
    #[pyo3(signature = (cookies = None))]
    pub fn new(cookies: Option<HashMap<String, String>>) -> Self {
        Self {
            inner: cookies.unwrap_or_default(),
        }
    }

    fn __getitem__(&self, key: &str) -> PyResult<String> {
        self.inner
            .get(key)
            .cloned()
            .ok_or_else(|| create_validation_error(&format!("Cookie not found: {}", key)))
    }

    fn __setitem__(&mut self, key: String, value: String) {
        self.inner.insert(key, value);
    }

    fn __delitem__(&mut self, key: &str) -> PyResult<()> {
        if self.inner.remove(key).is_none() {
            return Err(create_validation_error(&format!("Cookie not found: {}", key)));
        }
        Ok(())
    }

    fn get(&self, key: &str, default: Option<String>) -> Option<String> {
        self.inner.get(key).cloned().or(default)
    }

    #[pyo3(signature = (name, value, domain = None))]
    fn set(&mut self, name: String, value: String, domain: Option<String>) {
        // Note: domain parameter ignored for now, hyper handles cookie domains
        let _ = domain; // Suppress unused parameter warning
        self.inner.insert(name, value);
    }

    fn update(&mut self, other: HashMap<String, String>) {
        self.inner.extend(other);
    }

    fn items(&self) -> Vec<(String, String)> {
        self.inner
            .iter()
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect()
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

    fn __iter__(&self) -> HttpCookiesIterator {
        HttpCookiesIterator {
            keys: self.inner.keys().cloned().collect(),
            index: 0,
        }
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

/// Simple URL wrapper - parsing handled by hyper
#[pyclass(name = "URL", module = "faster_http")]
#[derive(Debug, Clone)]
pub struct HttpUrl {
    url: String,
    parsed: url::Url,
}

#[pymethods]
impl HttpUrl {
    #[new]
    pub fn new(url: String) -> PyResult<Self> {
        let parsed = url::Url::parse(&url)
            .map_err(|e| create_url_error(&e.to_string()))?;
        Ok(Self { url, parsed })
    }

    fn __str__(&self) -> String {
        // Match httpx behavior: exclude username/password from string representation for security
        // But preserve original URL format as much as possible (don't add trailing slash if not present)
        if self.parsed.username().is_empty() && self.parsed.password().is_none() {
            // No auth info to remove, return original string
            self.url.clone()
        } else {
            // Remove auth info but try to preserve original format
            let mut url_without_auth = self.parsed.clone();
            url_without_auth.set_username("").ok();
            url_without_auth.set_password(None).ok();
            let cleaned = url_without_auth.to_string();

            // If original URL didn't have trailing slash but cleaned version does, remove it
            if !self.url.ends_with('/') && cleaned.ends_with('/') {
                // Only remove trailing slash if it's just the root path
                match url::Url::parse(&cleaned) {
                    Ok(cleaned_url) => {
                        if cleaned_url.path() == "/" {
                            cleaned.trim_end_matches('/').to_string()
                        } else {
                            cleaned
                        }
                    }
                    Err(_) => cleaned // Fallback to cleaned string if parsing fails
                }
            } else {
                cleaned
            }
        }
    }

    #[getter]
    pub fn scheme(&self) -> String {
        self.parsed.scheme().to_string()
    }

    #[getter]
    pub fn host(&self) -> Option<String> {
        self.parsed.host_str().map(|s| s.to_string())
    }

    #[getter]
    pub fn port(&self) -> Option<u16> {
        self.parsed.port()
    }

    #[getter]
    pub fn path(&self) -> String {
        self.parsed.path().to_string()
    }

    #[getter]
    pub fn query(&self, py: Python) -> Option<PyObject> {
        use pyo3::types::PyBytes;
        self.parsed
            .query()
            .map(|q| PyBytes::new(py, q.as_bytes()).to_object(py))
    }

    #[getter]
    pub fn fragment(&self) -> String {
        // httpx compatibility: return empty string instead of None when fragment is missing
        self.parsed.fragment().map(|f| f.to_string()).unwrap_or_default()
    }

    #[getter]
    pub fn params(&self) -> HttpQueryParams {
        // Extract query parameters as HttpQueryParams object for httpx compatibility
        let mut inner = HashMap::new();
        if let Some(_query) = self.parsed.query() {
            for (key, value) in self.parsed.query_pairs() {
                inner.insert(key.to_string(), value.to_string());
            }
        }
        HttpQueryParams {
            inner,
            raw_string: self.parsed.query().map(|s| s.to_string()),
        }
    }

    #[getter]
    pub fn username(&self) -> String {
        self.parsed.username().to_string()
    }

    #[getter]
    pub fn password(&self) -> Option<String> {
        self.parsed.password().map(|p| p.to_string())
    }

    // Additional methods for httpx compatibility
    pub fn copy_with(
        &self,
        _py: Python,
        scheme: Option<&str>,
        _authority: Option<&str>,
        path: Option<&str>,
        query: Option<&PyAny>,
        fragment: Option<&str>,
    ) -> PyResult<Self> {
        let mut new_url = self.parsed.clone();
        
        if let Some(scheme) = scheme {
            new_url.set_scheme(scheme).map_err(|_| {
                create_url_error("Invalid scheme")
            })?;
        }
        
        if let Some(path) = path {
            new_url.set_path(path);
        }
        
        if let Some(query) = query {
            if let Ok(query_bytes) = query.extract::<&[u8]>() {
                let query_str = std::str::from_utf8(query_bytes)
                    .map_err(|_| create_url_error("Invalid query bytes"))?;
                new_url.set_query(Some(query_str));
            } else if let Ok(query_str) = query.extract::<String>() {
                new_url.set_query(Some(&query_str));
            }
        }
        
        if let Some(fragment) = fragment {
            new_url.set_fragment(Some(fragment));
        }
        
        Ok(Self {
            url: new_url.to_string(),
            parsed: new_url,
        })
    }

    pub fn resolve_reference(&self, reference: &str) -> PyResult<Self> {
        let resolved = self.parsed.join(reference).map_err(|e| {
            create_url_error(&format!("Cannot resolve reference: {}", e))
        })?;
        Ok(Self {
            url: resolved.to_string(),
            parsed: resolved,
        })
    }

    fn __repr__(&self) -> String {
        format!("URL('{}')", self.url)
    }

    fn __eq__(&self, other: &pyo3::PyAny) -> PyResult<bool> {
        // Support comparison with strings and other URL objects
        if let Ok(other_str) = other.extract::<String>() {
            Ok(self.url == other_str)
        } else if let Ok(other_url) = other.extract::<HttpUrl>() {
            Ok(self.url == other_url.url)
        } else {
            Ok(false)
        }
    }
}

impl HttpUrl {
    pub fn as_str(&self) -> &str {
        &self.url
    }
}

/// Timeout configuration - minimal wrapper for hyper
#[pyclass(name = "Timeout", module = "faster_http")]
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
    #[pyo3(signature = (timeout = -1.0, *, connect = -1.0, read = -1.0, write = -1.0, pool = -1.0))]
    pub fn new(
        timeout: f64,        // Use -1.0 as sentinel for "not provided", NaN for None
        connect: f64,        // Use -1.0 as sentinel for "not provided", NaN for None
        read: f64,           // Use -1.0 as sentinel for "not provided", NaN for None  
        write: f64,          // Use -1.0 as sentinel for "not provided", NaN for None
        pool: f64,           // Use -1.0 as sentinel for "not provided", NaN for None
    ) -> PyResult<Self> {
        // Helper function to parse timeout values
        let parse_timeout = |val: f64| -> Option<f64> {
            if val == -1.0 || val.is_nan() {
                None // Not provided or explicitly None
            } else {
                Some(val)
            }
        };
        
        let timeout_provided = timeout != -1.0;
        let timeout_is_none = timeout.is_nan();
        let timeout_value = parse_timeout(timeout);
        
        let connect_provided = connect != -1.0;
        let read_provided = read != -1.0;
        let write_provided = write != -1.0;
        let pool_provided = pool != -1.0;
        
        let connect_val = parse_timeout(connect);
        let read_val = parse_timeout(read);
        let write_val = parse_timeout(write);
        let pool_val = parse_timeout(pool);
        
        // Check if any individual timeout parameters were provided
        let has_individual_params = connect_provided || read_provided || write_provided || pool_provided;
        
        // Match httpx behavior
        if timeout_provided {
            if timeout_is_none {
                // timeout=None explicitly passed - infinite timeout (all None)
                Ok(Self {
                    connect: None,
                    read: None,
                    write: None,
                    pool: None,
                })
            } else if let Some(default_timeout) = timeout_value {
                // A numeric timeout was provided - use it as default for all unspecified timeouts
                Ok(Self {
                    connect: if connect_provided { connect_val } else { Some(default_timeout) },
                    read: if read_provided { read_val } else { Some(default_timeout) },
                    write: if write_provided { write_val } else { Some(default_timeout) },
                    pool: if pool_provided { pool_val } else { Some(default_timeout) },
                })
            } else {
                // Shouldn't happen with our logic but handle it
                Err(create_validation_error(
                    "Invalid timeout configuration."
                ))
            }
        } else if has_individual_params {
            // Individual parameters provided - all must be specified for httpx compatibility
            if connect_provided && read_provided && write_provided && pool_provided {
                Ok(Self {
                    connect: connect_val,
                    read: read_val,
                    write: write_val,
                    pool: pool_val,
                })
            } else {
                Err(create_validation_error(
                    "httpx.Timeout must either include a default, or set all four parameters explicitly."
                ))
            }
        } else {
            // No parameters at all - error like httpx Timeout()
            Err(create_validation_error(
                "httpx.Timeout must either include a default, or set all four parameters explicitly."
            ))
        }
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

    fn __repr__(&self) -> String {
        // Helper function to format timeout values with .1 precision for whole numbers
        let format_timeout = |val: Option<f64>| -> String {
            match val {
                Some(v) if v.fract() == 0.0 => format!("{:.1}", v),
                Some(v) => v.to_string(),
                None => "None".to_string(),
            }
        };
        
        // Match httpx format exactly
        if self.connect == self.read && self.read == self.write && self.write == self.pool {
            // All timeouts are the same - use compact format
            if let Some(timeout_val) = self.connect {
                format!("Timeout(timeout={})", format_timeout(Some(timeout_val)))
            } else {
                "Timeout(timeout=None)".to_string()
            }
        } else {
            // Different timeouts - use explicit format
            format!(
                "Timeout(connect={}, read={}, write={}, pool={})",
                format_timeout(self.connect),
                format_timeout(self.read),
                format_timeout(self.write),
                format_timeout(self.pool)
            )
        }
    }

    fn __eq__(&self, _py: Python, other: &pyo3::PyAny) -> PyResult<bool> {
        if let Ok(other_timeout) = other.extract::<HttpTimeout>() {
            Ok(self.connect == other_timeout.connect &&
               self.read == other_timeout.read &&
               self.write == other_timeout.write &&
               self.pool == other_timeout.pool)
        } else {
            Ok(false)
        }
    }
}

impl HttpTimeout {
    pub fn get_read_timeout(&self) -> f64 {
        self.read.unwrap_or(30.0)
    }
}

/// Connection pool limits - minimal wrapper for hyper
#[pyclass(name = "Limits", module = "faster_http")]
#[derive(Debug, Clone)]
pub struct HttpLimits {
    max_keepalive_connections: i32,
    max_connections: i32,
    keepalive_expiry: f64,
}

#[pymethods]
impl HttpLimits {
    #[new]
    #[pyo3(signature = (max_keepalive_connections = None, max_connections = None, keepalive_expiry = 5.0))]
    pub fn new(
        max_keepalive_connections: Option<i32>,
        max_connections: Option<i32>,
        keepalive_expiry: f64,
    ) -> Self {
        Self {
            max_keepalive_connections: max_keepalive_connections.unwrap_or(-1), // Use -1 to represent None
            max_connections: max_connections.unwrap_or(-1), // Use -1 to represent None
            keepalive_expiry,
        }
    }

    #[getter]
    pub fn max_keepalive_connections(&self, py: Python) -> PyObject {
        if self.max_keepalive_connections == -1 {
            py.None()
        } else {
            self.max_keepalive_connections.to_object(py)
        }
    }

    #[getter]
    pub fn max_connections(&self, py: Python) -> PyObject {
        if self.max_connections == -1 {
            py.None()
        } else {
            self.max_connections.to_object(py)
        }
    }

    #[getter]
    pub fn keepalive_expiry(&self) -> f64 {
        self.keepalive_expiry
    }

    fn __repr__(&self) -> String {
        format!(
            "Limits(max_connections={}, max_keepalive_connections={}, keepalive_expiry={})",
            if self.max_connections == -1 { "None".to_string() } else { self.max_connections.to_string() },
            if self.max_keepalive_connections == -1 { "None".to_string() } else { self.max_keepalive_connections.to_string() },
            if self.keepalive_expiry.fract() == 0.0 { 
                format!("{:.1}", self.keepalive_expiry) 
            } else { 
                self.keepalive_expiry.to_string() 
            }
        )
    }

    fn __eq__(&self, _py: Python, other: &pyo3::PyAny) -> PyResult<bool> {
        if let Ok(other_limits) = other.extract::<HttpLimits>() {
            Ok(self.max_connections == other_limits.max_connections &&
               self.max_keepalive_connections == other_limits.max_keepalive_connections &&
               (self.keepalive_expiry - other_limits.keepalive_expiry).abs() < f64::EPSILON)
        } else {
            Ok(false)
        }
    }
}

/// Basic authentication - minimal interface wrapper for hyper
#[pyclass(name = "BasicAuth", module = "faster_http")]
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
    // Actual authentication is handled by hyper during request sending
    fn auth_flow(&self, request: PyObject) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            // Simple placeholder implementation for httpx compatibility
            // The real auth logic happens in the Rust request sending code using hyper
            let iter = py.eval(
                "iter([request])",
                Some([("request", &request)].into_py_dict(py)),
                None,
            )?;
            Ok(iter.to_object(py))
        })
    }

    fn __repr__(&self) -> String {
        format!("<BasicAuth [username={:?}]>", self.username)
    }

    fn __eq__(&self, other: &pyo3::PyAny) -> PyResult<bool> {
        if let Ok(other_auth) = other.extract::<HttpBasicAuth>() {
            Ok(self.username == other_auth.username && self.password == other_auth.password)
        } else {
            Ok(false)
        }
    }

    fn __hash__(&self) -> PyResult<isize> {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        self.username.hash(&mut hasher);
        self.password.hash(&mut hasher);
        Ok(hasher.finish() as isize)
    }
}

impl HttpBasicAuth {
    pub fn to_tuple(&self) -> (String, String) {
        (self.username.clone(), self.password.clone())
    }
}

/// Digest authentication - minimal interface wrapper for hyper
#[pyclass(name = "DigestAuth", module = "faster_http")]
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
    // Actual digest authentication is handled by hyper during request sending
    fn auth_flow(&self, request: PyObject) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            // Simple placeholder implementation for httpx compatibility
            // The real digest auth logic happens in the Rust request sending code using hyper
            let iter = py.eval(
                "iter([request])",
                Some([("request", &request)].into_py_dict(py)),
                None,
            )?;
            Ok(iter.to_object(py))
        })
    }

    fn __repr__(&self) -> String {
        format!("<DigestAuth [username={:?}]>", self.username)
    }

    fn __eq__(&self, other: &pyo3::PyAny) -> PyResult<bool> {
        if let Ok(other_auth) = other.extract::<HttpDigestAuth>() {
            Ok(self.username == other_auth.username && self.password == other_auth.password)
        } else {
            Ok(false)
        }
    }

    fn __hash__(&self) -> PyResult<isize> {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        self.username.hash(&mut hasher);
        self.password.hash(&mut hasher);
        Ok(hasher.finish() as isize)
    }
}

impl HttpDigestAuth {
    pub fn to_tuple(&self) -> (String, String) {
        (self.username.clone(), self.password.clone())
    }
}

/// NetRC authentication - minimal interface wrapper for hyper
#[pyclass(name = "NetRCAuth", module = "faster_http")]
#[derive(Debug, Clone)]
pub struct HttpNetRCAuth {
    file: Option<String>,
}

#[pymethods]
impl HttpNetRCAuth {
    #[new]
    #[pyo3(signature = (file = None))]
    pub fn new(file: Option<String>) -> PyResult<Self> {
        let file_path = file.or_else(|| {
            // Default to ~/.netrc like httpx
            std::env::var("HOME")
                .ok()
                .map(|home| format!("{}/.netrc", home))
        });

        // Check if the file actually exists, like httpx does
        if let Some(ref path) = file_path {
            if !std::path::Path::new(path).exists() {
                return Err(pyo3::exceptions::PyFileNotFoundError::new_err(format!(
                    "[Errno 2] No such file or directory: '{}'",
                    path
                )));
            }
        } else {
            return Err(pyo3::exceptions::PyFileNotFoundError::new_err(
                "[Errno 2] No such file or directory: '~/.netrc'"
            ));
        }

        Ok(Self { file: file_path })
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
            let iter = py.eval(
                "iter([request])",
                Some([("request", &request)].into_py_dict(py)),
                None,
            )?;
            Ok(iter.to_object(py))
        })
    }

    fn __repr__(&self) -> String {
        "<NetRCAuth>".to_string()
    }
}
