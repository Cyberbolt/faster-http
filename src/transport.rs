use crate::error::RequestError;
use crate::request::HttpRequest;
use crate::response::HttpResponse;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use pyo3::PyCell;
use reqwest::Client;
use std::collections::HashMap;

/// Transport配置结构体 - 对应httpx的Transport系统
#[derive(Clone, Default)]
pub struct TransportConfig {
    /// 默认transport (用于未匹配的请求)
    pub default_transport: Option<PyObject>,
    /// 挂载的transport映射 (scheme/domain -> transport)
    pub mounts: HashMap<String, PyObject>,
    /// 是否启用自定义transport
    pub enable_custom_transport: bool,
}

impl TransportConfig {
    /// 从Python参数创建Transport配置
    pub fn from_python_params(
        transport: Option<PyObject>,
        mounts: Option<&PyDict>,
    ) -> PyResult<Self> {
        let mut config = TransportConfig::default();

        // 设置默认transport
        if let Some(transport_obj) = transport {
            config.default_transport = Some(transport_obj);
            config.enable_custom_transport = true;
        }

        // 设置挂载的transport
        if let Some(mounts_dict) = mounts {
            for (key, value) in mounts_dict.iter() {
                let key_str = key.downcast::<PyString>()?.to_str()?.to_string();
                config
                    .mounts
                    .insert(key_str, value.to_object(mounts_dict.py()));
            }
            if !config.mounts.is_empty() {
                config.enable_custom_transport = true;
            }
        }

        Ok(config)
    }

    /// 为给定的URL选择合适的transport
    pub fn select_transport_for_url(&self, url: &str) -> Option<&PyObject> {
        // 解析URL获取scheme和host
        if let Ok(parsed_url) = url::Url::parse(url) {
            let scheme = parsed_url.scheme();
            let host = parsed_url.host_str().unwrap_or("");

            // 1. 首先检查完整URL匹配
            if let Some(transport) = self.mounts.get(url) {
                return Some(transport);
            }

            // 2. 检查scheme + host匹配 (例如: "https://example.com")
            let scheme_host = format!("{}://{}", scheme, host);
            if let Some(transport) = self.mounts.get(&scheme_host) {
                return Some(transport);
            }

            // 3. 检查host匹配 (例如: "example.com")
            if let Some(transport) = self.mounts.get(host) {
                return Some(transport);
            }

            // 4. 检查scheme匹配 (例如: "https://")
            let scheme_pattern = format!("{}://", scheme);
            if let Some(transport) = self.mounts.get(&scheme_pattern) {
                return Some(transport);
            }
        }

        // 5. 返回默认transport
        self.default_transport.as_ref()
    }

    /// 检查是否应该使用自定义transport处理请求
    pub fn should_use_custom_transport(&self, url: &str) -> bool {
        self.enable_custom_transport
            && (self.default_transport.is_some() || self.select_transport_for_url(url).is_some())
    }

    /// 使用自定义transport发送请求
    pub fn send_request_via_custom_transport(
        &self,
        transport: &PyObject,
        request: &HttpRequest,
    ) -> PyResult<HttpResponse> {
        Python::with_gil(|py| {
            // 将HttpRequest转换为Python对象
            let py_request = PyCell::new(py, request.clone())?;

            // 调用transport的handle_request方法
            let result = transport.call_method1(py, "handle_request", (py_request,))?;

            // 期望返回HttpResponse对象
            result.extract::<HttpResponse>(py)
        })
    }
}

/// 默认的faster-http Transport实现
/// 这个类包装了reqwest客户端，提供了与httpx.BaseTransport兼容的接口
#[pyclass]
pub struct FasterhttpTransport {
    #[allow(dead_code)]
    client: Client,
}

#[pymethods]
impl FasterhttpTransport {
    #[new]
    pub fn new() -> PyResult<Self> {
        let client = Client::builder()
            .build()
            .map_err(|e| RequestError::new_err(format!("Failed to create client: {}", e)))?;

        Ok(FasterhttpTransport { client })
    }

    /// 处理请求 - 实现httpx.BaseTransport接口
    pub fn handle_request(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        // 创建默认的配置和headers来调用build_and_send_request
        let empty_headers: HashMap<String, String> = HashMap::new();
        let config = crate::config::ClientConfig::new(
            None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None,
        )?;

        // 使用同步客户端避免block_on
        let sync_client = crate::sync_core::SyncHttpClient::new(config)?;
        let response = sync_client.send_request(
            request.get_method(),
            request.get_url(),
            request.get_content(),
            request.get_data().clone(),
            request.get_json().clone(),
            request.get_files().clone(),
            Some(request.get_params().clone()),
            Some(request.get_headers().clone()), // headers
            None,                                // timeout
            None,                                // auth
            Some(true),                          // follow_redirects
            Some(request.get_cookies().clone()), // cookies
        )?;

        Ok(response)
    }

