use pyo3::prelude::*;
use pyo3_asyncio::tokio::future_into_py;
use reqwest::Client;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use crate::config::ClientConfig;
use crate::request::HttpRequest;

use crate::core::{send_request, build_and_send_request};
use crate::utils::{build_full_url, add_query_params, merge_headers, merge_cookies};
use crate::auth::extract_auth;
use crate::error::RequestError;

// 异步 HTTP 客户端
#[pyclass]
pub struct AsyncHttpClient {
    client: Client,
    config: ClientConfig,
    is_closed: AtomicBool,
}

#[pymethods]
impl AsyncHttpClient {
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

        Ok(AsyncHttpClient { 
            client, 
            config, 
            is_closed: AtomicBool::new(false),
        })
    }

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

    pub fn send<'py>(&self, py: Python<'py>, request: &HttpRequest) -> PyResult<&'py PyAny> {
        self.check_not_closed()?;
        
        let client = self.client.clone();
        let config = self.config.clone();
        let request_clone = HttpRequest::new(
            request.method().to_string(),
            request.url().to_string(),
            Some(request.headers()),
            request.content().map(|b| b.to_vec()),
        );
        
        future_into_py(py, async move {
            send_request(&client, &request_clone, &config).await
        })
    }

    fn __aenter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> { slf }

    fn __aexit__(
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

    // 异步关闭客户端连接池
    pub fn aclose<'py>(&self, py: Python<'py>) -> PyResult<&'py PyAny> {
        self.close()?;
        future_into_py(py, async move { Ok(()) })
    }

    // 检查客户端是否已关闭
    fn check_not_closed(&self) -> PyResult<()> {
        if self.is_closed.load(Ordering::Relaxed) {
            return Err(RequestError::new_err("AsyncClient has been closed"));
        }
        Ok(())
    }

    pub fn get<'py>(&self, py: Python<'py>, url: String, params: Option<HashMap<String, String>>, headers: Option<HashMap<String, String>>, timeout: Option<f64>, auth: Option<(String, String)>, follow_redirects: Option<bool>, cookies: Option<HashMap<String, String>>) -> PyResult<&'py PyAny> {
        self.async_request(py, "GET", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn post<'py>(&self, py: Python<'py>, url: String, content: Option<Vec<u8>>, data: Option<HashMap<String, PyObject>>, json: Option<HashMap<String, PyObject>>, files: Option<HashMap<String, PyObject>>, params: Option<HashMap<String, String>>, headers: Option<HashMap<String, String>>, timeout: Option<f64>, auth: Option<(String, String)>, follow_redirects: Option<bool>, cookies: Option<HashMap<String, String>>) -> PyResult<&'py PyAny> {
        self.async_request(py, "POST", url, content, data, json, files, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn put<'py>(&self, py: Python<'py>, url: String, content: Option<Vec<u8>>, data: Option<HashMap<String, PyObject>>, json: Option<HashMap<String, PyObject>>, files: Option<HashMap<String, PyObject>>, params: Option<HashMap<String, String>>, headers: Option<HashMap<String, String>>, timeout: Option<f64>, auth: Option<(String, String)>, follow_redirects: Option<bool>, cookies: Option<HashMap<String, String>>) -> PyResult<&'py PyAny> {
        self.async_request(py, "PUT", url, content, data, json, files, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn patch<'py>(&self, py: Python<'py>, url: String, content: Option<Vec<u8>>, data: Option<HashMap<String, PyObject>>, json: Option<HashMap<String, PyObject>>, files: Option<HashMap<String, PyObject>>, params: Option<HashMap<String, String>>, headers: Option<HashMap<String, String>>, timeout: Option<f64>, auth: Option<(String, String)>, follow_redirects: Option<bool>, cookies: Option<HashMap<String, String>>) -> PyResult<&'py PyAny> {
        self.async_request(py, "PATCH", url, content, data, json, files, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn delete<'py>(&self, py: Python<'py>, url: String, params: Option<HashMap<String, String>>, headers: Option<HashMap<String, String>>, timeout: Option<f64>, auth: Option<(String, String)>, follow_redirects: Option<bool>, cookies: Option<HashMap<String, String>>) -> PyResult<&'py PyAny> {
        self.async_request(py, "DELETE", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn head<'py>(&self, py: Python<'py>, url: String, params: Option<HashMap<String, String>>, headers: Option<HashMap<String, String>>, timeout: Option<f64>, auth: Option<(String, String)>, follow_redirects: Option<bool>, cookies: Option<HashMap<String, String>>) -> PyResult<&'py PyAny> {
        self.async_request(py, "HEAD", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn options<'py>(&self, py: Python<'py>, url: String, params: Option<HashMap<String, String>>, headers: Option<HashMap<String, String>>, timeout: Option<f64>, auth: Option<(String, String)>, follow_redirects: Option<bool>, cookies: Option<HashMap<String, String>>) -> PyResult<&'py PyAny> {
        self.async_request(py, "OPTIONS", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }

    fn async_request<'py>(
        &self,
        py: Python<'py>,
        method: &str,
        url: String,
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
    ) -> PyResult<&'py PyAny> {
        self.check_not_closed()?;
        
        let merged_cookies = merge_cookies(&self.config.default_cookies, cookies);
        let auth_option = auth.or_else(|| extract_auth(&self.config.auth));
        let follow_redirects = follow_redirects.unwrap_or(self.config.follow_redirects);
        
        let client = self.client.clone();
        let base_url = self.config.base_url.clone();
        let default_headers = self.config.default_headers.clone();
        let default_timeout = self.config.default_timeout;
        let method = method.to_string();
        
        future_into_py(py, async move {
            build_and_send_request(
                &client, &method, &url, content, data, json, files, params, headers,
                timeout, &base_url, &default_headers, default_timeout, auth_option,
                follow_redirects, merged_cookies
            ).await
        })
    }
} 