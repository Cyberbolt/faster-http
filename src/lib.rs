use pyo3::prelude::*;
use pyo3::exceptions::{PyException, PyValueError};
use reqwest::Client;
use std::collections::HashMap;
use std::sync::{Arc, OnceLock};
use std::time::{Duration, Instant};
use tokio::runtime::Runtime;
use bytes::Bytes;
use serde_json::Value;
use pyo3_asyncio::tokio::future_into_py;

// 创建自定义异常类型
pyo3::create_exception!(faster_http, HTTPError, PyException);
pyo3::create_exception!(faster_http, ConnectTimeout, HTTPError);
pyo3::create_exception!(faster_http, ReadTimeout, HTTPError);
pyo3::create_exception!(faster_http, RequestError, HTTPError);

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
    is_redirect_status: bool,
    http_version: String,
    cookies: HashMap<String, String>,
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
        (200..300).contains(&self.status_code)
    }

    #[getter]
    pub fn content(&self) -> &[u8] {
        &self.body
    }

    #[getter]
    pub fn text(&self) -> PyResult<String> {
        String::from_utf8(self.body.to_vec())
            .map_err(|e| PyValueError::new_err(format!("Failed to decode response as UTF-8: {}", e)))
    }

    #[getter]
    pub fn elapsed(&self) -> f64 {
        self.elapsed
    }

    #[getter]
    pub fn is_client_error(&self) -> bool {
        (400..500).contains(&self.status_code)
    }

    #[getter]
    pub fn is_server_error(&self) -> bool {
        self.status_code >= 500
    }

    #[getter]
    pub fn is_redirect(&self) -> bool {
        self.is_redirect_status
    }

    #[getter]
    pub fn http_version(&self) -> &str {
        &self.http_version
    }

    #[getter]
    pub fn cookies(&self) -> HashMap<String, String> {
        self.cookies.clone()
    }

    pub fn json(&self, py: Python) -> PyResult<PyObject> {
        let json_str = self.text()?;
        let json_value: Value = serde_json::from_str(&json_str)
            .map_err(|e| PyValueError::new_err(format!("Failed to parse JSON: {}", e)))?;
        pythonize::pythonize(py, &json_value)
            .map_err(|e| PyValueError::new_err(format!("Failed to convert JSON to Python: {}", e)))
    }

    pub fn raise_for_status(&self) -> PyResult<()> {
        if self.status_code >= 400 {
            return Err(HTTPError::new_err(format!(
                "HTTP {} error for url: {}",
                self.status_code, self.url
            )));
        }
        Ok(())
    }

    fn __repr__(&self) -> String {
        format!("<Response [{}]>", self.status_code)
    }
}

// 认证类型枚举
#[derive(Clone)]
pub enum AuthType {
    Basic { username: String, password: String },
    Bearer { token: String },
}

