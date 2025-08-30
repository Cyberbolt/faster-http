// HTTP connection pool with connection reuse and Keep-Alive support
// Enables connection management for faster-http

use hyper::Uri;
use hyper_util::client::legacy::{Client, connect::HttpConnector};
// HTTPS support restored for HTTPS functionality
use hyper_rustls::HttpsConnector;
use http_body_util::Full;
use bytes::Bytes;
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};
use pyo3::prelude::*;
use crate::error::RequestError;
use hyper_util::rt::TokioExecutor;
// Removed unused imports

// Branch prediction hints for performance optimization
#[inline(always)]
const fn likely(b: bool) -> bool {
    b
}

#[inline(always)]
#[allow(dead_code)]
const fn unlikely(b: bool) -> bool {
    !b
}

/// Configuration performance mode
#[derive(Clone, Debug, Copy, Default)]
pub enum ConfigMode {
    /// Conservative mode - prioritizes stability and resource safety
    Conservative,
    /// Balanced mode - good performance with reasonable resource usage
    Balanced,
    /// Standard mode - configured for moderate resource usage
    Standard,
    /// High resource mode - configured for higher resource usage
    #[default]
    ResourceIntensive,
}

/// Configuration for the connection pool
#[derive(Clone, Debug)]
pub struct PoolConfig {
    /// Maximum number of idle connections per host
    pub max_idle_per_host: usize,
    /// Keep-alive timeout for idle connections
    pub keep_alive_timeout: Duration,
    /// Maximum total number of connections across all hosts
    #[allow(dead_code)]
    pub max_total_connections: usize,
    /// Connection timeout
    #[allow(dead_code)]
    pub connect_timeout: Duration,
    /// Request timeout (entire request duration)
    pub request_timeout: Duration,
    /// Enable HTTP/2
    #[allow(dead_code)]
    pub http2_only: bool,
    /// Enable HTTP/1 only
    #[allow(dead_code)]
    pub http1_only: bool,
    /// Configuration mode
    pub mode: ConfigMode,
}

impl Default for PoolConfig {
    fn default() -> Self {
        Self::standard()  // Use standard mode by default
    }
}

impl PoolConfig {
    /// Create conservative configuration - prioritizes stability
    pub fn conservative() -> Self {
        Self {
            max_idle_per_host: 10,   // Very conservative for resource safety
            keep_alive_timeout: Duration::from_secs(30), // Short keep-alive
            max_total_connections: 100, // Low total connections
            connect_timeout: Duration::from_secs(10),  // Generous connection timeout
            request_timeout: Duration::from_secs(30), // Standard request timeout - unified
            http2_only: false,
            http1_only: false,
            mode: ConfigMode::Conservative,
        }
    }

    /// Create balanced configuration - good performance with reasonable resources
    pub fn balanced() -> Self {
        Self {
            max_idle_per_host: 50,   // Balanced value for stability
            keep_alive_timeout: Duration::from_secs(90), // 1.5 minutes keep-alive
            max_total_connections: 500, // Reasonable total for most use cases
            connect_timeout: Duration::from_millis(5000),  // 5 second connection timeout
            request_timeout: Duration::from_secs(30), // 30 second request timeout
            http2_only: false,
            http1_only: false,
            mode: ConfigMode::Balanced,
        }
    }

    /// Create high resource configuration with higher resource limits
    pub fn resource_intensive() -> Self {
        Self {
            max_idle_per_host: 200,   // High resource setting
            keep_alive_timeout: Duration::from_secs(300), // 5 minutes keep-alive
            max_total_connections: 2000, // High resource connection limit
            connect_timeout: Duration::from_millis(2000),  // Standard connection timeout
            request_timeout: Duration::from_secs(30), // Standard request timeout - unified
            http2_only: false,
            http1_only: false,
            mode: ConfigMode::ResourceIntensive,
        }
    }

    /// Create standard configuration  
    /// This mode provides standard performance with resource management
    pub fn standard() -> Self {
        Self {
            max_idle_per_host: 1000,   // Standard per-host connections
            keep_alive_timeout: Duration::from_secs(300), // 5 minutes keep-alive
            max_total_connections: 10000, // Standard connection pool size
            connect_timeout: Duration::from_millis(500),  // Standard connection timeout
            request_timeout: Duration::from_secs(30), // Standard request timeout - CRITICAL FIX!
            http2_only: false,
            http1_only: false,
            mode: ConfigMode::ResourceIntensive,
        }
    }

