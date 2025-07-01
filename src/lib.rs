// 允许 PyO3 宏产生的警告
#![allow(non_local_definitions)]

use pyo3::prelude::*;
use pyo3::exceptions::{PyException, PyValueError};
use reqwest::Client;
use std::collections::HashMap;
use std::sync::{Arc, OnceLock};
use std::time::{Duration, Instant};

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

// Request 对象
#[pyclass]
pub struct HttpRequest {
    method: String,
    url: String,
    headers: HashMap<String, String>,
    content: Option<Bytes>,
}

#[pymethods]
impl HttpRequest {
    #[new]
    pub fn new(
        method: String,
        url: String,
        headers: Option<HashMap<String, String>>,
        content: Option<Vec<u8>>,
    ) -> Self {
        HttpRequest {
            method,
            url,
            headers: headers.unwrap_or_default(),
            content: content.map(Bytes::from),
        }
    }

    #[getter]
    pub fn method(&self) -> &str {
        &self.method
    }

    #[getter]
    pub fn url(&self) -> &str {
        &self.url
    }

    #[getter]
    pub fn headers(&self) -> HashMap<String, String> {
        self.headers.clone()
    }

    #[getter]
    pub fn content(&self) -> Option<&[u8]> {
        self.content.as_ref().map(|b| b.as_ref())
    }

    fn __repr__(&self) -> String {
        format!("<Request('{}', '{}')>", self.method, self.url)
    }
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
    encoding: Option<String>, // 新增：编码属性
    history: Vec<PyObject>, // 新增：重定向历史
    request: Option<PyObject>, // 新增：原始请求对象
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
    pub fn text(&self) -> String {
        // 根据编码解码，默认使用 UTF-8
        let encoding = self.encoding.as_deref().unwrap_or("utf-8");
        match encoding.to_lowercase().as_str() {
            "utf-8" | "utf8" => String::from_utf8_lossy(&self.body).to_string(),
            _ => {
                // 对于其他编码，暂时使用 UTF-8，未来可以添加更多编码支持
                String::from_utf8_lossy(&self.body).to_string()
            }
        }
    }

    #[getter]
    pub fn encoding(&self) -> Option<String> {
        self.encoding.clone()
    }

    #[setter]
    pub fn set_encoding(&mut self, encoding: Option<String>) {
        self.encoding = encoding;
    }

