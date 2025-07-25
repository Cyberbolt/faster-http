use pyo3::prelude::*;
use bytes::Bytes;
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
    pub fn new(
        method: String,
        url: String,
        headers: Option<HashMap<String, String>>,
        content: Option<Vec<u8>>,
        params: Option<HashMap<String, String>>,
        cookies: Option<HashMap<String, String>>,
        data: Option<PyObject>,
        files: Option<PyObject>,
        json: Option<PyObject>,
        stream: Option<bool>,
    ) -> Self {
        HttpRequest {
            method,
            url,
            headers: headers.unwrap_or_default(),
            content: content.map(Bytes::from),
            params: params.unwrap_or_default(),
            cookies: cookies.unwrap_or_default(),
            data,
            files,
            json,
            stream: stream.unwrap_or(false),
        }
    }

    #[getter]
    pub fn method(&self) -> &str {
        &self.method
    }

    #[getter]
    pub fn url(&self) -> &str {
        &self.url
    }

    #[getter]
    pub fn headers(&self) -> HashMap<String, String> {
        self.headers.clone()
    }

    #[getter]
    pub fn content(&self) -> Option<&[u8]> {
        self.content.as_ref().map(|b| b.as_ref())
    }

    #[getter]
    pub fn params(&self) -> HashMap<String, String> {
        self.params.clone()
    }

    #[getter]
    pub fn cookies(&self) -> HashMap<String, String> {
        self.cookies.clone()
    }

    #[getter]
    pub fn data(&self) -> Option<PyObject> {
        self.data.clone()
    }

    #[getter]
    pub fn files(&self) -> Option<PyObject> {
        self.files.clone()
    }

    #[getter]
    pub fn json(&self) -> Option<PyObject> {
        self.json.clone()
    }

    #[getter]
    pub fn stream(&self) -> bool {
        self.stream
    }

    fn __repr__(&self) -> String {
        format!("<Request('{}', '{}')>", self.method, self.url)
    }
} 