    /// Create async configuration for concurrent request processing
    /// Configured for async workload patterns
    pub fn async_configured() -> Self {
        Self {
            max_idle_per_host: 100,    // Configured per-host connections for async patterns
            keep_alive_timeout: Duration::from_secs(90), // Configured for async connection lifecycle
            max_total_connections: 800, // Configured for async concurrent processing
            connect_timeout: Duration::from_millis(200),  // Standard connection timeout
            request_timeout: Duration::from_secs(30), // Match client timeout for consistency
            http2_only: false,
            http1_only: true, // HTTP/1.1 only for consistent async processing
            mode: ConfigMode::ResourceIntensive,
        }
    }

    /// Create async high resource configuration for concurrent processing
    /// High resource settings for async workloads
    pub fn async_extended_resources() -> Self {
        Self {
            max_idle_per_host: 300,    // High resource per-host connections for async patterns
            keep_alive_timeout: Duration::from_secs(45), // High resource keepalive for async processing
            max_total_connections: 2000, // High resource connections for async concurrent processing
            connect_timeout: Duration::from_millis(100),  // Standard connection timeout
            request_timeout: Duration::from_secs(30), // Match client timeout for consistency
            http2_only: false,
            http1_only: true, // HTTP/1.1 only for async processing
            mode: ConfigMode::ResourceIntensive,
        }
    }

    /// Create balanced async configuration for concurrent processing
    /// Balanced settings for async processing with resource efficiency
    pub fn async_balanced() -> Self {
        Self {
            max_idle_per_host: 150,    // Balanced per-host connections for async processing
            keep_alive_timeout: Duration::from_secs(60), // Balanced keepalive for async patterns
            max_total_connections: 1000, // Balanced connections for concurrent processing
            connect_timeout: Duration::from_millis(500),  // Balanced connection timeout
            request_timeout: Duration::from_secs(30), // Match client timeout for consistency
            http2_only: false,
            http1_only: true, // HTTP/1.1 only for async processing
            mode: ConfigMode::ResourceIntensive,
        }
    }

    /// Create concurrent async configuration for high-volume processing
    /// Concurrent settings for async HTTP client workloads
    pub fn async_concurrent() -> Self {
        Self {
            max_idle_per_host: 400,    // Concurrent per-host connection pool for async patterns
            keep_alive_timeout: Duration::from_secs(30), // Concurrent keepalive for async processing
            max_total_connections: 3000, // Concurrent connection limit for async processing
            connect_timeout: Duration::from_millis(200),  // Standard connection timeout
            request_timeout: Duration::from_secs(30), // Match client timeout for consistency
            http2_only: false,
            http1_only: true, // HTTP/1.1 only for async processing
            mode: ConfigMode::ResourceIntensive,
        }
    }

    /// Create standard async configuration for reliable high-volume processing
    /// Standard settings: Configured for async workloads
    pub fn async_standard() -> Self {
        Self {
            max_idle_per_host: 250,    // Match sync client configuration
            keep_alive_timeout: Duration::from_secs(30), // Standard 30s keep-alive
            max_total_connections: 1200, // Match sync client total connections
            connect_timeout: Duration::from_secs(5),  // Reasonable connect timeout
            request_timeout: Duration::from_secs(30), // Match sync client timeout - CRITICAL FIX!
            http2_only: false,
            http1_only: false, // Allow both HTTP/1.1 and HTTP/2
            mode: ConfigMode::Standard, // Use standard instead of resource intensive
        }
    }

