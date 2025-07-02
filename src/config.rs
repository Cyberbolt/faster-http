use pyo3::prelude::*;
use reqwest::Client;
use std::collections::HashMap;
use std::time::Duration;
use crate::auth::AuthType;
use crate::error::RequestError;

// 核心客户端配置
#[derive(Clone)]
pub struct ClientConfig {
    pub base_url: Option<String>,
    pub default_timeout: Option<Duration>,
    pub default_headers: HashMap<String, String>,
    pub follow_redirects: bool,
    pub auth: Option<AuthType>,
    pub proxy: Option<String>,
    pub default_cookies: HashMap<String, String>,
    pub http2: bool,
}

impl ClientConfig {
    pub fn new(
        base_url: Option<String>,
        timeout: Option<f64>,
        headers: Option<HashMap<String, String>>,
        _verify: Option<bool>,
        follow_redirects: Option<bool>,
        auth: Option<(String, String)>,
        proxy: Option<String>,
        cookies: Option<HashMap<String, String>>,
        http2: Option<bool>,
    ) -> PyResult<Self> {
        let auth_type = auth.map(|(username, password)| AuthType::Basic { username, password });

        Ok(ClientConfig {
            base_url,
            default_timeout: timeout.map(Duration::from_secs_f64),
            default_headers: headers.unwrap_or_default(),
            follow_redirects: follow_redirects.unwrap_or(true),
            auth: auth_type,
            proxy,
            default_cookies: cookies.unwrap_or_default(),
            http2: http2.unwrap_or(false),
        })
    }

    pub fn build_client(&self, verify: Option<bool>) -> PyResult<Client> {
        let verify = verify.unwrap_or(true);
        
        let mut builder = Client::builder()
            .danger_accept_invalid_certs(!verify)
            .redirect(if self.follow_redirects { 
                reqwest::redirect::Policy::limited(10) 
            } else { 
                reqwest::redirect::Policy::none() 
            });

        // HTTP/2 support - 完全兼容httpx的行为
        if self.http2 {
            // http2=True: 启用HTTP/2协商，支持自动降级到HTTP/1.1
            // 这与httpx的行为完全一致：客户端会尝试HTTP/2，如果服务器不支持则降级到HTTP/1.1
            // reqwest默认就支持这种行为，我们只需要确保HTTP/2功能启用
            // 同时启用HTTP/2的优化设置
            builder = builder
                .http2_keep_alive_interval(Some(std::time::Duration::from_secs(20)))
                .http2_keep_alive_timeout(std::time::Duration::from_secs(10));
        } else {
            // http2=False: 强制只使用HTTP/1.1
            // 这与httpx的默认行为一致
            builder = builder.http1_only();
        }

        if let Some(proxy_url) = &self.proxy {
            let proxy = reqwest::Proxy::all(proxy_url)
                .map_err(|e| RequestError::new_err(format!("Invalid proxy URL: {}", e)))?;
            builder = builder.proxy(proxy);
        }

        builder.build()
            .map_err(|e| RequestError::new_err(format!("Failed to create client: {}", e)))
    }
} 