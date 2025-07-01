use pyo3::prelude::*;
use pyo3::{exceptions::PyException, PyResult};
use pyo3_asyncio::tokio::future_into_py;
use reqwest::{Client, Method, Url};
use serde_json::Value;
use std::collections::HashMap;
use std::sync::OnceLock;
use std::time::{Duration, Instant};
use bytes::Bytes;

// 创建自定义异常类型
pyo3::create_exception!(faster_http, HTTPError, PyException);
pyo3::create_exception!(faster_http, ConnectTimeout, HTTPError);
pyo3::create_exception!(faster_http, ReadTimeout, HTTPError);
pyo3::create_exception!(faster_http, RequestError, HTTPError);

// 全局运行时，用于同步客户端
static RUNTIME: OnceLock<tokio::runtime::Runtime> = OnceLock::new();

fn get_runtime() -> &'static tokio::runtime::Runtime {
    RUNTIME.get_or_init(|| {
        tokio::runtime::Runtime::new().expect("Failed to create tokio runtime")
    })
}

// 响应对象
#[pyclass]
pub struct HttpResponse {
    status_code: u16,
    headers: HashMap<String, String>,
    body: Bytes,
    url: String,
    elapsed: f64,
}

#[pymethods]
impl HttpResponse {
    #[getter]
    pub fn status_code(&self) -> u16 {
        self.status_code
    }

    #[getter]
    pub fn headers(&self) -> HashMap<String, String> {
        self.headers.clone()
    }

    #[getter]
    pub fn url(&self) -> &str {
        &self.url
    }

    #[getter]
    pub fn ok(&self) -> bool {
        self.status_code < 400
    }

    #[getter]
    pub fn content(&self) -> &[u8] {
        &self.body
    }

    #[getter]
    pub fn text(&self) -> PyResult<String> {
        String::from_utf8(self.body.to_vec())
            .map_err(|e| RequestError::new_err(format!("Invalid UTF-8: {}", e)))
    }

    #[getter]
    pub fn elapsed(&self) -> f64 {
        self.elapsed
    }

    #[getter]
    pub fn is_client_error(&self) -> bool {
        self.status_code >= 400 && self.status_code < 500
    }

    #[getter]
    pub fn is_server_error(&self) -> bool {
        self.status_code >= 500
    }

    pub fn json(&self, py: Python) -> PyResult<PyObject> {
        let text = self.text()?;
        let value: Value = serde_json::from_str(&text)
            .map_err(|e| RequestError::new_err(format!("JSON decode error: {}", e)))?;
        pythonize::pythonize(py, &value)
            .map_err(|e| RequestError::new_err(format!("Python conversion error: {}", e)))
    }

    pub fn raise_for_status(&self) -> PyResult<()> {
        if self.status_code >= 400 {
            return Err(HTTPError::new_err(format!(
                "HTTP {} Error: {} for url: {}",
                self.status_code,
                self.status_code,
                self.url
            )));
        }
        Ok(())
    }

    pub fn __repr__(&self) -> String {
        format!("<Response [{}]>", self.status_code)
    }
}

// 同步HTTP客户端 - 使用全局runtime
#[pyclass]
pub struct HttpClient {
    client: Client,
    base_url: Option<String>,
    default_timeout: Option<Duration>,
    default_headers: HashMap<String, String>,
}

#[pymethods]
impl HttpClient {
    #[new]
    pub fn new(
        base_url: Option<String>,
        timeout: Option<f64>,
        headers: Option<HashMap<String, String>>,
        verify: Option<bool>,
    ) -> PyResult<Self> {
        let verify = verify.unwrap_or(true);
        let client = Client::builder()
            .danger_accept_invalid_certs(!verify)
            .build()
            .map_err(|e| RequestError::new_err(format!("Failed to create client: {}", e)))?;

        Ok(HttpClient {
            client,
            base_url,
            default_timeout: timeout.map(Duration::from_secs_f64),
            default_headers: headers.unwrap_or_default(),
        })
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
        Ok(false)
    }

    fn _request(
        &self,
        method: &str,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        let rt = get_runtime();
        rt.block_on(self._async_request(method, url, content, data, json, params, headers, timeout))
    }

    pub fn get(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self._request("GET", url, None, None, None, params, headers, timeout)
    }

    pub fn post(
        &self,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self._request("POST", url, content, data, json, params, headers, timeout)
    }