    /// Validate configuration parameters for safety
    pub fn validate(&self) -> Result<(), String> {
        if self.max_idle_per_host == 0 {
            return Err("max_idle_per_host must be greater than 0".to_string());
        }
        if self.max_idle_per_host > 2000 {
            return Err(format!(
                "WARNING: max_idle_per_host ({}) is very high and may cause resource exhaustion. Consider using a value <= 500.",
                self.max_idle_per_host
            ));
        }
        if self.max_total_connections == 0 {
            return Err("max_total_connections must be greater than 0".to_string());
        }
        if self.max_total_connections > 10000 {
            return Err(format!(
                "WARNING: max_total_connections ({}) is very high and may cause system instability. Consider using a value <= 5000.",
                self.max_total_connections
            ));
        }
        if self.keep_alive_timeout > Duration::from_secs(1200) {
            return Err(format!(
                "WARNING: keep_alive_timeout ({:?}) is very long and may hold resources unnecessarily. Consider using a value <= 600s.",
                self.keep_alive_timeout
            ));
        }
        if self.request_timeout < Duration::from_millis(100) {
            return Err(format!(
                "WARNING: request_timeout ({:?}) is too short and may cause frequent timeouts. Consider using a value >= 5s.",
                self.request_timeout
            ));
        }
        if self.connect_timeout < Duration::from_millis(100) {
            return Err(format!(
                "WARNING: connect_timeout ({:?}) is too short and may cause frequent connection failures. Consider using a value >= 1s.",
                self.connect_timeout
            ));
        }
        
        // Mode-specific warnings
        match self.mode {
            ConfigMode::Conservative => {
                if self.max_idle_per_host > 50 {
                    eprintln!("WARNING: Conservative mode with max_idle_per_host > 50 may not be truly conservative.");
                }
            }
            ConfigMode::Balanced => {
                // Balanced mode is flexible, no specific warnings
            }
            ConfigMode::Standard => {
                eprintln!("Standard mode active: Configured with moderate resource usage.");
            }
            ConfigMode::ResourceIntensive => {
                eprintln!("Resource intensive mode active: Configured with resource management.");
            }
        }
        
        Ok(())
    }
}

/// Smart client container that holds both HTTP and HTTPS clients
#[derive(Clone)]
pub struct SmartHttpClient {
    /// HTTP-only client for localhost and plain HTTP
    http_client: Client<HttpConnector, Full<Bytes>>,
    /// HTTPS client for secure connections
    https_client: Client<HttpsConnector<HttpConnector>, Full<Bytes>>,
}

/// HTTP connection pool that reuses connections
/// This enables Keep-Alive and connection reuse
#[derive(Clone)]
pub struct HttpConnectionPool {
    /// Smart client container with both HTTP and HTTPS clients
    client: SmartHttpClient,
    /// Pool configuration
    config: PoolConfig,
    /// Connection statistics for monitoring
    stats: Arc<RwLock<PoolStats>>,
    /// Pool creation timestamp for health monitoring
    created_at: Instant,
    /// Background cleanup task handle (optional)
    #[allow(dead_code)]
    cleanup_handle: Option<Arc<std::sync::atomic::AtomicBool>>,
}

/// Statistics about the connection pool with monitoring capabilities
#[derive(Debug, Default)]
pub struct PoolStats {
    /// Total number of requests made
    pub total_requests: u64,
    /// Number of reused connections
    pub connection_reuses: u64,
    /// Number of new connections created
    pub new_connections: u64,
    /// Number of active connections
    pub active_connections: u64,
    /// Number of failed requests
    pub failed_requests: u64,
    /// Number of timeout errors
    pub timeout_errors: u64,
    /// Number of connection errors
    pub connection_errors: u64,
    /// Average response time in milliseconds
    pub avg_response_time_ms: f64,
    /// Connection pool health score (0.0 - 1.0)
    pub health_score: f64,
    /// Last cleanup timestamp
    pub last_cleanup: Option<Instant>,
    /// Memory usage estimate in bytes
    pub memory_usage_bytes: u64,
}

