use crate::auth::{extract_auth_from_object, AuthType};
use crate::hooks::EventHooks;
use crate::hyper_client::{HyperHttpClient, HyperClientConfig};
use crate::proxy_config_stub::ProxySystem;
use crate::ssl_config_stub::SslConfig;
use crate::transport_stub::TransportConfig;
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
    pub proxy_system: ProxySystem,     // Advanced proxy configuration
    pub default_cookies: HashMap<String, String>,
    pub http1: bool,
    pub http2: bool,
    pub event_hooks: Arc<Mutex<EventHooks>>, // Event hooks for request/response logging
    pub ssl_config: SslConfig,               // SSL/TLS configuration
    pub transport_config: TransportConfig,   // Custom transport configuration
    pub limits: Option<crate::models::HttpLimits>, // Connection pool limits
    pub max_redirects: i32,                  // Maximum number of redirects to follow
    pub default_encoding: String,            // Default character encoding
    pub default_params: HashMap<String, PyObject>, // Default query parameters
    // Pre-built clients to support efficient redirect control
    pub redirect_client: HyperHttpClient,
    pub no_redirect_client: HyperHttpClient,
}

impl ClientConfig {
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

        // Process HTTP version parameters - default to HTTP/1.1 only for better localhost compatibility
        let http1_enabled = http1.unwrap_or(true);
        let http2_enabled = http2.unwrap_or(false);

        // Pre-build two clients to support efficient redirect control
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
