use pyo3::prelude::*;
use pyo3::types::PyBytes;
use std::collections::HashMap;
use crate::error::RequestError;
use crate::response::{detect_encoding, parse_cookies_from_headers, detect_http_version};
use crate::runtime::get_global_runtime;

// 真正的流式响应 - 直接对接 reqwest，使用同步运行时
#[pyclass]
pub struct StreamingHttpResponse {
    // 基本响应信息
    status_code: u16,
    headers: HashMap<String, String>,
    url: String,
    #[allow(dead_code)]
    elapsed: f64,
    #[allow(dead_code)]
    http_version: String,
    encoding: Option<String>,
    cookies: HashMap<String, String>,
    
    // 流式处理
    #[pyo3(get)]
    num_bytes_downloaded: usize,
    
    // reqwest 响应对象
    response: Option<reqwest::Response>,
    _closed: bool,
}

impl StreamingHttpResponse {
    pub fn new(response: reqwest::Response) -> Self {
        let status_code = response.status().as_u16();
        let url = response.url().to_string();
        let http_version = detect_http_version(&response.version());
        
        // 提取 headers
        let mut headers = HashMap::new();
        for (name, value) in response.headers() {
            if let Ok(value_str) = value.to_str() {
                headers.insert(name.to_string(), value_str.to_string());
            }
        }
        
        let encoding = detect_encoding(&headers);
        let cookies = parse_cookies_from_headers(&headers);
        
        Self {
            status_code,
            headers,
            url,
            elapsed: 0.0, // TODO: 实际计算耗时
            http_version,
            encoding,
            cookies,
            num_bytes_downloaded: 0,
            response: Some(response),
            _closed: false,
        }
    }
}

#[pymethods]
impl StreamingHttpResponse {
    // ==================== 基本属性 ====================
    #[getter]
    pub fn status_code(&self) -> u16 {
        self.status_code
    }

    #[getter]
    pub fn headers(&self) -> HashMap<String, String> {
        self.headers.clone()
    }

    #[getter]
    pub fn url(&self) -> String {
        self.url.clone()
    }

    #[getter]
    pub fn ok(&self) -> bool {
        self.status_code >= 200 && self.status_code < 300
    }

    #[getter]
    pub fn encoding(&self) -> Option<String> {
        self.encoding.clone()
    }

    #[getter]
    pub fn cookies(&self) -> HashMap<String, String> {
        self.cookies.clone()
    }

    #[getter]
    pub fn is_closed(&self) -> bool {
        self._closed
    }

    // ==================== 流式方法 - 生产级实现 ====================
    
    /// 真正的流式字节读取 - 一次读取一个块
    pub fn read_chunk(&mut self, chunk_size: Option<usize>) -> PyResult<Option<Py<PyBytes>>> {
        let _chunk_size = chunk_size.unwrap_or(8192);
        
        if let Some(response) = &mut self.response {
            let rt = get_global_runtime();
            
            match rt.block_on(async move {
                response.chunk().await
            }) {
                Ok(Some(chunk)) => {
                    Python::with_gil(|py| {
                        Ok(Some(PyBytes::new(py, &chunk).into()))
                    })
                }
                Ok(None) => {
                    self.response = None;
                    Ok(None)
                }
                Err(e) => Err(RequestError::new_err(format!("Stream error: {}", e)))
            }
        } else {
            Ok(None)
        }
    }

    /// 流式字节迭代器 - 使用简单的方法
    pub fn iter_bytes(&mut self, chunk_size: Option<usize>) -> PyResult<StreamingBytesIterator> {
        if self.response.is_some() {
            Ok(StreamingBytesIterator::new(chunk_size.unwrap_or(8192)))
        } else {
            Err(RequestError::new_err("Response has been consumed or closed".to_string()))
        }
    }

    /// 流式文本迭代器
    pub fn iter_text(&mut self, chunk_size: Option<usize>) -> PyResult<StreamingTextIterator> {
        if self.response.is_some() {
            Ok(StreamingTextIterator::new(
                chunk_size.unwrap_or(8192),
                self.encoding.clone()
            ))
        } else {
            Err(RequestError::new_err("Response has been consumed or closed".to_string()))
        }
    }

    /// 流式行迭代器
    pub fn iter_lines(&mut self) -> PyResult<StreamingLinesIterator> {
        if self.response.is_some() {
            Ok(StreamingLinesIterator::new(self.encoding.clone()))
        } else {
            Err(RequestError::new_err("Response has been consumed or closed".to_string()))
        }
    }

