// Proxy configuration for faster-http using hyper
use pyo3::prelude::*;
use std::collections::HashMap;
use url::Url;

/// Proxy configuration system for HTTP/HTTPS connections
#[derive(Clone, Debug)]
pub struct ProxySystem {
    /// Proxy configurations per scheme
    proxies: HashMap<String, ProxyConfig>,
    /// Whether to trust environment proxy settings
    trust_env: bool,
    /// Default proxy to use if no scheme-specific proxy is found
    default_proxy: Option<ProxyConfig>,
}

/// Individual proxy configuration
#[derive(Clone, Debug)]
pub struct ProxyConfig {
    /// Proxy URL (http:// or https://)
    pub url: Url,
    /// Optional authentication
    pub auth: Option<ProxyAuth>,
    /// Headers to send to the proxy
    pub headers: HashMap<String, String>,
}

/// Proxy authentication credentials
#[derive(Clone, Debug)]
pub struct ProxyAuth {
    /// Username
    pub username: String,
    /// Password
    pub password: String,
}

impl Default for ProxySystem {
    fn default() -> Self {
        Self {
            proxies: HashMap::new(),
            trust_env: true,
            default_proxy: None,
        }
    }
}

impl ProxySystem {
    /// Create proxy system from Python httpx-compatible parameters
    pub fn from_python_params(
        proxy: Option<&PyAny>,
        proxies: Option<&pyo3::types::PyDict>, 
        trust_env: Option<bool>
    ) -> PyResult<Self> {
        use pyo3::types::PyString;
        
        let mut system = Self::default();
        
        // Handle trust_env parameter
        if let Some(trust_env_param) = trust_env {
            system.trust_env = trust_env_param;
        }
        
        // Handle single proxy parameter
        if let Some(proxy_param) = proxy {
            let proxy_config = Self::parse_proxy_param(proxy_param)?;
            system.default_proxy = Some(proxy_config);
        }
        
        // Handle proxies dict parameter (overrides single proxy)
        if let Some(proxies_dict) = proxies {
            for item in proxies_dict.items() {
                let tuple = item.downcast::<pyo3::types::PyTuple>()?;
                let scheme = tuple.get_item(0)?;
                let proxy_url = tuple.get_item(1)?;
                
                let scheme_str = scheme.downcast::<PyString>()?.to_str()?;
                let proxy_config = Self::parse_proxy_param(proxy_url)?;
                system.proxies.insert(scheme_str.to_lowercase(), proxy_config);
            }
        }
        
        // Load proxy settings from environment if enabled
        if system.trust_env {
            system.load_from_env()?;
        }
        
        Ok(system)
    }
    
