use crate::response::HttpResponse;
use crate::sync_core::SyncHttpClient;
use crate::streaming_stub::StreamingClient;
use pyo3::prelude::*;
use std::collections::HashMap;


// Unified synchronous request execution
#[allow(clippy::too_many_arguments)]
fn execute_request_with_sync_client(
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
    auth_tuple: Option<(String, String)>,
    follow_redirects: bool,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Use the provided config to create a client with proper timeout settings
    let sync_client = SyncHttpClient::new_with_config(config.clone())?;
    
    // Convert HashMap types to PyObject for sync_client (data is already PyObject)
    let json_obj = json.as_ref().map(|j| Python::with_gil(|py| j.to_object(py)));
    let files_obj = files.as_ref().map(|f| Python::with_gil(|py| f.to_object(py)));
    
    // Execute request using client with proper timeout configuration
    sync_client.send_request(
        method,
        url,
        content,
        data,
        json_obj,
        files_obj,
        params,
        headers,
        timeout,
        auth_tuple,
        Some(follow_redirects),
        cookies,
    )
}
use crate::auth::{extract_auth, extract_auth_from_object};
use crate::config::ClientConfig;
use crate::models::HttpHeaders;

// Helper function to extract headers from either HashMap or Headers object
fn extract_headers(headers: Option<PyObject>) -> PyResult<Option<HashMap<String, String>>> {
    if let Some(h) = headers {
        Python::with_gil(|py| {
            // Try to extract as HashMap first
            if let Ok(hashmap) = h.extract::<HashMap<String, String>>(py) {
                return Ok(Some(hashmap));
            }

            // Try to extract as Headers object
            if let Ok(headers_obj) = h.extract::<PyRef<HttpHeaders>>(py) {
                return Ok(Some(headers_obj.to_hashmap()));
            }

            // If neither works, return an error
            Err(pyo3::exceptions::PyTypeError::new_err(
                "headers must be a dict or Headers object",
            ))
        })
    } else {
        Ok(None)
    }
}

// Helper function to extract timeout from either f64 or Timeout object
fn extract_timeout_parameter(timeout: Option<f64>) -> Option<PyObject> {
    timeout.map(|t| Python::with_gil(|py| t.to_object(py)))
}

// Helper function to extract auth from either tuple or Auth object
fn extract_auth_parameter(auth: Option<PyObject>) -> PyResult<Option<(String, String)>> {
    if let Some(auth_obj) = auth {
        Python::with_gil(|py| {
            // Try to extract as tuple first (for backward compatibility)
            if let Ok(tuple) = auth_obj.extract::<(String, String)>(py) {
                return Ok(Some(tuple));
            }

            // Try to extract as Auth object
            if let Ok(auth_type) = extract_auth_from_object(&auth_obj) {
                if let Some(auth_data) = extract_auth(&auth_type) {
                    return Ok(Some(auth_data));
                }
            }

            // If neither works, return an error
            Err(pyo3::exceptions::PyTypeError::new_err(
                "auth must be a tuple (username, password) or Auth object",
            ))
        })
    } else {
        Ok(None)
    }
}

// Create a new client config for each request, mirroring httpx's behavior
fn create_ephemeral_config(
    cookies: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    follow_redirects: bool,
) -> PyResult<ClientConfig> {
    ClientConfig::new(
        None,                               // base_url
        extract_timeout_parameter(timeout), // timeout - convert f64 to PyObject
        None,                               // headers
        None,                               // verify
        Some(follow_redirects),             // follow_redirects
        None,                               // auth
        None,                               // proxy
        None,                               // proxies
        cookies,                            // cookies
        None,                               // http1
        None,                               // http2
        None,                               // event_hooks
        None,                               // cert
        None,                               // trust_env
        None,                               // transport
        None,                               // mounts
        None,                               // limits
        None,                               // max_redirects
        None,                               // default_encoding
        None,                               // params
    )
}