    pub fn put(
        &self,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self._request("PUT", url, content, data, json, params, headers, timeout)
    }

    pub fn patch(
        &self,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self._request("PATCH", url, content, data, json, params, headers, timeout)
    }

    pub fn delete(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self._request("DELETE", url, None, None, None, params, headers, timeout)
    }

    pub fn head(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self._request("HEAD", url, None, None, None, params, headers, timeout)
    }

    pub fn options(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self._request("OPTIONS", url, None, None, None, params, headers, timeout)
    }
}

impl HttpClient {
    async fn _async_request(
        &self,
        method: &str,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        let start_time = Instant::now();
        
        let method = Method::from_bytes(method.as_bytes())
            .map_err(|e| RequestError::new_err(format!("Invalid method: {}", e)))?;

        let full_url = if let Some(base) = &self.base_url {
            format!("{}/{}", base.trim_end_matches('/'), url.trim_start_matches('/'))
        } else {
            url.to_string()
        };

        let mut url_with_params = Url::parse(&full_url)
            .map_err(|e| RequestError::new_err(format!("Invalid URL: {}", e)))?;

        if let Some(params) = params {
            for (key, value) in params {
                url_with_params.query_pairs_mut().append_pair(&key, &value);
            }
        }

        let mut request = self.client.request(method, url_with_params);

        // 设置默认headers
        for (key, value) in &self.default_headers {
            request = request.header(key, value);
        }

        // 设置请求特定的headers
        if let Some(headers) = headers {
            for (key, value) in headers {
                request = request.header(key, value);
            }
        }

        // 设置body - 优先级：content > json > data
        if let Some(content_bytes) = content {
            request = request.body(content_bytes);
        } else if let Some(json_data) = json {
            let json_value = python_dict_to_json_value(json_data)?;
            request = request.json(&json_value);
        } else if let Some(form_data) = data {
            // 使用 form encoded 而不是 multipart
            let form_string = python_dict_to_form_string(form_data)?;
            request = request
                .header("Content-Type", "application/x-www-form-urlencoded")
                .body(form_string);
        }

        // 设置超时
        let timeout_duration = timeout
            .map(Duration::from_secs_f64)
            .or(self.default_timeout)
            .unwrap_or(Duration::from_secs(30));
        request = request.timeout(timeout_duration);

        let response = request.send().await
            .map_err(|e| {
                if e.is_timeout() {
                    ReadTimeout::new_err(format!("Request timeout: {}", e))
                } else if e.is_connect() {
                    ConnectTimeout::new_err(format!("Connection timeout: {}", e))
                } else {
                    RequestError::new_err(format!("Request failed: {}", e))
                }
            })?;

        // 先获取response的信息再读取body
        let status_code = response.status().as_u16();
        let url = response.url().to_string();
        let headers = response
            .headers()
            .iter()
            .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
            .collect();

        let body = response.bytes().await
            .map_err(|e| RequestError::new_err(format!("Failed to read response body: {}", e)))?;

        let elapsed = start_time.elapsed().as_secs_f64();

        Ok(HttpResponse {
            status_code,
            headers,
            body,
            url,
            elapsed,
        })
    }
}

// 异步HTTP客户端 - 真正的异步方法
#[pyclass]
pub struct AsyncHttpClient {
    client: Client,
    base_url: Option<String>,
    default_timeout: Option<Duration>,
    default_headers: HashMap<String, String>,
}

#[pymethods]
impl AsyncHttpClient {
    #[new]
    pub fn new(
        base_url: Option<String>,
        timeout: Option<f64>,
        headers: Option<HashMap<String, String>>,
        verify: Option<bool>,
    ) -> PyResult<Self> {
        let verify = verify.unwrap_or(true);
        let client = Client::builder()
            .danger_accept_invalid_certs(!verify)
            .build()
            .map_err(|e| RequestError::new_err(format!("Failed to create client: {}", e)))?;

        Ok(AsyncHttpClient {
            client,
            base_url,
            default_timeout: timeout.map(Duration::from_secs_f64),
            default_headers: headers.unwrap_or_default(),
        })
    }

    fn __aenter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __aexit__(
        &self,
        _exc_type: Option<PyObject>,
        _exc_val: Option<PyObject>,
        _exc_tb: Option<PyObject>,
    ) -> PyResult<bool> {
        Ok(false)
    }

