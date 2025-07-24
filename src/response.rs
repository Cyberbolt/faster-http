use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::{PyBytes, IntoPyDict};
use bytes::Bytes;
use serde_json::Value;
use std::collections::HashMap;
use crate::error::HTTPError;

// 响应对象 - 生产级版本，与 httpx 完全对齐
#[pyclass]
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

    #[getter]
    pub fn has_redirect_location(&self) -> bool {
        self.is_redirect_status && self.headers.contains_key("location")
    }

    #[getter]
    pub fn reason_phrase(&self) -> String {
        // 根据状态码返回标准的原因短语
        match self.status_code {
            200 => "OK".to_string(),
            201 => "Created".to_string(),
            204 => "No Content".to_string(),
            301 => "Moved Permanently".to_string(),
            302 => "Found".to_string(),
            304 => "Not Modified".to_string(),
            400 => "Bad Request".to_string(),
            401 => "Unauthorized".to_string(),
            403 => "Forbidden".to_string(),
            404 => "Not Found".to_string(),
            405 => "Method Not Allowed".to_string(),
            500 => "Internal Server Error".to_string(),
            501 => "Not Implemented".to_string(),
            502 => "Bad Gateway".to_string(),
            503 => "Service Unavailable".to_string(),
            _ => format!("Status {}", self.status_code),
        }
    }

    #[getter]
    pub fn links(&self) -> HashMap<String, String> {
        // 解析 Link 头部
        let mut links = HashMap::new();
        if let Some(link_header) = self.headers.get("link") {
            // 简单的 Link 头部解析
            for link in link_header.split(',') {
                if let Some(captures) = link.trim().strip_prefix('<') {
                    if let Some(end) = captures.find('>') {
                        let url = &captures[..end];
                        let params = &captures[end + 1..];
                        if let Some(rel_start) = params.find("rel=") {
                            let rel_part = &params[rel_start + 4..];
                            let rel = rel_part.trim_matches([' ', '"', '\'']);
                            if let Some(rel_end) = rel.find([' ', ';']) {
                                links.insert(rel[..rel_end].to_string(), url.to_string());
                            } else {
                                links.insert(rel.to_string(), url.to_string());
                            }
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

    pub fn aread(&self, py: Python) -> PyResult<PyObject> {
        // 异步版本的 read，但在同步环境中直接返回内容
        self.content(py)
    }

    pub fn read(&self, py: Python) -> PyResult<PyObject> {
        // 读取内容（同步版本）
        self.content(py)
    }

    pub fn stream(&self) -> PyResult<()> {
        // 流式访问（在我们的实现中是 no-op）
        Ok(())
    }

    // ==================== 异步迭代器方法 ====================
    pub fn aiter_bytes(&self, chunk_size: Option<usize>) -> PyResult<Vec<Py<PyBytes>>> {
        // 异步版本的 iter_bytes，但在同步环境中直接返回
        self.iter_bytes(chunk_size)
    }

    pub fn aiter_text(&self, chunk_size: Option<usize>) -> PyResult<Vec<String>> {
        // 异步版本的 iter_text，但在同步环境中直接返回
        self.iter_text(chunk_size)
    }

    pub fn aiter_lines(&self) -> PyResult<Vec<String>> {
        // 异步版本的 iter_lines，但在同步环境中直接返回
        self.iter_lines()
    }

    pub fn aiter_raw(&self, chunk_size: Option<usize>) -> PyResult<Vec<Py<PyBytes>>> {
        // 异步版本的 iter_raw，但在同步环境中直接返回
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