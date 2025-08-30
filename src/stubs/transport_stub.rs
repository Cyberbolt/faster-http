// Transport configuration for faster-http using hyper
use pyo3::prelude::*;
use std::collections::HashMap;
use std::time::Duration;

/// Transport configuration for HTTP connections
#[derive(Clone, Debug)]
pub struct TransportConfig {
    /// Connection limits and pooling settings
    pub limits: ConnectionLimits,
    /// Timeout settings
    pub timeouts: TimeoutSettings,
    /// HTTP version preferences
    pub http_version: HttpVersionConfig,
    /// Keep-alive settings
    pub keep_alive: KeepAliveConfig,
    /// Protocol-specific mounts (scheme -> custom transport)
    pub mounts: HashMap<String, MountConfig>,
    /// Whether to enable connection pooling
    pub enable_pooling: bool,
    /// Socket options
    pub socket_options: SocketOptions,
}

/// Connection limits and pooling configuration
#[derive(Clone, Debug)]
pub struct ConnectionLimits {
    /// Maximum number of connections per host
    pub max_connections_per_host: usize,
    /// Maximum total connections across all hosts
    pub max_total_connections: usize,
    /// Maximum number of idle connections to keep alive
    pub max_idle_connections: usize,
    /// Maximum time to keep idle connections alive
    pub max_idle_time: Duration,
}

/// Timeout configuration for various operations
#[derive(Clone, Debug)]
pub struct TimeoutSettings {
    /// Connection establishment timeout
    pub connect_timeout: Option<Duration>,
    /// Read timeout for receiving data
    pub read_timeout: Option<Duration>,
    /// Write timeout for sending data  
    pub write_timeout: Option<Duration>,
    /// Total request timeout (entire operation)
    pub total_timeout: Option<Duration>,
    /// Pool timeout for getting connection from pool
    pub pool_timeout: Option<Duration>,
}

/// HTTP version preferences
#[derive(Clone, Debug)]
pub struct HttpVersionConfig {
    /// Force HTTP/1.1 only
    pub http1_only: bool,
    /// Force HTTP/2 only
    pub http2_only: bool,
    /// Enable HTTP/2 with prior knowledge
    pub http2_prior_knowledge: bool,
    /// Maximum HTTP/2 concurrent streams
    pub http2_max_concurrent_streams: Option<u32>,
}

/// Keep-alive configuration
#[derive(Clone, Debug)]
pub struct KeepAliveConfig {
    /// Enable keep-alive connections
    pub enabled: bool,
    /// Idle timeout before closing keep-alive connections
    pub idle_timeout: Duration,
    /// Interval between keep-alive probes
    pub probe_interval: Duration,
    /// Number of keep-alive probes before giving up
    pub max_probes: u8,
}

/// Mount configuration for custom transports per scheme
#[derive(Clone, Debug)]
pub struct MountConfig {
    /// Base URL pattern to match
    pub pattern: String,
    /// Custom transport type (placeholder for future expansion)
    pub transport_type: TransportType,
}

/// Transport type enumeration
#[derive(Clone, Debug)]
pub enum TransportType {
    /// Standard HTTP transport
    Http,
    /// Mock transport for testing
    Mock,
    /// Custom transport (placeholder)
    Custom(String),
}

/// Socket-level configuration options
#[derive(Clone, Debug)]
pub struct SocketOptions {
    /// TCP no-delay (Nagle algorithm)
    pub tcp_nodelay: bool,
    /// Socket keep-alive
    pub so_keepalive: bool,
    /// Send buffer size
    pub send_buffer_size: Option<usize>,
    /// Receive buffer size
    pub recv_buffer_size: Option<usize>,
    /// Local interface to bind to
    pub local_address: Option<String>,
}

impl Default for TransportConfig {
    fn default() -> Self {
        Self {
            limits: ConnectionLimits::default(),
            timeouts: TimeoutSettings::default(),
            http_version: HttpVersionConfig::default(),
            keep_alive: KeepAliveConfig::default(),
            mounts: HashMap::new(),
            enable_pooling: true,
            socket_options: SocketOptions::default(),
        }
    }
}

