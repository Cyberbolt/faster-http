use bytes::Bytes;
use pyo3::prelude::*;
use std::collections::HashMap;

// Request 对象 - Enhanced version with full httpx compatibility
#[pyclass]
#[derive(Clone)]
pub struct HttpRequest {
    method: String,
    url: String,
    headers: HashMap<String, String>,
    content: Option<Bytes>,
    params: HashMap<String, String>,
    cookies: HashMap<String, String>,
    data: Option<PyObject>,  // Form data
    files: Option<PyObject>, // File uploads
    json: Option<PyObject>,  // JSON payload
    stream: bool,            // Stream flag
}

#[pymethods]
impl HttpRequest {
    #[new]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        method: String,
        url: String,
        headers: Option<PyObject>,
        content: Option<Vec<u8>>,
        params: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        data: Option<PyObject>,
        files: Option<PyObject>,
        json: Option<PyObject>,
        stream: Option<bool>,
    ) -> PyResult<Self> {
        let mut final_headers = HashMap::new();

        // Handle headers parameter - can be dict or Headers object
        if let Some(headers_obj) = headers {
            Python::with_gil(|py| -> PyResult<()> {
                if let Ok(dict) = headers_obj.extract::<HashMap<String, String>>(py) {
                    final_headers = dict;
                } else if let Ok(headers) = headers_obj.extract::<crate::models::HttpHeaders>(py) {
                    final_headers = headers.to_hashmap();
                } else {
                    return Err(pyo3::exceptions::PyTypeError::new_err(
                        "headers must be a dict or Headers object",
                    ));
                }
                Ok(())
            })?;
        }

        // Automatically add standard HTTP headers like httpx does
        if let Ok(parsed_url) = url::Url::parse(&url) {
            if let Some(host) = parsed_url.host_str() {
                // Add host header if not already present
                if !final_headers
                    .iter()
                    .any(|(k, _)| k.to_lowercase() == "host")
                {
                    final_headers.insert("host".to_string(), host.to_string());
                }
            }
        }

        // Handle JSON serialization like httpx does
        let mut final_content = content.map(Bytes::from);
        let final_json = json.clone();

        if let Some(json_obj) = &json {
            // Serialize JSON to content bytes
            Python::with_gil(|py| -> PyResult<()> {
                let json_module = py.import("json")?;
                let json_str = json_module
                    .call_method1("dumps", (json_obj,))?
                    .extract::<String>()?;
                final_content = Some(Bytes::from(json_str.into_bytes()));

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

        // Add or update content-length header if content is present
        if let Some(ref content_bytes) = final_content {
            // Always set content-length to match actual content (like httpx does)
            final_headers.insert(
                "content-length".to_string(),
                content_bytes.len().to_string(),
            );
        }

        Ok(HttpRequest {
            method,
            url,
            headers: final_headers,
            content: final_content,
            params: params.unwrap_or_default(),
            cookies: cookies.unwrap_or_default(),
            data,
            files,
            json: final_json,
            stream: stream.unwrap_or(false),
        })
    }

    // httpx-compatible public interface - matching httpx.Request instance attributes
    #[getter]
    pub fn method(&self) -> &str {
        &self.method
    }

    #[getter]
    pub fn url(&self) -> crate::models::HttpUrl {
        // Return URL object for httpx compatibility
        crate::models::HttpUrl::new(self.url.clone()).unwrap_or_else(|_| {
            // Fallback if URL parsing fails
            crate::models::HttpUrl::new("http://invalid".to_string()).unwrap()
        })
    }

    #[getter]
    pub fn headers(&self) -> crate::models::HttpHeaders {
        crate::models::HttpHeaders::new(Some(self.headers.clone()))
    }

    #[getter]
    pub fn content(&self, py: Python) -> PyResult<PyObject> {
        use pyo3::types::PyBytes;
        match &self.content {
            Some(bytes) => Ok(PyBytes::new(py, bytes).to_object(py)),
            None => Ok(PyBytes::new(py, b"").to_object(py)),
        }
    }

    #[getter]
    pub fn stream(&self) -> bool {
        self.stream
    }

    #[getter]
    pub fn extensions(&self, py: Python) -> PyResult<PyObject> {
        // Return empty dict for httpx compatibility
        use pyo3::types::PyDict;
        Ok(PyDict::new(py).to_object(py))
    }

    pub fn read(&self, py: Python) -> PyResult<PyObject> {
        use pyo3::types::PyBytes;
        match &self.content {
            Some(bytes) => Ok(PyBytes::new(py, bytes).to_object(py)),
            None => Ok(PyBytes::new(py, b"").to_object(py)),
        }
    }

    pub fn aread<'p>(&self, py: Python<'p>) -> PyResult<&'p pyo3::PyAny> {
        use pyo3_asyncio::tokio::future_into_py;
        let content = self.content.clone();

        future_into_py(py, async move {
            use pyo3::types::PyBytes;
            // Use with_gil directly without spawn_blocking to avoid async context conflicts
            Python::with_gil(|py| -> PyResult<pyo3::Py<PyBytes>> {
                match content {
                    Some(bytes) => Ok(PyBytes::new(py, &bytes).into()),
                    None => Ok(PyBytes::new(py, b"").into()),
                }
            })
        })
    }

    fn __repr__(&self) -> String {
        format!("<Request('{}', '{}')>", self.method, self.url)
    }
}

impl HttpRequest {
    // Internal constructor that avoids GIL - for use within Rust code
    #[allow(clippy::too_many_arguments)]
    pub fn new_internal(
        method: String,
        url: String,
        headers: HashMap<String, String>,
        content: Option<Vec<u8>>,
        params: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        data: Option<PyObject>,
        files: Option<PyObject>,
        json: Option<PyObject>,
        stream: Option<bool>,
    ) -> Self {
        Self {
            method,
            url,
            headers,
            content: content.map(Bytes::from),
            params: params.unwrap_or_default(),
            cookies: cookies.unwrap_or_default(),
            data,
            files,
            json,
            stream: stream.unwrap_or(false),
        }
    }

    // Internal methods for use within the crate - not exposed to Python
    pub fn method_str(&self) -> &str {
        &self.method
    }

    pub fn url_str(&self) -> &str {
        &self.url
    }

    pub fn headers_map(&self) -> &HashMap<String, String> {
        &self.headers
    }

    pub fn content_bytes(&self) -> Option<&Bytes> {
        self.content.as_ref()
    }

    pub fn params_internal(&self) -> &HashMap<String, String> {
        &self.params
    }

    pub fn cookies_internal(&self) -> &HashMap<String, String> {
        &self.cookies
    }

    pub fn data_internal(&self) -> &Option<PyObject> {
        &self.data
    }

    pub fn files_internal(&self) -> &Option<PyObject> {
        &self.files
    }

    pub fn json_internal(&self) -> &Option<PyObject> {
        &self.json
    }

    pub fn stream_internal(&self) -> bool {
        self.stream
    }
}
