use crate::core::error::HTTPStatusError;
use bytes::Bytes;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyBytes};
use serde_json::Value;
use std::collections::HashMap;


// Response object - fully aligned with httpx
#[pyclass(module = "faster_http")]
#[derive(Clone, Debug)]
pub struct HttpResponse {
    status_code: u16,
    headers: HashMap<String, String>,
    body: Bytes,
    url: String,
    elapsed: f64,
    is_redirect_status: bool,
    http_version: String,
    cookies: HashMap<String, String>,
    encoding: Option<String>,
    history: Vec<PyObject>,
    request: Option<PyObject>,
    num_bytes_downloaded: usize,
    // httpx extensions
    extensions: HashMap<String, PyObject>,
    next_request: Option<PyObject>,
    // Internal state
    _closed: bool,
}

impl HttpResponse {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        status_code: u16,
        headers: HashMap<String, String>,
        body: Bytes,
        url: String,
        elapsed: f64,
        is_redirect_status: bool,
        http_version: String,
        cookies: HashMap<String, String>,
        encoding: Option<String>,
        history: Vec<PyObject>,
        request: Option<PyObject>,
        num_bytes_downloaded: usize,
    ) -> Self {
        // Prepare extensions before building the struct
        let extensions = {
            let mut ext = HashMap::new();
            Python::with_gil(|py| {
                // Add http_version as bytes (similar to httpx)
                let http_version_bytes = pyo3::types::PyBytes::new(py, http_version.as_bytes()).to_object(py);
                ext.insert("http_version".to_string(), http_version_bytes);
                
                // Add reason_phrase as bytes (similar to httpx) 
                let reason = match status_code {
                    200 => "OK",
                    201 => "Created",
                    202 => "Accepted", 
                    204 => "No Content",
                    301 => "Moved Permanently",
                    302 => "Found",
                    303 => "See Other",
                    304 => "Not Modified",
                    307 => "Temporary Redirect",
                    308 => "Permanent Redirect",
                    400 => "Bad Request",
                    401 => "Unauthorized",
                    403 => "Forbidden",
                    404 => "Not Found",
                    405 => "Method Not Allowed",
                    408 => "Request Timeout",
                    409 => "Conflict", 
                    410 => "Gone",
                    422 => "Unprocessable Entity",
                    429 => "Too Many Requests",
                    500 => "Internal Server Error",
                    501 => "Not Implemented",
                    502 => "Bad Gateway",
                    503 => "Service Unavailable",
                    504 => "Gateway Timeout",
                    _ => "Unknown Status",
                };
                let reason_bytes = pyo3::types::PyBytes::new(py, reason.as_bytes()).to_object(py);
                ext.insert("reason_phrase".to_string(), reason_bytes);
            });
            ext
        };

        // Ensure request is always available - create default if None
        let final_request = request.or_else(|| {
            // Create a default HttpRequest object if none provided
            Python::with_gil(|py| {
                crate::models::request::HttpRequest::new(
                    "GET".to_string(),
                    url.clone(),
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ).ok().and_then(|req| Py::new(py, req).ok().map(|obj| obj.to_object(py)))
            })
        });

        HttpResponse {
            status_code,
            headers,
            body,
            url,
            elapsed,
            is_redirect_status,
            http_version,
            cookies,
            encoding,
            history,
            request: final_request,
            num_bytes_downloaded,
            extensions,
            next_request: None,
            _closed: true, // Response is closed after reading the entire content
        }
    }
}