impl HttpConnectionPool {
    /// Create a new connection pool with the given configuration
    pub fn new(config: PoolConfig) -> PyResult<Self> {
        // Validate configuration for safety
        if let Err(warning_msg) = config.validate() {
            if warning_msg.starts_with("WARNING:") {
                eprintln!("{}", warning_msg);
            } else {
                return Err(crate::error::RequestError::new_err(warning_msg));
            }
        }

        // Initialize HTTPS crypto provider for TLS support
        std::sync::Once::new().call_once(|| {
            rustls::crypto::aws_lc_rs::default_provider()
                .install_default()
                .ok(); // Ignore error if already installed
        });

        // Create HTTP-only connector for localhost connections
        let create_http_only_connector = || {
            let mut connector = HttpConnector::new();
            connector.enforce_http(true);  // Force HTTP-only for localhost
            connector.set_connect_timeout(Some(Duration::from_millis(1000))); // Standard timeout for localhost
            connector.set_nodelay(true);  // Enable TCP_NODELAY for minimum latency
            connector.set_keepalive(Some(Duration::from_secs(300))); // Standard keepalive for connection reuse
            connector.set_reuse_address(true); // Enable socket reuse
            connector.set_send_buffer_size(Some(2 * 1024 * 1024)); // 2MB send buffer
            connector.set_recv_buffer_size(Some(2 * 1024 * 1024)); // 2MB receive buffer
            connector.set_happy_eyeballs_timeout(Some(Duration::from_millis(10))); // IPv6/IPv4 fallback
            connector.set_local_address(None); // Let system choose interface
            connector
        };

        // Create HTTP connector for HTTPS wrapper (allows both HTTP and HTTPS)
        let _create_https_base_connector = || {
            let mut connector = HttpConnector::new();
            connector.enforce_http(false);  // Allow both HTTP and HTTPS
            connector.set_connect_timeout(Some(config.connect_timeout));
            connector.set_nodelay(true);  // Enable TCP_NODELAY for minimum latency
            connector.set_keepalive(Some(Duration::from_secs(300))); // Standard keepalive for connection reuse
            connector.set_reuse_address(true); // Enable socket reuse
            connector.set_send_buffer_size(Some(2 * 1024 * 1024)); // 2MB send buffer
            connector.set_recv_buffer_size(Some(2 * 1024 * 1024)); // 2MB receive buffer
            connector.set_happy_eyeballs_timeout(Some(Duration::from_millis(10))); // Standard IPv6/IPv4 fallback
            connector.set_local_address(None); // Let system choose interface
            connector
        };

        // Create HTTP-only client (for localhost and plain HTTP)
        let http_client = Client::builder(TokioExecutor::new())
            .pool_idle_timeout(config.keep_alive_timeout) // Use config timeout
            .pool_max_idle_per_host(config.max_idle_per_host) // Use config pooling
            .http1_title_case_headers(false) // Configure HTTP/1.1 headers for efficiency
            .http1_preserve_header_case(false) // Configure header case for processing speed
            .http1_read_buf_exact_size(8 * 1024 * 1024) // 8MB read buffer
            .http1_max_buf_size(8 * 1024 * 1024) // 8MB max buffer
            .http2_only(false)  // Allow HTTP/1.1 for compatibility and processing speed
            .http1_writev(true) // Enable vectored writes
            .http2_initial_stream_window_size(Some(16 * 1024 * 1024)) // 16MB HTTP/2 stream window
            .http2_initial_connection_window_size(Some(32 * 1024 * 1024)) // 32MB HTTP/2 connection window
            .http2_max_frame_size(Some(64 * 1024)) // 64KB max frame size
            .http2_max_concurrent_reset_streams(1000) // Allow 1000 concurrent reset streams for concurrent processing
            .build(create_http_only_connector());

        // HTTPS connector restored for HTTPS functionality
        let https_connector = match hyper_rustls::HttpsConnectorBuilder::new()
            .with_native_roots() 
        {
            Ok(builder) => {
                // Successfully loaded native roots
                builder
                    .https_or_http()
                    .enable_http1()
                    .enable_http2()
                    .wrap_connector(_create_https_base_connector())
            }
            Err(_) => {
                // Fallback: Use webpki roots if native roots fail
                hyper_rustls::HttpsConnectorBuilder::new()
                    .with_webpki_roots()
                    .https_or_http()
                    .enable_http1()
                    .enable_http2()
                    .wrap_connector(_create_https_base_connector())
            }
        };
        
        // HTTPS client configured for HTTPS functionality
        let https_client = Client::builder(TokioExecutor::new())
            .pool_idle_timeout(config.keep_alive_timeout) // Use config timeout
            .pool_max_idle_per_host(config.max_idle_per_host) // Use config pooling
            .http1_title_case_headers(false) // Configure HTTP/1.1 headers for efficiency
            .http1_preserve_header_case(false) // Configure header case for processing speed
            .http1_read_buf_exact_size(4 * 1024 * 1024) // 4MB read buffer
            .http1_max_buf_size(4 * 1024 * 1024) // 4MB max buffer
            .http1_writev(true) // Enable vectored writes
            .http2_only(false) // Allow both HTTP/1.1 and HTTP/2 for processing speed
            .http2_initial_stream_window_size(Some(16 * 1024 * 1024)) // 16MB HTTP/2 stream window
            .http2_initial_connection_window_size(Some(32 * 1024 * 1024)) // 32MB HTTP/2 connection window
            .http2_max_frame_size(Some(64 * 1024)) // 64KB max frame size
            .http2_max_concurrent_reset_streams(1000) // Allow 1000 concurrent reset streams for concurrent processing
            .build(https_connector);

        let pool = Self {
            client: SmartHttpClient {
                http_client,
                https_client,
            },
            config,
            stats: Arc::new(RwLock::new(PoolStats::default())),
            created_at: Instant::now(),
            cleanup_handle: None,
        };
        
        // Initialize health score
        if let Ok(mut stats) = pool.stats.write() {
            stats.health_score = 1.0;
            stats.last_cleanup = Some(Instant::now());
        }
        
        Ok(pool)
    }

