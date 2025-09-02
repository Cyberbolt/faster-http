// SSL configuration for faster-http using rustls
use pyo3::prelude::*;
use std::path::{Path, PathBuf};

/// SSL configuration for HTTPS connections
#[derive(Clone, Debug)]
pub struct SslConfig {
    /// Whether to verify SSL certificates
    pub verify: bool,
    /// Custom CA certificate file path
    pub ca_cert_file: Option<PathBuf>,
    /// Client certificate for mutual TLS
    pub client_cert: Option<ClientCert>,
    /// Whether to trust environment CA bundle
    pub trust_env: bool,
}

/// Client certificate configuration for mutual TLS
#[derive(Clone)]
pub struct ClientCert {
    /// Certificate file path
    pub cert_file: PathBuf,
    /// Private key file path
    pub key_file: PathBuf,
    /// Optional password for encrypted private key
    pub password: Option<String>,
}

// SECURITY: Custom Debug implementation to prevent password leakage
impl std::fmt::Debug for ClientCert {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ClientCert")
            .field("cert_file", &self.cert_file)
            .field("key_file", &self.key_file)
            .field("password", &self.password.as_ref().map(|_| "***REDACTED***"))
            .finish()
    }
}

impl Default for SslConfig {
    fn default() -> Self {
        Self {
            verify: true,
            ca_cert_file: None,
            client_cert: None,
            trust_env: true,
        }
    }
}

impl SslConfig {
    /// Create SSL config from Python httpx-compatible parameters
    pub fn from_python_params(
        verify: Option<&PyAny>,
        cert: Option<&PyAny>,
        trust_env: Option<bool>,
    ) -> PyResult<Self> {
        use pyo3::types::{PyBool, PyString, PyTuple};

        let mut config = Self::default();

        // Handle verify parameter (bool or str path to CA file)
        if let Some(verify_param) = verify {
            if let Ok(verify_bool) = verify_param.downcast::<PyBool>() {
                config.verify = verify_bool.is_true();
            } else if let Ok(verify_str) = verify_param.downcast::<PyString>() {
                config.verify = true;
                let ca_path = verify_str.to_str()?;
                config.ca_cert_file = Some(PathBuf::from(ca_path));
            } else {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "verify must be bool or str path to CA file",
                ));
            }
        }

        // Handle cert parameter (tuple of (cert_file, key_file) or (cert_file, key_file, password))
        if let Some(cert_param) = cert {
            if let Ok(cert_tuple) = cert_param.downcast::<PyTuple>() {
                let tuple_len = cert_tuple.len();
                if tuple_len >= 2 {
                    let cert_file = cert_tuple.get_item(0)?.downcast::<PyString>()?.to_str()?;
                    let key_file = cert_tuple.get_item(1)?.downcast::<PyString>()?.to_str()?;

                    let password = if tuple_len >= 3 {
                        let password_obj = cert_tuple.get_item(2)?;
                        if password_obj.is_none() {
                            None
                        } else {
                            Some(password_obj.downcast::<PyString>()?.to_str()?.to_string())
                        }
                    } else {
                        None
                    };

                    config.client_cert = Some(ClientCert {
                        cert_file: PathBuf::from(cert_file),
                        key_file: PathBuf::from(key_file),
                        password,
                    });
                } else {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "cert must be tuple of (cert_file, key_file) or (cert_file, key_file, password)"
                    ));
                }
            } else {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "cert must be tuple of certificate and key files",
                ));
            }
        }

        // Handle trust_env parameter
        if let Some(trust_env_param) = trust_env {
            config.trust_env = trust_env_param;
        }

        Ok(config)
    }

    /// Load CA bundle from environment variables if trust_env is enabled
    pub fn load_ca_bundle_from_env(&mut self) {
        if !self.trust_env {
            return;
        }

        // Check common environment variables for CA bundle
        let env_vars = [
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
            "REQUESTS_CA_BUNDLE",
            "CURL_CA_BUNDLE",
        ];

        for env_var in &env_vars {
            if let Ok(ca_path) = std::env::var(env_var) {
                let path = PathBuf::from(ca_path);
                if path.exists() {
                    self.ca_cert_file = Some(path);
                    break;
                }
            }
        }
    }

    /// Validate SSL configuration
    pub fn validate(&self) -> PyResult<()> {
        // Check if CA cert file exists when specified
        if let Some(ref ca_file) = self.ca_cert_file {
            if !ca_file.exists() {
                return Err(crate::core::error::create_ssl_error(&format!(
                    "CA certificate file not found: {}",
                    ca_file.display()
                )));
            }
        }

        // Check client certificate files when specified
        if let Some(ref client_cert) = self.client_cert {
            if !client_cert.cert_file.exists() {
                return Err(crate::core::error::create_ssl_error(&format!(
                    "Client certificate file not found: {}",
                    client_cert.cert_file.display()
                )));
            }
            if !client_cert.key_file.exists() {
                return Err(crate::core::error::create_ssl_error(&format!(
                    "Client private key file not found: {}",
                    client_cert.key_file.display()
                )));
            }
        }

        Ok(())
    }

    /// Check if SSL verification is enabled
    pub fn should_verify(&self) -> bool {
        self.verify
    }

    /// Get custom CA certificate file if any
    pub fn ca_cert_file(&self) -> Option<&Path> {
        self.ca_cert_file.as_deref()
    }

    /// Get client certificate configuration if any
    pub fn client_cert(&self) -> Option<&ClientCert> {
        self.client_cert.as_ref()
    }
}

impl ClientCert {
    /// Get certificate file path
    pub fn cert_file(&self) -> &Path {
        &self.cert_file
    }

    /// Get private key file path
    pub fn key_file(&self) -> &Path {
        &self.key_file
    }

    /// Get password for encrypted private key
    pub fn password(&self) -> Option<&str> {
        self.password.as_deref()
    }
}
