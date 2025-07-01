use pyo3::prelude::*;
use pyo3::types::{PyDict, PyAnyMethods};
use pyo3::{exceptions::PyException, PyErr, PyResult};
use reqwest::{Client, Method, Url};
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;
use bytes::Bytes;

// 创建自定义异常类型
pyo3::create_exception!(faster_http, HTTPError, PyException);
pyo3::create_exception!(faster_http, ConnectTimeout, HTTPError);
pyo3::create_exception!(faster_http, ReadTimeout, HTTPError);
pyo3::create_exception!(faster_http, RequestError, HTTPError);

// 响应对象
#[pyclass]
pub struct HttpResponse {
    #[pyo3(get)]
    status_code: u16,
    #[pyo3(get)]
    headers: HashMap<String, String>,
    #[pyo3(get)]
    url: String,
    content: Bytes,
    #[pyo3(get)]
    encoding: Option<String>,
    #[pyo3(get)]
    elapsed: f64,
}

#[pymethods]
impl HttpResponse {
    #[getter]
    fn content(&self) -> &[u8] {
        &self.content
    }

    #[getter]
    fn text(&self) -> PyResult<String> {
        match std::str::from_utf8(&self.content) {
            Ok(text) => Ok(text.to_string()),
            Err(_) => {
                // 尝试使用指定的编码或默认使用 UTF-8
                Ok(String::from_utf8_lossy(&self.content).into_owned())
            }
        }
    }

    fn json(&self, py: Python) -> PyResult<PyObject> {
        let text = self.text()?;
        let value: Value = serde_json::from_str(&text)
            .map_err(|e| PyErr::new::<PyException, _>(format!("JSON decode error: {}", e)))?;
        
        // 手动转换 serde_json::Value 到 Python 对象
        json_value_to_python(py, &value)
    }

    fn raise_for_status(&self) -> PyResult<()> {
        if self.status_code >= 400 {
            return Err(PyErr::new::<HTTPError, _>(format!(
                "HTTP {} Error: {} for url: {}",
                self.status_code,
                self.status_code,
                self.url
            )));
        }
        Ok(())
    }

    #[getter]
    fn ok(&self) -> bool {
        self.status_code < 400
    }

    #[getter]
    fn is_redirect(&self) -> bool {
        matches!(self.status_code, 301 | 302 | 303 | 307 | 308)
    }

    #[getter]
    fn is_client_error(&self) -> bool {
        (400..500).contains(&self.status_code)
    }

    #[getter]
    fn is_server_error(&self) -> bool {
        (500..600).contains(&self.status_code)
    }

    fn __repr__(&self) -> String {
        format!("<Response [{}]>", self.status_code)
    }
}

// 辅助函数：将 serde_json::Value 转换为 Python 对象
fn json_value_to_python(py: Python, value: &Value) -> PyResult<PyObject> {
    match value {
        Value::Null => Ok(py.None()),
        Value::Bool(b) => Ok(b.into_py(py)),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.into_py(py))
            } else if let Some(u) = n.as_u64() {
                Ok(u.into_py(py))
            } else if let Some(f) = n.as_f64() {
                Ok(f.into_py(py))
            } else {
                Ok(py.None())
            }
        },
        Value::String(s) => Ok(s.into_py(py)),
        Value::Array(arr) => {
            let py_list = pyo3::types::PyList::empty_bound(py);
            for item in arr {
                py_list.append(json_value_to_python(py, item)?)?;
            }
            Ok(py_list.into())
        },
        Value::Object(obj) => {
            let py_dict = pyo3::types::PyDict::new_bound(py);
            for (key, value) in obj {
                py_dict.set_item(key, json_value_to_python(py, value)?)?;
            }
            Ok(py_dict.into())
        }
    }
}

// 同步客户端
#[pyclass]
pub struct HttpClient {
    client: Arc<Client>,
    base_url: Option<String>,
    timeout: Option<Duration>,
    headers: HashMap<String, String>,
}

impl Default for HttpClient {
    fn default() -> Self {
        Self::new(None, None, None, None)
    }
}