    /// 关闭transport
    pub fn close(&self) -> PyResult<()> {
        // reqwest客户端没有显式的关闭方法
        Ok(())
    }

    /// 异步关闭transport
    pub fn aclose(&self) -> PyResult<()> {
        // reqwest客户端没有显式的关闭方法
        Ok(())
    }
}

/// 创建一个mock transport用于测试
#[pyclass]
pub struct MockTransport {
    /// 预定义的响应映射 (URL -> Response)
    responses: HashMap<String, HttpResponse>,
    /// 默认响应
    default_response: Option<HttpResponse>,
}

#[pymethods]
impl MockTransport {
    #[new]
    pub fn new(
        responses: Option<HashMap<String, HttpResponse>>,
        default_response: Option<HttpResponse>,
    ) -> Self {
        MockTransport {
            responses: responses.unwrap_or_default(),
            default_response,
        }
    }

    /// 添加mock响应
    pub fn add_response(&mut self, url: String, response: HttpResponse) {
        self.responses.insert(url, response);
    }

    /// 设置默认响应
    pub fn set_default_response(&mut self, response: HttpResponse) {
        self.default_response = Some(response);
    }

    /// 处理请求 - 返回预定义的mock响应
    pub fn handle_request(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        let url = request.url_str();

        // 检查是否有特定URL的响应
        if let Some(response) = self.responses.get(url) {
            return Ok(response.clone());
        }

        // 检查是否有默认响应
        if let Some(response) = &self.default_response {
            return Ok(response.clone());
        }

        // 如果没有配置响应，返回404
        Err(RequestError::new_err(format!(
            "No mock response configured for URL: {}",
            url
        )))
    }

    pub fn close(&self) -> PyResult<()> {
        Ok(())
    }

    pub fn aclose(&self) -> PyResult<()> {
        Ok(())
    }
}

/// 重定向Transport - 将HTTP请求重定向到HTTPS
#[pyclass]
pub struct HTTPSRedirectTransport {
    /// 底层transport
    transport: FasterhttpTransport,
}

#[pymethods]
impl HTTPSRedirectTransport {
    #[new]
    pub fn new() -> PyResult<Self> {
        Ok(HTTPSRedirectTransport {
            transport: FasterhttpTransport::new()?,
        })
    }

    /// 处理请求 - 将HTTP重定向到HTTPS
    pub fn handle_request(&self, request: &HttpRequest) -> PyResult<HttpResponse> {
        let original_url = request.url_str();

        // 检查是否为HTTP URL
        if original_url.starts_with("http://") {
            // 创建HTTPS版本的请求
            let https_url = original_url.replacen("http://", "https://", 1);
            let https_request = Python::with_gil(|py| {
                HttpRequest::new(
                    request.method_str().to_string(),
                    https_url,
                    Some(request.headers_map().clone().into_py(py)),
                    request.content_bytes().map(|c| c.to_vec()),
                    Some(request.params_internal().clone()),
                    Some(request.cookies_internal().clone()),
                    request.data_internal().clone(),
                    request.files_internal().clone(),
                    request.json_internal().clone(),
                    Some(request.stream_internal()),
                )
            })?;

            // 使用底层transport发送HTTPS请求
            self.transport.handle_request(&https_request)
        } else {
            // 直接发送原始请求
            self.transport.handle_request(request)
        }
    }

    pub fn close(&self) -> PyResult<()> {
        self.transport.close()
    }

    pub fn aclose(&self) -> PyResult<()> {
        self.transport.aclose()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_transport_config_default() {
        let config = TransportConfig::default();
        assert!(!config.enable_custom_transport);
        assert!(config.default_transport.is_none());
        assert!(config.mounts.is_empty());
    }

    #[test]
    fn test_transport_url_selection() {
        let config = TransportConfig::default();

        // 这个测试需要Python对象，暂时跳过
        // 在实际使用中会有Python对象
        assert!(!config.should_use_custom_transport("https://example.com"));
    }

    #[tokio::test]
    async fn test_mock_transport() {
        // 创建mock transport
        let mock_transport = MockTransport::new(None, None);

        // 测试没有配置响应的情况
        let request = Python::with_gil(|_py| {
            HttpRequest::new(
                "GET".to_string(),
                "https://example.com".to_string(),
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )
        })
        .unwrap();

        let result = mock_transport.handle_request(&request);
        assert!(result.is_err());
    }
}
