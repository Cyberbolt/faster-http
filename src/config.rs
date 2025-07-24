use pyo3::prelude::*;
use reqwest::Client;
use std::collections::HashMap;
use std::time::Duration;
use crate::auth::{AuthType, extract_auth_from_object};
use crate::error::RequestError;

// Core client configuration
#[derive(Clone)]
pub struct ClientConfig {
    pub base_url: Option<String>,
    pub default_timeout: Option<Duration>,
    pub default_headers: HashMap<String, String>,
    pub follow_redirects: bool,
    pub auth: Option<AuthType>,
    pub auth_object: Option<PyObject>, // Store original auth object for httpx compatibility
    pub proxy: Option<String>,
    pub default_cookies: HashMap<String, String>,
    pub http2: bool,
    // 预构建的客户端以支持高效的重定向控制
    pub redirect_client: Client,
    pub no_redirect_client: Client,
}

impl ClientConfig {
    pub fn new(
        base_url: Option<String>,
        timeout: Option<f64>,
        headers: Option<HashMap<String, String>>,
        verify: Option<bool>,
        follow_redirects: Option<bool>,
        auth: Option<PyObject>,  // Accept either tuple or auth object
        proxy: Option<String>,
        cookies: Option<HashMap<String, String>>,
        http2: Option<bool>,
    ) -> PyResult<Self> {
        let (auth_type, auth_object) = if let Some(auth_obj) = auth {
            Python::with_gil(|py| -> PyResult<(Option<AuthType>, Option<PyObject>)> {
                // Try to extract as auth object first
                if let Ok(Some(auth_type)) = extract_auth_from_object(&auth_obj) {
                    return Ok((Some(auth_type), Some(auth_obj.clone())));
                }
                
                // Fallback to tuple format for backward compatibility
                if let Ok((username, password)) = auth_obj.extract::<(String, String)>(py) {
                    return Ok((Some(AuthType::Basic { username, password }), Some(auth_obj.clone())));
                }
                
                Ok((None, None))
            })?
        } else {
            (None, None)
        };

        // 预构建两个客户端以支持高效的重定向控制
        let redirect_client = Self::build_client_with_redirect(true, verify, &proxy, http2)?;
        let no_redirect_client = Self::build_client_with_redirect(false, verify, &proxy, http2)?;

        Ok(ClientConfig {
            base_url,
            default_timeout: timeout.map(Duration::from_secs_f64).or(Some(Duration::from_secs(30))), // 设置默认30秒超时
            default_headers: headers.unwrap_or_default(),
            follow_redirects: follow_redirects.unwrap_or(true),
            auth: auth_type,
            auth_object,
            proxy,
            default_cookies: cookies.unwrap_or_default(),
            http2: http2.unwrap_or(false),
            redirect_client,
            no_redirect_client,
        })
    }

    fn build_client_with_redirect(
        follow_redirects: bool, 
        verify: Option<bool>, 
        proxy: &Option<String>, 
        http2: Option<bool>
    ) -> PyResult<Client> {
        let verify = verify.unwrap_or(true);
        let http2 = http2.unwrap_or(false);
        
        let mut builder = Client::builder();

        // Simplified HTTP configuration
        if !http2 {
            builder = builder.http1_only();
        }

        if let Some(proxy_url) = proxy {
            let proxy = reqwest::Proxy::all(proxy_url)
                .map_err(|e| RequestError::new_err(format!("Invalid proxy URL: {}", e)))?;
            builder = builder.proxy(proxy);
        }

        builder.build()
            .map_err(|e| RequestError::new_err(format!("Failed to create client: {}", e)))
    }

    pub fn build_client(&self, verify: Option<bool>) -> PyResult<Client> {
        let verify = verify.unwrap_or(true);
        
        let mut builder = Client::builder();

        // Simplified HTTP configuration
        if !self.http2 {
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
    
    // 根据 follow_redirects 参数选择合适的客户端
    pub fn get_client_for_redirect(&self, follow_redirects: bool) -> &Client {
        if follow_redirects {
            &self.redirect_client
        } else {
            &self.no_redirect_client
        }
    }
} 