#[pymethods]
impl HttpResponse {
    // Python constructor for creating mock Response objects - httpx compatible
    #[new]
    #[pyo3(signature = (
        status_code,
        *,
        headers = None,
        content = None,
        text = None,
        html = None,
        json = None,
        _stream = None,
        request = None,
        extensions = None,
        history = None,
        default_encoding = "utf-8"
    ))]
    #[allow(clippy::too_many_arguments)]
    pub fn py_new(
        status_code: u16,
        headers: Option<HashMap<String, String>>,
        content: Option<Vec<u8>>,
        text: Option<String>,
        html: Option<String>,
        json: Option<PyObject>,
        _stream: Option<PyObject>,
        request: Option<PyObject>,
        extensions: Option<HashMap<String, PyObject>>,
        history: Option<Vec<PyObject>>,
        default_encoding: &str,
    ) -> PyResult<Self> {
        // Determine content based on parameters (text, html, json, or content)
        let body = if let Some(content_bytes) = content {
            Bytes::from(content_bytes)
        } else if let Some(text_str) = text {
            Bytes::from(text_str.as_bytes().to_vec())
        } else if let Some(html_str) = html {
            Bytes::from(html_str.as_bytes().to_vec())
        } else if let Some(json_obj) = json {
            // Convert JSON object to bytes
            Python::with_gil(|py| -> PyResult<Bytes> {
                let json_str = py.import("json")?.call_method1("dumps", (json_obj,))?;
                let json_bytes = json_str.extract::<String>()?;
                Ok(Bytes::from(json_bytes.as_bytes().to_vec()))
            })?
        } else {
            Bytes::from("")
        };

        let mut response = HttpResponse::new(
            status_code,
            headers.unwrap_or_default(),
            body,
            "http://example.com".to_string(), // Default URL for mock responses
            0.0, // elapsed
            (300..400).contains(&status_code), // is_redirect_status
            "HTTP/1.1".to_string(),
            HashMap::new(), // cookies
            Some(default_encoding.to_string()),
            history.unwrap_or_default(),
            request,
            0, // num_bytes_downloaded
        );

        // Set extensions if provided
        if let Some(ext) = extensions {
            response.extensions = ext;
        }

        Ok(response)
    }
    // ==================== Basic properties ====================
    #[getter]
    pub fn status_code(&self) -> u16 {
        self.status_code
    }

    #[getter]
    pub fn headers(&self) -> crate::models::HttpHeaders {
        // Return Headers object to maintain httpx compatibility
        crate::models::HttpHeaders::new(Some(self.headers.clone()))
    }

    #[getter]
    pub fn url(&self) -> PyResult<crate::models::HttpUrl> {
        // Return URL object to maintain httpx compatibility
        crate::models::HttpUrl::new(self.url.clone())
    }

    #[getter]
    pub fn elapsed(&self) -> PyResult<PyObject> {
        // Return datetime.timedelta object to maintain httpx compatibility
        Python::with_gil(|py| {
            let datetime = py.import("datetime")?;
            let timedelta = datetime.getattr("timedelta")?;
            // Use seconds parameter instead of days
            timedelta
                .call((), Some([("seconds", self.elapsed)].into_py_dict(py)))
                .map(|obj| obj.to_object(py))
        })
    }

    #[getter]
    pub fn http_version(&self) -> &str {
        // Return string reference, avoid clone
        &self.http_version
    }

    #[getter]
    pub fn cookies(&self) -> crate::models::HttpCookies {
        // Return Cookies object to maintain httpx compatibility
        crate::models::HttpCookies::new(Some(self.cookies.clone()))
    }

    #[getter]
    pub fn encoding(&self) -> Option<&str> {
        // Return Option of string reference, avoid clone
        self.encoding.as_deref()
    }

    #[getter]
    pub fn num_bytes_downloaded(&self) -> usize {
        self.num_bytes_downloaded
    }

    // ==================== httpx standard properties ====================
    #[getter]
    pub fn is_redirect(&self) -> bool {
        // HTTP redirect status codes: 3xx series
        matches!(self.status_code, 300..=399)
    }

    // Removed: ok() method - httpx uses is_success() instead

    #[getter]
    pub fn is_client_error(&self) -> bool {
        (400..500).contains(&self.status_code)
    }

    #[getter]
    pub fn is_server_error(&self) -> bool {
        self.status_code >= 500
    }

    #[getter]
    pub fn is_error(&self) -> bool {
        self.status_code >= 400
    }

    #[getter]
    pub fn is_success(&self) -> bool {
        (200..300).contains(&self.status_code)
    }

    #[getter]
    pub fn is_informational(&self) -> bool {
        (100..200).contains(&self.status_code)
    }

    #[getter]
    pub fn history(&self) -> Vec<PyObject> {
        self.history.clone()
    }

    /// Create a new response with the same data but different history
    pub fn with_history(&self, new_history: Vec<PyObject>) -> Self {
        Self {
            status_code: self.status_code,
            headers: self.headers.clone(),
            body: self.body.clone(),
            url: self.url.clone(),
            elapsed: self.elapsed,
            is_redirect_status: self.is_redirect_status,
            http_version: self.http_version.clone(),
            cookies: self.cookies.clone(),
            encoding: self.encoding.clone(),
            history: new_history,
            request: self.request.clone(),
            num_bytes_downloaded: self.num_bytes_downloaded,
            extensions: self.extensions.clone(),
            next_request: self.next_request.clone(),
            _closed: self._closed,
        }
    }

    #[getter]
    pub fn request(&self) -> Option<PyObject> {
        self.request.clone()
    }

    #[getter]
    pub fn extensions(&self) -> HashMap<String, PyObject> {
        self.extensions.clone()
    }

    #[getter]
    pub fn next_request(&self) -> Option<PyObject> {
        self.next_request.clone()
    }

    // ==================== Content access ====================
    #[getter]
    pub fn content(&self, py: Python) -> PyResult<PyObject> {
        // Return real bytes object, not &[u8]
        Ok(PyBytes::new(py, &self.body).to_object(py))
    }

    #[getter]
    pub fn text(&self) -> PyResult<String> {
        let encoding = self.encoding.as_deref().unwrap_or("utf-8");

        match encoding.to_lowercase().as_str() {
            "utf-8" | "utf8" => Ok(String::from_utf8_lossy(&self.body).to_string()),
            "latin-1" | "iso-8859-1" => {
                // Latin-1 each byte corresponds to one Unicode code point
                let text = self.body.iter().map(|&b| b as char).collect::<String>();
                Ok(text)
            }
            _ => {
                // Other encodings, try UTF-8, fallback to latin-1 if failed
                match String::from_utf8(self.body.to_vec()) {
                    Ok(text) => Ok(text),
                    Err(_) => {
                        let text = self.body.iter().map(|&b| b as char).collect::<String>();
                        Ok(text)
                    }
                }
            }
        }
    }

    pub fn json(&self, py: Python) -> PyResult<PyObject> {
        let text = self.text()?;
        let json_value: Value = serde_json::from_str(&text)
            .map_err(|e| PyValueError::new_err(format!("JSON decode error: {e}")))?;
        pythonize::pythonize(py, &json_value)
            .map_err(|e| PyValueError::new_err(format!("Failed to convert JSON to Python: {e}")))
    }

    // ==================== Streaming methods ====================
    pub fn iter_bytes(&self, chunk_size: Option<usize>) -> PyResult<PyObject> {
        let chunk_size = chunk_size.unwrap_or(8192);
        let body = self.body.clone();

        Python::with_gil(|py| {
            // Create a Python generator that yields bytes chunks
            let code = r#"
def iter_bytes_impl(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i+chunk_size]

iter_bytes_impl(data, chunk_size)
"#;

            let locals = pyo3::types::PyDict::new(py);
            locals.set_item("data", pyo3::types::PyBytes::new(py, &body))?;
            locals.set_item("chunk_size", chunk_size)?;
            py.run(code, None, Some(locals))?;
            Ok(locals
                .get_item("iter_bytes_impl")?
                .ok_or_else(|| crate::error::InternalError::new_err("Failed to get iter_bytes_impl from locals"))?
                .call1((pyo3::types::PyBytes::new(py, &body), chunk_size))?
                .to_object(py))
        })
    }

    pub fn iter_text(&self, chunk_size: Option<usize>) -> PyResult<PyObject> {
        let chunk_size = chunk_size.unwrap_or(8192);
        let text = self.text()?;

        Python::with_gil(|py| {
            // Create a Python generator that yields text chunks
            let code = r#"
def iter_text_impl(text, chunk_size):
    for i in range(0, len(text), chunk_size):
        yield text[i:i+chunk_size]

iter_text_impl(text, chunk_size)
"#;

            let locals = pyo3::types::PyDict::new(py);
            locals.set_item("text", text.clone())?;
            locals.set_item("chunk_size", chunk_size)?;
            py.run(code, None, Some(locals))?;
            Ok(locals
                .get_item("iter_text_impl")?
                .ok_or_else(|| crate::error::InternalError::new_err("Failed to get iter_text_impl from locals"))?
                .call1((text, chunk_size))?
                .to_object(py))
        })
    }

    pub fn iter_lines(&self) -> PyResult<PyObject> {
        let text = self.text()?;

        Python::with_gil(|py| {
            // Create a Python generator that yields lines
            let lines: Vec<String> = text.lines().map(|line| line.to_string()).collect();
            let py_lines = lines.to_object(py);

            let code = r#"
def iter_lines_impl(lines):
    for line in lines:
        yield line

iter_lines_impl(lines)
"#;

            let locals = pyo3::types::PyDict::new(py);
            locals.set_item("lines", py_lines.clone())?;
            py.run(code, None, Some(locals))?;
            Ok(locals
                .get_item("iter_lines_impl")?
                .ok_or_else(|| crate::error::InternalError::new_err("Failed to get iter_lines_impl from locals"))?
                .call1((py_lines,))?
                .to_object(py))
        })
    }

    pub fn iter_raw(&self, chunk_size: Option<usize>) -> PyResult<PyObject> {
        // iter_raw is the same as iter_bytes, representing raw unencoded data
        self.iter_bytes(chunk_size)
    }

    // ==================== Read methods - httpx compatible ====================
    pub fn read(&self) -> PyResult<Py<PyBytes>> {
        // Synchronous read - return the entire response body
        Python::with_gil(|py| Ok(PyBytes::new(py, &self.body).into()))
    }

    pub fn aread<'p>(&self, py: Python<'p>) -> PyResult<&'p PyAny> {
        // Asynchronous read - return the entire response body
        use pyo3_asyncio::tokio::future_into_py;
        let body = self.body.clone();

        future_into_py(py, async move {
            // Use with_gil directly without spawn_blocking to avoid async context conflicts
            Python::with_gil(|py| -> PyResult<Py<PyBytes>> { 
                Ok(PyBytes::new(py, &body).into()) 
            })
        })
    }

    // Removed next() and anext() methods - httpx only provides next_request property

    // ==================== Next request property ====================
    #[setter]
    pub fn set_next_request(&mut self, request: Option<PyObject>) {
        self.next_request = request;
    }

    // ==================== Other methods ====================
    pub fn raise_for_status(&self) -> PyResult<()> {
        if self.status_code >= 400 {
            let (request_obj, response_obj) = Python::with_gil(|py| {
                // Convert self to PyObject
                let response = Py::new(py, self.clone()).map(|obj| obj.to_object(py)).ok();
                // Get the request object from self.request
                let request = self.request.clone();
                (request, response)
            });

            return Err(HTTPStatusError::new_err_with_request_response(
                format!("HTTP {} error for url: {}", self.status_code, self.url),
                request_obj,
                response_obj,
            ));
        }
        Ok(())
    }

    pub fn close(&mut self) -> PyResult<()> {
        self._closed = true;
        Ok(())
    }

    #[getter]
    pub fn is_closed(&self) -> bool {
        self._closed
    }

    // ==================== httpx compatibility properties ====================
    #[getter]
    pub fn default_encoding(&self) -> &str {
        "utf-8"
    }

    #[getter]
    pub fn charset_encoding(&self) -> Option<&str> {
        self.encoding.as_deref()
    }

    #[getter]
    pub fn is_stream_consumed(&self) -> bool {
        true // We always cache the entire response, so stream is always consumed
    }

    // ==================== Extensions manipulation ====================
    // Removed get_extension method - httpx only provides extensions property

    // Removed extension manipulation methods - httpx only provides read-only extensions property

    // Removed request and history manipulation methods - httpx only provides read-only properties

    #[getter]
    pub fn has_redirect_location(&self) -> bool {
        self.headers.contains_key("location") || self.headers.contains_key("Location")
    }

    // Removed redirect_location method - httpx only provides has_redirect_location

    // ==================== Additional httpx compatibility ====================
    #[getter]
    pub fn reason_phrase(&self) -> String {
        match self.status_code {
            200 => "OK",
            201 => "Created",
            202 => "Accepted",
            204 => "No Content",
            301 => "Moved Permanently",
            302 => "Found",
            303 => "See Other",
            304 => "Not Modified",
            307 => "Temporary Redirect",
            308 => "Permanent Redirect",
            400 => "Bad Request",
            401 => "Unauthorized",
            403 => "Forbidden",
            404 => "Not Found",
            405 => "Method Not Allowed",
            408 => "Request Timeout",
            409 => "Conflict",
            410 => "Gone",
            422 => "Unprocessable Entity",
            429 => "Too Many Requests",
            500 => "Internal Server Error",
            501 => "Not Implemented",
            502 => "Bad Gateway",
            503 => "Service Unavailable",
            504 => "Gateway Timeout",
            _ => "Unknown Status",
        }
        .to_string()
    }

    #[getter]
    pub fn links(&self) -> HashMap<String, HashMap<String, String>> {
        let mut links = HashMap::new();

        if let Some(link_header) = self
            .headers
            .get("link")
            .or_else(|| self.headers.get("Link"))
        {
            // Parse Link header according to RFC 5988
            for link_part in link_header.split(',') {
                let link_part = link_part.trim();
                
                // Extract URL first
                if let Some(url_start) = link_part.find('<') {
                    if let Some(url_end) = link_part.find('>') {
                        let url = link_part.get(url_start + 1..url_end).unwrap_or("").to_string();
                        
                        // Parse all attributes after the URL
                        let attributes_part = link_part.get(url_end + 1..).unwrap_or("");
                        let mut link_info = HashMap::new();
                        link_info.insert("url".to_string(), url);
                        
                        let mut rel_value = String::new();
                        
                        // Parse all attributes separated by semicolons
                        for attr_part in attributes_part.split(';') {
                            let attr_part = attr_part.trim();
                            if let Some(eq_pos) = attr_part.find('=') {
                                let key = attr_part[..eq_pos].trim();
                                let value = attr_part[eq_pos + 1..]
                                    .trim()
                                    .trim_matches('"')
                                    .trim_matches('\'')
                                    .to_string();
                                
                                link_info.insert(key.to_string(), value.clone());
                                
                                // Keep track of rel value for the key
                                if key == "rel" {
                                    rel_value = value;
                                }
                            }
                        }
                        
                        // Only add to links if we found a rel attribute
                        if !rel_value.is_empty() {
                            links.insert(rel_value, link_info);
                        }
                    }
                }
            }
        }

        links
    }

    // ==================== Sync versions of async methods ====================
    pub fn aclose(&self) -> PyResult<()> {
        // Async version of close, but return directly in sync environment
        Ok(())
    }

    pub fn stream(&self) -> PyResult<()> {
        // Streaming access (no-op in our implementation)
        Ok(())
    }

    // ==================== Async iterator methods ====================
    #[allow(clippy::needless_borrow)]
    pub fn aiter_bytes(&self, chunk_size: Option<usize>) -> PyResult<PyObject> {
        let chunk_size = chunk_size.unwrap_or(8192);
        let body = self.body.clone();

        Python::with_gil(|py| {
            // Create Python bytes object from the body data
            let py_bytes = pyo3::types::PyBytes::new(py, &body);

            let code = r#"
async def aiter_bytes_impl(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i+chunk_size]

aiter_bytes_impl(data, chunk_size)
"#
            .to_string();

            let locals = pyo3::types::PyDict::new(py);
            locals.set_item("data", py_bytes)?;
            locals.set_item("chunk_size", chunk_size)?;
            py.run(&code, None, Some(locals))?;
            Ok(locals
                .get_item("aiter_bytes_impl")?
                .ok_or_else(|| crate::error::InternalError::new_err("Failed to get aiter_bytes_impl from locals"))?
                .call1((py_bytes, chunk_size))?
                .to_object(py))
        })
    }

    #[allow(clippy::needless_borrow)]
    pub fn aiter_text(&self, chunk_size: Option<usize>) -> PyResult<PyObject> {
        let chunk_size = chunk_size.unwrap_or(8192);
        let text = self.text()?;

        Python::with_gil(|py| {
            let code = r#"
async def aiter_text_impl(text, chunk_size):
    for i in range(0, len(text), chunk_size):
        yield text[i:i+chunk_size]

aiter_text_impl(text, chunk_size)
"#;

            let locals = pyo3::types::PyDict::new(py);
            locals.set_item("text", text.clone())?;
            locals.set_item("chunk_size", chunk_size)?;
            py.run(&code, None, Some(locals))?;
            Ok(locals
                .get_item("aiter_text_impl")?
                .ok_or_else(|| crate::error::InternalError::new_err("Failed to get aiter_text_impl from locals"))?
                .call1((text, chunk_size))?
                .to_object(py))
        })
    }

    #[allow(clippy::needless_borrow)]
    pub fn aiter_lines(&self) -> PyResult<PyObject> {
        let text = self.text()?;

        Python::with_gil(|py| {
            let lines: Vec<String> = text.lines().map(|line| line.to_string()).collect();
            let py_lines = lines.to_object(py);

            let code = r#"
async def aiter_lines_impl(lines):
    for line in lines:
        yield line

aiter_lines_impl(lines)
"#;

            let locals = pyo3::types::PyDict::new(py);
            locals.set_item("lines", py_lines.clone())?;
            py.run(&code, None, Some(locals))?;
            Ok(locals
                .get_item("aiter_lines_impl")?
                .ok_or_else(|| crate::error::InternalError::new_err("Failed to get aiter_lines_impl from locals"))?
                .call1((py_lines,))?
                .to_object(py))
        })
    }

    pub fn aiter_raw(&self, chunk_size: Option<usize>) -> PyResult<PyObject> {
        // aiter_raw is same as aiter_bytes for raw data
        self.aiter_bytes(chunk_size)
    }

    // ==================== Python special methods ====================
    fn __repr__(&self) -> String {
        format!("<Response [{}]>", self.status_code)
    }

    fn __enter__(slf: PyRefMut<Self>) -> PyResult<PyRefMut<Self>> {
        Ok(slf)
    }

    fn __exit__(
        #[allow(unused_mut)] mut slf: PyRefMut<Self>,
        _exc_type: Option<PyObject>,
        _exc_value: Option<PyObject>,
        _traceback: Option<PyObject>,
    ) -> PyResult<bool> {
        slf.close()?;
        Ok(false)
    }
}

