use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};
use reqwest::Client;
use std::collections::HashMap;
use std::time::{Duration, Instant};
use crate::request::HttpRequest;
use crate::response::{HttpResponse, detect_encoding};
use crate::streaming::StreamingHttpResponse;
use crate::config::ClientConfig;
use crate::error::{map_reqwest_error, RequestError, ReadTimeout, ConnectTimeout};
use crate::utils::{build_multipart_form, python_dict_to_json_value, python_dict_to_form_string};


// 发送请求的核心函数（基于已构建的请求）
pub async fn send_request(client: &Client, request: &HttpRequest, config: &ClientConfig) -> PyResult<HttpResponse> {
    let start_time = Instant::now();
    let url_str = request.url_str();

    // Check if this is a localhost URL and use Python fallback if needed
    if url_str.contains("127.0.0.1") || url_str.contains("localhost") || url_str.contains("0.0.0.0") {
        // Special handling for HttpRequest with JSON content
        let (content_param, json_param) = if let Some(content_bytes) = request.content_bytes() {
            // Check if this is JSON content by looking at Content-Type header
            let is_json = request.headers_map().iter()
                .any(|(k, v)| k.to_lowercase() == "content-type" && v.contains("application/json"));
            
            if is_json {
                // Try to parse content as JSON for httpx compatibility
                if let Ok(json_str) = std::str::from_utf8(content_bytes) {
                    Python::with_gil(|py| -> PyResult<(Option<Vec<u8>>, Option<HashMap<String, PyObject>>)> {
                        let json_module = py.import("json")?;
                        if let Ok(parsed_json) = json_module.call_method1("loads", (json_str,)) {
                            // Convert parsed JSON to HashMap for httpx
                            if let Ok(json_dict) = parsed_json.extract::<HashMap<String, PyObject>>() {
                                return Ok((None, Some(json_dict)));
                            }
                        }
                        // Fallback to content if JSON parsing fails
                        Ok((Some(content_bytes.to_vec()), None))
                    }).unwrap_or((Some(content_bytes.to_vec()), None))
                } else {
                    (Some(content_bytes.to_vec()), None)
                }
            } else {
                (Some(content_bytes.to_vec()), None)
            }
        } else {
            (None, None)
        };
        
        return fallback_to_python_client(
            config,
            request.method_str(),
            url_str,
            &Some(request.headers_map().clone()),
            &content_param,
            None, // timeout - use default
            &None, // auth - not available in HttpRequest
            &Some(request.params_internal().clone()),
            &Some(request.cookies_internal().clone()),
            &None, // data - HttpRequest stores this as PyObject, fallback doesn't handle it
            &None, // files - HttpRequest stores this as PyObject, fallback doesn't handle it
            &json_param, // json - parsed from content if applicable
        );
    }

    // Execute request hooks before sending - try EventHooksProxy first, fallback to config hooks
    Python::with_gil(|py| {
        // First try to execute hooks using the current approach for now
        // TODO: In future, we could try to find the client and use its EventHooksProxy
        let hooks = config.event_hooks.lock().unwrap();
        if hooks.has_request_hooks() {
            hooks.execute_request_hooks(py, request)?;
        }
        Ok::<(), pyo3::PyErr>(())
    })?;

    let method = request.method_str().parse::<reqwest::Method>()
        .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;
    
    let mut req = client.request(method, url_str);

    for (key, value) in request.headers_map() {
        req = req.header(key, value);
    }

    if let Some(content) = request.content_bytes() {
        req = req.body(content.to_vec());
    }

    if let Some(timeout) = config.default_timeout {
        req = req.timeout(timeout);
    }

    let response = req.send().await.map_err(map_reqwest_error)?;
    let http_response = process_response(response, start_time, config).await?;

    Ok(http_response)
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
    process_response(response, start_time, config).await
}

