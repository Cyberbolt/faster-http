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

// Request/Response exceptions
pyo3::create_exception!(faster_http, RequestError, HTTPError);
pyo3::create_exception!(faster_http, ResponseError, HTTPError);

// HTTP status related exceptions
pyo3::create_exception!(faster_http, HTTPStatusError, ResponseError);
pyo3::create_exception!(faster_http, ClientError, HTTPStatusError);  // 4xx
pyo3::create_exception!(faster_http, ServerError, HTTPStatusError);  // 5xx

// Stream related exceptions
pyo3::create_exception!(faster_http, StreamError, HTTPError);
pyo3::create_exception!(faster_http, StreamConsumed, StreamError);
pyo3::create_exception!(faster_http, StreamClosed, StreamError);

// Protocol related exceptions
pyo3::create_exception!(faster_http, ProtocolError, HTTPError);
pyo3::create_exception!(faster_http, DecodingError, ProtocolError);
pyo3::create_exception!(faster_http, TooManyRedirects, ProtocolError);

// Transport related exceptions
pyo3::create_exception!(faster_http, TransportError, HTTPError);
pyo3::create_exception!(faster_http, ProxyError, TransportError);
pyo3::create_exception!(faster_http, SSLError, TransportError);
pyo3::create_exception!(faster_http, CertificateError, SSLError);

// Network related exceptions
pyo3::create_exception!(faster_http, NetworkError, HTTPError);
pyo3::create_exception!(faster_http, DNSError, NetworkError);

// 错误处理工具 - 增强的错误映射
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
        DecodingError::new_err(format!("Response decoding error: {}", error_msg))
    } else if let Some(status) = error.status() {
        let status_code = status.as_u16();
        match status_code {
            400..=499 => ClientError::new_err(format!("HTTP {} error: {}", status_code, error_msg)),
            500..=599 => ServerError::new_err(format!("HTTP {} error: {}", status_code, error_msg)),
            _ => HTTPStatusError::new_err(format!("HTTP {} error: {}", status_code, error_msg)),
        }
    } else {
        // Check for specific error patterns in the message
        if error_msg.contains("ssl") || error_msg.contains("tls") || error_msg.contains("certificate") {
            if error_msg.contains("certificate") {
                CertificateError::new_err(format!("Certificate error: {}", error_msg))
            } else {
                SSLError::new_err(format!("SSL/TLS error: {}", error_msg))
            }
        } else if error_msg.contains("proxy") {
            ProxyError::new_err(format!("Proxy error: {}", error_msg))
        } else if error_msg.contains("dns") || error_msg.contains("resolve") {
            DNSError::new_err(format!("DNS resolution error: {}", error_msg))
        } else {
            NetworkError::new_err(format!("Network error: {}", error_msg))
        }
    }
}

/// Create HTTP status error with proper exception type
pub fn create_http_status_error(status_code: u16, message: &str) -> PyErr {
    match status_code {
        400..=499 => ClientError::new_err(format!("HTTP {} Client Error: {}", status_code, message)),
        500..=599 => ServerError::new_err(format!("HTTP {} Server Error: {}", status_code, message)),
        _ => HTTPStatusError::new_err(format!("HTTP {} Error: {}", status_code, message)),
    }
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
    match error_type {
        "consumed" => StreamConsumed::new_err(format!("Stream consumed: {}", message)),
        "closed" => StreamClosed::new_err(format!("Stream closed: {}", message)),
        _ => StreamError::new_err(format!("Stream error: {}", message)),
    }
} 