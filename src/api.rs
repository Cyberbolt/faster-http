use pyo3::prelude::*;
use std::collections::HashMap;
use crate::response::HttpResponse;
use crate::streaming::StreamingClient;
use crate::core::build_and_send_request;
use crate::runtime::get_global_runtime;
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
            Err(pyo3::exceptions::PyTypeError::new_err("headers must be a dict or Headers object"))
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
        None,                       // base_url
        timeout,                    // timeout
        None,                       // headers
        None,                       // verify
        Some(follow_redirects),     // follow_redirects
        None,                       // auth
        None,                       // proxy
        None,                       // proxies
        cookies,                    // cookies
        None,                       // http1
        None,                       // http2
        None,                       // event_hooks
        None,                       // cert
        None,                       // trust_env
        None,                       // transport
        None,                       // mounts
        None,                       // limits
        None,                       // max_redirects
        None,                       // default_encoding
        None,                       // params
    )
}

// Top-level API functions that create ephemeral clients (matching httpx behavior)
#[pyfunction]
pub fn get(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Create ephemeral config for this request only
    let config = create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;
    
    let rt = get_global_runtime();
    rt.block_on(build_and_send_request(
        &config, "GET", url, None, None, None, None, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
}

#[pyfunction]
pub fn post(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<PyObject>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Create ephemeral config for this request only
    let config = create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;
    
    let rt = get_global_runtime();
    let extracted_headers = extract_headers(headers)?;
    rt.block_on(build_and_send_request(
        &config, "POST", url, content, data, json, files, params, extracted_headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
}

#[pyfunction]
pub fn put(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Create ephemeral config for this request only
    let config = create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;
    
    let rt = get_global_runtime();
    rt.block_on(build_and_send_request(
        &config, "PUT", url, content, data, json, files, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
}

#[pyfunction]
pub fn patch(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Create ephemeral config for this request only
    let config = create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;
    
    let rt = get_global_runtime();
    rt.block_on(build_and_send_request(
        &config, "PATCH", url, content, data, json, files, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
}

#[pyfunction]
pub fn delete(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Create ephemeral config for this request only
    let config = create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;
    
    let rt = get_global_runtime();
    rt.block_on(build_and_send_request(
        &config, "DELETE", url, None, None, None, None, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
}

#[pyfunction]
pub fn head(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Create ephemeral config for this request only
    let config = create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;
    
    let rt = get_global_runtime();
    rt.block_on(build_and_send_request(
        &config, "HEAD", url, None, None, None, None, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
}

#[pyfunction]
pub fn options(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Create ephemeral config for this request only
    let config = create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;
    
    let rt = get_global_runtime();
    rt.block_on(build_and_send_request(
        &config, "OPTIONS", url, None, None, None, None, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
}

// Generic request function that creates ephemeral client
#[pyfunction]
pub fn request(
    method: &str,
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<PyObject>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    // Create ephemeral config for this request only
    let config = create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;
    
    let rt = get_global_runtime();
    let extracted_headers = extract_headers(headers)?;
    rt.block_on(build_and_send_request(
        &config, method, url, content, data, json, files, params, extracted_headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
}

// Enhanced streaming request function with ephemeral config
#[pyfunction]
pub fn stream(
    method: &str,
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<StreamingClient> {
    // Create ephemeral config for this request only
    let config = create_ephemeral_config(cookies.clone(), timeout, follow_redirects.unwrap_or(false))?;
    
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
        auth,
        follow_redirects.unwrap_or(false),
        cookies,
    ))
}