    #[getter]
    pub fn charset_encoding(&self) -> Option<String> {
        // 从 Content-Type 头中提取字符集
        if let Some(content_type) = self.headers.get("content-type").or_else(|| self.headers.get("Content-Type")) {
            if let Some(charset_pos) = content_type.find("charset=") {
                let charset = &content_type[charset_pos + 8..];
                let charset = charset.split(';').next().unwrap_or(charset).trim();
                return Some(charset.to_string());
            }
        }
        None
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

    #[getter]
    pub fn history(&self) -> Vec<PyObject> {
        self.history.clone()
    }

    #[getter]
    pub fn request(&self) -> Option<PyObject> {
        self.request.clone()
    }

    // 新增：响应迭代器方法
    pub fn iter_bytes(&self, chunk_size: Option<usize>) -> PyResult<Vec<Vec<u8>>> {
        let chunk_size = chunk_size.unwrap_or(8192);
        let mut chunks = Vec::new();
        let mut pos = 0;
        
        while pos < self.body.len() {
            let end = std::cmp::min(pos + chunk_size, self.body.len());
            chunks.push(self.body[pos..end].to_vec());
            pos = end;
        }
        
        Ok(chunks)
    }

    pub fn iter_text(&self, chunk_size: Option<usize>) -> PyResult<Vec<String>> {
        let chunk_size = chunk_size.unwrap_or(8192);
        let mut text_chunks = Vec::new();
        let text = self.text();
        let mut pos = 0;
        
        while pos < text.len() {
            let end = std::cmp::min(pos + chunk_size, text.len());
            text_chunks.push(text[pos..end].to_string());
            pos = end;
        }
        
        Ok(text_chunks)
    }

    pub fn iter_lines(&self) -> PyResult<Vec<String>> {
        let text = self.text();
        let lines: Vec<String> = text.lines().map(|line| line.to_string()).collect();
        Ok(lines)
    }

    pub fn iter_raw(&self, chunk_size: Option<usize>) -> PyResult<Vec<Vec<u8>>> {
        // 与 iter_bytes 相同，但表示未解码的原始数据
        self.iter_bytes(chunk_size)
    }

    pub fn json(&self, py: Python) -> PyResult<PyObject> {
        let json_str = self.text();
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

    // 新增：支持流式传输的标记方法
    pub fn is_streamable(&self) -> bool {
        // 检查响应是否可以进行流式传输
        true
    }

    // 新增：为 SSE 等流式传输添加辅助方法
    pub fn iter_sse_lines(&self) -> PyResult<Vec<String>> {
        let text = self.text();
        let mut sse_events = Vec::new();
        
        for line in text.lines() {
            if line.starts_with("data:") {
                sse_events.push(line.to_string());
            } else if line.starts_with("event:") || line.starts_with("id:") || line.starts_with("retry:") {
                sse_events.push(line.to_string());
            }
        }
        
        Ok(sse_events)
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
    #[allow(dead_code)]
    proxy: Option<String>,
    default_cookies: HashMap<String, String>,
    #[allow(dead_code)]
    http2: bool, // 新增：HTTP/2 支持
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
        http2: Option<bool>, // 新增：HTTP/2 支持
    ) -> PyResult<Self> {
        let verify = verify.unwrap_or(true);
        let follow_redirects = follow_redirects.unwrap_or(true);
        let http2 = http2.unwrap_or(false);
        
        let mut builder = Client::builder()
            .danger_accept_invalid_certs(!verify)
            .redirect(if follow_redirects { 
                reqwest::redirect::Policy::limited(10) 
            } else { 
                reqwest::redirect::Policy::none() 
            });

        // 添加 HTTP/2 支持
        if http2 {
            builder = builder.http2_prior_knowledge();
        }

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
            http2,
        })
    }

