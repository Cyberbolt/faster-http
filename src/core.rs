use pyo3::prelude::*;
use reqwest::Client;
use std::collections::HashMap;
use std::time::{Duration, Instant};
use crate::request::HttpRequest;
use crate::response::{HttpResponse, parse_cookies_from_headers, detect_encoding};
use crate::streaming::StreamingHttpResponse;
use crate::config::ClientConfig;
use crate::error::{map_reqwest_error, RequestError, ReadTimeout, ConnectTimeout};
use crate::utils::{build_multipart_form, python_dict_to_json_value, python_dict_to_form_string};


// 发送请求的核心函数（基于已构建的请求）
pub async fn send_request(client: &Client, request: &HttpRequest, config: &ClientConfig) -> PyResult<HttpResponse> {
    let start_time = Instant::now();

    let method = request.method().parse::<reqwest::Method>()
        .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;
    
    let mut req = client.request(method, request.url());

    for (key, value) in &request.headers() {
        req = req.header(key, value);
    }

    if let Some(content) = request.content() {
        req = req.body(content.to_vec());
    }

    if let Some(timeout) = config.default_timeout {
        req = req.timeout(timeout);
    }

    let response = req.send().await.map_err(map_reqwest_error)?;
    process_response(response, start_time).await
}

// 优化版：直接从数据发送请求，避免 HttpRequest 中间对象
pub async fn send_request_direct(
    client: &Client, 
    method: &str,
    url: &str,
    headers: &HashMap<String, String>,
    content: Option<&[u8]>,
    config: &ClientConfig
) -> PyResult<HttpResponse> {
    let start_time = Instant::now();

    let method = method.parse::<reqwest::Method>()
        .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;
    
    let mut req = client.request(method, url);

    for (key, value) in headers {
        req = req.header(key, value);
    }

    if let Some(content_bytes) = content {
        req = req.body(content_bytes.to_vec());
    }

    if let Some(timeout) = config.default_timeout {
        req = req.timeout(timeout);
    }

    let response = req.send().await.map_err(map_reqwest_error)?;
    process_response(response, start_time).await
}

// 处理响应的核心函数 - 简化版本，与 httpx 对齐
pub async fn process_response(response: reqwest::Response, start_time: Instant) -> PyResult<HttpResponse> {
    let status_code = response.status().as_u16();
    let url = response.url().to_string();
    
    let http_version = match response.version() {
        reqwest::Version::HTTP_09 => "HTTP/0.9",
        reqwest::Version::HTTP_10 => "HTTP/1.0",
        reqwest::Version::HTTP_11 => "HTTP/1.1",
        reqwest::Version::HTTP_2 => "HTTP/2",
        reqwest::Version::HTTP_3 => "HTTP/3",
        _ => "Unknown",
    }.to_string();
    
    let headers: HashMap<String, String> = response
        .headers()
        .iter()
        .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
        .collect();

    // 读取 body - 让 reqwest 处理流式优化
    let body = response.bytes().await
        .map_err(|e| RequestError::new_err(format!("Failed to read response body: {}", e)))?;

    let elapsed = start_time.elapsed().as_secs_f64();
    let is_redirect_status = matches!(status_code, 301 | 302 | 303 | 307 | 308);
    let encoding = detect_encoding(&headers);
    let cookies = parse_cookies_from_headers(&headers);
    let num_bytes_downloaded = body.len();
    
    Ok(HttpResponse::new(
        status_code,
        headers,
        body,
        url,
        elapsed,
        is_redirect_status,
        http_version,
        cookies,
        encoding,
        Vec::new(),
        None,
        num_bytes_downloaded,
    ))
}

// 现在只有一个简化的响应处理函数

// 核心请求构建和发送函数
pub async fn build_and_send_request(
    config: &ClientConfig,
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

    // 使用 ClientConfig 中预构建的客户端以获得最佳性能
    let client_to_use = config.get_client_for_redirect(follow_redirects);

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

    // 处理响应
    process_response(response, start_time).await
}

// 核心流式请求构建和发送函数 - 返回 StreamingHttpResponse
pub async fn build_and_send_streaming_request(
    config: &ClientConfig,
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
) -> PyResult<StreamingHttpResponse> {
    // 使用 ClientConfig 中预构建的客户端以获得最佳性能
    let client_to_use = config.get_client_for_redirect(follow_redirects);

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

    // 发送请求 - 关键：不读取响应体，保持流式
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

    // 创建流式响应 - 不读取 body，保持 reqwest::Response
    Ok(StreamingHttpResponse::new(response))
} 