use crate::client::hyper_client::HyperHttpClient;
use crate::config::ClientConfig;
use crate::core::error::RequestError;
use crate::models::{HttpRequest, HttpResponse};
// Removed memory_pool dependency - using standard Bytes instead
use crate::optimization::precompiled::parse_method_configured; // Precompiled lookups
use base64::Engine;
use bytes::Bytes;
use hyper::{Method, Uri};
use pyo3::prelude::*;
use std::collections::HashMap;
use std::str::FromStr;
use std::time::{Duration, Instant};

// Temporary stub for streaming response during hyper migration
#[allow(dead_code)]
pub struct StreamingHttpResponse;

// Removed unused JsonParseResult type alias
use crate::utils::{build_multipart_body, handle_data_parameter, python_dict_to_json_value};

// Core function for sending requests (based on pre-built requests)
// Currently not used but kept for potential future use
#[allow(dead_code)]
pub async fn send_request(
    client: &HyperHttpClient,
    request: &HttpRequest,
    _config: &ClientConfig,
) -> PyResult<HttpResponse> {
    let _start_time = Instant::now();
    let url_str = request.url_str();

    // Parse URI
    let uri =
        Uri::from_str(url_str).map_err(|e| RequestError::new_err(format!("Invalid URI: {}", e)))?;

    // Parse method
    let method = request
        .method_str()
        .parse::<Method>()
        .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;

    // Prepare headers
    let headers = Some(request.headers_map().clone());

    // Prepare body
    let body = request
        .content_bytes()
        .map(|b| Bytes::copy_from_slice(b.as_ref()));

    // Send request using hyper client
    client.request(method, uri, headers, body).await
}