    /// Make an HTTP request using the connection pool
    /// This method will reuse existing connections when possible
    #[inline(always)]  // Force inline for critical path
    pub async fn request(
        &self,
        method: hyper::Method,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
    ) -> PyResult<hyper::Response<hyper::body::Incoming>> {
        self.request_with_timeout(method, uri, headers, body, None).await
    }

    /// Make an HTTP request with a specific timeout
    /// This method will reuse existing connections when possible
    #[inline(always)]  // Force inline for critical path processing
    pub async fn request_with_timeout(
        &self,
        method: hyper::Method,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
        timeout: Option<Duration>,
    ) -> PyResult<hyper::Response<hyper::body::Incoming>> {
        // Method validation using request processing
        let method_str = method.as_str();
        if !matches!(method_str, "GET" | "POST" | "PUT" | "DELETE" | "HEAD" | "OPTIONS" | "PATCH" | "TRACE" | "CONNECT") {
            return Err(crate::error::RequestError::new_err(
                format!("Invalid HTTP method: {}", method_str)
            ));
        }

        // Client selection with configuration handling
        let scheme = uri.scheme_str();
        let use_http_client = likely(scheme == Some("http")); // Most common case is HTTP
        
        // Client selection logic complete

        // Stats update with lock management
        if let Ok(mut stats) = self.stats.try_write() {
            stats.total_requests += 1;
        }

        // Build the request
        let mut request_builder = hyper::Request::builder()
            .method(method.clone())
            .uri(uri.clone());

        // Add headers
        if let Some(ref headers_map) = headers {
            for (key, value) in headers_map {
                request_builder = request_builder.header(key, value);
            }
        }

        // Add appropriate Connection header based on client type  
        if use_http_client {
            // For localhost HTTP, use keep-alive connections
            request_builder = request_builder.header("Connection", "keep-alive");
        } else {
            // For remote HTTPS, use keep-alive for connection reuse
            request_builder = request_builder.header("Connection", "keep-alive");
        }

        // Build request with body
        let body_data = body.unwrap_or_default();
        let request = request_builder
            .body(Full::new(body_data))
            .map_err(|e| RequestError::new_err(format!("Failed to build request: {}", e)))?;

        // Send request using the appropriate client with timeout
        let timeout_duration = timeout.unwrap_or(self.config.request_timeout);
        
        let response = if use_http_client {
            // Use HTTP-only client for localhost HTTP
            tokio::time::timeout(timeout_duration, self.client.http_client.request(request))
                .await
                .map_err(|_| {
                    // Update timeout statistics
                    if let Ok(mut stats) = self.stats.write() {
                        stats.timeout_errors += 1;
                        stats.failed_requests += 1;
                        stats.health_score = calculate_health_score(
                            stats.failed_requests,
                            stats.total_requests,
                            timeout_duration.as_millis() as f64,
                            stats.timeout_errors + stats.connection_errors,
                        );
                    }
                    crate::error::ReadTimeout::new_err(format!(
                        "Request timeout after {}s: deadline has elapsed", 
                        timeout_duration.as_secs_f64()
                    ))
                })?
                .map_err(|e| {
                    // Update connection error statistics
                    if let Ok(mut stats) = self.stats.write() {
                        stats.connection_errors += 1;
                        stats.failed_requests += 1;
                        stats.health_score = calculate_health_score(
                            stats.failed_requests,
                            stats.total_requests,
                            timeout_duration.as_millis() as f64,
                            stats.timeout_errors + stats.connection_errors,
                        );
                    }
                    crate::error::map_hyper_util_error(e)
                })?
        } else {
            // Use HTTPS client for secure requests (HTTPS functionality restored)
            tokio::time::timeout(timeout_duration, self.client.https_client.request(request))
                .await
                .map_err(|_| {
                    // Update timeout statistics for HTTPS client  
                    if let Ok(mut stats) = self.stats.write() {
                        stats.timeout_errors += 1;
                        stats.failed_requests += 1;
                        stats.health_score = calculate_health_score(
                            stats.failed_requests,
                            stats.total_requests,
                            timeout_duration.as_millis() as f64,
                            stats.timeout_errors + stats.connection_errors,
                        );
                    }
                    crate::error::ReadTimeout::new_err(format!(
                        "Request timeout after {}s: deadline has elapsed", 
                        timeout_duration.as_secs_f64()
                    ))
                })?
                .map_err(|e| {
                    // Update connection error statistics for HTTPS client
                    if let Ok(mut stats) = self.stats.write() {
                        stats.connection_errors += 1;
                        stats.failed_requests += 1;
                        stats.health_score = calculate_health_score(
                            stats.failed_requests,
                            stats.total_requests,
                            timeout_duration.as_millis() as f64,
                            stats.timeout_errors + stats.connection_errors,
                        );
                    }
                    crate::error::map_hyper_util_error(e)
                })?
        };

        // Connection reuse stats tracking
        if let Ok(mut stats) = self.stats.try_write() {
            stats.connection_reuses += 1;
        }

        Ok(response)
    }

