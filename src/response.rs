use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::{PyBytes, IntoPyDict};
use bytes::Bytes;
use serde_json::Value;
use std::collections::HashMap;
use crate::error::HTTPError;

// 响应对象 - 生产级版本，与 httpx 完全对齐
#[pyclass]
#[derive(Clone)]
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
    // httpx 扩展
    extensions: HashMap<String, PyObject>,
    next_request: Option<PyObject>,
    // 内部状态
    _closed: bool,
}

impl HttpResponse {
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
            request,
            num_bytes_downloaded,
            extensions: HashMap::new(),
            next_request: None,
            _closed: false,
        }
    }
}

#[pymethods]
impl HttpResponse {
    // ==================== 基本属性 - 优化版本 ====================
    #[getter]
    pub fn status_code(&self) -> u16 {
        self.status_code
    }

    #[getter]
    pub fn headers(&self) -> crate::models::HttpHeaders {
        // 返回 Headers 对象以保持与 httpx 兼容
        crate::models::HttpHeaders::new(Some(self.headers.clone()))
    }

    #[getter]
    pub fn url(&self) -> crate::models::HttpUrl {
        // 返回 URL 对象以保持与 httpx 兼容
        crate::models::HttpUrl::new(self.url.clone())
    }

    #[getter]
    pub fn elapsed(&self) -> PyResult<PyObject> {
        // 返回 datetime.timedelta 对象以保持与 httpx 兼容
        Python::with_gil(|py| {
            let datetime = py.import("datetime")?;
            let timedelta = datetime.getattr("timedelta")?;
            // 使用 seconds 参数而不是 days
            timedelta.call((), Some([("seconds", self.elapsed)].into_py_dict(py))).map(|obj| obj.to_object(py))
        })
    }

    #[getter]
    pub fn http_version(&self) -> &str {
        // 返回字符串引用，避免clone
        &self.http_version
    }

    #[getter]
    pub fn cookies(&self) -> crate::models::HttpCookies {
        // 返回 Cookies 对象以保持与 httpx 兼容
        crate::models::HttpCookies::new(Some(self.cookies.clone()))
    }

    #[getter]
    pub fn encoding(&self) -> Option<&str> {
        // 返回字符串引用的Option，避免clone
        self.encoding.as_deref()
    }

    #[getter]
    pub fn num_bytes_downloaded(&self) -> usize {
        self.num_bytes_downloaded
    }

    // ==================== httpx 标准属性 ====================
    #[getter]
    pub fn is_redirect(&self) -> bool {
        self.is_redirect_status
    }

    #[getter]
    pub fn ok(&self) -> bool {
        self.status_code >= 200 && self.status_code < 300
    }

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

    // ==================== 内容访问 ====================
    #[getter]
    pub fn content(&self, py: Python) -> PyResult<PyObject> {
        // 返回真正的 bytes 对象，不是 &[u8]
        Ok(PyBytes::new(py, &self.body).to_object(py))
    }

