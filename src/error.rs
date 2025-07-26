use pyo3::prelude::*;
use pyo3::exceptions::PyException;

// 创建自定义异常类型 - 完整的 httpx 兼容异常层次结构
pyo3::create_exception!(faster_http, HTTPError, PyException);

// Connection related exceptions
pyo3::create_exception!(faster_http, ConnectError, HTTPError);
pyo3::create_exception!(faster_http, ConnectTimeout, ConnectError);

// Timeout exceptions
pyo3::create_exception!(faster_http, TimeoutException, HTTPError);
pyo3::create_exception!(faster_http, ReadTimeout, TimeoutException);
pyo3::create_exception!(faster_http, WriteTimeout, TimeoutException);
pyo3::create_exception!(faster_http, PoolTimeout, TimeoutException);

// Request/Response exceptions (httpx-compatible only)
pyo3::create_exception!(faster_http, RequestError, HTTPError);

// HTTP status related exceptions 
pyo3::create_exception!(faster_http, HTTPStatusError, HTTPError);

impl HTTPStatusError {
    pub fn new_err_with_response(message: String, response: Option<PyObject>) -> PyErr {
        Python::with_gil(|py| {
            // Create the basic exception
            let mut err = HTTPStatusError::new_err(message);
            
            // Add response attribute directly to the exception instance
            if let Some(resp) = response {
                let exc_obj = err.value(py);
                let _ = exc_obj.setattr("response", resp);
            }
            
            err
        })
    }
}

// Stream related exceptions
pyo3::create_exception!(faster_http, StreamError, HTTPError);

// Protocol related exceptions
pyo3::create_exception!(faster_http, ProtocolError, HTTPError);
pyo3::create_exception!(faster_http, TooManyRedirects, ProtocolError);

// Transport related exceptions
pyo3::create_exception!(faster_http, TransportError, HTTPError);

// 错误处理工具 - httpx 兼容的错误映射
pub fn map_reqwest_error(error: reqwest::Error) -> PyErr {
    let error_msg = error.to_string();
    
    if error.is_timeout() {
        ReadTimeout::new_err(format!("Request timeout: {}", error_msg))
    } else if error.is_connect() {
        if error_msg.contains("timeout") {
            ConnectTimeout::new_err(format!("Connection timeout: {}", error_msg))
        } else {
            ConnectError::new_err(format!("Connection error: {}", error_msg))
        }
    } else if error.is_request() {
        RequestError::new_err(format!("Request error: {}", error_msg))
    } else if error.is_redirect() {
        TooManyRedirects::new_err(format!("Too many redirects: {}", error_msg))
    } else if error.is_body() || error.is_decode() {
        RequestError::new_err(format!("Response decoding error: {}", error_msg))
    } else if let Some(status) = error.status() {
        let status_code = status.as_u16();
        HTTPStatusError::new_err(format!("HTTP {} error: {}", status_code, error_msg))
    } else {
        // Map all other errors to appropriate httpx-compatible exceptions
        if error_msg.contains("transport") || error_msg.contains("connection") {
            TransportError::new_err(format!("Transport error: {}", error_msg))
        } else {
            HTTPError::new_err(format!("HTTP error: {}", error_msg))
        }
    }
}

/// Create HTTP status error with proper exception type
pub fn create_http_status_error(status_code: u16, message: &str) -> PyErr {
    HTTPStatusError::new_err(format!("HTTP {} Error: {}", status_code, message))
}

/// Create appropriate timeout error
pub fn create_timeout_error(timeout_type: &str, message: &str) -> PyErr {
    match timeout_type {
        "connect" => ConnectTimeout::new_err(format!("Connect timeout: {}", message)),
        "read" => ReadTimeout::new_err(format!("Read timeout: {}", message)),
        "write" => WriteTimeout::new_err(format!("Write timeout: {}", message)),
        "pool" => PoolTimeout::new_err(format!("Pool timeout: {}", message)),
        _ => TimeoutException::new_err(format!("Timeout: {}", message)),
    }
}

/// Create stream related error
pub fn create_stream_error(error_type: &str, message: &str) -> PyErr {
    StreamError::new_err(format!("Stream error: {}", message))
} 