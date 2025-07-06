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
        auth: Option<PyObject>,  // Accept either tuple or auth object
        proxy: Option<String>,
        cookies: Option<HashMap<String, String>>,
        http2: Option<bool>,
    ) -> PyResult<Self> {
        let auth_type = if let Some(auth_obj) = auth {
            Python::with_gil(|py| -> PyResult<Option<AuthType>> {
                // Try to extract as auth object first
                if let Ok(Some(auth_type)) = extract_auth_from_object(&auth_obj) {
                    return Ok(Some(auth_type));
                }
                
                // Fallback to tuple format for backward compatibility
                if let Ok((username, password)) = auth_obj.extract::<(String, String)>(py) {
                    return Ok(Some(AuthType::Basic { username, password }));
                }
                
                Ok(None)
            })?
        } else {
            None
        };

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

        // HTTP/2 support - fully compatible with httpx behavior
        if self.http2 {
            // http2=True: Enable HTTP/2 negotiation with automatic fallback to HTTP/1.1
            // This is fully consistent with httpx behavior: client will try HTTP/2, fallback to HTTP/1.1 if unsupported
            // reqwest supports this by default, we just need to ensure HTTP/2 is enabled
            // Also enable HTTP/2 optimization settings
            builder = builder
                .http2_keep_alive_interval(Some(std::time::Duration::from_secs(20)))
                .http2_keep_alive_timeout(std::time::Duration::from_secs(10));
        } else {
            // http2=False: Force HTTP/1.1 only
            // This is consistent with httpx default behavior
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