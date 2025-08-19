use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use std::error::Error;

// Create custom exception types - complete httpx-compatible exception hierarchy
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
            let err = HTTPStatusError::new_err(message);

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

// Additional httpx-compatible exceptions
pyo3::create_exception!(faster_http, InvalidURL, RequestError);
pyo3::create_exception!(faster_http, LocalProtocolError, ProtocolError);
pyo3::create_exception!(faster_http, RemoteProtocolError, ProtocolError);
pyo3::create_exception!(faster_http, ReadError, RequestError);
pyo3::create_exception!(faster_http, WriteError, RequestError);
pyo3::create_exception!(faster_http, UnsupportedProtocol, RequestError);

// Error handling utilities - httpx-compatible error mapping

/// Maps hyper errors to appropriate httpx-compatible exceptions  
pub fn map_hyper_error(error: hyper::Error) -> PyErr {
    let error_msg = error.to_string();

    if error.is_timeout() {
        ReadTimeout::new_err(format!("Request timeout: {}", error_msg))
    } else if error_msg.contains("connection") || error_msg.contains("connect") {
        ConnectError::new_err(format!("Connection error: {}", error_msg))
    } else if error.is_closed() || error.is_incomplete_message() {
        ProtocolError::new_err(format!("Protocol error: {}", error_msg))
    } else if error.is_parse() || error.is_parse_status() {
        LocalProtocolError::new_err(format!("Parse error: {}", error_msg))
    } else if error.is_user() {
        RequestError::new_err(format!("Request error: {}", error_msg))
    } else if error.is_canceled() {
        RequestError::new_err(format!("Request canceled: {}", error_msg))
    } else {
        // Map all other errors to appropriate httpx-compatible exceptions
        if error_msg.contains("transport") {
            TransportError::new_err(format!("Transport error: {}", error_msg))
        } else {
            HTTPError::new_err(format!("HTTP error: {}", error_msg))
        }
    }
}

/// Maps hyper-util errors to appropriate httpx-compatible exceptions
pub fn map_hyper_util_error(error: hyper_util::client::legacy::Error) -> PyErr {
    let error_msg = error.to_string();
    
    // Check error message patterns since hyper::Error doesn't implement Clone 
    // We'll match on error message patterns instead
    let error_msg = error.to_string();
    
    // Check for timeout errors
    if error_msg.contains("timeout") {
        if error_msg.contains("connect") {
            ConnectTimeout::new_err(format!("Connection timeout: {}", error_msg))
        } else {
            ReadTimeout::new_err(format!("Request timeout: {}", error_msg))
        }
    } else if error_msg.contains("connection") {
        ConnectError::new_err(format!("Connection error: {}", error_msg))
    } else if error_msg.contains("redirect") {
        TooManyRedirects::new_err(format!("Too many redirects: {}", error_msg))
    } else {
        RequestError::new_err(format!("Request error: {}", error_msg))
    }
}

/// Maps Tower service errors to appropriate httpx-compatible exceptions
pub fn map_tower_error<E: std::error::Error + Send + Sync + 'static>(error: E) -> PyErr {
    let error_msg = error.to_string();
    
    if error_msg.contains("timeout") {
        ReadTimeout::new_err(format!("Service timeout: {}", error_msg))
    } else if error_msg.contains("connection") {
        ConnectError::new_err(format!("Service connection error: {}", error_msg))
    } else {
        TransportError::new_err(format!("Service error: {}", error_msg))
    }
}

/// Maps HTTP body errors to appropriate httpx-compatible exceptions
pub fn map_http_body_error<E: std::error::Error + Send + Sync + 'static>(error: E) -> PyErr {
    let error_msg = error.to_string();
    ReadError::new_err(format!("Body read error: {}", error_msg))
}

// Legacy error mapping functions - removed as reqwest and ureq are no longer dependencies

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
pub fn create_stream_error(_error_type: &str, message: &str) -> PyErr {
    StreamError::new_err(format!("Stream error: {}", message))
}

/// Create URL validation error
pub fn create_url_error(message: &str) -> PyErr {
    InvalidURL::new_err(format!("Invalid URL: {}", message))
}

/// Create generic request error
pub fn create_request_error(message: &str) -> PyErr {
    RequestError::new_err(message.to_string())
}

/// Create file not found error (maps to RequestError for API consistency)
pub fn create_file_error(message: &str) -> PyErr {
    RequestError::new_err(format!("File error: {}", message))
}

/// Create validation error for invalid input
pub fn create_validation_error(message: &str) -> PyErr {
    RequestError::new_err(format!("Validation error: {}", message))
}

/// Create protocol error for low-level protocol issues
pub fn create_protocol_error(message: &str) -> PyErr {
    ProtocolError::new_err(format!("Protocol error: {}", message))
}

/// Create read/write error for I/O operations
pub fn create_io_error(message: &str, is_read: bool) -> PyErr {
    if is_read {
        ReadError::new_err(format!("Read error: {}", message))
    } else {
        WriteError::new_err(format!("Write error: {}", message))
    }
}

/// Create connection error with detailed context
pub fn create_connection_error(message: &str, is_timeout: bool) -> PyErr {
    if is_timeout {
        ConnectTimeout::new_err(format!("Connection timeout: {}", message))
    } else {
        ConnectError::new_err(format!("Connection error: {}", message))
    }
}

/// Map std::io::Error to appropriate exception
pub fn map_io_error(error: std::io::Error) -> PyErr {
    let msg = error.to_string();
    match error.kind() {
        std::io::ErrorKind::NotFound => create_file_error(&msg),
        std::io::ErrorKind::PermissionDenied => create_validation_error(&msg),
        std::io::ErrorKind::ConnectionRefused | 
        std::io::ErrorKind::ConnectionAborted |
        std::io::ErrorKind::ConnectionReset => create_connection_error(&msg, false),
        std::io::ErrorKind::TimedOut => create_connection_error(&msg, true),
        std::io::ErrorKind::InvalidInput | 
        std::io::ErrorKind::InvalidData => create_validation_error(&msg),
        _ => create_request_error(&msg),
    }
}

/// Map JSON parsing errors to appropriate exception
pub fn map_json_error(error: serde_json::Error) -> PyErr {
    create_validation_error(&format!("JSON decode error: {}", error))
}

/// Map URL parsing errors to appropriate exception  
pub fn map_url_error(error: url::ParseError) -> PyErr {
    create_url_error(&error.to_string())
}