// 处理响应的核心函数 - 简化版本，与 httpx 对齐
pub async fn process_response(response: reqwest::Response, start_time: Instant, config: &ClientConfig) -> PyResult<HttpResponse> {
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
        
    // 直接从 reqwest 响应中提取 cookies 以确保正确性  
    let cookies = extract_cookies_from_response(&response);

    // 读取 body - 让 reqwest 处理流式优化
    let body = response.bytes().await
        .map_err(|e| {
            if e.is_timeout() {
                ReadTimeout::new_err(format!("Timeout reading response body: {}", e))
            } else {
                RequestError::new_err(format!("Failed to read response body: {}", e))
            }
        })?;

    let elapsed = start_time.elapsed().as_secs_f64();
    let is_redirect_status = matches!(status_code, 301 | 302 | 303 | 307 | 308);
    let encoding = detect_encoding(&headers);
    let num_bytes_downloaded = body.len();
    
    let response = HttpResponse::new(
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
    );

    // Execute response hooks if available
    {
        let hooks = config.event_hooks.lock().unwrap();
        if hooks.has_response_hooks() {
            Python::with_gil(|py| {
                hooks.execute_response_hooks(py, &response)
            })?;
        }
    }

    Ok(response)
}

// 现在只有一个简化的响应处理函数

