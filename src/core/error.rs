use pyo3::exceptions::PyException;
use pyo3::prelude::*;

// HTTPX-COMPATIBLE EXCEPTION HIERARCHY - FIXED
// Based on encode/httpx exception structure for full compatibility

// Base HTTP exception - matches httpx.HTTPError
pyo3::create_exception!(faster_http, HTTPError, PyException);

// Request-related exceptions - matches httpx.RequestError
// Should include .request attribute for context
pyo3::create_exception!(faster_http, RequestError, HTTPError);

// HTTP status related exceptions - matches httpx.HTTPStatusError
// Should include both .request and .response attributes
pyo3::create_exception!(faster_http, HTTPStatusError, HTTPError);

// Transport and Protocol exceptions (defined first for inheritance)  
pyo3::create_exception!(faster_http, TransportError, RequestError);

// Network related exceptions - matches httpx network error hierarchy
pyo3::create_exception!(faster_http, NetworkError, TransportError);

// Connection related exceptions - matches httpx.ConnectError
pyo3::create_exception!(faster_http, ConnectError, NetworkError);
pyo3::create_exception!(faster_http, ConnectTimeout, ConnectError);

// Timeout exceptions - matches httpx timeout structure
pyo3::create_exception!(faster_http, TimeoutException, RequestError);
pyo3::create_exception!(faster_http, ReadTimeout, TimeoutException);
pyo3::create_exception!(faster_http, WriteTimeout, TimeoutException);
pyo3::create_exception!(faster_http, PoolTimeout, TimeoutException);

// Additional httpx-compatible exceptions
pyo3::create_exception!(faster_http, ProxyError, RequestError);
pyo3::create_exception!(faster_http, UnsupportedProtocol, RequestError);
pyo3::create_exception!(faster_http, DecodingError, HTTPError);
pyo3::create_exception!(faster_http, TooManyRedirects, RequestError);

// SSL/TLS related exceptions
pyo3::create_exception!(faster_http, SSLError, ConnectError); // Matches httpx SSL handling

// HTTPStatusError already defined above in proper hierarchy

impl HTTPStatusError {
    /// Create HTTPStatusError with request and response parameters (httpx-compatible)
    pub fn new_err_with_request_response(
        message: String,
        request: Option<PyObject>,
        response: Option<PyObject>,
    ) -> PyErr {
        Python::with_gil(|py| {
            // Create the basic exception
            let err = HTTPStatusError::new_err(message);

            // Add request and response attributes directly to the exception instance
            let exc_obj = err.value(py);

            if let Some(req) = request {
                let _ = exc_obj.setattr("request", req);
            } else {
                let _ = exc_obj.setattr("request", py.None());
            }

            if let Some(resp) = response {
                let _ = exc_obj.setattr("response", resp);
            } else {
                let _ = exc_obj.setattr("response", py.None());
            }

            err
        })
    }

    /// Backward compatibility method - deprecated
    pub fn new_err_with_response(message: String, response: Option<PyObject>) -> PyErr {
        Self::new_err_with_request_response(message, None, response)
    }
}

/// Factory function to create HTTPStatusError with keyword arguments
#[pyfunction]
#[pyo3(signature = (message, *, request = None, response = None))]
pub fn new_http_status_error(
    py: Python<'_>,
    message: String,
    request: Option<PyObject>,
    response: Option<PyObject>,
) -> PyResult<PyObject> {
    // Create the HTTPStatusError exception instance
    let exc_type = py.get_type::<HTTPStatusError>();
    let exc_instance = exc_type.call1((message.clone(),))?;

    // Set request and response attributes
    if let Some(req) = request {
        exc_instance.setattr("request", req)?;
    } else {
        exc_instance.setattr("request", py.None())?;
    }

    if let Some(resp) = response {
        exc_instance.setattr("response", resp)?;
    } else {
        exc_instance.setattr("response", py.None())?;
    }

    Ok(exc_instance.to_object(py))
}