impl Default for ConnectionLimits {
    fn default() -> Self {
        Self {
            max_connections_per_host: 10,
            max_total_connections: 100,
            max_idle_connections: 20,
            max_idle_time: Duration::from_secs(90),
        }
    }
}

impl Default for TimeoutSettings {
    fn default() -> Self {
        Self {
            connect_timeout: Some(Duration::from_secs(5)),
            read_timeout: Some(Duration::from_secs(30)),
            write_timeout: Some(Duration::from_secs(30)),
            total_timeout: Some(Duration::from_secs(120)),
            pool_timeout: Some(Duration::from_secs(5)),
        }
    }
}

impl Default for HttpVersionConfig {
    fn default() -> Self {
        Self {
            http1_only: false,
            http2_only: false,
            http2_prior_knowledge: false,
            http2_max_concurrent_streams: Some(100),
        }
    }
}

impl Default for KeepAliveConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            idle_timeout: Duration::from_secs(90),
            probe_interval: Duration::from_secs(30),
            max_probes: 3,
        }
    }
}

impl Default for SocketOptions {
    fn default() -> Self {
        Self {
            tcp_nodelay: true,
            so_keepalive: true,
            send_buffer_size: None,
            recv_buffer_size: None,
            local_address: None,
        }
    }
}

impl TransportConfig {
    /// Create transport config from Python httpx-compatible parameters
    pub fn from_python_params(
        transport: Option<PyObject>,
        mounts: Option<&pyo3::types::PyDict>,
    ) -> PyResult<Self> {
        let mut config = Self::default();

        // Handle transport parameter (if it's a custom transport object)
        if let Some(_transport_obj) = transport {
            // For now, we'll just use default config
            // In the future, we could extract configuration from custom transport objects
        }

        // Handle mounts dictionary
        if let Some(mounts_dict) = mounts {
            config.parse_mounts(mounts_dict)?;
        }

        Ok(config)
    }

    /// Parse mounts dictionary from Python
    fn parse_mounts(&mut self, mounts_dict: &pyo3::types::PyDict) -> PyResult<()> {
        use pyo3::types::PyString;

        for item in mounts_dict.items() {
            let tuple = item.downcast::<pyo3::types::PyTuple>()?;
            let pattern = tuple.get_item(0)?;
            let _transport = tuple.get_item(1)?;

            let pattern_str = pattern.downcast::<PyString>()?.to_str()?;

            // For now, we'll treat all mounts as HTTP transports
            // In the future, we could inspect the transport object to determine type
            let mount_config = MountConfig {
                pattern: pattern_str.to_string(),
                transport_type: TransportType::Http,
            };

            self.mounts.insert(pattern_str.to_string(), mount_config);
        }

        Ok(())
    }

    /// Apply timeout settings from httpx-style parameters
    pub fn with_timeouts(
        mut self,
        connect: Option<f64>,
        read: Option<f64>,
        write: Option<f64>,
        pool: Option<f64>,
    ) -> Self {
        if let Some(connect_timeout) = connect {
            self.timeouts.connect_timeout = Some(Duration::from_secs_f64(connect_timeout));
        }
        if let Some(read_timeout) = read {
            self.timeouts.read_timeout = Some(Duration::from_secs_f64(read_timeout));
        }
        if let Some(write_timeout) = write {
            self.timeouts.write_timeout = Some(Duration::from_secs_f64(write_timeout));
        }
        if let Some(pool_timeout) = pool {
            self.timeouts.pool_timeout = Some(Duration::from_secs_f64(pool_timeout));
        }
        self
    }

    /// Configure connection limits
    pub fn with_limits(
        mut self,
        max_connections: Option<usize>,
        max_keepalive_connections: Option<usize>,
    ) -> Self {
        if let Some(max_conn) = max_connections {
            self.limits.max_total_connections = max_conn;
            self.limits.max_connections_per_host = (max_conn / 10).max(1);
        }
        if let Some(max_keepalive) = max_keepalive_connections {
            self.limits.max_idle_connections = max_keepalive;
        }
        self
    }

