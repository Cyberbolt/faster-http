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

        if self.http2 {
            builder = builder.http2_prior_knowledge();
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