    /// Get connection pool statistics
    #[allow(dead_code)]
    pub fn get_stats(&self) -> PyResult<PoolStats> {
        let stats = self.stats.read().map_err(|_| {
            RequestError::new_err("Failed to acquire stats lock")
        })?;
        Ok(PoolStats {
            total_requests: stats.total_requests,
            connection_reuses: stats.connection_reuses,
            new_connections: stats.new_connections,
            active_connections: stats.active_connections,
            failed_requests: stats.failed_requests,
            timeout_errors: stats.timeout_errors,
            connection_errors: stats.connection_errors,
            avg_response_time_ms: stats.avg_response_time_ms,
            health_score: stats.health_score,
            last_cleanup: stats.last_cleanup,
            memory_usage_bytes: stats.memory_usage_bytes,
        })
    }

    /// Get connection pool type information
    #[allow(dead_code)]
    pub fn get_client_type(&self) -> &str {
        "Smart Client (HTTP + HTTPS)"
    }

    /// Check if connection pooling is working by measuring consecutive request times
    /// This is a diagnostic method to verify that connections are being reused
    #[allow(dead_code)]
    pub async fn test_connection_reuse(&self, uri: Uri, num_requests: usize) -> PyResult<Vec<Duration>> {
        let mut times = Vec::with_capacity(num_requests);
        
        for _ in 0..num_requests {
            let start = Instant::now();
            
            let _response = self.request(
                hyper::Method::GET,
                uri.clone(),
                None,
                None,
            ).await?;
            
            times.push(start.elapsed());
        }
        
        Ok(times)
    }
}

/// Global connection pool instance for optimal performance
/// Uses safe OnceLock pattern for thread-safe initialization
#[allow(dead_code)]
static GLOBAL_CONNECTION_POOL: std::sync::OnceLock<Result<Arc<HttpConnectionPool>, String>> = std::sync::OnceLock::new();


