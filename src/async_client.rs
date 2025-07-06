use pyo3::prelude::*;
use pyo3_asyncio::tokio::future_into_py;
use reqwest::Client;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use crate::config::ClientConfig;
use crate::request::HttpRequest;

use crate::core::{send_request, build_and_send_request};
// Removed utils imports - delegate URL/header processing to reqwest
use crate::auth::extract_auth;
use crate::error::RequestError;

// Asynchronous HTTP client
#[pyclass]
#[derive(Clone)]
pub struct AsyncHttpClient {
    client: Client,
    config: ClientConfig,
    is_closed: Arc<AtomicBool>,
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
        auth: Option<PyObject>,
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
            is_closed: Arc::new(AtomicBool::new(false)),
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
        // Let reqwest handle URL building and query params
        let mut final_url = url.to_string();
        
        // Basic base URL handling if needed
        if let Some(base) = &self.config.base_url {
            if !url.starts_with("http://") && !url.starts_with("https://") {
                final_url = format!("{}/{}", base.trim_end_matches('/'), url.trim_start_matches('/'));
            }
        }
        
        // Let reqwest handle query params
        if let Some(params) = params {
            let mut parsed_url = reqwest::Url::parse(&final_url)
                .map_err(|e| RequestError::new_err(format!("Invalid URL: {}", e)))?;
            
            for (key, value) in params {
                parsed_url.query_pairs_mut().append_pair(&key, &value);
            }
            final_url = parsed_url.to_string();
        }
        
        // Simple header merging
        let mut final_headers = self.config.default_headers.clone();
        if let Some(headers) = headers {
            final_headers.extend(headers);
        }

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
        // Avoid unnecessary cloning by moving data directly
        let method = request.method().to_string();
        let url = request.url().to_string();
        let headers = request.headers();
        let content = request.content().map(|b| b.to_vec());
        
        future_into_py(py, async move {
            let request_obj = HttpRequest::new(method, url, Some(headers), content);
            send_request(&client, &request_obj, &config).await
        })
    }

    fn __aenter__<'py>(&self, py: Python<'py>) -> PyResult<&'py PyAny> {
        // Return self in async context manager
        let self_ref = self.clone();
        future_into_py(py, async move {
            Ok(self_ref)
        })
    }

    fn __aexit__<'py>(
        &self,
        py: Python<'py>,
        _exc_type: Option<PyObject>,
        _exc_val: Option<PyObject>,
        _exc_tb: Option<PyObject>,
    ) -> PyResult<&'py PyAny> {
        future_into_py(py, async move {
            Ok(false)
        })
    }

    // Close client connection pool
    pub fn close(&self) -> PyResult<()> {
        self.is_closed.store(true, Ordering::Relaxed);
        Ok(())
    }

    // Async close client connection pool
    pub fn aclose<'py>(&self, py: Python<'py>) -> PyResult<&'py PyAny> {
        self.close()?;
        future_into_py(py, async move { Ok(()) })
    }

    // Check if client is closed
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
        
        // Simple cookie merging - delegate actual cookie handling to reqwest
        let merged_cookies = match cookies {
            Some(request_cookies) => {
                let mut merged = self.config.default_cookies.clone();
                merged.extend(request_cookies);
                Some(merged)
            }
            None if !self.config.default_cookies.is_empty() => Some(self.config.default_cookies.clone()),
            _ => None,
        };
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