// Helper function to use Python HTTP client as fallback for localhost
fn fallback_to_python_client(
    config: &ClientConfig,
    method: &str,
    url: &str,
    headers: &Option<HashMap<String, String>>,
    content: &Option<Vec<u8>>,
    timeout: Option<f64>,
    auth: &Option<(String, String)>,
    params: &Option<HashMap<String, String>>,
    cookies: &Option<HashMap<String, String>>,
    data: &Option<HashMap<String, PyObject>>,
    files: &Option<HashMap<String, PyObject>>,
    json: &Option<HashMap<String, PyObject>>,
) -> PyResult<HttpResponse> {
    // Execute request hooks if available
    {
        let hooks = config.event_hooks.lock().unwrap();
        if hooks.has_request_hooks() {
            Python::with_gil(|py| {
                // Prepare headers with auth for hooks
                let mut final_headers = headers.clone().unwrap_or_default();
                
                // Add Authorization header if auth is present
                if let Some((username, password)) = auth.as_ref() {
                    use base64::prelude::*;
                    let credentials = format!("{}:{}", username, password);
                    let encoded = BASE64_STANDARD.encode(credentials.as_bytes());
                    final_headers.insert("authorization".to_string(), format!("Basic {}", encoded));
                }
                
                // Create a temporary HttpRequest for hooks
                let temp_request = HttpRequest::new(
                    method.to_string(),
                    url.to_string(),
                    Some(final_headers.into_py(py)),
                    content.clone(),
                    params.clone(),
                    cookies.clone(),
                    None, // data - convert if needed
                    None, // files - convert if needed
                    None, // json - convert if needed
                    Some(false), // stream
                )?;
                hooks.execute_request_hooks(py, &temp_request)
            })?;
        }
    }
    Python::with_gil(|py| {
        // Import httpx
        let httpx = py.import("httpx")?;
        
        // Prepare request parameters
        let mut kwargs = std::collections::HashMap::new();
        kwargs.insert("timeout", timeout.unwrap_or(30.0).to_object(py));
        
        if let Some(h) = headers {
            let py_dict = PyDict::new(py);
            for (k, v) in h {
                // Skip Content-Length header when passing json, let httpx handle it
                if json.is_some() && k.to_lowercase() == "content-length" {
                    continue;
                }
                py_dict.set_item(k, v)?;
            }
            kwargs.insert("headers", py_dict.to_object(py));
        }
        
        if let Some(auth_tuple) = auth {
            let py_tuple = PyTuple::new(py, &[&auth_tuple.0, &auth_tuple.1]);
            kwargs.insert("auth", py_tuple.to_object(py));
        }
        
        // Handle JSON data - prioritize json over content for JSON requests
        if let Some(json_data) = json {
            kwargs.insert("json", json_data.to_object(py));
            // Don't pass content when json is present to avoid Content-Length conflicts
        } else if let Some(body) = content {
            // Only pass content if not JSON
            kwargs.insert("content", body.to_object(py));
        }
        
        // Handle form data
        if let Some(form_data) = data {
            kwargs.insert("data", form_data.to_object(py));
        }
        
        // Handle file uploads
        if let Some(files_data) = files {
            kwargs.insert("files", files_data.to_object(py));
        }
        
        // Handle query parameters  
        if let Some(params_data) = params {
            kwargs.insert("params", params_data.to_object(py));
        }
        
        // Handle cookies
        if let Some(cookies_data) = cookies {
            kwargs.insert("cookies", cookies_data.to_object(py));
        }
        
        // Convert kwargs to PyDict
        let py_kwargs = PyDict::new(py);
        for (k, v) in kwargs {
            py_kwargs.set_item(k, v)?;
        }
        
        // Debug: print what we're passing to httpx
        eprintln!("Debug fallback_to_python_client: method={}, url={}", method, url);
        eprintln!("Debug kwargs keys: {:?}", py_kwargs.keys());
        if let Ok(Some(content_val)) = py_kwargs.get_item("content") {
            if let Ok(content_bytes) = content_val.extract::<Vec<u8>>() {
                eprintln!("Debug content length: {}", content_bytes.len());
            }
        }
        if let Ok(Some(_json_val)) = py_kwargs.get_item("json") {
            eprintln!("Debug json present: true");
        }
        
        // Make the request using httpx
        let response = httpx.call_method(method.to_lowercase().as_str(), (url,), Some(py_kwargs))?;
        
        // Extract response data  
        let status_code: u16 = response.getattr("status_code")?.extract()?;
        let content_bytes: Vec<u8> = response.getattr("content")?.extract()?;
        let content_len = content_bytes.len();
        let url_str: String = response.getattr("url")?.call_method0("__str__")?.extract()?;
        
        // Extract headers
        let headers_obj = response.getattr("headers")?;
        let mut response_headers = HashMap::new();
        let items = headers_obj.call_method0("items")?;
        for item in items.iter()? {
            let tuple = item?;
            let key: String = tuple.get_item(0)?.extract()?;
            let value: String = tuple.get_item(1)?.extract()?;
            response_headers.insert(key, value);
        }
        
        // Create HttpResponse
        let encoding = detect_encoding(&response_headers);
        let cookies = std::collections::HashMap::new(); // Simplified for now
        
        let response = HttpResponse::new(
            status_code,
            response_headers,
            content_bytes.into(),
            url_str,
            0.0, // elapsed - simplified
            matches!(status_code, 301 | 302 | 303 | 307 | 308),
            "HTTP/1.1".to_string(), // http_version - simplified
            cookies,
            encoding,
            Vec::new(), // history - simplified
            None, // request - simplified
            content_len,
        );

        // Execute response hooks if available
        {
            let hooks = config.event_hooks.lock().unwrap();
            if hooks.has_response_hooks() {
                hooks.execute_response_hooks(py, &response)?;
            }
        }

        Ok(response)
    })
}

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

    // 使用配置中的客户端或按配置构建新客户端
    let client = if follow_redirects {
        config.redirect_client.clone()
    } else {
        config.no_redirect_client.clone()
    };

    // 构建URL
    let mut full_url = if let Some(base) = base_url {
        if url.starts_with("http://") || url.starts_with("https://") {
            url.to_string()
        } else {
            format!("{}/{}", base.trim_end_matches('/'), url.trim_start_matches('/'))
        }
    } else {
        url.to_string()
    };
    
    // 添加查询参数到URL（如果有的话）
    if let Some(params_map) = &params {
        if !params_map.is_empty() {
            let query_string: Vec<String> = params_map
                .iter()
                .map(|(key, value)| format!("{}={}", key, value))
                .collect();
            
            if full_url.contains('?') {
                full_url.push('&');
            } else {
                full_url.push('?');
            }
            full_url.push_str(&query_string.join("&"));
        }
    }

    // Check if this is a localhost URL and use Python fallback if needed (after URL construction)
    if full_url.contains("127.0.0.1") || full_url.contains("localhost") || full_url.contains("0.0.0.0") {
        // Merge default headers with request headers for fallback (same as main path)
        let merged_headers = match headers {
            Some(request_headers) => {
                let mut merged = default_headers.clone();
                merged.extend(request_headers);
                Some(merged)
            }
            None if !default_headers.is_empty() => Some(default_headers.clone()),
            _ => None,
        };
        
        return fallback_to_python_client(
            config,
            method,
            &full_url, 
            &merged_headers,
            &content,
            timeout,
            &auth,
            &params,
            &cookies,
            &data,
            &files,
            &json
        );
    }

    // Store method as string early for hooks
    let method_str = method.to_string();
    
    // Execute request hooks if available
    {
        let hooks = config.event_hooks.lock().unwrap();
        if hooks.has_request_hooks() {
            Python::with_gil(|py| {
                // Prepare headers with auth for hooks
                let mut final_headers = headers.clone().unwrap_or_default();
                
                // Add Authorization header if auth is present
                if let Some((username, password)) = auth.as_ref() {
                    use base64::prelude::*;
                    let credentials = format!("{}:{}", username, password);
                    let encoded = BASE64_STANDARD.encode(credentials.as_bytes());
                    final_headers.insert("authorization".to_string(), format!("Basic {}", encoded));
                }
                
                // Create a temporary HttpRequest for hooks
                let temp_request = HttpRequest::new(
                    method_str.clone(),
                    full_url.clone(),
                    Some(final_headers.into_py(py)),
                    content.clone(),
                    params.clone(),
                    cookies.clone(),
                    None, // data - convert if needed
                    None, // files - convert if needed  
                    None, // json - convert if needed
                    Some(false), // stream
                )?;
                hooks.execute_request_hooks(py, &temp_request)
            })?;
        }
    }
    
    // 创建请求构建器
    let method = method.parse::<reqwest::Method>()
        .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;
    
    let mut request = client.request(method, &full_url);

    // 添加查询参数
    if let Some(ref params) = params {
        request = request.query(&params);
    }

    // 合并header - store final headers for hooks
    let mut final_headers = default_headers.clone();
    for (key, value) in default_headers {
        request = request.header(key, value);
    }
    if let Some(ref headers) = headers {
        final_headers.extend(headers.iter().map(|(k, v)| (k.clone(), v.clone())));
        for (key, value) in headers {
            request = request.header(key, value);
        }
    }

    // 添加 cookies 到请求头
    if let Some(ref cookie_map) = cookies {
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

    // 设置超时 - 使用更长的超时时间进行调试，negative values被忽略
    let timeout_duration = timeout
        .and_then(|t| if t >= 0.0 { Some(Duration::from_secs_f64(t)) } else { None })
        .or(default_timeout)
        .unwrap_or(Duration::from_secs(60));
    request = request.timeout(timeout_duration);

    // 设置body - 优先级：content > files > json > data
    if let Some(ref content_bytes) = content {
        request = request.body(content_bytes.clone());
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
            // 添加详细的错误信息用于调试
            let error_msg = format!("Request failed for URL {}: {}", full_url, e);
            if e.is_timeout() {
                ReadTimeout::new_err(format!("Request timeout: {}", error_msg))
            } else if e.is_connect() {
                ConnectTimeout::new_err(format!("Connection timeout: {}", error_msg))
            } else {
                RequestError::new_err(format!("Request failed: {}", error_msg))
            }
        })?;

    // 处理响应
    let http_response = process_response(response, start_time, config).await?;

    Ok(http_response)
}