/// Get or create the global connection pool instance
/// This provides a singleton pattern for connection pool access
#[allow(dead_code)]
pub fn get_global_connection_pool() -> PyResult<Arc<HttpConnectionPool>> {
    let result = GLOBAL_CONNECTION_POOL.get_or_init(|| {
        let config = PoolConfig::default();
        match HttpConnectionPool::new(config) {
            Ok(pool) => Ok(Arc::new(pool)),
            Err(_) => {
                // Fallback: create a minimal pool if default creation fails
                let minimal_config = PoolConfig {
                    max_idle_per_host: 5,
                    keep_alive_timeout: Duration::from_secs(30),
                    max_total_connections: 50,
                    connect_timeout: Duration::from_secs(10),
                    request_timeout: Duration::from_secs(30),
                    http2_only: false,
                    http1_only: false,
                    mode: ConfigMode::Conservative,
                };
                
                match HttpConnectionPool::new(minimal_config) {
                    Ok(pool) => Ok(Arc::new(pool)),
                    Err(e) => Err(format!("Failed to create any connection pool: {}", e))
                }
            }
        }
    });
    
    match result {
        Ok(pool) => Ok(pool.clone()),
        Err(msg) => Err(crate::error::RequestError::new_err(msg.clone()))
    }
}

/// Create a connection pool with custom configuration
/// This allows fine-tuning of connection pool behavior
pub fn create_custom_pool(config: PoolConfig) -> PyResult<Arc<HttpConnectionPool>> {
    Ok(Arc::new(HttpConnectionPool::new(config)?))
}

/// Create a conservative connection pool - prioritizes stability and resource safety
pub fn create_conservative_pool() -> PyResult<Arc<HttpConnectionPool>> {
    Ok(Arc::new(HttpConnectionPool::new(PoolConfig::conservative())?))
}

/// Create a balanced connection pool - good performance with reasonable resource usage
pub fn create_balanced_pool() -> PyResult<Arc<HttpConnectionPool>> {
    Ok(Arc::new(HttpConnectionPool::new(PoolConfig::balanced())?))
}

/// Create a high resource connection pool with higher resource usage
pub fn create_resource_intensive_pool() -> PyResult<Arc<HttpConnectionPool>> {
    Ok(Arc::new(HttpConnectionPool::new(PoolConfig::resource_intensive())?))
}

/// Create a standard connection pool
/// This mode provides standard performance with resource management
pub fn create_standard_pool() -> PyResult<Arc<HttpConnectionPool>> {
    Ok(Arc::new(HttpConnectionPool::new(PoolConfig::standard())?))
}

/// Calculate connection pool health score (0.0 = unhealthy, 1.0 = healthy)
/// Based on error rates, response times, and overall performance
fn calculate_health_score(
    failed_requests: u64,
    total_requests: u64,
    current_response_time_ms: f64,
    error_count: u64,
) -> f64 {
    if total_requests == 0 {
        return 1.0;  // Default health score for newly created pools
    }
    
    // Error rate score (0.0 - 1.0, higher values indicate fewer errors)
    let error_rate = failed_requests as f64 / total_requests as f64;
    let error_score = (1.0 - error_rate).max(0.0);
    
    // Response time score (penalize slow responses)
    let response_time_score = if current_response_time_ms > 10000.0 {
        0.1  // Very slow
    } else if current_response_time_ms > 5000.0 {
        0.5  // Slow
    } else if current_response_time_ms > 1000.0 {
        0.8  // Acceptable
    } else {
        1.0  // Fast
    };
    
    // Error frequency penalty
    let error_frequency_score = if error_count > total_requests / 4 {
        0.2  // Too many errors
    } else if error_count > total_requests / 10 {
        0.6  // Some errors
    } else {
        1.0  // Low error rate
    };
    
    // Weighted average (error rate is most important)
    (error_score * 0.5 + response_time_score * 0.3 + error_frequency_score * 0.2).clamp(0.0, 1.0)
}

/// Additional monitoring and diagnostic methods for the connection pool
impl HttpConnectionPool {
    /// Get detailed health metrics for monitoring systems
    pub fn get_health_metrics(&self) -> PyResult<HashMap<String, f64>> {
        let stats = self.stats.read().map_err(|_| {
            crate::error::InternalError::new_err("Failed to acquire stats lock for health metrics".to_string())
        })?;
        
        let mut metrics = HashMap::new();
        metrics.insert("health_score".to_string(), stats.health_score);
        metrics.insert("total_requests".to_string(), stats.total_requests as f64);
        metrics.insert("failed_requests".to_string(), stats.failed_requests as f64);
        metrics.insert("connection_reuses".to_string(), stats.connection_reuses as f64);
        metrics.insert("timeout_errors".to_string(), stats.timeout_errors as f64);
        metrics.insert("connection_errors".to_string(), stats.connection_errors as f64);
        metrics.insert("avg_response_time_ms".to_string(), stats.avg_response_time_ms);
        metrics.insert("uptime_seconds".to_string(), self.created_at.elapsed().as_secs_f64());
        
        if stats.total_requests > 0 {
            metrics.insert("success_rate".to_string(), 
                (stats.total_requests - stats.failed_requests) as f64 / stats.total_requests as f64);
            metrics.insert("error_rate".to_string(), 
                stats.failed_requests as f64 / stats.total_requests as f64);
        }
        
        Ok(metrics)
    }
    
