use crate::auth::{extract_auth_from_object, AuthType};
use crate::utils::hooks::EventHooks;
use crate::client::hyper_client::{HyperHttpClient, HyperClientConfig};
use crate::config::proxy_config_stub::ProxySystem;
use crate::config::ssl_config_stub::SslConfig;
use crate::stubs::transport_stub::TransportConfig;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Duration;

// Core client configuration
#[derive(Clone)]
pub struct ClientConfig {
    pub base_url: Option<String>,
    pub default_timeout: Option<Duration>,
    pub default_headers: HashMap<String, String>,
    pub follow_redirects: bool,
    pub auth: Option<AuthType>,
    pub auth_object: Option<PyObject>, // Store original auth object for httpx compatibility
    pub proxy_system: ProxySystem,     // Proxy configuration management
    pub default_cookies: HashMap<String, String>,
    pub cookie_jar: Arc<Mutex<HashMap<String, String>>>, // Dynamic cookie jar for session management
    pub http1: bool,
    pub http2: bool,
    pub event_hooks: Arc<Mutex<EventHooks>>, // Event hooks for request/response logging
    pub ssl_config: SslConfig,               // SSL/TLS configuration
    pub transport_config: TransportConfig,   // Custom transport configuration
    pub limits: Option<crate::models::HttpLimits>, // Connection pool limits
    pub max_redirects: i32,                  // Maximum number of redirects to follow
    pub default_encoding: String,            // Default character encoding
    pub default_params: HashMap<String, PyObject>, // Default query parameters
    // Pre-built clients to support redirect control
    pub redirect_client: HyperHttpClient,
    pub no_redirect_client: HyperHttpClient,
}

/// Configuration validation errors
#[derive(Debug, Clone)]
pub enum ConfigValidationError {
    InvalidTimeout(String),
    InvalidUrl(String),
    InvalidRedirectCount(String),
    InvalidHeaders(String),
    InvalidAuth(String),
    InvalidProxy(String),
    SecurityViolation(String),
    ResourceLimitExceeded(String),
}

impl std::fmt::Display for ConfigValidationError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ConfigValidationError::InvalidTimeout(msg) => write!(f, "Invalid timeout: {}", msg),
            ConfigValidationError::InvalidUrl(msg) => write!(f, "Invalid URL: {}", msg),
            ConfigValidationError::InvalidRedirectCount(msg) => write!(f, "Invalid redirect count: {}", msg),
            ConfigValidationError::InvalidHeaders(msg) => write!(f, "Invalid headers: {}", msg),
            ConfigValidationError::InvalidAuth(msg) => write!(f, "Invalid authentication: {}", msg),
            ConfigValidationError::InvalidProxy(msg) => write!(f, "Invalid proxy: {}", msg),
            ConfigValidationError::SecurityViolation(msg) => write!(f, "Security violation: {}", msg),
            ConfigValidationError::ResourceLimitExceeded(msg) => write!(f, "Resource limit exceeded: {}", msg),
        }
    }
}

impl std::error::Error for ConfigValidationError {}

impl ClientConfig {
    /// Validate the configuration for security and correctness
    pub fn validate(&self) -> Result<(), Vec<ConfigValidationError>> {
        let mut errors = Vec::new();
        
        // Validate timeout settings
        if let Some(timeout) = self.default_timeout {
            if timeout.as_secs() == 0 && timeout.subsec_millis() < 100 {
                errors.push(ConfigValidationError::InvalidTimeout(
                    "Timeout must be at least 100ms to prevent connection failures".to_string()
                ));
            }
            if timeout.as_secs() > 3600 {
                errors.push(ConfigValidationError::InvalidTimeout(
                    "Timeout exceeds 1 hour, which may cause resource exhaustion".to_string()
                ));
            }
        }
        
        // Validate base URL if present
        if let Some(ref base_url) = self.base_url {
            if base_url.is_empty() {
                errors.push(ConfigValidationError::InvalidUrl(
                    "Base URL cannot be empty".to_string()
                ));
            } else if !base_url.starts_with("http://") && !base_url.starts_with("https://") {
                errors.push(ConfigValidationError::InvalidUrl(
                    "Base URL must start with http:// or https://".to_string()
                ));
            }
        }
        
        // Validate redirect count
        if self.max_redirects < 0 {
            errors.push(ConfigValidationError::InvalidRedirectCount(
                "Maximum redirects cannot be negative".to_string()
            ));
        } else if self.max_redirects > 50 {
            errors.push(ConfigValidationError::InvalidRedirectCount(
                "Maximum redirects exceeds safe limit of 50".to_string()
            ));
        }
        
        // Validate headers for security issues
        for (key, value) in &self.default_headers {
            if key.is_empty() {
                errors.push(ConfigValidationError::InvalidHeaders(
                    "Header name cannot be empty".to_string()
                ));
            }
            if value.len() > 8192 {
                errors.push(ConfigValidationError::InvalidHeaders(
                    format!("Header '{}' value exceeds 8KB limit", key)
                ));
            }
            // Check for potentially dangerous headers
            let key_lower = key.to_lowercase();
            if key_lower == "host" {
                errors.push(ConfigValidationError::SecurityViolation(
                    "Host header should not be set manually to prevent request smuggling".to_string()
                ));
            }
        }
        
        // Validate encoding
        if self.default_encoding.is_empty() {
            errors.push(ConfigValidationError::InvalidHeaders(
                "Default encoding cannot be empty".to_string()
            ));
        }
        
        // Security checks
        if self.http1 && self.http2 {
            // This is actually valid, both can be enabled
        } else if !self.http1 && !self.http2 {
            errors.push(ConfigValidationError::SecurityViolation(
                "At least one HTTP version must be enabled".to_string()
            ));
        }
        
        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }
    