#[pymethods]
impl HttpClient {
    #[new]
    #[pyo3(signature = (base_url=None, timeout=None, headers=None, verify=None))]
    fn new(
        base_url: Option<String>,
        timeout: Option<f64>,
        headers: Option<HashMap<String, String>>,
        verify: Option<bool>,
    ) -> Self {
        let mut client_builder = Client::builder()
            .user_agent("faster-http/0.1.0");

        if let Some(timeout_secs) = timeout {
            client_builder = client_builder.timeout(Duration::from_secs_f64(timeout_secs));
        }

        if let Some(verify_ssl) = verify {
            client_builder = client_builder.danger_accept_invalid_certs(!verify_ssl);
        }

        let client = client_builder.build().unwrap();

        Self {
            client: Arc::new(client),
            base_url,
            timeout: timeout.map(Duration::from_secs_f64),
            headers: headers.unwrap_or_default(),
        }
    }

    #[pyo3(signature = (url, params=None, headers=None, timeout=None))]
    fn get(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.request("GET", url, None, None, params, headers, timeout)
    }

    #[pyo3(signature = (url, data=None, json=None, params=None, headers=None, timeout=None))]
    fn post(
        &self,
        py: Python,
        url: &str,
        data: Option<Bound<PyDict>>,
        json: Option<Bound<PyDict>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        let (body, content_type) = if let Some(json_data) = json {
            (Some(self.dict_to_json_bytes(py, &json_data)?), Some("application/json"))
        } else if let Some(form_data) = data {
            (Some(self.dict_to_form_bytes(py, &form_data)?), Some("application/x-www-form-urlencoded"))
        } else {
            (None, None)
        };
        self.request("POST", url, body, content_type, params, headers, timeout)
    }

    #[pyo3(signature = (url, data=None, json=None, params=None, headers=None, timeout=None))]
    fn put(
        &self,
        py: Python,
        url: &str,
        data: Option<Bound<PyDict>>,
        json: Option<Bound<PyDict>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        let (body, content_type) = if let Some(json_data) = json {
            (Some(self.dict_to_json_bytes(py, &json_data)?), Some("application/json"))
        } else if let Some(form_data) = data {
            (Some(self.dict_to_form_bytes(py, &form_data)?), Some("application/x-www-form-urlencoded"))
        } else {
            (None, None)
        };
        self.request("PUT", url, body, content_type, params, headers, timeout)
    }

    #[pyo3(signature = (url, data=None, json=None, params=None, headers=None, timeout=None))]
    fn patch(
        &self,
        py: Python,
        url: &str,
        data: Option<Bound<PyDict>>,
        json: Option<Bound<PyDict>>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        let (body, content_type) = if let Some(json_data) = json {
            (Some(self.dict_to_json_bytes(py, &json_data)?), Some("application/json"))
        } else if let Some(form_data) = data {
            (Some(self.dict_to_form_bytes(py, &form_data)?), Some("application/x-www-form-urlencoded"))
        } else {
            (None, None)
        };
        self.request("PATCH", url, body, content_type, params, headers, timeout)
    }

    #[pyo3(signature = (url, params=None, headers=None, timeout=None))]
    fn delete(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.request("DELETE", url, None, None, params, headers, timeout)
    }

    #[pyo3(signature = (url, params=None, headers=None, timeout=None))]
    fn head(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.request("HEAD", url, None, None, params, headers, timeout)
    }

    #[pyo3(signature = (url, params=None, headers=None, timeout=None))]
    fn options(
        &self,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        self.request("OPTIONS", url, None, None, params, headers, timeout)
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
}

impl HttpClient {
    fn dict_to_json_bytes(&self, py: Python, dict: &Bound<PyDict>) -> PyResult<Bytes> {
        // 手动转换 PyDict 到 serde_json::Value
        let value = python_dict_to_json_value(py, dict)?;
        let json_str = serde_json::to_string(&value)
            .map_err(|e| PyErr::new::<PyException, _>(format!("JSON encode error: {}", e)))?;
        Ok(Bytes::from(json_str))
    }

    fn dict_to_form_bytes(&self, _py: Python, dict: &Bound<PyDict>) -> PyResult<Bytes> {
        let mut form_data = Vec::new();
        for (key, value) in dict.iter() {
            let key_str: String = key.extract()?;
            let value_str: String = value.extract()?;
            if !form_data.is_empty() {
                form_data.push(b'&');
            }
            form_data.extend_from_slice(
                urlencoding::encode(&key_str).as_bytes()
            );
            form_data.push(b'=');
            form_data.extend_from_slice(
                urlencoding::encode(&value_str).as_bytes()
            );
        }
        Ok(Bytes::from(form_data))
    }