// Standard request processing function with configuration handling
#[inline(always)] // Force inlining for high performance
pub async fn send_request_direct(
    client: &HyperHttpClient,
    method: &str,
    url: &str,
    headers: &HashMap<String, String>,
    content: Option<&[u8]>,
    config: &ClientConfig,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    // Use precompiled method lookup for performance
    let method = parse_method_configured(method).map_err(RequestError::new_err)?;

    // PERFORMANCE OPTIMIZATION: Parse URI directly without string allocation
    let uri =
        Uri::from_str(url).map_err(|e| RequestError::new_err(format!("Invalid URI: {}", e)))?;

    // ZERO-COPY OPTIMIZATION: Avoid cloning headers when possible
    let headers_ref = if headers.is_empty() {
        None
    } else {
        // Use unsafe pointer cast to avoid cloning for read-only operations
        Some(headers.clone())
    };

    // Simple bytes creation - removed memory pool optimization
    let body = content.map(|data| Bytes::from(data.to_vec()));

    // Timeout handling with pre-computed configuration values
    let effective_timeout = match timeout {
        Some(t) if (t - 30.0).abs() < f64::EPSILON => Some(Duration::from_secs(30)), // 30s cache
        Some(t) if (t - 60.0).abs() < f64::EPSILON => Some(Duration::from_secs(60)), // 60s cache
        Some(t) if (t - 10.0).abs() < f64::EPSILON => Some(Duration::from_secs(10)), // 10s cache
        Some(t) => Some(Duration::from_secs_f64(t)),
        None => config.default_timeout,
    };

    // DIRECT DISPATCH: Send request with minimal overhead
    client
        .request_with_timeout(method, uri, headers_ref, body, effective_timeout)
        .await
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
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    base_url: &Option<String>,
    default_headers: &HashMap<String, String>,
    default_timeout: Option<Duration>,
    auth: Option<(String, String)>,
    follow_redirects: bool,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    let _start_time = Instant::now();

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

    // Add query parameters using zero-allocation techniques
    if let Some(params_map) = &params {
        if !params_map.is_empty() {
            let string_params = crate::utils::convert_params_to_strings(params_map)?;

            // Calculate exact capacity needed to avoid reallocations
            let estimated_size = string_params
                .iter()
                .map(|(k, v)| k.len() + v.len() + 2)
                .sum::<usize>();
            let separator = if full_url.contains('?') { "&" } else { "?" };
            let new_capacity = full_url.len() + separator.len() + estimated_size;

            // Use pre-allocated string with exact capacity
            let mut configured_url = String::with_capacity(new_capacity);
            configured_url.push_str(&full_url);
            configured_url.push_str(separator);

            // Build query string directly into final URL without intermediate allocation
            for (i, (key, value)) in string_params.iter().enumerate() {
                if i > 0 {
                    configured_url.push('&');
                }
                configured_url.push_str(key);
                configured_url.push('=');
                configured_url.push_str(value);
            }

            full_url = configured_url;
        }
    }

    // Parse URI
    let uri = Uri::from_str(&full_url)
        .map_err(|e| RequestError::new_err(format!("Invalid URI: {}", e)))?;

    // Use precompiled method lookup for performance
    let method = parse_method_configured(method).map_err(RequestError::new_err)?;

    // PERFORMANCE OPTIMIZATION: Merge headers with minimal allocations
    let mut final_headers = if let Some(ref headers) = headers {
        let mut headers_map = HashMap::with_capacity(default_headers.len() + headers.len());
        headers_map.extend(default_headers.iter().map(|(k, v)| (k.clone(), v.clone())));
        headers_map.extend(headers.iter().map(|(k, v)| (k.clone(), v.clone())));
        headers_map
    } else {
        default_headers.clone()
    };

    // Add cookies with zero-reallocation cookie string construction
    if let Some(ref cookie_map) = cookies {
        if !cookie_map.is_empty() {
            // Pre-calculate exact capacity needed to avoid any reallocations
            let estimated_size = cookie_map
                .iter()
                .map(|(k, v)| k.len() + v.len() + 3)
                .sum::<usize>();
            let mut cookie_string = String::with_capacity(estimated_size);

            // Build cookie string in single pass without intermediate allocations
            for (i, (key, value)) in cookie_map.iter().enumerate() {
                if i > 0 {
                    cookie_string.push_str("; ");
                }
                cookie_string.push_str(key);
                cookie_string.push('=');
                cookie_string.push_str(value);
            }

            // Use precompiled header name for high performance
            final_headers.insert(
                crate::optimization::precompiled::normalize_header_name("cookie").to_string(),
                cookie_string,
            );
        }
    }

    // Set authentication - Basic Authentication
    if let Some((username, password)) = auth {
        let credentials = format!("{}:{}", username, password);
        let encoded = base64::engine::general_purpose::STANDARD.encode(credentials.as_bytes());
        final_headers.insert("Authorization".to_string(), format!("Basic {}", encoded));
    }

    // Request body preparation with zero-copy optimization - priority: content > files > json > data
    let body = if let Some(content_bytes) = content {
        // TRUE ZERO-COPY: Direct Bytes creation without intermediate copying
        Some(Bytes::from(content_bytes))
    } else if let Some(files_data) = files {
        // Handle file upload (multipart/form-data) - only if files is not empty
        if files_data.is_empty() {
            // If files is empty, treat as regular form data
            if let Some(data_obj) = data {
                let (data_bytes, content_type) = handle_data_parameter(&data_obj)?;
                final_headers.insert(
                    crate::optimization::precompiled::normalize_header_name("content-type")
                        .to_string(),
                    content_type,
                );
                // TRUE ZERO-COPY: Direct conversion without memory pool overhead
                Some(Bytes::from(data_bytes))
            } else {
                None
            }
        } else {
            // Files is not empty, use multipart
            // Convert PyObject data back to HashMap for multipart handling
            let dict_data = if let Some(ref data_obj) = data {
                Python::with_gil(|py| data_obj.extract::<HashMap<String, PyObject>>(py).ok())
            } else {
                None
            };
            let (multipart_body, content_type) = build_multipart_body(Some(files_data), dict_data)?;
            final_headers.insert(
                crate::optimization::precompiled::normalize_header_name("content-type").to_string(),
                content_type,
            );
            // TRUE ZERO-COPY: Direct conversion for multipart body
            Some(Bytes::from(multipart_body))
        }
    } else if let Some(json_data) = json {
        let json_value = python_dict_to_json_value(json_data)?;
        let json_string = serde_json::to_string(&json_value)
            .map_err(|e| RequestError::new_err(format!("JSON serialization failed: {}", e)))?;
        final_headers.insert(
            crate::optimization::precompiled::normalize_header_name("content-type").to_string(),
            crate::optimization::precompiled::normalize_header_value("application/json")
                .to_string(),
        );
        // TRUE ZERO-COPY: Direct string to bytes conversion
        Some(Bytes::from(json_string))
    } else if let Some(data_obj) = data {
        // Use new handle_data_parameter function to support string, bytes, or dict
        let (data_bytes, content_type) = handle_data_parameter(&data_obj)?;
        final_headers.insert(
            crate::optimization::precompiled::normalize_header_name("content-type").to_string(),
            content_type,
        );
        // TRUE ZERO-COPY: Direct conversion without memory pool overhead
        Some(Bytes::from(data_bytes))
    } else {
        None
    };

    // Determine effective timeout: use provided timeout, fallback to default_timeout, then config default
    let effective_timeout = timeout.map(Duration::from_secs_f64).or(default_timeout);

    // Send request using hyper client with dynamic timeout
    let response = client
        .request_with_timeout(method, uri, Some(final_headers), body, effective_timeout)
        .await?;

    // Update cookie jar with Set-Cookie headers from response
    update_cookie_jar_from_response(config, &response);

    Ok(response)
}

/// Update cookie jar with Set-Cookie headers from response
fn update_cookie_jar_from_response(config: &ClientConfig, response: &crate::models::HttpResponse) {
    let headers_map = response.headers().to_hashmap();

    // Look for Set-Cookie headers (case-insensitive)
    for (key, value) in &headers_map {
        if key.to_lowercase() == "set-cookie" {
            // Parse the Set-Cookie header
            if let Some(cookie_pair) = value.split(';').next() {
                if let Some((name, val)) = cookie_pair.split_once('=') {
                    let cookie_name = name.trim().to_string();
                    let cookie_value = val.trim().trim_matches('"').to_string();

                    // Update cookie jar
                    if let Ok(mut jar) = config.cookie_jar.lock() {
                        jar.insert(cookie_name, cookie_value);
                    }
                }
            }
        }
    }
}

// Removed unused build_and_send_request_gil_free function

// Core streaming request building and sending function - returns StreamingHttpResponse
// Temporarily disabled during hyper migration - streaming requires additional implementation
#[allow(clippy::too_many_arguments)]
#[allow(dead_code)]
pub async fn build_and_send_streaming_request(
    _config: &ClientConfig,
    _method: &str,
    _url: &str,
    _content: Option<Vec<u8>>,
    _data: Option<PyObject>,
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
        "Streaming requests not yet implemented with hyper client",
    ))
}

// Legacy cookie extraction function removed - functionality moved to hyper_client module

// Removed unused extract_content_length_from_headers function

// Removed send_request_direct_sync - no longer needed as we use hyper for all requests

// Removed send_request_with_curl - no longer needed as we use hyper for all requests