// ==================== Utility functions ====================

// Parse cookies from headers
#[allow(dead_code)]
pub fn parse_cookies_from_headers(headers: &HashMap<String, String>) -> HashMap<String, String> {
    let mut cookies = HashMap::new();

    for (key, value) in headers {
        if key.to_lowercase() == "set-cookie" {
            // Each Set-Cookie header is independent, should not be split by comma
            // Because cookie values themselves may contain commas
            if let Some(cookie_pair) = value.split(';').next() {
                if let Some((name, val)) = cookie_pair.split_once('=') {
                    cookies.insert(
                        name.trim().to_string(),
                        val.trim().trim_matches('"').to_string(),
                    );
                }
            }
        }
    }

    cookies
}

// Detect encoding
#[allow(dead_code)]
pub fn detect_encoding(headers: &HashMap<String, String>) -> Option<String> {
    // 1. First check Content-Type header
    if let Some(content_type) = headers.get("content-type") {
        if let Some(charset_start) = content_type.to_lowercase().find("charset=") {
            let charset = content_type.get(charset_start + 8..).unwrap_or("");
            let charset = charset.split(';').next().unwrap_or(charset);
            let charset = charset.trim().trim_matches('"').trim_matches('\'');

            // Normalize encoding name
            let normalized = normalize_encoding_name(charset);
            if !normalized.is_empty() {
                return Some(normalized);
            }
        }
    }

    // 2. Default to UTF-8
    Some("utf-8".to_string())
}