    fn build_url(&self, url: &str, params: Option<HashMap<String, String>>) -> PyResult<Url> {
        let full_url = if let Some(base) = &self.base_url {
            if url.starts_with("http://") || url.starts_with("https://") {
                url.to_string()
            } else {
                format!("{}/{}", base.trim_end_matches('/'), url.trim_start_matches('/'))
            }
        } else {
            url.to_string()
        };

        let mut parsed_url = Url::parse(&full_url)
            .map_err(|e| PyErr::new::<PyException, _>(format!("Invalid URL: {}", e)))?;

        if let Some(params) = params {
            let mut query_pairs = parsed_url.query_pairs_mut();
            for (key, value) in params {
                query_pairs.append_pair(&key, &value);
            }
        }

        Ok(parsed_url)
    }

    fn request(
        &self,
        method: &str,
        url: &str,
        body: Option<Bytes>,
        content_type: Option<&str>,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
    ) -> PyResult<HttpResponse> {
        let rt = tokio::runtime::Runtime::new()
            .map_err(|e| PyErr::new::<PyException, _>(format!("Failed to create runtime: {}", e)))?;

        rt.block_on(async {
            let start_time = std::time::Instant::now();
            
            let url = self.build_url(url, params)?;
            let method = Method::from_bytes(method.as_bytes())
                .map_err(|e| PyErr::new::<PyException, _>(format!("Invalid method: {}", e)))?;

            let mut request_builder = self.client.request(method, url.clone());

            // 添加默认头部
            for (key, value) in &self.headers {
                request_builder = request_builder.header(key, value);
            }

            // 添加请求特定的头部
            if let Some(req_headers) = headers {
                for (key, value) in req_headers {
                    request_builder = request_builder.header(key, value);
                }
            }

            // 添加 Content-Type 头部
            if let Some(ct) = content_type {
                request_builder = request_builder.header("Content-Type", ct);
            }

            // 添加请求体
            if let Some(body_data) = body {
                request_builder = request_builder.body(body_data);
            }

            // 设置超时
            if let Some(timeout_secs) = timeout {
                request_builder = request_builder.timeout(Duration::from_secs_f64(timeout_secs));
            } else if let Some(default_timeout) = self.timeout {
                request_builder = request_builder.timeout(default_timeout);
            }

            let response = request_builder.send().await
                .map_err(|e| {
                    if e.is_timeout() {
                        PyErr::new::<ReadTimeout, _>("Request timeout")
                    } else if e.is_connect() {
                        PyErr::new::<ConnectTimeout, _>("Connection timeout")
                    } else {
                        PyErr::new::<RequestError, _>(format!("Request error: {}", e))
                    }
                })?;

            let status_code = response.status().as_u16();
            let headers = response.headers().iter()
                .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
                .collect();

            let content = response.bytes().await
                .map_err(|e| PyErr::new::<RequestError, _>(format!("Failed to read response: {}", e)))?;

            let elapsed = start_time.elapsed().as_secs_f64();

            Ok(HttpResponse {
                status_code,
                headers,
                url: url.to_string(),
                content,
                encoding: None, // TODO: 检测编码
                elapsed,
            })
        })
    }
}

// 辅助函数：将 Python dict 转换为 serde_json::Value
fn python_dict_to_json_value(py: Python, dict: &Bound<PyDict>) -> PyResult<Value> {
    let mut map = serde_json::Map::new();
    for (key, value) in dict.iter() {
        let key_str: String = key.extract()?;
        let json_value = python_to_json_value(py, &value)?;
        map.insert(key_str, json_value);
    }
    Ok(Value::Object(map))
}

// 辅助函数：将 Python 对象转换为 serde_json::Value
fn python_to_json_value(py: Python, obj: &Bound<PyAny>) -> PyResult<Value> {
    if obj.is_none() {
        Ok(Value::Null)
    } else if let Ok(b) = obj.extract::<bool>() {
        Ok(Value::Bool(b))
    } else if let Ok(i) = obj.extract::<i64>() {
        Ok(Value::Number(serde_json::Number::from(i)))
    } else if let Ok(f) = obj.extract::<f64>() {
        if let Some(n) = serde_json::Number::from_f64(f) {
            Ok(Value::Number(n))
        } else {
            Ok(Value::Null)
        }
    } else if let Ok(s) = obj.extract::<String>() {
        Ok(Value::String(s))
    } else if let Ok(list) = obj.downcast::<pyo3::types::PyList>() {
        let mut vec = Vec::new();
        for item in list.iter() {
            vec.push(python_to_json_value(py, &item)?);
        }
        Ok(Value::Array(vec))
    } else if let Ok(dict) = obj.downcast::<PyDict>() {
        python_dict_to_json_value(py, dict)
    } else {
        // 对于其他类型，尝试转换为字符串
        if let Ok(s) = obj.str() {
            Ok(Value::String(s.to_string()))
        } else {
            Ok(Value::Null)
        }
    }
}

// 异步客户端
#[pyclass]
pub struct AsyncHttpClient {
    client: Arc<Client>,
    base_url: Option<String>,
    timeout: Option<Duration>,
    headers: HashMap<String, String>,
}

impl Default for AsyncHttpClient {
    fn default() -> Self {
        Self::new(None, None, None, None)
    }
}

#[pymethods]
impl AsyncHttpClient {
    #[new]
    #[pyo3(signature = (base_url=None, timeout=None, headers=None, verify=None))]
    fn new(
        base_url: Option<String>,
        timeout: Option<f64>,
        headers: Option<HashMap<String, String>>,
        verify: Option<bool>,
    ) -> Self {
        let mut client_builder = Client::builder()
            .user_agent("faster-http/0.1.0");

        if let Some(timeout_secs) = timeout {
            client_builder = client_builder.timeout(Duration::from_secs_f64(timeout_secs));
        }

        if let Some(verify_ssl) = verify {
            client_builder = client_builder.danger_accept_invalid_certs(!verify_ssl);
        }

        let client = client_builder.build().unwrap();

        Self {
            client: Arc::new(client),
            base_url,
            timeout: timeout.map(Duration::from_secs_f64),
            headers: headers.unwrap_or_default(),
        }
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
}

// 顶级函数
#[pyfunction]
#[pyo3(signature = (url, params=None, headers=None, timeout=None))]
fn get(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::default();
    client.get(url, params, headers, timeout)
}

#[pyfunction]
#[pyo3(signature = (url, data=None, json=None, params=None, headers=None, timeout=None))]
fn post(
    py: Python,
    url: &str,
    data: Option<Bound<PyDict>>,
    json: Option<Bound<PyDict>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::default();
    client.post(py, url, data, json, params, headers, timeout)
}

#[pyfunction]
#[pyo3(signature = (url, data=None, json=None, params=None, headers=None, timeout=None))]
fn put(
    py: Python,
    url: &str,
    data: Option<Bound<PyDict>>,
    json: Option<Bound<PyDict>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::default();
    client.put(py, url, data, json, params, headers, timeout)
}

#[pyfunction]
#[pyo3(signature = (url, data=None, json=None, params=None, headers=None, timeout=None))]
fn patch(
    py: Python,
    url: &str,
    data: Option<Bound<PyDict>>,
    json: Option<Bound<PyDict>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::default();
    client.patch(py, url, data, json, params, headers, timeout)
}

#[pyfunction]
#[pyo3(signature = (url, params=None, headers=None, timeout=None))]
fn delete(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::default();
    client.delete(url, params, headers, timeout)
}

#[pyfunction]
#[pyo3(signature = (url, params=None, headers=None, timeout=None))]
fn head(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::default();
    client.head(url, params, headers, timeout)
}

#[pyfunction]
#[pyo3(signature = (url, params=None, headers=None, timeout=None))]
fn options(
    url: &str,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
) -> PyResult<HttpResponse> {
    let client = HttpClient::default();
    client.options(url, params, headers, timeout)
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // 添加异常类
    m.add("HTTPError", m.py().get_type_bound::<HTTPError>())?;
    m.add("ConnectTimeout", m.py().get_type_bound::<ConnectTimeout>())?;
    m.add("ReadTimeout", m.py().get_type_bound::<ReadTimeout>())?;
    m.add("RequestError", m.py().get_type_bound::<RequestError>())?;

    // 添加类
    m.add_class::<HttpResponse>()?;
    m.add_class::<HttpClient>()?;
    m.add_class::<AsyncHttpClient>()?;

    // 添加顶级函数
    m.add_function(wrap_pyfunction!(get, m)?)?;
    m.add_function(wrap_pyfunction!(post, m)?)?;
    m.add_function(wrap_pyfunction!(put, m)?)?;
    m.add_function(wrap_pyfunction!(patch, m)?)?;
    m.add_function(wrap_pyfunction!(delete, m)?)?;
    m.add_function(wrap_pyfunction!(head, m)?)?;
    m.add_function(wrap_pyfunction!(options, m)?)?;

    Ok(())
}