    pub fn get<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<&'py PyAny> {
        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let default_timeout = self.default_timeout;
        let default_headers = self.default_headers.clone();

        future_into_py(py, async move {
            let start_time = Instant::now();
            let request = AsyncHttpClient::build_request(
                &client, "GET", &url, None, None, None, params, headers, 
                &base_url, default_timeout, &default_headers, timeout
            ).await?;
            
            let response = request.send().await
                .map_err(|e| RequestError::new_err(format!("Request failed: {}", e)))?;
            
            // 先获取response信息
            let status_code = response.status().as_u16();
            let url = response.url().to_string();
            let headers = response
                .headers()
                .iter()
                .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
                .collect();

            let body = response.bytes().await
                .map_err(|e| RequestError::new_err(format!("Failed to read response: {}", e)))?;

            let elapsed = start_time.elapsed().as_secs_f64();

            Ok(HttpResponse {
                status_code,
                headers,
                body,
                url,
                elapsed,
            })
        })
    }

    pub fn post<'py>(
        &self,
        py: Python<'py>,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<&'py PyAny> {
        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let default_timeout = self.default_timeout;
        let default_headers = self.default_headers.clone();

        future_into_py(py, async move {
            let start_time = Instant::now();
            let request = AsyncHttpClient::build_request(
                &client, "POST", &url, content, data, json, params, headers,
                &base_url, default_timeout, &default_headers, timeout
            ).await?;
            
            let response = request.send().await
                .map_err(|e| RequestError::new_err(format!("Request failed: {}", e)))?;
            
            let status_code = response.status().as_u16();
            let url = response.url().to_string();
            let headers = response
                .headers()
                .iter()
                .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
                .collect();

            let body = response.bytes().await
                .map_err(|e| RequestError::new_err(format!("Failed to read response: {}", e)))?;

            let elapsed = start_time.elapsed().as_secs_f64();

            Ok(HttpResponse {
                status_code,
                headers,
                body,
                url,
                elapsed,
            })
        })
    }

    pub fn put<'py>(
        &self,
        py: Python<'py>,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<&'py PyAny> {
        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let default_timeout = self.default_timeout;
        let default_headers = self.default_headers.clone();

        future_into_py(py, async move {
            let start_time = Instant::now();
            let request = AsyncHttpClient::build_request(
                &client, "PUT", &url, content, data, json, params, headers,
                &base_url, default_timeout, &default_headers, timeout
            ).await?;
            
            let response = request.send().await
                .map_err(|e| RequestError::new_err(format!("Request failed: {}", e)))?;
            
            let status_code = response.status().as_u16();
            let url = response.url().to_string();
            let headers = response
                .headers()
                .iter()
                .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
                .collect();

            let body = response.bytes().await
                .map_err(|e| RequestError::new_err(format!("Failed to read response: {}", e)))?;

            let elapsed = start_time.elapsed().as_secs_f64();

            Ok(HttpResponse {
                status_code,
                headers,
                body,
                url,
                elapsed,
            })
        })
    }

    pub fn patch<'py>(
        &self,
        py: Python<'py>,
        url: String,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<&'py PyAny> {
        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let default_timeout = self.default_timeout;
        let default_headers = self.default_headers.clone();

        future_into_py(py, async move {
            let start_time = Instant::now();
            let request = AsyncHttpClient::build_request(
                &client, "PATCH", &url, content, data, json, params, headers,
                &base_url, default_timeout, &default_headers, timeout
            ).await?;
            
            let response = request.send().await
                .map_err(|e| RequestError::new_err(format!("Request failed: {}", e)))?;
            
            let status_code = response.status().as_u16();
            let url = response.url().to_string();
            let headers = response
                .headers()
                .iter()
                .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
                .collect();

            let body = response.bytes().await
                .map_err(|e| RequestError::new_err(format!("Failed to read response: {}", e)))?;

            let elapsed = start_time.elapsed().as_secs_f64();

            Ok(HttpResponse {
                status_code,
                headers,
                body,
                url,
                elapsed,
            })
        })
    }

    pub fn delete<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<&'py PyAny> {
        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let default_timeout = self.default_timeout;
        let default_headers = self.default_headers.clone();

        future_into_py(py, async move {
            let start_time = Instant::now();
            let request = AsyncHttpClient::build_request(
                &client, "DELETE", &url, None, None, None, params, headers,
                &base_url, default_timeout, &default_headers, timeout
            ).await?;
            
            let response = request.send().await
                .map_err(|e| RequestError::new_err(format!("Request failed: {}", e)))?;
            
            let status_code = response.status().as_u16();
            let url = response.url().to_string();
            let headers = response
                .headers()
                .iter()
                .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
                .collect();

            let body = response.bytes().await
                .map_err(|e| RequestError::new_err(format!("Failed to read response: {}", e)))?;

            let elapsed = start_time.elapsed().as_secs_f64();

            Ok(HttpResponse {
                status_code,
                headers,
                body,
                url,
                elapsed,
            })
        })
    }

    pub fn head<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<&'py PyAny> {
        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let default_timeout = self.default_timeout;
        let default_headers = self.default_headers.clone();

        future_into_py(py, async move {
            let start_time = Instant::now();
            let request = AsyncHttpClient::build_request(
                &client, "HEAD", &url, None, None, None, params, headers,
                &base_url, default_timeout, &default_headers, timeout
            ).await?;
            
            let response = request.send().await
                .map_err(|e| RequestError::new_err(format!("Request failed: {}", e)))?;
            
            let status_code = response.status().as_u16();
            let url = response.url().to_string();
            let headers = response
                .headers()
                .iter()
                .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
                .collect();

            let body = response.bytes().await
                .map_err(|e| RequestError::new_err(format!("Failed to read response: {}", e)))?;

            let elapsed = start_time.elapsed().as_secs_f64();

            Ok(HttpResponse {
                status_code,
                headers,
                body,
                url,
                elapsed,
            })
        })
    }

    pub fn options<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<&'py PyAny> {
        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let default_timeout = self.default_timeout;
        let default_headers = self.default_headers.clone();

        future_into_py(py, async move {
            let start_time = Instant::now();
            let request = AsyncHttpClient::build_request(
                &client, "OPTIONS", &url, None, None, None, params, headers,
                &base_url, default_timeout, &default_headers, timeout
            ).await?;
            
            let response = request.send().await
                .map_err(|e| RequestError::new_err(format!("Request failed: {}", e)))?;
            
            let status_code = response.status().as_u16();
            let url = response.url().to_string();
            let headers = response
                .headers()
                .iter()
                .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
                .collect();

            let body = response.bytes().await
                .map_err(|e| RequestError::new_err(format!("Failed to read response: {}", e)))?;

            let elapsed = start_time.elapsed().as_secs_f64();

            Ok(HttpResponse {
                status_code,
                headers,
                body,
                url,
                elapsed,
            })
        })
    }
}