    // 新增：构建请求对象
    pub fn build_request(
        &self,
        method: &str,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        content: Option<Vec<u8>>,
    ) -> PyResult<HttpRequest> {
        // 构建URL
        let full_url = if let Some(base) = &self.base_url {
            if url.starts_with("http://") || url.starts_with("https://") {
                url.to_string()
            } else {
                format!("{}/{}", base.trim_end_matches('/'), url.trim_start_matches('/'))
            }
        } else {
            url.to_string()
        };

        // 添加查询参数
        let final_url = if let Some(params) = params {
            let mut url_with_params = reqwest::Url::parse(&full_url)
                .map_err(|e| RequestError::new_err(format!("Invalid URL: {}", e)))?;
            
            for (key, value) in params {
                url_with_params.query_pairs_mut().append_pair(&key, &value);
            }
            url_with_params.to_string()
        } else {
            full_url
        };

        // 合并headers
        let mut final_headers = self.default_headers.clone();
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

    // 新增：发送预构建的请求
    pub fn send(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        let rt = get_runtime();
        
        let client = &self.client;
        let method = &request.method;
        let url = &request.url;
        let headers = Some(request.headers.clone());
        let content = request.content.as_ref().map(|b| b.to_vec());
        let default_timeout = self.default_timeout;
        
        rt.block_on(async {
            let start_time = Instant::now();

            // 构建请求
            let method = method.parse::<reqwest::Method>()
                .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;
            
            let mut req = client.request(method, url);

            // 添加headers
            if let Some(headers) = headers {
                for (key, value) in headers {
                    req = req.header(key, value);
                }
            }

            // 添加body
            if let Some(content) = content {
                req = req.body(content);
            }

            // 设置默认超时
            if let Some(timeout) = default_timeout {
                req = req.timeout(timeout);
            }

            // 发送请求
            let response = req.send().await
                .map_err(|e| {
                    if e.is_timeout() {
                        ReadTimeout::new_err(format!("Request timeout: {}", e))
                    } else if e.is_connect() {
                        ConnectTimeout::new_err(format!("Connection timeout: {}", e))
                    } else {
                        RequestError::new_err(format!("Request failed: {}", e))
                    }
                })?;

            // 处理响应
            let status_code = response.status().as_u16();
            let url = response.url().to_string();
            
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

            // 检测编码
            let encoding = detect_encoding(&headers);

            Ok(HttpResponse {
                status_code,
                headers: headers.clone(),
                body,
                url,
                elapsed,
                is_redirect_status,
                http_version,
                cookies: parse_cookies_from_headers(&headers),
                encoding,
                history: Vec::new(),
                request: None,
            })
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

// 编码检测函数
fn detect_encoding(headers: &HashMap<String, String>) -> Option<String> {
    if let Some(content_type) = headers.get("content-type").or_else(|| headers.get("Content-Type")) {
        if let Some(charset_pos) = content_type.find("charset=") {
            let charset = &content_type[charset_pos + 8..];
            let charset = charset.split(';').next().unwrap_or(charset).trim();
            return Some(charset.to_string());
        }
    }
    
    // 默认返回 UTF-8
    Some("utf-8".to_string())
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
    follow_redirects: bool,
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
    
    // 检测编码
    let encoding = detect_encoding(&headers);

    Ok(HttpResponse {
        status_code,
        headers: headers.clone(),
        body,
        url,
        elapsed,
        is_redirect_status,
        http_version,
        cookies: parse_cookies_from_headers(&headers),
        encoding,
        history: Vec::new(),
        request: None,
    })
}

// 辅助函数：解析 cookies 从响应头
fn parse_cookies_from_headers(headers: &HashMap<String, String>) -> HashMap<String, String> {
    let mut cookies = HashMap::new();
    
    for (key, value) in headers {
        if key.to_lowercase() == "set-cookie" {
            // 简单的 cookie 解析，实际应用中可能需要更复杂的解析
            if let Some(eq_pos) = value.find('=') {
                let name = value[..eq_pos].trim();
                let rest = &value[eq_pos + 1..];
                let cookie_value = rest.split(';').next().unwrap_or(rest).trim();
                cookies.insert(name.to_string(), cookie_value.to_string());
            }
        }
    }
    
    cookies
}

// 辅助函数：构建 multipart form
fn build_multipart_form(files_data: HashMap<String, PyObject>) -> PyResult<reqwest::multipart::Form> {
    Python::with_gil(|py| {
        let mut form = reqwest::multipart::Form::new();
        
        for (field_name, file_obj) in files_data {
            // 处理不同的文件输入格式
            if let Ok(bytes_data) = file_obj.extract::<Vec<u8>>(py) {
                // 字节数据
                let part = reqwest::multipart::Part::bytes(bytes_data)
                    .file_name(format!("{}.bin", field_name))
                    .mime_str("application/octet-stream")
                    .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?;
                form = form.part(field_name, part);
            } else if let Ok(string_data) = file_obj.extract::<String>(py) {
                // 字符串数据
                let part = reqwest::multipart::Part::text(string_data)
                    .file_name(format!("{}.txt", field_name))
                    .mime_str("text/plain")
                    .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?;
                form = form.part(field_name, part);
            } else if let Ok(tuple_data) = file_obj.extract::<(Option<String>, PyObject)>(py) {
                // (filename, content) 格式
                let (filename, content_obj) = tuple_data;
                
                if let Ok(bytes_content) = content_obj.extract::<Vec<u8>>(py) {
                    let mut part = reqwest::multipart::Part::bytes(bytes_content);
                    
                    if let Some(fname) = filename {
                        part = part.file_name(fname.clone());
                        
                        // 根据文件扩展名推测MIME类型
                        if let Some(mime_type) = guess_mime_type(&fname) {
                            part = part.mime_str(&mime_type)
                                .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?;
                        }
                    }
                    
                    form = form.part(field_name, part);
                } else if let Ok(string_content) = content_obj.extract::<String>(py) {
                    let mut part = reqwest::multipart::Part::text(string_content);
                    
                    if let Some(fname) = filename {
                        part = part.file_name(fname);
                    }
                    
                    form = form.part(field_name, part);
                }
            } else if let Ok(triple_data) = file_obj.extract::<(Option<String>, PyObject, String)>(py) {
                // (filename, content, content_type) 格式
                let (filename, content_obj, content_type) = triple_data;
                
                if let Ok(bytes_content) = content_obj.extract::<Vec<u8>>(py) {
                    let mut part = reqwest::multipart::Part::bytes(bytes_content)
                        .mime_str(&content_type)
                        .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?;
                    
                    if let Some(fname) = filename {
                        part = part.file_name(fname);
                    }
                    
                    form = form.part(field_name, part);
                } else if let Ok(string_content) = content_obj.extract::<String>(py) {
                    let mut part = reqwest::multipart::Part::text(string_content)
                        .mime_str(&content_type)
                        .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?;
                    
                    if let Some(fname) = filename {
                        part = part.file_name(fname);
                    }
                    
                    form = form.part(field_name, part);
                }
            } else {
                // 尝试调用Python对象的方法获取字节数据
                // 这可能是一个FileUpload对象或其他类型
                if let Ok(to_bytes_method) = file_obj.getattr(py, "to_bytes") {
                    if let Ok(bytes_data) = to_bytes_method.call0(py)?.extract::<Vec<u8>>(py) {
                        // 尝试获取文件名和内容类型
                        let filename = file_obj.getattr(py, "filename")
                            .ok()
                            .and_then(|f| f.extract::<Option<String>>(py).ok())
                            .flatten();
                            
                        let content_type = file_obj.getattr(py, "get_content_type")
                            .ok()
                            .and_then(|method| method.call0(py).ok())
                            .and_then(|ct| ct.extract::<String>(py).ok());
                        
                        let mut part = reqwest::multipart::Part::bytes(bytes_data);
                        
                        if let Some(fname) = filename {
                            part = part.file_name(fname);
                        }
                        
                        if let Some(ct) = content_type {
                            part = part.mime_str(&ct)
                                .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?;
                        }
                        
                        form = form.part(field_name, part);
                        continue;
                    }
                }
                
                return Err(RequestError::new_err(format!(
                    "Unsupported file format for field '{}'. Expected bytes, string, tuple, or FileUpload object.",
                    field_name
                )));
            }
        }
        
        Ok(form)
    })
}

// 新增：MIME类型推测函数
fn guess_mime_type(filename: &str) -> Option<String> {
    let extension = std::path::Path::new(filename)
        .extension()?
        .to_str()?
        .to_lowercase();
    
    match extension.as_str() {
        "txt" => Some("text/plain".to_string()),
        "html" | "htm" => Some("text/html".to_string()),
        "css" => Some("text/css".to_string()),
        "js" => Some("application/javascript".to_string()),
        "json" => Some("application/json".to_string()),
        "xml" => Some("application/xml".to_string()),
        "pdf" => Some("application/pdf".to_string()),
        "png" => Some("image/png".to_string()),
        "jpg" | "jpeg" => Some("image/jpeg".to_string()),
        "gif" => Some("image/gif".to_string()),
        "svg" => Some("image/svg+xml".to_string()),
        "mp4" => Some("video/mp4".to_string()),
        "mp3" => Some("audio/mpeg".to_string()),
        "zip" => Some("application/zip".to_string()),
        "csv" => Some("text/csv".to_string()),
        "xlsx" => Some("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet".to_string()),
        "docx" => Some("application/vnd.openxmlformats-officedocument.wordprocessingml.document".to_string()),
        _ => Some("application/octet-stream".to_string()),
    }
}

// 异步 HTTP 客户端
#[pyclass]
pub struct AsyncHttpClient {
    client: Client,
    base_url: Option<String>,
    default_timeout: Option<Duration>,
    default_headers: HashMap<String, String>,
    follow_redirects: bool,
    auth: Option<AuthType>,
    #[allow(dead_code)]
    proxy: Option<String>,
    default_cookies: HashMap<String, String>,
    #[allow(dead_code)]
    http2: bool, // 新增：HTTP/2 支持
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
        http2: Option<bool>, // 新增：HTTP/2 支持
    ) -> PyResult<Self> {
        let verify = verify.unwrap_or(true);
        let follow_redirects = follow_redirects.unwrap_or(true);
        let http2 = http2.unwrap_or(false);
        
        let mut builder = Client::builder()
            .danger_accept_invalid_certs(!verify)
            .redirect(if follow_redirects { 
                reqwest::redirect::Policy::limited(10) 
            } else { 
                reqwest::redirect::Policy::none() 
            });

        // 添加 HTTP/2 支持
        if http2 {
            builder = builder.http2_prior_knowledge();
        }

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
            http2,
        })
    }

    // 新增：构建请求对象
    pub fn build_request(
        &self,
        method: &str,
        url: &str,
        params: Option<HashMap<String, String>>,
        headers: Option<HashMap<String, String>>,
        content: Option<Vec<u8>>,
    ) -> PyResult<HttpRequest> {
        // 构建URL
        let full_url = if let Some(base) = &self.base_url {
            if url.starts_with("http://") || url.starts_with("https://") {
                url.to_string()
            } else {
                format!("{}/{}", base.trim_end_matches('/'), url.trim_start_matches('/'))
            }
        } else {
            url.to_string()
        };

        // 添加查询参数
        let final_url = if let Some(params) = params {
            let mut url_with_params = reqwest::Url::parse(&full_url)
                .map_err(|e| RequestError::new_err(format!("Invalid URL: {}", e)))?;
            
            for (key, value) in params {
                url_with_params.query_pairs_mut().append_pair(&key, &value);
            }
            url_with_params.to_string()
        } else {
            full_url
        };

        // 合并headers
        let mut final_headers = self.default_headers.clone();
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

    // 新增：发送预构建的请求 (异步)
    pub fn send<'py>(&self, py: Python<'py>, request: &HttpRequest) -> PyResult<&'py PyAny> {
        let request_clone = HttpRequest::new(
            request.method.clone(),
            request.url.clone(),
            Some(request.headers.clone()),
            request.content.as_ref().map(|b| b.to_vec()),
        );
        
        let client = self.client.clone();
        let default_timeout = self.default_timeout;
        
        future_into_py(py, async move {
            let start_time = Instant::now();

            // 构建请求
            let method = request_clone.method.parse::<reqwest::Method>()
                .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;
            
            let mut req = client.request(method, &request_clone.url);

            // 添加headers
            for (key, value) in &request_clone.headers {
                req = req.header(key, value);
            }

            // 添加body
            if let Some(content) = &request_clone.content {
                req = req.body(content.clone());
            }

            // 设置默认超时
            if let Some(timeout) = default_timeout {
                req = req.timeout(timeout);
            }

            // 发送请求
            let response = req.send().await
                .map_err(|e| {
                    if e.is_timeout() {
                        ReadTimeout::new_err(format!("Request timeout: {}", e))
                    } else if e.is_connect() {
                        ConnectTimeout::new_err(format!("Connection timeout: {}", e))
                    } else {
                        RequestError::new_err(format!("Request failed: {}", e))
                    }
                })?;

            // 处理响应
            let status_code = response.status().as_u16();
            let url = response.url().to_string();
            
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

            // 检测编码
            let encoding = detect_encoding(&headers);

            Ok(HttpResponse {
                status_code,
                headers: headers.clone(),
                body,
                url,
                elapsed,
                is_redirect_status,
                http_version,
                cookies: parse_cookies_from_headers(&headers),
                encoding,
                history: Vec::new(),
                request: None,
            })
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

        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let default_headers = self.default_headers.clone();
        let default_timeout = self.default_timeout;
        let method = method.to_string(); // 克隆方法字符串以避免生命周期问题
        
        let auth_option = auth.or_else(|| {
            match &self.auth {
                Some(AuthType::Basic { username, password }) => Some((username.clone(), password.clone())),
                _ => None,
            }
        });
        
        let follow_redirects = follow_redirects.unwrap_or(self.follow_redirects);
        
        future_into_py(py, async move {
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
                auth_option,
                follow_redirects,
                merged_cookies
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
    m.add_class::<HttpRequest>()?;
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