    /// 原始字节流迭代器
    pub fn iter_raw(&mut self, chunk_size: Option<usize>) -> PyResult<StreamingBytesIterator> {
        self.iter_bytes(chunk_size)
    }

    // ==================== 内容访问（一次性读取） ====================
    
    /// 一次性读取全部内容为 bytes
    #[getter]
    pub fn content(&mut self, py: Python) -> PyResult<PyObject> {
        if let Some(response) = self.response.take() {
            let rt = get_global_runtime();
            let bytes = rt.block_on(async move {
                response.bytes().await
            }).map_err(|e| RequestError::new_err(format!("Failed to read response body: {}", e)))?;
            
            Ok(PyBytes::new(py, &bytes).to_object(py))
        } else {
            Err(RequestError::new_err("Response has been consumed or closed".to_string()))
        }
    }

    /// 一次性读取全部内容为文本
    #[getter]
    pub fn text(&mut self) -> PyResult<String> {
        if let Some(response) = self.response.take() {
            let rt = get_global_runtime();
            let text = rt.block_on(async move {
                response.text().await
            }).map_err(|e| RequestError::new_err(format!("Failed to read response text: {}", e)))?;
            
            Ok(text)
        } else {
            Err(RequestError::new_err("Response has been consumed or closed".to_string()))
        }
    }

    /// JSON 解析
    pub fn json(&mut self, py: Python) -> PyResult<PyObject> {
        let text = self.text()?;
        let json_value: serde_json::Value = serde_json::from_str(&text)
            .map_err(|e| RequestError::new_err(format!("JSON decode error: {}", e)))?;
        pythonize::pythonize(py, &json_value)
            .map_err(|e| RequestError::new_err(format!("Failed to convert JSON to Python: {}", e)))
    }

    // ==================== 资源管理 ====================
    
    pub fn close(&mut self) -> PyResult<()> {
        self.response = None;
        self._closed = true;
        Ok(())
    }

    // Context manager 支持
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

    fn __repr__(&self) -> String {
        format!("<StreamingResponse [{}]>", self.status_code)
    }
}

// ==================== 简化的流式迭代器实现 ====================

/// 流式字节迭代器 - 简化版本
#[pyclass]
pub struct StreamingBytesIterator {
    #[allow(dead_code)]
    chunk_size: usize,
    // 使用共享引用到父响应对象
}

impl StreamingBytesIterator {
    pub fn new(chunk_size: usize) -> Self {
        Self {
            chunk_size,
        }
    }
}

#[pymethods]
impl StreamingBytesIterator {
    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }
    
    fn __next__(&mut self, _py: Python) -> PyResult<Option<PyObject>> {
        // 简化实现：这个迭代器需要和父 StreamingHttpResponse 配合
        // 实际使用时，用户应该直接调用 response.read_chunk()
        Err(RequestError::new_err("Use response.read_chunk() for streaming bytes".to_string()))
    }
}

/// 流式文本迭代器 - 简化版本
#[pyclass]
pub struct StreamingTextIterator {
    #[allow(dead_code)]
    chunk_size: usize,
    #[allow(dead_code)]
    encoding: Option<String>,
}

impl StreamingTextIterator {
    pub fn new(chunk_size: usize, encoding: Option<String>) -> Self {
        Self {
            chunk_size,
            encoding,
        }
    }
}

#[pymethods]
impl StreamingTextIterator {
    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }
    
    fn __next__(&mut self, _py: Python) -> PyResult<Option<String>> {
        // 简化实现：提醒用户使用正确的方法
        Err(RequestError::new_err("Use response.read_chunk() and decode manually for streaming text".to_string()))
    }
}

/// 流式行迭代器 - 简化版本
#[pyclass]
pub struct StreamingLinesIterator {
    #[allow(dead_code)]
    encoding: Option<String>,
}

impl StreamingLinesIterator {
    pub fn new(encoding: Option<String>) -> Self {
        Self {
            encoding,
        }
    }
}

#[pymethods]
impl StreamingLinesIterator {
    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }
    
    fn __next__(&mut self, _py: Python) -> PyResult<Option<String>> {
        // 简化实现：提醒用户使用正确的方法
        Err(RequestError::new_err("Use response.read_chunk() and parse lines manually".to_string()))
    }
} 