impl AsyncHttpClient {
    async fn build_request(
        client: &Client,
        method: &str,
        url: &str,
        content: Option<Vec<u8>>,
        data: Option<HashMap<String, PyObject>>,
        json: Option<HashMap<String, PyObject>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        base_url: &Option<String>,
        default_timeout: Option<Duration>,
        default_headers: &HashMap<String, String>,
        timeout: Option<f64>,
    ) -> PyResult<reqwest::RequestBuilder> {
        let method = Method::from_bytes(method.as_bytes())
            .map_err(|e| RequestError::new_err(format!("Invalid method: {}", e)))?;

        let full_url = if let Some(base) = base_url {
            format!("{}/{}", base.trim_end_matches('/'), url.trim_start_matches('/'))
        } else {
            url.to_string()
        };

        let mut url_with_params = Url::parse(&full_url)
            .map_err(|e| RequestError::new_err(format!("Invalid URL: {}", e)))?;

        if let Some(params) = params {
            for (key, value) in params {
                url_with_params.query_pairs_mut().append_pair(&key, &value);
            }
        }

        let mut request = client.request(method, url_with_params);

        // 设置默认headers
        for (key, value) in default_headers {
            request = request.header(key, value);
        }

        // 设置请求特定的headers
        if let Some(headers) = headers {
            for (key, value) in headers {
                request = request.header(key, value);
            }
        }

        // 设置body - 优先级：content > json > data
        if let Some(content_bytes) = content {
            request = request.body(content_bytes);
        } else if let Some(json_data) = json {
            let json_value = python_dict_to_json_value(json_data)?;
            request = request.json(&json_value);
        } else if let Some(form_data) = data {
            // 使用 form encoded 而不是 multipart
            let form_string = python_dict_to_form_string(form_data)?;
            request = request
                .header("Content-Type", "application/x-www-form-urlencoded")
                .body(form_string);
        }

        // 设置超时
        let timeout_duration = timeout
            .map(Duration::from_secs_f64)
            .or(default_timeout)
            .unwrap_or(Duration::from_secs(30));
        request = request.timeout(timeout_duration);

        Ok(request)
    }
}

