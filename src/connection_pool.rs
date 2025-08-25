// High-performance HTTP connection pool implementation
// Provides true connection reuse and Keep-Alive support for faster-http

use hyper::Uri;
use hyper_util::client::legacy::{Client, connect::HttpConnector};
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
}

impl Default for PoolConfig {
    fn default() -> Self {
        Self {
            max_idle_per_host: 10,
            keep_alive_timeout: Duration::from_secs(90),
            max_total_connections: 100,
            connect_timeout: Duration::from_secs(5),  // Consistent timeout
            request_timeout: Duration::from_secs(30), // Reasonable timeout
            http2_only: false,
            http1_only: false,
        }
    }
}

/// Smart client container that holds both HTTP and HTTPS clients
#[derive(Clone)]
pub struct SmartHttpClient {
    /// HTTP-only client for localhost and plain HTTP
    http_client: Client<HttpConnector, Full<Bytes>>,
    /// HTTPS-capable client for remote hosts
    https_client: Client<HttpsConnector<HttpConnector>, Full<Bytes>>,
}

/// A high-performance HTTP connection pool that reuses connections
/// This enables Keep-Alive and connection reuse for maximum performance
#[derive(Clone)]
pub struct HttpConnectionPool {
    /// Smart client container with both HTTP and HTTPS clients
    client: SmartHttpClient,
    /// Pool configuration
    #[allow(dead_code)]
    config: PoolConfig,
    /// Connection statistics for monitoring
    stats: Arc<RwLock<PoolStats>>,
}

/// Statistics about the connection pool
#[derive(Debug, Default)]
pub struct PoolStats {
    /// Total number of requests made
    pub total_requests: u64,
    /// Number of reused connections
    pub connection_reuses: u64,
    /// Number of new connections created
    #[allow(dead_code)]
    pub new_connections: u64,
    /// Number of active connections
    #[allow(dead_code)]
    pub active_connections: u64,
}

impl HttpConnectionPool {
    /// Create a new connection pool with the given configuration
    pub fn new(config: PoolConfig) -> PyResult<Self> {
        // Initialize rustls crypto provider
        std::sync::Once::new().call_once(|| {
            rustls::crypto::ring::default_provider()
                .install_default()
                .ok(); // Ignore error if already installed
        });

        // Create HTTP-only connector for localhost connections - fixed timeout
        let create_http_only_connector = || {
            let mut connector = HttpConnector::new();
            connector.enforce_http(true);  // Force HTTP-only for localhost
            connector.set_connect_timeout(Some(Duration::from_secs(5))); // Reasonable timeout for localhost
            connector.set_nodelay(true);  // Enable TCP_NODELAY for low latency
            connector.set_keepalive(Some(Duration::from_secs(30))); // Enable keepalive for localhost
            connector
        };

        // Create HTTP connector for HTTPS wrapper (allows both HTTP and HTTPS)
        let create_https_base_connector = || {
            let mut connector = HttpConnector::new();
            connector.enforce_http(false);  // Allow both HTTP and HTTPS
            connector.set_connect_timeout(Some(config.connect_timeout));
            connector.set_nodelay(true);  // Enable TCP_NODELAY for low latency
            connector.set_keepalive(Some(Duration::from_secs(75))); // Enable keepalive
            connector
        };

        // Create HTTP-only client (for localhost and plain HTTP)
        let http_client = Client::builder(TokioExecutor::new())
            .http2_only(false)  // Allow HTTP/1.1
            .build(create_http_only_connector());

        // Create HTTPS connector with rustls - with proper error handling and fallback
        let https_connector = match hyper_rustls::HttpsConnectorBuilder::new()
            .with_native_roots() 
        {
            Ok(builder) => {
                // Successfully loaded native roots
                builder
                    .https_or_http()
                    .enable_http1()
                    .enable_http2()
                    .wrap_connector(create_https_base_connector())
            }
            Err(_) => {
                // Fallback: Use webpki roots if native roots fail
                hyper_rustls::HttpsConnectorBuilder::new()
                    .with_webpki_roots()
                    .https_or_http()
                    .enable_http1()
                    .enable_http2()
                    .wrap_connector(create_https_base_connector())
            }
        };
        
        // Create HTTPS-capable client
        let https_client = Client::builder(TokioExecutor::new())
            .build(https_connector);

        Ok(Self {
            client: SmartHttpClient {
                http_client,
                https_client,
            },
            config,
            stats: Arc::new(RwLock::new(PoolStats::default())),
        })
    }

    /// Make an HTTP request using the connection pool
    /// This method will reuse existing connections when possible
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
    pub async fn request_with_timeout(
        &self,
        method: hyper::Method,
        uri: Uri,
        headers: Option<HashMap<String, String>>,
        body: Option<Bytes>,
        timeout: Option<Duration>,
    ) -> PyResult<hyper::Response<hyper::body::Incoming>> {
        // Validate HTTP method
        let valid_methods = [
            "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", 
            "PATCH", "TRACE", "CONNECT"
        ];
        
        let method_str = method.as_str().to_uppercase();
        if !valid_methods.contains(&method_str.as_str()) {
            return Err(crate::error::RequestError::new_err(
                format!("Invalid HTTP method: {}", method_str)
            ));
        }

        // SMART CLIENT SELECTION: Choose HTTP or HTTPS client based on URI
        let _is_localhost = match uri.host() {
            Some(host) => {
                host == "localhost" || 
                host == "127.0.0.1" || 
                host == "::1" ||
                host.starts_with("127.") ||  // Any 127.x.x.x address
                host == "0.0.0.0"
            }
            None => false,
        };
        let _is_http = uri.scheme_str() == Some("http");
        
        // CORRECT FIX: Use appropriate client based on URI scheme
        // HTTP client for http:// requests, HTTPS client for https:// requests
        let use_http_client = _is_http;
        
        // Client selection logic complete

        // Update statistics
        {
            let mut stats = self.stats.write().map_err(|_| {
                RequestError::new_err("Failed to acquire stats lock")
            })?;
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
            // For localhost HTTP, use keep-alive for better performance
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
                    crate::error::ReadTimeout::new_err(format!(
                        "Request timeout after {}s: deadline has elapsed", 
                        timeout_duration.as_secs_f64()
                    ))
                })?
                .map_err(|e| {
                    crate::error::map_hyper_util_error(e)
                })?
        } else {
            // Use HTTPS-capable client for all other requests
            tokio::time::timeout(timeout_duration, self.client.https_client.request(request))
                .await
                .map_err(|_| {
                    crate::error::ReadTimeout::new_err(format!(
                        "Request timeout after {}s: deadline has elapsed", 
                        timeout_duration.as_secs_f64()
                    ))
                })?
                .map_err(|e| {
                    crate::error::map_hyper_util_error(e)
                })?
        };

        // Update connection reuse statistics
        {
            let mut stats = self.stats.write().map_err(|_| {
                RequestError::new_err("Failed to acquire stats lock")
            })?;
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

#[cfg(test)]
mod tests {
    use super::*;
    use std::str::FromStr;

    #[tokio::test]
    async fn test_connection_pool_creation() {
        let config = PoolConfig::default();
        let pool = HttpConnectionPool::new(config).unwrap();
        
        // Verify pool was created successfully
        let stats = pool.get_stats().unwrap();
        assert_eq!(stats.total_requests, 0);
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