use crate::config::ClientConfig;
use crate::error::{RequestError};
use crate::hyper_client::HyperHttpClient;
use crate::request::HttpRequest;
use crate::response::HttpResponse;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::time::{Duration, Instant};
use hyper::{Method, Uri};
use bytes::Bytes;
use std::str::FromStr;
use base64::Engine;

// Temporary stub for streaming response during hyper migration
pub struct StreamingHttpResponse;

// Removed unused JsonParseResult type alias
use crate::utils::{python_dict_to_form_string, python_dict_to_json_value, build_multipart_body};


// Core function for sending requests (based on pre-built requests)
pub async fn send_request(
    client: &HyperHttpClient,
    request: &HttpRequest,
    _config: &ClientConfig,
) -> PyResult<HttpResponse> {
    let start_time = Instant::now();
    let url_str = request.url_str();

    // Parse URI
    let uri = Uri::from_str(url_str)
        .map_err(|e| RequestError::new_err(format!("Invalid URI: {}", e)))?;

    // Parse method
    let method = request
        .method_str()
        .parse::<Method>()
        .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;

    // Prepare headers
    let headers = Some(request.headers_map().clone());

    // Prepare body
    let body = request.content_bytes().map(|b| Bytes::copy_from_slice(b));

    // Send request using hyper client
    client.request(method, uri, headers, body).await
}

// Optimized version: send requests directly from data, avoiding HttpRequest intermediate objects
pub async fn send_request_direct(
    client: &HyperHttpClient,
    method: &str,
    url: &str,
    headers: &HashMap<String, String>,
    content: Option<&[u8]>,
    config: &ClientConfig,
) -> PyResult<HttpResponse> {
    let start_time = Instant::now();

    // Parse URI
    let uri = Uri::from_str(url)
        .map_err(|e| RequestError::new_err(format!("Invalid URI: {}", e)))?;

    // Parse method
    let method = method
        .parse::<Method>()
        .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;

    // Prepare headers
    let headers = Some(headers.clone());

    // Prepare body
    let body = content.map(|b| Bytes::copy_from_slice(b));

    // Send request using hyper client
    client.request(method, uri, headers, body).await
}

// Legacy response processing function - removed in hyper migration
// Response processing is now handled directly by hyper_client module


// Core request building and sending function
#[allow(clippy::too_many_arguments)]
pub async fn build_and_send_request(
    config: &ClientConfig,
    method: &str,
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    base_url: &Option<String>,
    default_headers: &HashMap<String, String>,
    default_timeout: Option<Duration>,
    auth: Option<(String, String)>,
    follow_redirects: bool,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    let start_time = Instant::now();

    // Use client from configuration
    let client = if follow_redirects {
        &config.redirect_client
    } else {
        &config.no_redirect_client
    };

    // Build URL
    let mut full_url = if let Some(base) = base_url {
        if url.starts_with("http://") || url.starts_with("https://") {
            url.to_string()
        } else {
            format!(
                "{}/{}",
                base.trim_end_matches('/'),
                url.trim_start_matches('/')
            )
        }
    } else {
        url.to_string()
    };

    // Add query parameters to URL (if any)
    if let Some(params_map) = &params {
        if !params_map.is_empty() {
            let query_string: Vec<String> = params_map
                .iter()
                .map(|(key, value)| format!("{}={}", key, value))
                .collect();

            if full_url.contains('?') {
                full_url.push('&');
            } else {
                full_url.push('?');
            }
            full_url.push_str(&query_string.join("&"));
        }
    }

    // Parse URI
    let uri = Uri::from_str(&full_url)
        .map_err(|e| RequestError::new_err(format!("Invalid URI: {}", e)))?;

    // Parse method
    let method = method
        .parse::<Method>()
        .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;

    // Merge headers
    let mut final_headers = default_headers.clone();
    if let Some(ref headers) = headers {
        final_headers.extend(headers.iter().map(|(k, v)| (k.clone(), v.clone())));
    }

    // Add cookies to request headers
    if let Some(ref cookie_map) = cookies {
        if !cookie_map.is_empty() {
            let cookie_string = cookie_map
                .iter()
                .map(|(k, v)| format!("{}={}", k, v))
                .collect::<Vec<_>>()
                .join("; ");
            final_headers.insert("Cookie".to_string(), cookie_string);
        }
    }

    // Set authentication - Basic Authentication
    if let Some((username, password)) = auth {
        let credentials = format!("{}:{}", username, password);
        let encoded = base64::engine::general_purpose::STANDARD.encode(credentials.as_bytes());
        final_headers.insert("Authorization".to_string(), format!("Basic {}", encoded));
    }

    // Prepare request body - priority: content > files > json > data
    let body = if let Some(content_bytes) = content {
        Some(Bytes::from(content_bytes))
    } else if let Some(files_data) = files {
        // Handle file upload (multipart/form-data)
        let (multipart_body, content_type) = build_multipart_body(Some(files_data), data)?;
        final_headers.insert("Content-Type".to_string(), content_type);
        Some(Bytes::from(multipart_body))
    } else if let Some(json_data) = json {
        let json_value = python_dict_to_json_value(json_data)?;
        let json_string = serde_json::to_string(&json_value)
            .map_err(|e| RequestError::new_err(format!("JSON serialization failed: {}", e)))?;
        final_headers.insert("Content-Type".to_string(), "application/json".to_string());
        Some(Bytes::from(json_string))
    } else if let Some(form_data) = data {
        // Use form encoded instead of multipart
        let form_string = python_dict_to_form_string(form_data)?;
        final_headers.insert("Content-Type".to_string(), "application/x-www-form-urlencoded".to_string());
        Some(Bytes::from(form_string))
    } else {
        None
    };

    // Send request using hyper client
    client.request(method, uri, Some(final_headers), body).await
}


// Core streaming request building and sending function - returns StreamingHttpResponse
// Temporarily disabled during hyper migration - streaming requires additional implementation
#[allow(clippy::too_many_arguments)]
pub async fn build_and_send_streaming_request(
    _config: &ClientConfig,
    _method: &str,
    _url: &str,
    _content: Option<Vec<u8>>,
    _data: Option<HashMap<String, PyObject>>,
    _json: Option<HashMap<String, PyObject>>,
    _files: Option<HashMap<String, PyObject>>,
    _params: Option<HashMap<String, String>>,
    _headers: Option<HashMap<String, String>>,
    _timeout: Option<f64>,
    _base_url: &Option<String>,
    _default_headers: &HashMap<String, String>,
    _default_timeout: Option<Duration>,
    _auth: Option<(String, String)>,
    _follow_redirects: bool,
    _cookies: Option<HashMap<String, String>>,
) -> PyResult<StreamingHttpResponse> {
    // TODO: Implement streaming with hyper client  
    // Return a placeholder error for now
    Err(RequestError::new_err(
        "Streaming requests not yet implemented with hyper client"
    ))
}

// Legacy cookie extraction function removed - functionality moved to hyper_client module
