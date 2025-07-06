use pyo3::prelude::*;
use bytes::Bytes;
use std::collections::HashMap;

// Request 对象
#[pyclass]
#[derive(Clone)]
pub struct HttpRequest {
    method: String,
    url: String,
    headers: HashMap<String, String>,
    content: Option<Bytes>,
}

#[pymethods]
impl HttpRequest {
    #[new]
    pub fn new(
        method: String,
        url: String,
        headers: Option<HashMap<String, String>>,
        content: Option<Vec<u8>>,
    ) -> Self {
        HttpRequest {
            method,
            url,
            headers: headers.unwrap_or_default(),
            content: content.map(Bytes::from),
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

    fn __repr__(&self) -> String {
        format!("<Request('{}', '{}')>", self.method, self.url)
    }
} 