    /// Parse a proxy parameter (string URL or dict with url/auth)
    fn parse_proxy_param(proxy_param: &PyAny) -> PyResult<ProxyConfig> {
        use pyo3::types::{PyDict, PyString, PyTuple};
        
        if let Ok(proxy_str) = proxy_param.downcast::<PyString>() {
            // Simple string URL
            let url_str = proxy_str.to_str()?;
            let url = Url::parse(url_str).map_err(|e| {
                pyo3::exceptions::PyValueError::new_err(format!("Invalid proxy URL: {}", e))
            })?;
            
            let auth = Self::extract_auth_from_url(&url);
            
            Ok(ProxyConfig {
                url,
                auth,
                headers: HashMap::new(),
            })
        } else if let Ok(proxy_dict) = proxy_param.downcast::<PyDict>() {
            // Dictionary with url and optional auth
            let url_item = proxy_dict.get_item("url")?
                .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("proxy dict must contain 'url' key"))?;
            let url_str = url_item.downcast::<PyString>()?.to_str()?;
            let url = Url::parse(url_str).map_err(|e| {
                pyo3::exceptions::PyValueError::new_err(format!("Invalid proxy URL: {}", e))
            })?;
            
            // Check for explicit auth
            let mut auth = Self::extract_auth_from_url(&url);
            if let Ok(Some(auth_item)) = proxy_dict.get_item("auth") {
                if let Ok(auth_tuple) = auth_item.downcast::<PyTuple>() {
                    if auth_tuple.len() >= 2 {
                        let username = auth_tuple.get_item(0)?.downcast::<PyString>()?.to_str()?;
                        let password = auth_tuple.get_item(1)?.downcast::<PyString>()?.to_str()?;
                        auth = Some(ProxyAuth {
                            username: username.to_string(),
                            password: password.to_string(),
                        });
                    }
                }
            }
            
            // Check for headers
            let mut headers = HashMap::new();
            if let Ok(Some(headers_item)) = proxy_dict.get_item("headers") {
                if let Ok(headers_dict) = headers_item.downcast::<PyDict>() {
                    for item in headers_dict.items() {
                        let tuple = item.downcast::<pyo3::types::PyTuple>()?;
                        let key = tuple.get_item(0)?;
                        let value = tuple.get_item(1)?;
                        
                        let key_str = key.downcast::<PyString>()?.to_str()?;
                        let value_str = value.downcast::<PyString>()?.to_str()?;
                        headers.insert(key_str.to_string(), value_str.to_string());
                    }
                }
            }
            
            Ok(ProxyConfig {
                url,
                auth,
                headers,
            })
        } else {
            Err(pyo3::exceptions::PyTypeError::new_err(
                "proxy must be string URL or dict with 'url' key"
            ))
        }
    }
    
    /// Extract authentication from proxy URL
    fn extract_auth_from_url(url: &Url) -> Option<ProxyAuth> {
        if !url.username().is_empty() {
            Some(ProxyAuth {
                username: url.username().to_string(),
                password: url.password().unwrap_or("").to_string(),
            })
        } else {
            None
        }
    }
    
    /// Load proxy settings from environment variables
    fn load_from_env(&mut self) -> PyResult<()> {
        // Standard environment variables for proxies
        let env_vars = [
            ("http_proxy", "http"),
            ("HTTP_PROXY", "http"),
            ("https_proxy", "https"),
            ("HTTPS_PROXY", "https"),
            ("all_proxy", "all"),
            ("ALL_PROXY", "all"),
        ];
        
        for (env_var, scheme) in &env_vars {
            if let Ok(proxy_url) = std::env::var(env_var) {
                if !proxy_url.is_empty() {
                    match Url::parse(&proxy_url) {
                        Ok(url) => {
                            let auth = Self::extract_auth_from_url(&url);
                            let proxy_config = ProxyConfig {
                                url,
                                auth,
                                headers: HashMap::new(),
                            };
                            
                            if *scheme == "all" {
                                self.default_proxy = Some(proxy_config.clone());
                                // Also set for common schemes if not already set
                                for common_scheme in ["http", "https"] {
                                    self.proxies.entry(common_scheme.to_string())
                                        .or_insert(proxy_config.clone());
                                }
                            } else {
                                self.proxies.insert(scheme.to_string(), proxy_config);
                            }
                        }
                        Err(e) => {
                            // Log warning but don't fail - environment might have invalid proxy
                            eprintln!("Warning: Invalid proxy URL in {}: {}", env_var, e);
                        }
                    }
                }
            }
        }
        
        Ok(())
    }
    
    /// Get proxy configuration for a specific scheme
    pub fn get_proxy_for_scheme(&self, scheme: &str) -> Option<&ProxyConfig> {
        self.proxies.get(scheme).or(self.default_proxy.as_ref())
    }
    
    /// Get proxy configuration for a URL
    pub fn get_proxy_for_url(&self, url: &Url) -> Option<&ProxyConfig> {
        let scheme = url.scheme();
        self.get_proxy_for_scheme(scheme)
    }
    
    /// Check if proxy should be bypassed for a URL
    pub fn should_bypass_proxy(&self, url: &Url) -> bool {
        // Check NO_PROXY environment variable
        if let Ok(no_proxy) = std::env::var("NO_PROXY").or_else(|_| std::env::var("no_proxy")) {
            let host = url.host_str().unwrap_or("");
            
            for pattern in no_proxy.split(',') {
                let pattern = pattern.trim();
                if pattern.is_empty() {
                    continue;
                }
                
                if pattern == "*" || pattern == host {
                    return true;
                }
                
                // Check for domain matching (e.g., .example.com)
                if pattern.starts_with('.') && host.ends_with(pattern) {
                    return true;
                }
                
                // Check for suffix matching
                if host.ends_with(&format!(".{}", pattern)) {
                    return true;
                }
                
                // Check for localhost
                if host == "localhost" || host.starts_with("127.") || host == "::1" {
                    if pattern == "localhost" || pattern == "127.0.0.1" || pattern == "::1" {
                        return true;
                    }
                }
            }
        }
        
        false
    }
    
    /// Check if any proxy is configured
    pub fn has_proxy(&self) -> bool {
        !self.proxies.is_empty() || self.default_proxy.is_some()
    }
    
    /// Get all configured proxies
    pub fn get_all_proxies(&self) -> HashMap<String, &ProxyConfig> {
        let mut result = HashMap::new();
        
        for (scheme, config) in &self.proxies {
            result.insert(scheme.clone(), config);
        }
        
        if let Some(ref default) = self.default_proxy {
            result.insert("default".to_string(), default);
        }
        
        result
    }
}

impl ProxyConfig {
    /// Get the proxy URL
    pub fn url(&self) -> &Url {
        &self.url
    }
    
    /// Get proxy authentication if configured
    pub fn auth(&self) -> Option<&ProxyAuth> {
        self.auth.as_ref()
    }
    
    /// Get proxy headers
    pub fn headers(&self) -> &HashMap<String, String> {
        &self.headers
    }
    
    /// Check if this is an HTTP proxy (vs SOCKS)
    pub fn is_http_proxy(&self) -> bool {
        matches!(self.url.scheme(), "http" | "https")
    }
    
    /// Get proxy host and port for connection
    pub fn host_port(&self) -> (String, u16) {
        let host = self.url.host_str().unwrap_or("localhost").to_string();
        let port = self.url.port().unwrap_or_else(|| {
            match self.url.scheme() {
                "http" => 80,
                "https" => 443,
                _ => 8080,
            }
        });
        (host, port)
    }
}

impl ProxyAuth {
    /// Get username
    pub fn username(&self) -> &str {
        &self.username
    }
    
    /// Get password
    pub fn password(&self) -> &str {
        &self.password
    }
    
    /// Get basic auth header value
    pub fn basic_auth_header(&self) -> String {
        use base64::Engine;
        let credentials = format!("{}:{}", self.username, self.password);
        let encoded = base64::engine::general_purpose::STANDARD.encode(credentials.as_bytes());
        format!("Basic {}", encoded)
    }
}