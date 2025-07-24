use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::OnceLock;
use crate::response::HttpResponse;
use crate::streaming::StreamingHttpResponse;
use crate::core::{build_and_send_request, build_and_send_streaming_request};
use crate::runtime::get_global_runtime;
use crate::config::ClientConfig;
use crate::models::HttpHeaders;

// 全局配置实例
static GLOBAL_CONFIG: OnceLock<ClientConfig> = OnceLock::new();

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

fn get_global_config() -> &'static ClientConfig {
    GLOBAL_CONFIG.get_or_init(|| {
        ClientConfig::new(
            None, None, None, None, None, None, None, None, None
        ).expect("Failed to create global config")
    })
}

// 全局函数
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
    let rt = get_global_runtime();
    let config = get_global_config();
    rt.block_on(build_and_send_request(
        config, "GET", url, None, None, None, None, params, headers, timeout,
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
    headers: Option<PyObject>,  // Changed to PyObject to support both dict and Headers
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    let rt = get_global_runtime();
    let config = get_global_config();
    let extracted_headers = extract_headers(headers)?;
    rt.block_on(build_and_send_request(
        config, "POST", url, content, data, json, files, params, extracted_headers, timeout,
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
    let rt = get_global_runtime();
    let config = get_global_config();
    rt.block_on(build_and_send_request(
        config, "PUT", url, content, data, json, files, params, headers, timeout,
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
    let rt = get_global_runtime();
    let config = get_global_config();
    rt.block_on(build_and_send_request(
        config, "PATCH", url, content, data, json, files, params, headers, timeout,
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
    let rt = get_global_runtime();
    let config = get_global_config();
    rt.block_on(build_and_send_request(
        config, "DELETE", url, None, None, None, None, params, headers, timeout,
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
    let rt = get_global_runtime();
    let config = get_global_config();
    rt.block_on(build_and_send_request(
        config, "HEAD", url, None, None, None, None, params, headers, timeout,
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
    let rt = get_global_runtime();
    let config = get_global_config();
    rt.block_on(build_and_send_request(
        config, "OPTIONS", url, None, None, None, None, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
}

// 通用请求函数
#[pyfunction]
pub fn request(
    method: &str,
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<PyObject>,  // Support both dict and Headers
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    let rt = get_global_runtime();
    let config = get_global_config();
    let extracted_headers = extract_headers(headers)?;
    rt.block_on(build_and_send_request(
        config, method, url, content, data, json, files, params, extracted_headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
}

// 流式请求函数
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
) -> PyResult<StreamingHttpResponse> {
    let rt = get_global_runtime();
    let config = get_global_config();
    rt.block_on(build_and_send_streaming_request(
        config, method, url, content, data, json, files, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(false), cookies
    ))
} 