    #[getter]
    pub fn text(&self) -> PyResult<String> {
        let encoding = self.encoding.as_deref().unwrap_or("utf-8");
        
        match encoding.to_lowercase().as_str() {
            "utf-8" | "utf8" => {
                Ok(String::from_utf8_lossy(&self.body).to_string())
            }
            "latin-1" | "iso-8859-1" => {
                // Latin-1 每个字节对应一个 Unicode 码点
                let text = self.body.iter()
                    .map(|&b| b as char)
                    .collect::<String>();
                Ok(text)
            }
            _ => {
                // 其他编码，尝试 UTF-8，失败则用 latin-1
                match String::from_utf8(self.body.to_vec()) {
                    Ok(text) => Ok(text),
                    Err(_) => {
                        let text = self.body.iter()
                            .map(|&b| b as char)
                            .collect::<String>();
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

    // ==================== 流式方法 - 生产级实现 ====================
    pub fn iter_bytes(&self, chunk_size: Option<usize>) -> PyResult<Vec<Py<PyBytes>>> {
        let chunk_size = chunk_size.unwrap_or(8192);
        let mut chunks = Vec::new();
        
        Python::with_gil(|py| {
            for chunk in self.body.chunks(chunk_size) {
                chunks.push(PyBytes::new(py, chunk).into());
            }
            Ok(chunks)
        })
    }

    pub fn iter_text(&self, chunk_size: Option<usize>) -> PyResult<Vec<String>> {
        let chunk_size = chunk_size.unwrap_or(8192);
        let text = self.text()?;
        let mut text_chunks = Vec::new();
        let chars: Vec<char> = text.chars().collect();
        
        let mut pos = 0;
        while pos < chars.len() {
            let end = std::cmp::min(pos + chunk_size, chars.len());
            let chunk: String = chars[pos..end].iter().collect();
            text_chunks.push(chunk);
            pos = end;
        }
        
        Ok(text_chunks)
    }

    pub fn iter_lines(&self) -> PyResult<Vec<String>> {
        let text = self.text()?;
        let lines: Vec<String> = text.lines().map(|line| line.to_string()).collect();
        Ok(lines)
    }

    pub fn iter_raw(&self, chunk_size: Option<usize>) -> PyResult<Vec<Py<PyBytes>>> {
        // iter_raw 与 iter_bytes 相同，表示未解码的原始数据
        self.iter_bytes(chunk_size)
    }

    // ==================== Read methods - httpx compatible ====================
    pub fn read(&self) -> PyResult<Py<PyBytes>> {
        // Synchronous read - return the entire response body
        Python::with_gil(|py| {
            Ok(PyBytes::new(py, &self.body).into())
        })
    }

    pub fn aread<'p>(&self, py: Python<'p>) -> PyResult<&'p PyAny> {
        // Asynchronous read - return the entire response body
        use pyo3_asyncio::tokio::future_into_py;
        let body = self.body.clone();
        
        future_into_py(py, async move {
            Python::with_gil(|py| -> PyResult<Py<PyBytes>> {
                Ok(PyBytes::new(py, &body).into())
            })
        })
    }

    // ==================== Next methods for redirect handling ====================
    pub fn next(&self) -> PyResult<Option<PyObject>> {
        // Return the next response in redirect chain (synchronous)
        Ok(self.next_request.clone())
    }

    pub fn anext<'p>(&self, py: Python<'p>) -> PyResult<&'p PyAny> {
        // Asynchronous version of next()
        use pyo3_asyncio::tokio::future_into_py;
        let next_request = self.next_request.clone();
        
        future_into_py(py, async move {
            Ok(next_request)
        })
    }

    // ==================== Next request property ====================
    #[setter]
    pub fn set_next_request(&mut self, request: Option<PyObject>) {
        self.next_request = request;
    }

    // ==================== 其他方法 ====================
    pub fn raise_for_status(&self) -> PyResult<()> {
        if self.status_code >= 400 {
            return Err(HTTPError::new_err(format!(
                "HTTP {} error for url: {}",
                self.status_code, self.url
            )));
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

    // ==================== httpx 兼容性属性 ====================
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
        false  // 我们总是缓存整个响应
    }

    // ==================== Extensions manipulation ====================
    pub fn get_extension(&self, key: &str) -> Option<PyObject> {
        self.extensions.get(key).cloned()
    }

    pub fn set_extension(&mut self, key: String, value: PyObject) {
        self.extensions.insert(key, value);
    }

    pub fn has_extension(&self, key: &str) -> bool {
        self.extensions.contains_key(key)
    }

    pub fn remove_extension(&mut self, key: &str) -> Option<PyObject> {
        self.extensions.remove(key)
    }

    pub fn clear_extensions(&mut self) {
        self.extensions.clear();
    }

    // ==================== Request association ====================
    pub fn set_request(&mut self, request: PyObject) {
        self.request = Some(request);
    }

    pub fn clear_request(&mut self) {
        self.request = None;
    }

    // ==================== History manipulation ====================
    pub fn add_history_entry(&mut self, response: PyObject) {
        self.history.push(response);
    }

    pub fn clear_history(&mut self) {
        self.history.clear();
    }

    #[getter] 
    pub fn has_redirect_location(&self) -> bool {
        self.headers.contains_key("location") || self.headers.contains_key("Location")
    }

    #[getter]
    pub fn redirect_location(&self) -> Option<String> {
        self.headers.get("location")
            .or_else(|| self.headers.get("Location"))
            .cloned()
    }

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
            _ => "Unknown Status"
        }.to_string()
    }