    /// Configure HTTP version preferences
    pub fn with_http_version(
        mut self,
        http1_only: bool,
        http2_only: bool,
        http2_prior_knowledge: bool,
    ) -> Self {
        self.http_version.http1_only = http1_only;
        self.http_version.http2_only = http2_only;
        self.http_version.http2_prior_knowledge = http2_prior_knowledge;
        self
    }

    /// Get mount configuration for a URL pattern
    pub fn get_mount_for_url(&self, url: &str) -> Option<&MountConfig> {
        // Find the most specific mount pattern that matches
        let mut best_match: Option<&MountConfig> = None;
        let mut best_match_len = 0;

        for (pattern, config) in &self.mounts {
            if url.starts_with(pattern) && pattern.len() > best_match_len {
                best_match = Some(config);
                best_match_len = pattern.len();
            }
        }

        best_match
    }

    /// Check if connection pooling is enabled
    pub fn is_pooling_enabled(&self) -> bool {
        self.enable_pooling
    }

    /// Get connection limits
    pub fn limits(&self) -> &ConnectionLimits {
        &self.limits
    }

    /// Get timeout settings
    pub fn timeouts(&self) -> &TimeoutSettings {
        &self.timeouts
    }

    /// Get HTTP version config
    pub fn http_version(&self) -> &HttpVersionConfig {
        &self.http_version
    }

    /// Get keep-alive config
    pub fn keep_alive(&self) -> &KeepAliveConfig {
        &self.keep_alive
    }

    /// Get socket options
    pub fn socket_options(&self) -> &SocketOptions {
        &self.socket_options
    }

    /// Validate transport configuration
    pub fn validate(&self) -> PyResult<()> {
        // Check for conflicting HTTP version settings
        if self.http_version.http1_only && self.http_version.http2_only {
            return Err(crate::core::error::create_request_error(
                "Cannot set both http1_only and http2_only to true",
            ));
        }

        // Validate timeout values
        if let Some(connect_timeout) = self.timeouts.connect_timeout {
            if connect_timeout.as_secs() == 0 {
                return Err(crate::core::error::create_request_error(
                    "Connect timeout must be greater than 0",
                ));
            }
        }

        // Validate connection limits
        if self.limits.max_connections_per_host > self.limits.max_total_connections {
            return Err(crate::core::error::create_request_error(
                "max_connections_per_host cannot exceed max_total_connections",
            ));
        }

        Ok(())
    }
}

impl TimeoutSettings {
    /// Get the effective connect timeout
    pub fn effective_connect_timeout(&self) -> Duration {
        self.connect_timeout.unwrap_or(Duration::from_secs(5))
    }

    /// Get the effective read timeout  
    pub fn effective_read_timeout(&self) -> Duration {
        self.read_timeout.unwrap_or(Duration::from_secs(30))
    }

    /// Get the effective write timeout
    pub fn effective_write_timeout(&self) -> Duration {
        self.write_timeout.unwrap_or(Duration::from_secs(30))
    }

    /// Get the effective total timeout
    pub fn effective_total_timeout(&self) -> Duration {
        self.total_timeout.unwrap_or(Duration::from_secs(120))
    }

    /// Get the effective pool timeout
    pub fn effective_pool_timeout(&self) -> Duration {
        self.pool_timeout.unwrap_or(Duration::from_secs(5))
    }
}

impl MountConfig {
    /// Get the URL pattern this mount matches
    pub fn pattern(&self) -> &str {
        &self.pattern
    }

    /// Get the transport type
    pub fn transport_type(&self) -> &TransportType {
        &self.transport_type
    }
}

impl TransportType {
    /// Check if this is a standard HTTP transport
    pub fn is_http(&self) -> bool {
        matches!(self, TransportType::Http)
    }

    /// Check if this is a mock transport
    pub fn is_mock(&self) -> bool {
        matches!(self, TransportType::Mock)
    }

    /// Get custom transport name if applicable
    pub fn custom_name(&self) -> Option<&str> {
        match self {
            TransportType::Custom(name) => Some(name),
            _ => None,
        }
    }
}
