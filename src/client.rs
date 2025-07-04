use pyo3::prelude::*;
use reqwest::Client;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use crate::config::ClientConfig;
use crate::request::HttpRequest;
use crate::response::HttpResponse;
use crate::core::{send_request, build_and_send_request};
use crate::utils::{build_full_url, add_query_params, merge_headers, merge_cookies};
use crate::auth::extract_auth;
use crate::runtime::get_global_runtime;
use crate::error::RequestError;

// 同步HTTP客户端
#[pyclass]
pub struct HttpClient {
    client: Client,
    config: ClientConfig,
    is_closed: AtomicBool,
}

#[pymethods]
impl HttpClient {
    #[new]
    pub fn new(
        base_url: Option<String>,
        timeout: Option<f64>,
        headers: Option<HashMap<String, String>>,
        verify: Option<bool>,
        follow_redirects: Option<bool>,
        auth: Option<(String, String)>,
        proxy: Option<String>,
        cookies: Option<HashMap<String, String>>,
        http2: Option<bool>,
    ) -> PyResult<Self> {
        let config = ClientConfig::new(
            base_url, timeout, headers, verify, follow_redirects, 
            auth, proxy, cookies, http2
        )?;
        let client = config.build_client(verify)?;

        Ok(HttpClient { 
            client, 
            config, 
            is_closed: AtomicBool::new(false),
        })
    }

    // 构建请求对象
    pub fn build_request(
        &self,
        method: &str,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        content: Option<Vec<u8>>,
    ) -> PyResult<HttpRequest> {
        let full_url = build_full_url(&self.config.base_url, url)?;
        let final_url = add_query_params(&full_url, params)?;
        let final_headers = merge_headers(&self.config.default_headers, headers);

        Ok(HttpRequest::new(
            method.to_string(),
            final_url,
            Some(final_headers),
            content,
        ))
    }

    // 发送预构建的请求
    pub fn send(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        self.check_not_closed()?;
        let rt = get_global_runtime();
        rt.block_on(send_request(&self.client, request, &self.config))
    }

    fn __enter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __exit__(
        &self,
        _exc_type: Option<PyObject>,
        _exc_val: Option<PyObject>,
        _exc_tb: Option<PyObject>,
    ) -> PyResult<bool> {
        self.close()?;
        Ok(false)
    }

    // 关闭客户端连接池
    pub fn close(&self) -> PyResult<()> {
        self.is_closed.store(true, Ordering::Relaxed);
        Ok(())
    }

    // 检查客户端是否已关闭
    fn check_not_closed(&self) -> PyResult<()> {
        if self.is_closed.load(Ordering::Relaxed) {
            return Err(RequestError::new_err("Client has been closed"));
        }
        Ok(())
    }

    // 通用请求方法，减少重复代码
    fn _request(
        &self,
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
    ) -> PyResult<HttpResponse> {
        self.check_not_closed()?;
        let rt = get_global_runtime();
        
        let merged_cookies = merge_cookies(&self.config.default_cookies, cookies);
        let auth_option = auth.or_else(|| extract_auth(&self.config.auth));
        let follow_redirects = follow_redirects.unwrap_or(self.config.follow_redirects);
        
        rt.block_on(build_and_send_request(
            &self.client,
            method, 
            url, 
            content, 
            data, 
            json, 
            files, 
            params, 
            headers, 
            timeout, 
            &self.config.base_url, 
            &self.config.default_headers, 
            self.config.default_timeout, 
            auth_option, 
            follow_redirects,
            merged_cookies
        ))
    }

    pub fn get(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self._request("GET", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn post(
        &self,
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
        self._request("POST", url, content, data, json, files, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn put(
        &self,
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
        self._request("PUT", url, content, data, json, files, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn patch(
        &self,
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
        self._request("PATCH", url, content, data, json, files, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn delete(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self._request("DELETE", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn head(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self._request("HEAD", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn options(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<HttpResponse> {
        self._request("OPTIONS", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }
} 