// Normalize encoding name
#[allow(dead_code)]
fn normalize_encoding_name(encoding: &str) -> String {
    let normalized = encoding.to_lowercase().replace(['_', '-'], "");

    match normalized.as_str() {
        "utf8" | "utf-8" => "utf-8".to_string(),
        "latin1" | "iso88591" | "iso-8859-1" => "latin-1".to_string(),
        "ascii" | "us-ascii" => "ascii".to_string(),
        "cp1252" | "windows1252" => "cp1252".to_string(),
        _ => encoding.to_lowercase(),
    }
}

// Detect HTTP version - updated for hyper
#[allow(dead_code)]
pub fn detect_http_version(version: &hyper::Version) -> String {
    match *version {
        hyper::Version::HTTP_09 => "HTTP/0.9".to_string(),
        hyper::Version::HTTP_10 => "HTTP/1.0".to_string(),
        hyper::Version::HTTP_11 => "HTTP/1.1".to_string(),
        hyper::Version::HTTP_2 => "HTTP/2".to_string(),
        hyper::Version::HTTP_3 => "HTTP/3".to_string(),
        _ => "HTTP/1.1".to_string(), // Default value
    }
}

// Implement ToPyObject for HttpResponse to enable Python conversion
impl pyo3::ToPyObject for HttpResponse {
    fn to_object(&self, py: Python) -> PyObject {
        // Return the PyClass instance as a PyObject
        self.clone().into_py(py)
    }
}
