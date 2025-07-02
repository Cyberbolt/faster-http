use pyo3::prelude::*;
use reqwest::Client;
use std::collections::HashMap;
use std::sync::{Arc, OnceLock};
use crate::response::HttpResponse;
use crate::streaming::StreamingHttpResponse;
use crate::core::{build_and_send_request, build_and_send_streaming_request};
use crate::runtime::get_global_runtime;

// 全局客户端实例，用于复用连接池
static GLOBAL_CLIENT: OnceLock<Arc<Client>> = OnceLock::new();

fn get_global_client() -> Arc<Client> {
    GLOBAL_CLIENT.get_or_init(|| {
        Arc::new(Client::builder()
            .redirect(reqwest::redirect::Policy::limited(10)) // 全局客户端默认跟随重定向
            .build()
            .expect("Failed to create global client"))
    }).clone()
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
    let client = get_global_client();
    rt.block_on(build_and_send_request(
        &client, "GET", url, None, None, None, None, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(true), cookies
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
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    let rt = get_global_runtime();
    let client = get_global_client();
    rt.block_on(build_and_send_request(
        &client, "POST", url, content, data, json, files, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(true), cookies
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
    let client = get_global_client();
    rt.block_on(build_and_send_request(
        &client, "PUT", url, content, data, json, files, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(true), cookies
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
    let client = get_global_client();
    rt.block_on(build_and_send_request(
        &client, "PATCH", url, content, data, json, files, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(true), cookies
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
    let client = get_global_client();
    rt.block_on(build_and_send_request(
        &client, "DELETE", url, None, None, None, None, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(true), cookies
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
    let client = get_global_client();
    rt.block_on(build_and_send_request(
        &client, "HEAD", url, None, None, None, None, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(true), cookies
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
    let client = get_global_client();
    rt.block_on(build_and_send_request(
        &client, "OPTIONS", url, None, None, None, None, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(true), cookies
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
    let client = get_global_client();
    rt.block_on(build_and_send_streaming_request(
        &client, method, url, content, data, json, files, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(true), cookies
    ))
} 