// 辅助函数：将Python对象转换为JSON Value
fn python_dict_to_json_value(data: HashMap<String, PyObject>) -> PyResult<Value> {
    let mut map = serde_json::Map::new();
    
    Python::with_gil(|py| {
        for (key, value) in data {
            let json_value = python_to_json_value(py, &value)?;
            map.insert(key, json_value);
        }
        Ok(Value::Object(map))
    })
}

// 辅助函数：将Python对象转换为表单字符串
fn python_dict_to_form_string(data: HashMap<String, PyObject>) -> PyResult<String> {
    let mut form_pairs = Vec::new();
    
    Python::with_gil(|py| {
        for (key, value) in data {
            let value_str = if value.is_none(py) {
                "".to_string()
            } else {
                // 使用format!处理PyObject到字符串的转换
                format!("{}", value.as_ref(py))
            };
            form_pairs.push(format!("{}={}", 
                urlencoding::encode(&key), 
                urlencoding::encode(&value_str)
            ));
        }
        Ok(form_pairs.join("&"))
    })
}

// 辅助函数：将Python对象转换为JSON Value
fn python_to_json_value(py: Python, obj: &PyObject) -> PyResult<Value> {
    if obj.is_none(py) {
        Ok(Value::Null)
    } else if let Ok(b) = obj.extract::<bool>(py) {
        Ok(Value::Bool(b))
    } else if let Ok(i) = obj.extract::<i64>(py) {
        Ok(Value::Number(serde_json::Number::from(i)))
    } else if let Ok(f) = obj.extract::<f64>(py) {
        if let Some(n) = serde_json::Number::from_f64(f) {
            Ok(Value::Number(n))
        } else {
            Ok(Value::Null)
        }
    } else if let Ok(s) = obj.extract::<String>(py) {
        Ok(Value::String(s))
    } else {
        // 对于其他类型，尝试转换为字符串
        Ok(Value::String(format!("{}", obj.as_ref(py))))
    }
}

// 全局函数
#[pyfunction]
pub fn get(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::new(None, None, None, None)?;
    client.get(url, params, headers, timeout)
}

#[pyfunction]
pub fn post(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::new(None, None, None, None)?;
    client.post(url, content, data, json, params, headers, timeout)
}

#[pyfunction]
pub fn put(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::new(None, None, None, None)?;
    client.put(url, content, data, json, params, headers, timeout)
}

#[pyfunction]
pub fn patch(
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::new(None, None, None, None)?;
    client.patch(url, content, data, json, params, headers, timeout)
}

#[pyfunction]
pub fn delete(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::new(None, None, None, None)?;
    client.delete(url, params, headers, timeout)
}

#[pyfunction]
pub fn head(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::new(None, None, None, None)?;
    client.head(url, params, headers, timeout)
}

#[pyfunction]
pub fn options(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::new(None, None, None, None)?;
    client.options(url, params, headers, timeout)
}

// Python模块定义
#[pymodule]
fn _core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<HttpResponse>()?;
    m.add_class::<HttpClient>()?;
    m.add_class::<AsyncHttpClient>()?;
    
    m.add_function(wrap_pyfunction!(get, m)?)?;
    m.add_function(wrap_pyfunction!(post, m)?)?;
    m.add_function(wrap_pyfunction!(put, m)?)?;
    m.add_function(wrap_pyfunction!(patch, m)?)?;
    m.add_function(wrap_pyfunction!(delete, m)?)?;
    m.add_function(wrap_pyfunction!(head, m)?)?;
    m.add_function(wrap_pyfunction!(options, m)?)?;
    
    m.add("HTTPError", py.get_type::<HTTPError>())?;
    m.add("ConnectTimeout", py.get_type::<ConnectTimeout>())?;
    m.add("ReadTimeout", py.get_type::<ReadTimeout>())?;
    m.add("RequestError", py.get_type::<RequestError>())?;
    
    Ok(())
}
