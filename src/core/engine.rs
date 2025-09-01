use crate::client::hyper_client::HyperHttpClient;
use crate::config::ClientConfig;
use crate::core::error::RequestError;
use crate::models::{HttpRequest, HttpResponse};
use bytes::Bytes;
use hyper::{Method, Uri};
use pyo3::prelude::*;
use std::collections::HashMap;
use std::str::FromStr;
use std::time::Duration;

/// Simple conversion function: Python parameters -> hyper request
pub async fn send_request_direct(
    client: &HyperHttpClient,
    method: &str,
    url: &str,
    headers: &HashMap<String, String>,
    content: Option<&[u8]>,
    _config: &ClientConfig, // Minimal config usage
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    // Convert method string to hyper Method
    let method = Method::from_str(method)
        .map_err(|e| RequestError::new_err(format!("Invalid method: {}", e)))?;

    // Convert URL string to hyper Uri
    let uri = Uri::from_str(url)
        .map_err(|e| RequestError::new_err(format!("Invalid URI: {}", e)))?;

    // Convert headers (simple copy)
    let headers_opt = if headers.is_empty() {
        None
    } else {
        Some(headers.clone())
    };

    // Convert body content
    let body = content.map(|data| Bytes::from(data.to_vec()));

    // Convert timeout
    let timeout_duration = timeout.map(Duration::from_secs_f64);

    // Delegate to hyper client
    client
        .request_with_timeout(method, uri, headers_opt, body, timeout_duration)
        .await
}

/// Send request using pre-built HttpRequest object
pub async fn send_request(
    client: &HyperHttpClient,
    request: &HttpRequest,
    _config: &ClientConfig,
) -> PyResult<HttpResponse> {
    // Simple conversion: HttpRequest -> hyper parameters
    let method = Method::from_str(request.method_str())
        .map_err(|e| RequestError::new_err(format!("Invalid method: {}", e)))?;
    
    let uri = Uri::from_str(request.url_str())
        .map_err(|e| RequestError::new_err(format!("Invalid URI: {}", e)))?;
    
    let headers = Some(request.headers_map().clone());
    let body = request.content_bytes().map(|b| Bytes::copy_from_slice(b.as_ref()));

    // Delegate to hyper client
    client.request(method, uri, headers, body).await
}

// Note: build_and_send_request function removed as it was unused