use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use bytes::Bytes;
use serde_json::Value;
use std::collections::HashMap;
use crate::error::HTTPError;

// 响应对象
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
        }
    }
}

#[pymethods]
impl HttpResponse {
    #[getter]
    pub fn status_code(&self) -> u16 {
        self.status_code
    }

    #[getter]
    pub fn headers(&self) -> HashMap<String, String> {
        self.headers.clone()
    }

    #[getter]
    pub fn url(&self) -> &str {
        &self.url
    }

    #[getter]
    pub fn ok(&self) -> bool {
        (200..300).contains(&self.status_code)
    }

    #[getter]
    pub fn content(&self) -> &[u8] {
        &self.body
    }

    #[getter]
    pub fn text(&self) -> String {
        // 根据编码解码，默认使用 UTF-8
        let encoding = self.encoding.as_deref().unwrap_or("utf-8");
        match encoding.to_lowercase().as_str() {
            "utf-8" | "utf8" => String::from_utf8_lossy(&self.body).to_string(),
            _ => {
                // 对于其他编码，暂时使用 UTF-8，未来可以添加更多编码支持
                String::from_utf8_lossy(&self.body).to_string()
            }
        }
    }

    #[getter]
    pub fn encoding(&self) -> Option<String> {
        self.encoding.clone()
    }

    #[setter]
    pub fn set_encoding(&mut self, encoding: Option<String>) {
        self.encoding = encoding;
    }

    #[getter]
    pub fn charset_encoding(&self) -> Option<String> {
        // 从 Content-Type 头中提取字符集
        for content_type in self.headers.values() {
            if let Some(charset_pos) = content_type.find("charset=") {
                let charset = &content_type[charset_pos + 8..];
                let charset = charset.split(';').next().unwrap_or(charset).trim();
                return Some(charset.to_string());
            }
        }
        None
    }

    #[getter]
    pub fn elapsed(&self) -> f64 {
        self.elapsed
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
    pub fn is_redirect(&self) -> bool {
        self.is_redirect_status
    }

    #[getter]
    pub fn http_version(&self) -> &str {
        &self.http_version
    }

    #[getter]
    pub fn cookies(&self) -> HashMap<String, String> {
        self.cookies.clone()
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
    pub fn num_bytes_downloaded(&self) -> usize {
        self.num_bytes_downloaded
    }

    // 新增：响应迭代器方法
    pub fn iter_bytes(&self, chunk_size: Option<usize>) -> PyResult<Vec<Vec<u8>>> {
        let chunk_size = chunk_size.unwrap_or(8192);
        let mut chunks = Vec::new();
        let mut pos = 0;
        
        while pos < self.body.len() {
            let end = std::cmp::min(pos + chunk_size, self.body.len());
            chunks.push(self.body[pos..end].to_vec());
            pos = end;
        }
        
        Ok(chunks)
    }

    pub fn iter_text(&self, chunk_size: Option<usize>) -> PyResult<Vec<String>> {
        let chunk_size = chunk_size.unwrap_or(8192);
        let mut text_chunks = Vec::new();
        let text = self.text();
        let mut pos = 0;
        
        while pos < text.len() {
            let end = std::cmp::min(pos + chunk_size, text.len());
            text_chunks.push(text[pos..end].to_string());
            pos = end;
        }
        
        Ok(text_chunks)
    }

    pub fn iter_lines(&self) -> PyResult<Vec<String>> {
        let text = self.text();
        let lines: Vec<String> = text.lines().map(|line| line.to_string()).collect();
        Ok(lines)
    }

    pub fn iter_raw(&self, chunk_size: Option<usize>) -> PyResult<Vec<Vec<u8>>> {
        // 与 iter_bytes 相同，但表示未解码的原始数据
        self.iter_bytes(chunk_size)
    }

    pub fn json(&self, py: Python) -> PyResult<PyObject> {
        let json_str = self.text();
        let json_value: Value = serde_json::from_str(&json_str)
            .map_err(|e| PyValueError::new_err(format!("Failed to parse JSON: {}", e)))?;
        pythonize::pythonize(py, &json_value)
            .map_err(|e| PyValueError::new_err(format!("Failed to convert JSON to Python: {}", e)))
    }

    pub fn raise_for_status(&self) -> PyResult<()> {
        if self.status_code >= 400 {
            return Err(HTTPError::new_err(format!(
                "HTTP {} error for url: {}",
                self.status_code, self.url
            )));
        }
        Ok(())
    }

    fn __repr__(&self) -> String {
        format!("<Response [{}]>", self.status_code)
    }

    // 新增：支持流式传输的标记方法
    pub fn is_streamable(&self) -> bool {
        // 检查响应是否可以进行流式传输
        true
    }

    // 新增：为 SSE 等流式传输添加辅助方法
    pub fn iter_sse_lines(&self) -> PyResult<Vec<String>> {
        let text = self.text();
        let mut sse_events = Vec::new();
        
        for line in text.lines() {
            if line.starts_with("data:") {
                sse_events.push(line.to_string());
            } else if line.starts_with("event:") || line.starts_with("id:") || line.starts_with("retry:") {
                sse_events.push(line.to_string());
            }
        }
        
        Ok(sse_events)
    }
}

// 辅助函数
pub fn parse_cookies_from_headers(headers: &HashMap<String, String>) -> HashMap<String, String> {
    let mut cookies = HashMap::new();
    
    for (key, value) in headers {
        if key.to_lowercase() == "set-cookie" {
            if let Some(eq_pos) = value.find('=') {
                let name = value[..eq_pos].trim();
                let rest = &value[eq_pos + 1..];
                let cookie_value = rest.split(';').next().unwrap_or(rest).trim();
                cookies.insert(name.to_string(), cookie_value.to_string());
            }
        }
    }
    
    cookies
}

// 编码检测函数
pub fn detect_encoding(headers: &HashMap<String, String>) -> Option<String> {
    for (key, value) in headers {
        if key.to_lowercase() == "content-type" {
            if let Some(charset_pos) = value.find("charset=") {
                let charset = &value[charset_pos + 8..];
                let charset = charset.split(';').next().unwrap_or(charset).trim();
                return Some(charset.to_string());
            }
        }
    }
    
    // 默认返回 UTF-8
    Some("utf-8".to_string())
} 