    /// Apply security hardening to the configuration
    pub fn apply_security_hardening(&mut self) {
        // Set secure defaults
        if self.max_redirects > 20 {
            self.max_redirects = 20;  // Reduce to safe default
        }
        
        // Remove potentially dangerous default headers
        self.default_headers.retain(|key, _| {
            let key_lower = key.to_lowercase();
            !matches!(key_lower.as_str(), "host" | "content-length" | "transfer-encoding")
        });
        
        // Ensure reasonable timeout
        if self.default_timeout.is_none_or(|t| t.as_secs() > 300) {
            self.default_timeout = Some(Duration::from_secs(300));  // 5 minute max
        }
        if self.default_timeout.is_some_and(|t| t.as_millis() < 100) {
            self.default_timeout = Some(Duration::from_millis(1000));  // 1 second min
        }
    }
    
    /// Get configuration summary for debugging
    pub fn get_config_summary(&self) -> HashMap<String, String> {
        let mut summary = HashMap::new();
        
        summary.insert("base_url".to_string(), 
                      self.base_url.as_deref().unwrap_or("None").to_string());
        summary.insert("timeout_seconds".to_string(), 
                      self.default_timeout.map_or("None".to_string(), |t| t.as_secs().to_string()));
        summary.insert("follow_redirects".to_string(), self.follow_redirects.to_string());
        summary.insert("max_redirects".to_string(), self.max_redirects.to_string());
        summary.insert("http1_enabled".to_string(), self.http1.to_string());
        summary.insert("http2_enabled".to_string(), self.http2.to_string());
        summary.insert("default_headers_count".to_string(), self.default_headers.len().to_string());
        summary.insert("default_cookies_count".to_string(), self.default_cookies.len().to_string());
        summary.insert("default_params_count".to_string(), self.default_params.len().to_string());
        summary.insert("default_encoding".to_string(), self.default_encoding.clone());
        
        summary
    }
    
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        base_url: Option<String>,
        timeout: Option<PyObject>, // Accept either f64 or Timeout object
        headers: Option<HashMap<String, String>>,
        verify: Option<&PyAny>,
        follow_redirects: Option<bool>,
        auth: Option<PyObject>, // Accept either tuple or auth object
        proxy: Option<&PyAny>,  // Single proxy URL
        proxies: Option<&pyo3::types::PyDict>, // Proxy mapping dict
        cookies: Option<HashMap<String, String>>,
        http1: Option<bool>,
        http2: Option<bool>,
        event_hooks: Option<PyObject>,           // Event hooks dict
        cert: Option<&PyAny>,                    // Client certificate configuration
        trust_env: Option<bool>,                 // Trust environment variables for SSL
        transport: Option<PyObject>,             // Custom transport
        mounts: Option<&pyo3::types::PyDict>,    // Transport mounts
        limits: Option<PyObject>,                // Connection pool limits
        max_redirects: Option<i32>,              // Maximum number of redirects
        default_encoding: Option<String>,        // Default character encoding
        params: Option<HashMap<String, PyObject>>, // Default query parameters
    ) -> PyResult<Self> {
        let (auth_type, auth_object) = if let Some(auth_obj) = auth {
            Python::with_gil(|py| -> PyResult<(Option<AuthType>, Option<PyObject>)> {
                // Try to extract as auth object first
                if let Ok(Some(auth_type)) = extract_auth_from_object(&auth_obj) {
                    return Ok((Some(auth_type), Some(auth_obj.clone())));
                }

                // Fallback to tuple format for backward compatibility
                if let Ok((username, password)) = auth_obj.extract::<(String, String)>(py) {
                    return Ok((
                        Some(AuthType::Basic { username, password }),
                        Some(auth_obj.clone()),
                    ));
                }

                Ok((None, None))
            })?
        } else {
            (None, None)
        };

        // Handle timeout parameter - accept either f64 or Timeout object
        let timeout_value = if let Some(timeout_obj) = timeout {
            Python::with_gil(|py| -> PyResult<Option<f64>> {
                // Try to extract as f64 first (simple numeric timeout)
                if let Ok(timeout_num) = timeout_obj.extract::<f64>(py) {
                    return Ok(Some(timeout_num));
                }

                // Try to extract as HttpTimeout object
                if let Ok(timeout_instance) = timeout_obj.extract::<crate::models::HttpTimeout>(py)
                {
                    // Use read timeout as default timeout for the client
                    return Ok(Some(timeout_instance.get_read_timeout()));
                }

                Ok(None)
            })?
        } else {
            None
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

        // Parse limits configuration
        let limits_config = if let Some(limits_obj) = limits {
            Python::with_gil(|py| -> PyResult<Option<crate::models::HttpLimits>> {
                if let Ok(limits) = limits_obj.extract::<crate::models::HttpLimits>(py) {
                    Ok(Some(limits))
                } else {
                    Ok(None)
                }
            })?
        } else {
            None
        };

        // Process HTTP version parameters - default to HTTP/1.1 for localhost compatibility
        let http1_enabled = http1.unwrap_or(true);
        let http2_enabled = http2.unwrap_or(false);

        // Pre-build two clients to support redirect control
        let redirect_client = Self::build_hyper_client_with_redirect(
            true,
            http1_enabled,
            http2_enabled,
            max_redirects,
            timeout_value,
        )?;
        let no_redirect_client = Self::build_hyper_client_with_redirect(
            false,
            http1_enabled,
            http2_enabled,
            max_redirects,
            timeout_value,
        )?;

        Ok(ClientConfig {
            base_url,
            default_timeout: timeout_value
                .and_then(|t| {
                    if t >= 0.0 {
                        Some(Duration::from_secs_f64(t))
                    } else {
                        None
                    }
                })
                .or(Some(Duration::from_secs(30))), // Set default 30-second timeout, negative values are ignored
            default_headers: headers.unwrap_or_default(),
            follow_redirects: follow_redirects.unwrap_or(true),
            auth: auth_type,
            auth_object,
            proxy_system,
            default_cookies: cookies.unwrap_or_default(),
            cookie_jar: Arc::new(Mutex::new(HashMap::new())), // Initialize empty cookie jar
            http1: http1_enabled,
            http2: http2_enabled,
            event_hooks: Arc::new(Mutex::new(hooks)),
            ssl_config,
            transport_config,
            limits: limits_config,
            max_redirects: max_redirects.unwrap_or(21), // Allow 20 redirects to complete
            default_encoding: default_encoding.unwrap_or_else(|| "utf-8".to_string()),
            default_params: params.unwrap_or_default(),
            redirect_client,
            no_redirect_client,
        })
    }

    fn build_hyper_client_with_redirect(
        follow_redirects: bool,
        http1: bool,
        http2: bool,
        max_redirects: Option<i32>,
        timeout: Option<f64>,
    ) -> PyResult<HyperHttpClient> {
        let timeout_duration = timeout
            .and_then(|t| {
                if t >= 0.0 {
                    Some(Duration::from_secs_f64(t))
                } else {
                    None
                }
            })
            .or(Some(Duration::from_secs(5))); // Shorter timeout for debugging

        let config = HyperClientConfig {
            follow_redirects,
            max_redirects: max_redirects.unwrap_or(20) as usize,
            timeout: timeout_duration,
            http1_only: http1 && !http2,
            http2_only: http2 && !http1,
        };

        HyperHttpClient::new(config)
    }

    pub fn build_client(&self, _custom_verify: Option<&PyAny>) -> PyResult<HyperHttpClient> {
        let config = HyperClientConfig {
            follow_redirects: self.follow_redirects,
            max_redirects: self.max_redirects as usize,
            timeout: self.default_timeout,
            http1_only: self.http1 && !self.http2,
            http2_only: self.http2 && !self.http1,
        };

        HyperHttpClient::new(config)
    }

    // Select appropriate client based on follow_redirects parameter
    pub fn get_client_for_redirect(&self, follow_redirects: bool) -> &HyperHttpClient {
        if follow_redirects {
            &self.redirect_client
        } else {
            &self.no_redirect_client
        }
    }
}
