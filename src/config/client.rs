use crate::auth::{extract_auth_from_object, AuthType};
use crate::client::hyper_client::{HyperClientConfig, HyperHttpClient};
use crate::config::proxy_config_stub::ProxySystem;
use crate::config::ssl_config_stub::SslConfig;
use crate::stubs::transport_stub::TransportConfig;
use crate::utils::hooks::EventHooks;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Duration;

/// Simplified client configuration - pure conversion layer
#[derive(Clone)]
pub struct ClientConfig {
    pub base_url: Option<String>,
    pub default_timeout: Option<Duration>,
    pub default_headers: HashMap<String, String>,
    pub follow_redirects: bool,
    pub auth: Option<AuthType>,
    pub auth_object: Option<PyObject>,
    pub proxy_system: ProxySystem,
    pub default_cookies: HashMap<String, String>,
    pub cookie_jar: Arc<Mutex<HashMap<String, String>>>,
    pub http1: bool,
    pub http2: bool,
    pub event_hooks: Arc<Mutex<EventHooks>>,
    pub ssl_config: SslConfig,
    pub transport_config: TransportConfig,
    pub limits: Option<crate::models::HttpLimits>,
    pub max_redirects: i32,
    pub default_encoding: String,
    pub default_params: HashMap<String, PyObject>,
    // Pre-built clients to support redirect control
    pub redirect_client: HyperHttpClient,
    pub no_redirect_client: HyperHttpClient,
}

impl ClientConfig {
    /// Simplified constructor - minimal validation
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        base_url: Option<String>,
        timeout: Option<PyObject>,
        headers: Option<HashMap<String, String>>,
        verify: Option<&PyAny>,
        follow_redirects: Option<bool>,
        auth: Option<PyObject>,
        _proxy: Option<&PyAny>,
        _proxies: Option<&pyo3::types::PyDict>,
        cookies: Option<HashMap<String, String>>,
        http1: Option<bool>,
        http2: Option<bool>,
        _event_hooks: Option<PyObject>,
        cert: Option<&PyAny>,
        trust_env: Option<bool>,
        _transport: Option<PyObject>,
        _mounts: Option<&pyo3::types::PyDict>,
        _limits: Option<PyObject>,
        max_redirects: Option<i32>,
        default_encoding: Option<String>,
        params: Option<HashMap<String, PyObject>>,
    ) -> PyResult<Self> {
        // Simple auth extraction - no complex validation
        let (auth_type, auth_object) = if let Some(auth_obj) = auth {
            let extracted =
                Python::with_gil(|_py| extract_auth_from_object(&auth_obj).unwrap_or(None));
            (extracted, Some(auth_obj))
        } else {
            (None, None)
        };

        // Simple timeout processing - back to original approach for performance
        let default_timeout = timeout
            .and_then(|t| Python::with_gil(|py| t.extract::<f64>(py).ok()))
            .map(Duration::from_secs_f64);

        // Create default configurations with minimal setup
        let default_headers = headers.unwrap_or_default();
        let follow_redirects = follow_redirects.unwrap_or(true);
        let default_cookies = cookies.unwrap_or_default();
        let cookie_jar = Arc::new(Mutex::new(HashMap::new()));
        let event_hooks = Arc::new(Mutex::new(EventHooks::default()));
        let default_params = params.unwrap_or_default();

        // Create simple hyper client configurations
        let redirect_config = HyperClientConfig {
            follow_redirects: true,
            timeout: default_timeout,
            ..Default::default()
        };

        let no_redirect_config = HyperClientConfig {
            follow_redirects: false,
            timeout: default_timeout,
            ..Default::default()
        };

        // Create hyper clients with connection pool prewarming for better performance
        let redirect_client = HyperHttpClient::new_with_warmup(redirect_config)?;
        let no_redirect_client = HyperHttpClient::new_with_warmup(no_redirect_config)?;

        Ok(Self {
            base_url,
            default_timeout,
            default_headers,
            follow_redirects,
            auth: auth_type,
            auth_object,
            proxy_system: ProxySystem::default(),
            default_cookies,
            cookie_jar,
            http1: http1.unwrap_or(false),
            http2: http2.unwrap_or(false),
            event_hooks,
            ssl_config: SslConfig::from_python_params(verify, cert, trust_env)?,
            transport_config: TransportConfig::default(),
            limits: None, // Simplified - no limits processing
            max_redirects: max_redirects.unwrap_or(20),
            default_encoding: default_encoding.unwrap_or_else(|| "utf-8".to_string()),
            default_params,
            redirect_client,
            no_redirect_client,
        })
    }

    /// Simplified merge headers - no complex validation
    pub fn merge_headers(
        &self,
        request_headers: Option<HashMap<String, String>>,
    ) -> HashMap<String, String> {
        let mut merged = self.default_headers.clone();
        if let Some(headers) = request_headers {
            merged.extend(headers);
        }
        merged
    }

    /// Simplified timeout resolution  
    pub fn effective_timeout(&self, request_timeout: Option<f64>) -> Option<Duration> {
        request_timeout
            .map(Duration::from_secs_f64)
            .or(self.default_timeout)
    }

    /// Simple timeout resolution with Python object support
    pub fn effective_timeout_from_python(
        &self,
        request_timeout: Option<PyObject>,
    ) -> PyResult<Option<Duration>> {
        match request_timeout {
            Some(timeout_obj) => {
                let timeout_secs = Python::with_gil(|py| timeout_obj.extract::<f64>(py))?;
                Ok(Some(Duration::from_secs_f64(timeout_secs)))
            }
            None => Ok(self.default_timeout),
        }
    }

    /// Simple base URL handling
    pub fn build_url(&self, path: &str) -> String {
        if let Some(base) = &self.base_url {
            if path.starts_with("http://") || path.starts_with("https://") {
                path.to_string()
            } else {
                format!(
                    "{}/{}",
                    base.trim_end_matches('/'),
                    path.trim_start_matches('/')
                )
            }
        } else {
            path.to_string()
        }
    }

    /// Create from environment - simplified stub
    pub fn from_environment() -> PyResult<Self> {
        Self::new(
            None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None,
        )
    }
}