    /// Check if the connection pool is healthy based on error rates and performance
    pub fn is_healthy(&self) -> PyResult<bool> {
        let stats = self.stats.read().map_err(|_| {
            crate::error::InternalError::new_err("Failed to acquire stats lock for health check".to_string())
        })?;
        
        // Consider healthy if health score > 0.7 and not too many recent errors
        Ok(stats.health_score > 0.7 && 
           (stats.total_requests == 0 || stats.failed_requests * 10 < stats.total_requests))
    }
    
    /// Force cleanup of idle connections and reset health metrics
    pub async fn force_cleanup(&self) -> PyResult<()> {
        let mut stats = self.stats.write().map_err(|_| {
            crate::error::InternalError::new_err("Failed to acquire stats lock for cleanup".to_string())
        })?;
        
        stats.last_cleanup = Some(Instant::now());
        
        // Reset error counters if health is critically low
        if stats.health_score < 0.3 {
            stats.failed_requests /= 2;  // Reduce by half
            stats.timeout_errors /= 2;
            stats.connection_errors /= 2;
            stats.health_score = calculate_health_score(
                stats.failed_requests,
                stats.total_requests,
                stats.avg_response_time_ms,
                stats.timeout_errors + stats.connection_errors,
            );
        }
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_connection_pool_creation() {
        let config = PoolConfig::default();
        let pool = HttpConnectionPool::new(config).unwrap();
        
        // Verify pool was created successfully
        let stats = pool.get_stats().unwrap();
        assert_eq!(stats.total_requests, 0);
    }

    #[tokio::test]
    async fn test_config_modes() {
        // Test conservative mode
        let conservative = PoolConfig::conservative();
        assert!(conservative.validate().is_ok());
        assert!(matches!(conservative.mode, ConfigMode::Conservative));
        
        // Test balanced mode
        let balanced = PoolConfig::balanced();
        assert!(balanced.validate().is_ok());
        assert!(matches!(balanced.mode, ConfigMode::Balanced));
        
        // Test standard mode
        let standard = PoolConfig::standard();
        assert!(standard.validate().is_ok());
        assert!(matches!(standard.mode, ConfigMode::ResourceIntensive));
        
        // Verify conservative < balanced < standard in resource usage
        assert!(conservative.max_idle_per_host <= balanced.max_idle_per_host);
        assert!(balanced.max_idle_per_host <= standard.max_idle_per_host);
    }

    #[tokio::test]
    async fn test_config_validation() {
        let mut config = PoolConfig::balanced();
        
        // Test invalid configurations
        config.max_idle_per_host = 0;
        assert!(config.validate().is_err());
        
        config.max_idle_per_host = 50;
        config.max_total_connections = 0;
        assert!(config.validate().is_err());
        
        // Test warning configurations
        config.max_total_connections = 500;
        config.max_idle_per_host = 1500;  // Should trigger warning
        let result = config.validate();
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("WARNING"));
    }

    #[tokio::test]
    async fn test_global_pool_access() {
        let pool1 = get_global_connection_pool().unwrap();
        let pool2 = get_global_connection_pool().unwrap();
        
        // Verify same instance is returned
        assert!(Arc::ptr_eq(&pool1, &pool2));
    }

    #[tokio::test]
    async fn test_pool_stats() {
        let pool = HttpConnectionPool::new(PoolConfig::default()).unwrap();
        let stats = pool.get_stats().unwrap();
        
        assert_eq!(stats.total_requests, 0);
        assert_eq!(stats.connection_reuses, 0);
    }
}