// Protocol exceptions (TransportError already defined above)
pyo3::create_exception!(faster_http, ProtocolError, TransportError);
pyo3::create_exception!(faster_http, LocalProtocolError, ProtocolError);
pyo3::create_exception!(faster_http, RemoteProtocolError, ProtocolError);

// Stream related exceptions
pyo3::create_exception!(faster_http, StreamError, RequestError);
pyo3::create_exception!(faster_http, StreamClosed, StreamError);
pyo3::create_exception!(faster_http, StreamConsumed, StreamError);

// I/O exceptions
pyo3::create_exception!(faster_http, ReadError, RequestError);
pyo3::create_exception!(faster_http, WriteError, RequestError);

// URL and validation exceptions
pyo3::create_exception!(faster_http, InvalidURL, RequestError);
pyo3::create_exception!(faster_http, CookieConflict, RequestError);

// Close and Read/Write state exceptions
pyo3::create_exception!(faster_http, CloseError, RequestError);
pyo3::create_exception!(faster_http, RequestNotRead, RequestError);
pyo3::create_exception!(faster_http, ResponseNotRead, RequestError);

// Internal system exceptions (should be rare in normal operation)
pyo3::create_exception!(faster_http, InternalError, HTTPError); // For locks and internal state errors
pyo3::create_exception!(faster_http, ConnectionPoolInitFailed, InternalError);
pyo3::create_exception!(faster_http, RuntimeInitFailed, InternalError);
pyo3::create_exception!(faster_http, ClientInitFailed, InternalError);

// Error handling utilities - httpx-compatible error mapping

/// Maps hyper errors to appropriate httpx-compatible exceptions  
pub fn map_hyper_error(error: hyper::Error) -> PyErr {
    let error_msg = error.to_string();

    if error.is_timeout() {
        ReadTimeout::new_err(format!("Request timeout: {}", error_msg))
    } else if error_msg.contains("tls")
        || error_msg.contains("ssl")
        || error_msg.contains("certificate")
    {
        SSLError::new_err(format!("SSL error: {}", error_msg))
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
    // Check error message patterns since hyper::Error doesn't implement Clone
    // We'll match on error message patterns instead
    let error_msg = error.to_string();
    let error_msg_lower = error_msg.to_lowercase();

    // Check for timeout errors
    if error_msg_lower.contains("timeout") || error_msg_lower.contains("timed out") {
        if error_msg_lower.contains("connect") {
            ConnectTimeout::new_err(format!("Connection timeout: {}", error_msg))
        } else {
            ReadTimeout::new_err(format!("Request timeout: {}", error_msg))
        }
    } else if error_msg_lower.contains("tls")
        || error_msg_lower.contains("ssl")
        || error_msg_lower.contains("certificate")
    {
        SSLError::new_err(format!("SSL error: {}", error_msg))
    } else if error_msg_lower.contains("connection") || error_msg_lower.contains("connect") {
        ConnectError::new_err(format!("Connection error: {}", error_msg))
    } else if error_msg_lower.contains("redirect") {
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

/// Create SSL error for SSL/TLS related issues
pub fn create_ssl_error(message: &str) -> PyErr {
    SSLError::new_err(format!("SSL error: {}", message))
}

/// Map std::io::Error to appropriate exception
pub fn map_io_error(error: std::io::Error) -> PyErr {
    let msg = error.to_string();
    match error.kind() {
        std::io::ErrorKind::NotFound => create_file_error(&msg),
        std::io::ErrorKind::PermissionDenied => create_validation_error(&msg),
        std::io::ErrorKind::ConnectionRefused
        | std::io::ErrorKind::ConnectionAborted
        | std::io::ErrorKind::ConnectionReset => create_connection_error(&msg, false),
        std::io::ErrorKind::TimedOut => create_connection_error(&msg, true),
        std::io::ErrorKind::InvalidInput | std::io::ErrorKind::InvalidData => {
            create_validation_error(&msg)
        }
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