    #[getter]
    pub fn links(&self) -> HashMap<String, HashMap<String, String>> {
        let mut links = HashMap::new();
        
        if let Some(link_header) = self.headers.get("link").or_else(|| self.headers.get("Link")) {
            // Parse Link header according to RFC 5988
            for link_part in link_header.split(',') {
                let link_part = link_part.trim();
                if let Some(rel_start) = link_part.find("rel=") {
                    if let Some(url_end) = link_part.find('>') {
                        if let Some(url_start) = link_part.find('<') {
                            let url = link_part[url_start + 1..url_end].to_string();
                            let rel_part = &link_part[rel_start + 4..];
                            let rel = rel_part.split(';').next().unwrap_or("").trim_matches('"').trim();
                            
                            let mut link_info = HashMap::new();
                            link_info.insert("url".to_string(), url);
                            links.insert(rel.to_string(), link_info);
                        }
                    }
                }
            }
        }
        
        links
    }

    // ==================== 异步方法的同步版本 ====================
    pub fn aclose(&self) -> PyResult<()> {
        // 异步版本的 close，但在同步环境中直接返回
        Ok(())
    }


    pub fn stream(&self) -> PyResult<()> {
        // 流式访问（在我们的实现中是 no-op）
        Ok(())
    }

    // ==================== 异步迭代器方法 ====================
    // 为了简化和兼容性，返回同步数据，让Python端包装为异步迭代器
    pub fn aiter_bytes(&self, chunk_size: Option<usize>) -> PyResult<Vec<Py<PyBytes>>> {
        self.iter_bytes(chunk_size)
    }

    pub fn aiter_text(&self, chunk_size: Option<usize>) -> PyResult<Vec<String>> {
        self.iter_text(chunk_size)
    }

    pub fn aiter_lines(&self) -> PyResult<Vec<String>> {
        self.iter_lines()
    }

    pub fn aiter_raw(&self, chunk_size: Option<usize>) -> PyResult<Vec<Py<PyBytes>>> {
        self.iter_raw(chunk_size)
    }

    // ==================== Python 特殊方法 ====================
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

// ==================== 工具函数 ====================

// 从 headers 解析 cookies  
pub fn parse_cookies_from_headers(headers: &HashMap<String, String>) -> HashMap<String, String> {
    let mut cookies = HashMap::new();
    
    for (key, value) in headers {
        if key.to_lowercase() == "set-cookie" {
            // 每个 Set-Cookie 头都是独立的，不应该用逗号分割
            // 因为 cookie 值本身可能包含逗号
            if let Some(cookie_pair) = value.split(';').next() {
                if let Some((name, val)) = cookie_pair.split_once('=') {
                    cookies.insert(
                        name.trim().to_string(), 
                        val.trim().trim_matches('"').to_string()
                    );
                }
            }
        }
    }
    
    cookies
}

// 检测编码 - 生产级实现
pub fn detect_encoding(headers: &HashMap<String, String>) -> Option<String> {
    // 1. 首先检查 Content-Type 头
    if let Some(content_type) = headers.get("content-type") {
        if let Some(charset_start) = content_type.to_lowercase().find("charset=") {
            let charset = &content_type[charset_start + 8..];
            let charset = charset.split(';').next().unwrap_or(charset);
            let charset = charset.trim().trim_matches('"').trim_matches('\'');
            
            // 标准化编码名称
            let normalized = normalize_encoding_name(charset);
            if !normalized.is_empty() {
                return Some(normalized);
            }
        }
    }
    
    // 2. 默认使用 UTF-8
    Some("utf-8".to_string())
}

// 标准化编码名称
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

// 检测 HTTP 版本
pub fn detect_http_version(version: &reqwest::Version) -> String {
    match *version {
        reqwest::Version::HTTP_09 => "HTTP/0.9".to_string(),
        reqwest::Version::HTTP_10 => "HTTP/1.0".to_string(),
        reqwest::Version::HTTP_11 => "HTTP/1.1".to_string(),
        reqwest::Version::HTTP_2 => "HTTP/2".to_string(),
        reqwest::Version::HTTP_3 => "HTTP/3".to_string(),
        _ => "HTTP/1.1".to_string(), // 默认值
    }
} 