// 同步HTTP客户端
#[pyclass]
pub struct HttpClient {
    client: Client,
    base_url: Option<String>,
    default_timeout: Option<Duration>,
    default_headers: HashMap<String, String>,
    follow_redirects: bool,
    auth: Option<AuthType>,
    proxy: Option<String>,
    default_cookies: HashMap<String, String>,
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
    ) -> PyResult<Self> {
        let verify = verify.unwrap_or(true);
        let follow_redirects = follow_redirects.unwrap_or(true);
        
        let mut builder = Client::builder()
            .danger_accept_invalid_certs(!verify)
            .redirect(if follow_redirects { 
                reqwest::redirect::Policy::limited(10) 
            } else { 
                reqwest::redirect::Policy::none() 
            });

        // 添加代理支持
        if let Some(proxy_url) = &proxy {
            let proxy = reqwest::Proxy::all(proxy_url)
                .map_err(|e| RequestError::new_err(format!("Invalid proxy URL: {}", e)))?;
            builder = builder.proxy(proxy);
        }

        let client = builder.build()
            .map_err(|e| RequestError::new_err(format!("Failed to create client: {}", e)))?;

        let auth_type = auth.map(|(username, password)| AuthType::Basic { username, password });

        Ok(HttpClient {
            client,
            base_url,
            default_timeout: timeout.map(Duration::from_secs_f64),
            default_headers: headers.unwrap_or_default(),
            follow_redirects,
            auth: auth_type,
            proxy,
            default_cookies: cookies.unwrap_or_default(),
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
        let rt = get_runtime();
        
        // 合并 cookies
        let merged_cookies = match cookies {
            Some(request_cookies) => {
                let mut merged = self.default_cookies.clone();
                merged.extend(request_cookies);
                Some(merged)
            }
            None if !self.default_cookies.is_empty() => Some(self.default_cookies.clone()),
            _ => None,
        };

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
            &self.base_url, 
            &self.default_headers, 
            self.default_timeout, 
            auth.or_else(|| {
                match &self.auth {
                    Some(AuthType::Basic { username, password }) => Some((username.clone(), password.clone())),
                    _ => None,
                }
            }), 
            follow_redirects.unwrap_or(self.follow_redirects),
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

impl HttpClient {
    async fn _async_request(
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
    ) -> PyResult<HttpResponse> {
        build_and_send_request(
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
            &self.base_url,
            &self.default_headers,
            self.default_timeout,
            auth.or_else(|| {
                // 如果请求没有提供认证，使用客户端默认认证
                match &self.auth {
                    Some(AuthType::Basic { username, password }) => Some((username.clone(), password.clone())),
                    _ => None,
                }
            }),
            follow_redirects.unwrap_or(self.follow_redirects),
            Some(self.default_cookies.clone()),
        ).await
    }
}

// 核心请求构建和发送函数
async fn build_and_send_request(
    client: &Client,
    method: &str,
    url: &str,
    content: Option<Vec<u8>>,
    data: Option<HashMap<String, PyObject>>,
    json: Option<HashMap<String, PyObject>>,
    files: Option<HashMap<String, PyObject>>,
    params: Option<HashMap<String, String>>,
    headers: Option<HashMap<String, String>>,
    timeout: Option<f64>,
    base_url: &Option<String>,
    default_headers: &HashMap<String, String>,
    default_timeout: Option<Duration>,
    auth: Option<(String, String)>,
    follow_redirects: bool,  // 移除下划线，正确处理重定向参数
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    let start_time = Instant::now();

    // 根据 follow_redirects 选择合适的客户端
    let actual_client;
    let client_to_use = if !follow_redirects {
        // 如果不跟随重定向，创建临时客户端
        actual_client = Client::builder()
            .redirect(reqwest::redirect::Policy::none())
            .build()
            .map_err(|e| RequestError::new_err(format!("Failed to create no-redirect client: {}", e)))?;
        &actual_client
    } else {
        // 使用默认客户端（跟随重定向）
        client
    };

    // 构建URL
    let full_url = if let Some(base) = base_url {
        if url.starts_with("http://") || url.starts_with("https://") {
            url.to_string()
        } else {
            format!("{}/{}", base.trim_end_matches('/'), url.trim_start_matches('/'))
        }
    } else {
        url.to_string()
    };

    // 创建请求构建器
    let method = method.parse::<reqwest::Method>()
        .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;
    
    let mut request = client_to_use.request(method, &full_url);

    // 添加查询参数
    if let Some(params) = params {
        request = request.query(&params);
    }

    // 合并header
    for (key, value) in default_headers {
        request = request.header(key, value);
    }
    if let Some(headers) = headers {
        for (key, value) in headers {
            request = request.header(key, value);
        }
    }

    // 添加 cookies 到请求头
    if let Some(cookie_map) = cookies {
        if !cookie_map.is_empty() {
            let cookie_string = cookie_map
                .iter()
                .map(|(k, v)| format!("{}={}", k, v))
                .collect::<Vec<_>>()
                .join("; ");
            request = request.header("Cookie", cookie_string);
        }
    }

    // 设置认证
    if let Some((username, password)) = auth {
        request = request.basic_auth(username, Some(password));
    }

    // 设置超时
    let timeout_duration = timeout
        .map(Duration::from_secs_f64)
        .or(default_timeout)
        .unwrap_or(Duration::from_secs(30));
    request = request.timeout(timeout_duration);

    // 设置body - 优先级：content > files > json > data
    if let Some(content_bytes) = content {
        request = request.body(content_bytes);
    } else if let Some(files_data) = files {
        // 处理文件上传 (multipart/form-data)
        let form = build_multipart_form(files_data)?;
        request = request.multipart(form);
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

    // 发送请求
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

    // 获取响应信息
    let status_code = response.status().as_u16();
    let url = response.url().to_string();
    
    // 获取 HTTP 版本
    let http_version = match response.version() {
        reqwest::Version::HTTP_09 => "HTTP/0.9".to_string(),
        reqwest::Version::HTTP_10 => "HTTP/1.0".to_string(),
        reqwest::Version::HTTP_11 => "HTTP/1.1".to_string(),
        reqwest::Version::HTTP_2 => "HTTP/2".to_string(),
        reqwest::Version::HTTP_3 => "HTTP/3".to_string(),
        _ => "Unknown".to_string(),
    };
    
    let headers: HashMap<String, String> = response
        .headers()
        .iter()
        .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
        .collect();

    let body = response.bytes().await
        .map_err(|e| RequestError::new_err(format!("Failed to read response body: {}", e)))?;

    let elapsed = start_time.elapsed().as_secs_f64();
    let is_redirect_status = matches!(status_code, 301 | 302 | 303 | 307 | 308);

    Ok(HttpResponse {
        status_code,
        headers: headers.clone(),
        body,
        url,
        elapsed,
        is_redirect_status,
        http_version,
        cookies: parse_cookies_from_headers(&headers),
    })
}

// 辅助函数：解析 cookies 从响应头
fn parse_cookies_from_headers(headers: &HashMap<String, String>) -> HashMap<String, String> {
    let mut cookies = HashMap::new();
    
    // 从 Set-Cookie 头中提取 cookies
    for (key, value) in headers {
        if key.to_lowercase() == "set-cookie" {
            // 简单的 cookie 解析，只提取 name=value 部分
            if let Some(cookie_pair) = value.split(';').next() {
                if let Some((name, val)) = cookie_pair.split_once('=') {
                    cookies.insert(name.trim().to_string(), val.trim().to_string());
                }
            }
        }
    }
    
    cookies
}

// 构建 multipart form 用于文件上传
fn build_multipart_form(files_data: HashMap<String, PyObject>) -> PyResult<reqwest::multipart::Form> {
    let mut form = reqwest::multipart::Form::new();
    
    Python::with_gil(|py| {
        for (key, value) in files_data {
            // 简单的文件处理 - 假设值是字节串或文件路径
            if let Ok(bytes_data) = value.extract::<Vec<u8>>(py) {
                let part = reqwest::multipart::Part::bytes(bytes_data)
                    .file_name("uploaded_file");
                form = form.part(key, part);
            } else if let Ok(file_path) = value.extract::<String>(py) {
                // 如果是文件路径，我们只能传递路径字符串，实际文件读取需要在Python端处理
                let part = reqwest::multipart::Part::text(file_path);
                form = form.part(key, part);
            } else {
                // 其他类型作为文本处理
                let text_value = format!("{}", value.as_ref(py));
                let part = reqwest::multipart::Part::text(text_value);
                form = form.part(key, part);
            }
        }
        Ok(form)
    })
}

// 异步HTTP客户端
#[pyclass]
pub struct AsyncHttpClient {
    client: Client,
    base_url: Option<String>,
    default_timeout: Option<Duration>,
    default_headers: HashMap<String, String>,
    follow_redirects: bool,
    auth: Option<AuthType>,
    proxy: Option<String>,
    default_cookies: HashMap<String, String>,
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
    ) -> PyResult<Self> {
        let verify = verify.unwrap_or(true);
        let follow_redirects = follow_redirects.unwrap_or(true);
        
        let mut builder = Client::builder()
            .danger_accept_invalid_certs(!verify)
            .redirect(if follow_redirects { 
                reqwest::redirect::Policy::limited(10) 
            } else { 
                reqwest::redirect::Policy::none() 
            });

        // 添加代理支持
        if let Some(proxy_url) = &proxy {
            let proxy = reqwest::Proxy::all(proxy_url)
                .map_err(|e| RequestError::new_err(format!("Invalid proxy URL: {}", e)))?;
            builder = builder.proxy(proxy);
        }

        let client = builder.build()
            .map_err(|e| RequestError::new_err(format!("Failed to create client: {}", e)))?;

        let auth_type = auth.map(|(username, password)| AuthType::Basic { username, password });

        Ok(AsyncHttpClient {
            client,
            base_url,
            default_timeout: timeout.map(Duration::from_secs_f64),
            default_headers: headers.unwrap_or_default(),
            follow_redirects,
            auth: auth_type,
            proxy,
            default_cookies: cookies.unwrap_or_default(),
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

    // 通用异步请求方法
    fn _async_request<'py>(
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
        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let default_timeout = self.default_timeout;
        let default_headers = self.default_headers.clone();
        let client_auth = self.auth.clone();
        let client_follow_redirects = self.follow_redirects;
        let default_cookies = self.default_cookies.clone();
        let method = method.to_string(); // 克隆方法字符串以避免生命周期问题

        future_into_py(py, async move {
            // 合并 cookies
            let merged_cookies = match cookies {
                Some(request_cookies) => {
                    let mut merged = default_cookies;
                    merged.extend(request_cookies);
                    Some(merged)
                }
                None if !default_cookies.is_empty() => Some(default_cookies),
                _ => None,
            };

            build_and_send_request(
                &client,
                &method,
                &url,
                content,
                data,
                json,
                files,
                params,
                headers,
                timeout,
                &base_url,
                &default_headers,
                default_timeout,
                auth.or_else(|| {
                    match &client_auth {
                        Some(AuthType::Basic { username, password }) => Some((username.clone(), password.clone())),
                        _ => None,
                    }
                }),
                follow_redirects.unwrap_or(client_follow_redirects),
                merged_cookies,
            ).await
        })
    }

    pub fn get<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self._async_request(py, "GET", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn post<'py>(
        &self,
        py: Python<'py>,
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
        self._async_request(py, "POST", url, content, data, json, files, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn put<'py>(
        &self,
        py: Python<'py>,
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
        self._async_request(py, "PUT", url, content, data, json, files, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn patch<'py>(
        &self,
        py: Python<'py>,
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
        self._async_request(py, "PATCH", url, content, data, json, files, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn delete<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self._async_request(py, "DELETE", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn head<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self._async_request(py, "HEAD", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }

    pub fn options<'py>(
        &self,
        py: Python<'py>,
        url: String,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        timeout: Option<f64>,
        auth: Option<(String, String)>,
        follow_redirects: Option<bool>,
        cookies: Option<HashMap<String, String>>,
    ) -> PyResult<&'py PyAny> {
        self._async_request(py, "OPTIONS", url, None, None, None, None, params, headers, timeout, auth, follow_redirects, cookies)
    }
}

// 优化的全局函数，使用全局客户端实例

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
    auth: Option<(String, String)>,
    follow_redirects: Option<bool>,
    cookies: Option<HashMap<String, String>>,
) -> PyResult<HttpResponse> {
    let rt = get_runtime();
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
    let rt = get_runtime();
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
    let rt = get_runtime();
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
    let rt = get_runtime();
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
    let rt = get_runtime();
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
    let rt = get_runtime();
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
    let rt = get_runtime();
    let client = get_global_client();
    rt.block_on(build_and_send_request(
        &client, "OPTIONS", url, None, None, None, None, params, headers, timeout,
        &None, &HashMap::new(), None, auth, follow_redirects.unwrap_or(true), cookies
    ))
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
