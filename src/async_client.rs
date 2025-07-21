use pyo3::prelude::*;
use pyo3_asyncio::tokio::future_into_py;
use reqwest::Client;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use crate::config::ClientConfig;
use crate::request::HttpRequest;

use crate::core::{send_request_direct, build_and_send_request};
use crate::utils::build_url;
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
        // Use centralized URL building
        let final_url = build_url(url, self.config.base_url.as_ref(), params.as_ref())
            .map_err(|e| RequestError::new_err(e))?;
        
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
        // Extract minimal data needed, avoid unnecessary cloning
        let method = request.method().to_string();
        let url = request.url().to_string();
        let headers = request.headers();
        let content_bytes = request.content().map(|b| b.to_vec());
        
        future_into_py(py, async move {
            send_request_direct(
                &client, 
                &method, 
                &url, 
                &headers, 
                content_bytes.as_deref(),
                &config
            ).await
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

    // Public request method for httpx compatibility
    pub fn request<'py>(&self, py: Python<'py>, method: String, url: String, content: Option<Vec<u8>>, data: Option<HashMap<String, PyObject>>, json: Option<HashMap<String, PyObject>>, files: Option<HashMap<String, PyObject>>, params: Option<HashMap<String, String>>, headers: Option<HashMap<String, String>>, timeout: Option<f64>, auth: Option<(String, String)>, follow_redirects: Option<bool>, cookies: Option<HashMap<String, String>>) -> PyResult<&'py PyAny> {
        self.async_request(py, &method, url, content, data, json, files, params, headers, timeout, auth, follow_redirects, cookies)
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

    pub fn stream<'py>(&self, py: Python<'py>, method: String, url: String, content: Option<Vec<u8>>, data: Option<HashMap<String, PyObject>>, json: Option<HashMap<String, PyObject>>, files: Option<HashMap<String, PyObject>>, params: Option<HashMap<String, String>>, headers: Option<HashMap<String, String>>, timeout: Option<f64>, auth: Option<(String, String)>, follow_redirects: Option<bool>, cookies: Option<HashMap<String, String>>) -> PyResult<&'py PyAny> {
        use crate::core::build_and_send_streaming_request;
        
        self.check_not_closed()?;
        
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
        
        let config = self.config.clone();
        
        future_into_py(py, async move {
            build_and_send_streaming_request(
                &config,
                &method, 
                &url, 
                content, 
                data, 
                json, 
                files, 
                params, 
                headers, 
                timeout, 
                &config.base_url, 
                &config.default_headers, 
                config.default_timeout, 
                auth_option, 
                follow_redirects,
                merged_cookies
            ).await
        })
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
        
        let config = self.config.clone();
        let method = method.to_string();
        
        future_into_py(py, async move {
            build_and_send_request(
                &config, &method, &url, content, data, json, files, params, headers,
                timeout, &config.base_url, &config.default_headers, config.default_timeout, auth_option,
                follow_redirects, merged_cookies
            ).await
        })
    }

    // httpx compatibility attributes
    #[getter]
    pub fn base_url(&self) -> Option<String> {
        self.config.base_url.clone()
    }

    #[getter]
    pub fn headers(&self) -> HashMap<String, String> {
        self.config.default_headers.clone()
    }

    #[getter]
    pub fn cookies(&self) -> HashMap<String, String> {
        self.config.default_cookies.clone()
    }

    #[getter]
    pub fn params(&self) -> HashMap<String, String> {
        // Return empty hashmap for now (could be extended if needed)
        HashMap::new()
    }

    #[getter]
    pub fn auth(&self) -> Option<PyObject> {
        self.config.auth_object.clone()
    }
} 