// Top-level API functions that create ephemeral clients (matching httpx behavior)
#[pyfunction]
pub fn get(
    url: &str,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<PyObject>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Extract auth parameter
    let auth_tuple = extract_auth_parameter(auth)?;

    // Create ephemeral config for this request only
    let config =
        create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;

    execute_request_with_sync_client(
        &config,
        "GET",
        url,
        None,
        None,
        None,
        None,
        params,
        headers,
        timeout,
        auth_tuple,
        follow_redirects.unwrap_or(false),
        cookies,
    )
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub fn post(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<PyObject>,
    timeout: Option<f64>,
    auth: Option<PyObject>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Extract auth parameter
    let auth_tuple = extract_auth_parameter(auth)?;

    // Create ephemeral config for this request only
    let config =
        create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;

    let extracted_headers = extract_headers(headers)?;
    execute_request_with_sync_client(
        &config,
        "POST",
        url,
        content,
        data,
        json,
        files,
        params,
        extracted_headers,
        timeout,
        auth_tuple,
        follow_redirects.unwrap_or(false),
        cookies,
    )
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub fn put(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<PyObject>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Extract auth parameter
    let auth_tuple = extract_auth_parameter(auth)?;

    // Create ephemeral config for this request only
    let config =
        create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;

    execute_request_with_sync_client(
        &config,
        "PUT",
        url,
        content,
        data,
        json,
        files,
        params,
        headers,
        timeout,
        auth_tuple,
        follow_redirects.unwrap_or(false),
        cookies,
    )
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub fn patch(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<PyObject>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Extract auth parameter
    let auth_tuple = extract_auth_parameter(auth)?;

    // Create ephemeral config for this request only
    let config =
        create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;

    execute_request_with_sync_client(
        &config,
        "PATCH",
        url,
        content,
        data,
        json,
        files,
        params,
        headers,
        timeout,
        auth_tuple,
        follow_redirects.unwrap_or(false),
        cookies,
    )
}

#[pyfunction]
pub fn delete(
    url: &str,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<PyObject>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Extract auth parameter
    let auth_tuple = extract_auth_parameter(auth)?;

    // Create ephemeral config for this request only
    let config =
        create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;

    execute_request_with_sync_client(
        &config,
        "DELETE",
        url,
        None,
        None,
        None,
        None,
        params,
        headers,
        timeout,
        auth_tuple,
        follow_redirects.unwrap_or(false),
        cookies,
    )
}

#[pyfunction]
pub fn head(
    url: &str,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<PyObject>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Extract auth parameter
    let auth_tuple = extract_auth_parameter(auth)?;

    // Create ephemeral config for this request only
    let config =
        create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;

    execute_request_with_sync_client(
        &config,
        "HEAD",
        url,
        None,
        None,
        None,
        None,
        params,
        headers,
        timeout,
        auth_tuple,
        follow_redirects.unwrap_or(false),
        cookies,
    )
}

#[pyfunction]
pub fn options(
    url: &str,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<PyObject>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Extract auth parameter
    let auth_tuple = extract_auth_parameter(auth)?;

    // Create ephemeral config for this request only
    let config =
        create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;

    execute_request_with_sync_client(
        &config,
        "OPTIONS",
        url,
        None,
        None,
        None,
        None,
        params,
        headers,
        timeout,
        auth_tuple,
        follow_redirects.unwrap_or(false),
        cookies,
    )
}

// Generic request function that creates ephemeral client
#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub fn request(
    method: &str,
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<PyObject>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<PyObject>,
    timeout: Option<f64>,
    auth: Option<PyObject>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Extract auth parameter
    let auth_tuple = extract_auth_parameter(auth)?;

    // Create ephemeral config for this request only
    let config =
        create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;

    let extracted_headers = extract_headers(headers)?;
    execute_request_with_sync_client(
        &config,
        method,
        url,
        content,
        data,
        json,
        files,
        params,
        extracted_headers,
        timeout,
        auth_tuple,
        follow_redirects.unwrap_or(false),
        cookies,
    )
}

// Enhanced streaming request function with ephemeral config
#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub fn stream(
    method: &str,
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, PyObject>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<PyObject>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<StreamingClient> {
    // Extract auth parameter
    let auth_tuple = extract_auth_parameter(auth)?;

    // Create ephemeral config for this request only
    let config =
        create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;

    Ok(StreamingClient::new(
        config,
        method.to_string(),
        url.to_string(),
        content,
        data,
        json,
        files,
        params,
        headers,
        timeout,
        auth_tuple,
        follow_redirects.unwrap_or(false),
        cookies,
    ))
}
