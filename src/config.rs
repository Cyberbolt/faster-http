use pyo3::prelude::*;
use reqwest::Client;
use std::collections::HashMap;
use std::time::Duration;
use crate::auth::{AuthType, extract_auth_from_object};
use crate::error::RequestError;
use crate::hooks::EventHooks;
use crate::ssl_config::SslConfig;
use crate::transport::TransportConfig;
use crate::proxy_config::ProxySystem;

// Core client configuration
#[derive(Clone)]
pub struct ClientConfig {
    pub base_url: Option<String>,
    pub default_timeout: Option<Duration>,
    pub default_headers: HashMap<String, String>,
    pub follow_redirects: bool,
    pub auth: Option<AuthType>,
    pub auth_object: Option<PyObject>, // Store original auth object for httpx compatibility
    pub proxy_system: ProxySystem, // Advanced proxy configuration
    pub default_cookies: HashMap<String, String>,
    pub http2: bool,
    pub event_hooks: EventHooks, // Event hooks for request/response logging
    pub ssl_config: SslConfig, // SSL/TLS configuration
    pub transport_config: TransportConfig, // Custom transport configuration
    // 预构建的客户端以支持高效的重定向控制
    pub redirect_client: Client,
    pub no_redirect_client: Client,
}

impl ClientConfig {
    pub fn new(
        base_url: Option<String>,
        timeout: Option<f64>,
        headers: Option<HashMap<String, String>>,
        verify: Option<&PyAny>,
        follow_redirects: Option<bool>,
        auth: Option<PyObject>,  // Accept either tuple or auth object
        proxy: Option<&PyAny>, // Single proxy URL
        proxies: Option<&pyo3::types::PyDict>, // Proxy mapping dict
        cookies: Option<HashMap<String, String>>,
        http2: Option<bool>,
        event_hooks: Option<PyObject>, // Event hooks dict
        cert: Option<&PyAny>, // Client certificate configuration
        trust_env: Option<bool>, // Trust environment variables for SSL
        transport: Option<PyObject>, // Custom transport
        mounts: Option<&pyo3::types::PyDict>, // Transport mounts
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

        // Parse event hooks
        let hooks = if let Some(hooks_obj) = event_hooks {
            Python::with_gil(|py| EventHooks::from_python_dict(py, &hooks_obj))?
        } else {
            EventHooks::new()
        };

        // Create SSL configuration
        let mut ssl_config = SslConfig::from_python_params(verify, cert, trust_env)?;
        
        // Load CA bundle from environment if trust_env is enabled
        ssl_config.load_ca_bundle_from_env();

        // Create transport configuration
        let transport_config = TransportConfig::from_python_params(transport, mounts)?;

        // Create proxy system
        let proxy_system = ProxySystem::from_python_params(proxy, proxies, trust_env)?;

        // 预构建两个客户端以支持高效的重定向控制
        let redirect_client = Self::build_client_with_ssl_proxy_and_redirect(true, &ssl_config, &proxy_system, http2)?;
        let no_redirect_client = Self::build_client_with_ssl_proxy_and_redirect(false, &ssl_config, &proxy_system, http2)?;

        Ok(ClientConfig {
            base_url,
            default_timeout: timeout.map(Duration::from_secs_f64).or(Some(Duration::from_secs(30))), // 设置默认30秒超时
            default_headers: headers.unwrap_or_default(),
            follow_redirects: follow_redirects.unwrap_or(true),
            auth: auth_type,
            auth_object,
            proxy_system,
            default_cookies: cookies.unwrap_or_default(),
            http2: http2.unwrap_or(false),
            event_hooks: hooks,
            ssl_config,
            transport_config,
            redirect_client,
            no_redirect_client,
        })
    }

    fn build_client_with_ssl_proxy_and_redirect(
        follow_redirects: bool, 
        ssl_config: &SslConfig, 
        proxy_system: &ProxySystem,
        http2: Option<bool>
    ) -> PyResult<Client> {
        let http2 = http2.unwrap_or(false);
        
        let mut builder = Client::builder();

        // Configure redirects
        if !follow_redirects {
            builder = builder.redirect(reqwest::redirect::Policy::none());
        }

        // Apply SSL configuration
        builder = ssl_config.apply_to_client_builder(builder)
            .map_err(|e| RequestError::new_err(format!("SSL configuration error: {}", e)))?;

        // Configure HTTP version
        if !http2 {
            builder = builder.http1_only();
        }

        // Configure proxy (apply default proxy if available)
        if let Some(default_proxy) = &proxy_system.default_proxy {
            let reqwest_proxy = default_proxy.to_reqwest_proxy()
                .map_err(|e| RequestError::new_err(format!("Invalid proxy configuration: {}", e)))?;
            builder = builder.proxy(reqwest_proxy);
        }

        builder.build()
            .map_err(|e| RequestError::new_err(format!("Failed to create client: {}", e)))
    }

    pub fn build_client(&self, custom_verify: Option<&PyAny>) -> PyResult<Client> {
        let mut builder = Client::builder();

        // Use custom SSL config if provided, otherwise use the instance's SSL config
        let ssl_config = if let Some(verify) = custom_verify {
            SslConfig::from_python_params(Some(verify), None, Some(self.ssl_config.trust_env))?
        } else {
            self.ssl_config.clone()
        };

        // Apply SSL configuration
        builder = ssl_config.apply_to_client_builder(builder)
            .map_err(|e| RequestError::new_err(format!("SSL configuration error: {}", e)))?;

        // Configure HTTP version
        if !self.http2 {
            builder = builder.http1_only();
        }

        // Configure proxy (apply default proxy if available)
        if let Some(default_proxy) = &self.proxy_system.default_proxy {
            let reqwest_proxy = default_proxy.to_reqwest_proxy()
                .map_err(|e| RequestError::new_err(format!("Invalid proxy configuration: {}", e)))?;
            builder = builder.proxy(reqwest_proxy);
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