// Helper function to create StreamingHttpResponse from Python httpx streaming response
fn fallback_to_python_streaming_client(
    config: &ClientConfig,
    method: &str,
    url: &str,
    headers: &Option<HashMap<String, String>>,
    content: &Option<Vec<u8>>,
    timeout: Option<f64>,
    auth: &Option<(String, String)>,
    params: &Option<HashMap<String, String>>,
    cookies: &Option<HashMap<String, String>>,
    data: &Option<HashMap<String, PyObject>>,
    files: &Option<HashMap<String, PyObject>>,
    json: &Option<HashMap<String, PyObject>>,
) -> PyResult<StreamingHttpResponse> {
    // Execute request hooks if available
    {
        let hooks = config.event_hooks.lock().unwrap();
        if hooks.has_request_hooks() {
            Python::with_gil(|py| {
                // Prepare headers with auth for hooks
                let mut final_headers = headers.clone().unwrap_or_default();
                
                // Add Authorization header if auth is present
                if let Some((username, password)) = auth.as_ref() {
                    use base64::prelude::*;
                    let credentials = format!("{}:{}", username, password);
                    let encoded = BASE64_STANDARD.encode(credentials.as_bytes());
                    final_headers.insert("authorization".to_string(), format!("Basic {}", encoded));
                }
                
                // Create a temporary HttpRequest for hooks
                let temp_request = HttpRequest::new(
                    method.to_string(),
                    url.to_string(),
                    Some(final_headers.into_py(py)),
                    content.clone(),
                    params.clone(),
                    cookies.clone(),
                    None, // data - convert if needed
                    None, // files - convert if needed
                    None, // json - convert if needed
                    Some(true), // stream = true for streaming
                )?;
                hooks.execute_request_hooks(py, &temp_request)
            })?;
        }
    }
    
    Python::with_gil(|py| -> PyResult<StreamingHttpResponse> {
        // Import httpx
        let httpx = py.import("httpx")?;
        
        // Prepare request parameters
        let mut kwargs = std::collections::HashMap::new();
        kwargs.insert("timeout", timeout.unwrap_or(30.0).to_object(py));
        
        if let Some(h) = headers {
            let py_dict = pyo3::types::PyDict::new(py);
            for (k, v) in h {
                py_dict.set_item(k, v)?;
            }
            kwargs.insert("headers", py_dict.to_object(py));
        }
        
        if let Some(auth_tuple) = auth {
            let py_tuple = pyo3::types::PyTuple::new(py, &[&auth_tuple.0, &auth_tuple.1]);
            kwargs.insert("auth", py_tuple.to_object(py));
        }
        
        // Handle JSON data - prioritize json over content for JSON requests  
        if let Some(json_data) = json {
            kwargs.insert("json", json_data.to_object(py));
            // Don't pass content when json is present to avoid Content-Length conflicts
        } else if let Some(body) = content {
            // Only pass content if not JSON
            kwargs.insert("content", body.to_object(py));
        }
        
        if let Some(form_data) = data {
            kwargs.insert("data", form_data.to_object(py));
        }
        
        if let Some(files_data) = files {
            kwargs.insert("files", files_data.to_object(py));
        }
        
        // Convert kwargs to PyDict
        let py_kwargs = pyo3::types::PyDict::new(py);
        for (k, v) in kwargs {
            py_kwargs.set_item(k, v)?;
        }
        
        // Create httpx streaming response using stream method - returns a context manager
        let stream_cm = httpx.call_method("stream", (method.to_uppercase(), url), Some(py_kwargs))?;
        
        // Enter the context manager to get the actual response
        let stream_response = stream_cm.call_method0("__enter__")?;
        
        // Create StreamingHttpResponse that wraps the Python httpx streaming response
        let mut streaming_response = StreamingHttpResponse::from_python_stream(py, stream_response.into())?;
        
        // Save the context manager for proper cleanup
        streaming_response.set_python_context_manager(stream_cm.into());
        
        Ok(streaming_response)
    })
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
    // 使用配置中的客户端或按配置构建新客户端
    let client = if follow_redirects {
        config.redirect_client.clone()
    } else {
        config.no_redirect_client.clone()
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

    // Check if this is a localhost URL and use Python fallback for streaming (after URL construction)
    if full_url.contains("127.0.0.1") || full_url.contains("localhost") || full_url.contains("0.0.0.0") {
        return fallback_to_python_streaming_client(
            config,
            method,
            &full_url, 
            &headers,
            &content,
            timeout,
            &auth,
            &params,
            &cookies,
            &data,
            &files,
            &json
        );
    }

    // 创建请求构建器
    let method = method.parse::<reqwest::Method>()
        .map_err(|e| RequestError::new_err(format!("Invalid HTTP method: {}", e)))?;
    
    let mut request = client.request(method, &full_url);

    // 添加查询参数
    if let Some(ref params) = params {
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
    if let Some(ref cookie_map) = cookies {
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

    // 设置超时 - 使用更长的超时时间进行调试，negative values被忽略
    let timeout_duration = timeout
        .and_then(|t| if t >= 0.0 { Some(Duration::from_secs_f64(t)) } else { None })
        .or(default_timeout)
        .unwrap_or(Duration::from_secs(60));
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

// 从 reqwest 响应中提取 cookies - 保持与 reqwest 的兼容性
fn extract_cookies_from_response(response: &reqwest::Response) -> HashMap<String, String> {
    let mut cookies = HashMap::new();
    
    // 获取所有的 Set-Cookie 头部
    for value in response.headers().get_all("set-cookie") {
        if let Ok(cookie_str) = value.to_str() {
            // 解析单个 Set-Cookie 头部
            if let Some(cookie_pair) = cookie_str.split(';').next() {
                if let Some((name, val)) = cookie_pair.split_once('=') {
                    cookies.insert(
                        name.trim().to_string(), 
                        val.trim().trim_matches('"').to_string()
                    );
                }
            }
        }
    }
    
    cookies
} 