// EXTREME PERFORMANCE: Memory pool implementation for A级 performance
// Reduces allocation overhead through pre-allocated buffer pools

use std::sync::Arc;
use std::collections::VecDeque;
use std::sync::Mutex;
use bytes::Bytes;

/// High-performance memory pool for byte buffers
/// Pre-allocates buffers to avoid runtime memory allocation overhead
#[derive(Clone)]
pub struct ByteBufferPool {
    /// Small buffers (up to 4KB) for common requests/responses
    small_buffers: Arc<Mutex<VecDeque<Vec<u8>>>>,
    /// Medium buffers (up to 64KB) for larger payloads  
    medium_buffers: Arc<Mutex<VecDeque<Vec<u8>>>>,
    /// Large buffers (up to 2MB) for streaming and file uploads
    large_buffers: Arc<Mutex<VecDeque<Vec<u8>>>>,
    /// Configuration
    config: PoolConfig,
}

/// Memory pool configuration optimized for A级 performance
#[derive(Debug, Clone)]
pub struct PoolConfig {
    /// Maximum number of small buffers to keep in pool
    pub max_small_buffers: usize,
    /// Maximum number of medium buffers to keep in pool  
    pub max_medium_buffers: usize,
    /// Maximum number of large buffers to keep in pool
    pub max_large_buffers: usize,
    /// Small buffer size (4KB)
    pub small_buffer_size: usize,
    /// Medium buffer size (64KB)
    pub medium_buffer_size: usize,
    /// Large buffer size (2MB)
    pub large_buffer_size: usize,
    /// Enable aggressive pre-allocation for ULTRA mode
    pub aggressive_prealloc: bool,
}

impl Default for PoolConfig {
    fn default() -> Self {
        Self::ultra() // Use ULTRA configuration by default for A级 performance
    }
}

impl PoolConfig {
    /// Conservative configuration - lower memory usage
    #[allow(dead_code)]
    pub fn conservative() -> Self {
        Self {
            max_small_buffers: 16,
            max_medium_buffers: 8,
            max_large_buffers: 4,
            small_buffer_size: 4 * 1024,        // 4KB
            medium_buffer_size: 64 * 1024,      // 64KB
            large_buffer_size: 2 * 1024 * 1024, // 2MB
            aggressive_prealloc: false,
        }
    }

    /// Balanced configuration - good performance with reasonable memory
    #[allow(dead_code)]
    pub fn balanced() -> Self {
        Self {
            max_small_buffers: 32,
            max_medium_buffers: 16,
            max_large_buffers: 8,
            small_buffer_size: 4 * 1024,        // 4KB
            medium_buffer_size: 64 * 1024,      // 64KB
            large_buffer_size: 2 * 1024 * 1024, // 2MB
            aggressive_prealloc: false,
        }
    }

    /// ULTRA configuration - OPTIMIZED performance with balanced memory usage for A级 standard
    pub fn ultra() -> Self {
        Self {
            max_small_buffers: 256,   // Optimized small buffer count for memory efficiency
            max_medium_buffers: 128,  // Optimized medium buffer pool for memory efficiency
            max_large_buffers: 64,    // Optimized large buffer pool for memory efficiency
            small_buffer_size: 8 * 1024,        // 8KB - larger for async efficiency
            medium_buffer_size: 128 * 1024,     // 128KB - larger for async efficiency 
            large_buffer_size: 4 * 1024 * 1024, // 4MB - larger for async efficiency
            aggressive_prealloc: true,          // Pre-allocate for maximum async speed
        }
    }
}

impl ByteBufferPool {
    /// Create new memory pool with given configuration
    pub fn new(config: PoolConfig) -> Self {
        let pool = Self {
            small_buffers: Arc::new(Mutex::new(VecDeque::with_capacity(config.max_small_buffers))),
            medium_buffers: Arc::new(Mutex::new(VecDeque::with_capacity(config.max_medium_buffers))),
            large_buffers: Arc::new(Mutex::new(VecDeque::with_capacity(config.max_large_buffers))),
            config: config.clone(),
        };

        // Pre-allocate buffers for ULTRA performance
        if config.aggressive_prealloc {
            pool.preallocate_buffers();
        }

        pool
    }

    /// Pre-allocate buffers to avoid runtime allocation
    #[inline(always)]
    fn preallocate_buffers(&self) {
        // Pre-allocate small buffers
        if let Ok(mut small) = self.small_buffers.lock() {
            for _ in 0..self.config.max_small_buffers {
                small.push_back(vec![0; self.config.small_buffer_size]);
            }
        }

        // Pre-allocate medium buffers  
        if let Ok(mut medium) = self.medium_buffers.lock() {
            for _ in 0..self.config.max_medium_buffers {
                medium.push_back(vec![0; self.config.medium_buffer_size]);
            }
        }

        // Pre-allocate large buffers
        if let Ok(mut large) = self.large_buffers.lock() {
            for _ in 0..self.config.max_large_buffers {
                large.push_back(vec![0; self.config.large_buffer_size]);
            }
        }
    }

    /// Get optimized buffer for given size with zero-allocation when possible
    #[inline(always)]  // Critical hot path - force inline
    pub fn get_buffer(&self, size: usize) -> Vec<u8> {
        match size {
            // Small buffers - most common case, optimize for speed
            0..=4096 => {
                if let Ok(mut small) = self.small_buffers.lock() {
                    if let Some(mut buf) = small.pop_front() {
                        buf.resize(size, 0);
                        return buf;
                    }
                }
                // Fallback: allocate new buffer
                vec![0; size]
            },
            
            // Medium buffers - for larger payloads
            4097..=65536 => {
                if let Ok(mut medium) = self.medium_buffers.lock() {
                    if let Some(mut buf) = medium.pop_front() {
                        buf.resize(size, 0);
                        return buf;
                    }
                }
                // Fallback: allocate new buffer
                vec![0; size]
            },
            
            // Large buffers - for streaming and big uploads
            _ => {
                if size <= self.config.large_buffer_size {
                    if let Ok(mut large) = self.large_buffers.lock() {
                        if let Some(mut buf) = large.pop_front() {
                            buf.resize(size, 0);
                            return buf;
                        }
                    }
                }
                // Fallback: allocate new buffer
                vec![0; size]
            }
        }
    }

    /// Return buffer to pool for reuse
    #[inline(always)]  // Critical hot path - force inline
    #[allow(dead_code)]
    pub fn return_buffer(&self, mut buffer: Vec<u8>) {
        let capacity = buffer.capacity();
        buffer.clear(); // Clear data but keep capacity

        match capacity {
            // Return to small buffer pool
            size if size <= self.config.small_buffer_size => {
                if let Ok(mut small) = self.small_buffers.lock() {
                    if small.len() < self.config.max_small_buffers {
                        small.push_back(buffer);
                    }
                    // If pool is full, let buffer be dropped
                }
            },
            
            // Return to medium buffer pool
            size if size <= self.config.medium_buffer_size => {
                if let Ok(mut medium) = self.medium_buffers.lock() {
                    if medium.len() < self.config.max_medium_buffers {
                        medium.push_back(buffer);
                    }
                }
            },
            
            // Return to large buffer pool
            size if size <= self.config.large_buffer_size => {
                if let Ok(mut large) = self.large_buffers.lock() {
                    if large.len() < self.config.max_large_buffers {
                        large.push_back(buffer);
                    }
                }
            },
            
            // Buffer too large - let it be dropped
            _ => {}
        }
    }

    /// Create optimized Bytes from data using memory pool
    #[inline(always)]  // Critical hot path - force inline  
    pub fn create_bytes(&self, data: &[u8]) -> Bytes {
        match data.len() {
            // For small data, use direct copy - fastest approach
            0..=1024 => Bytes::copy_from_slice(data),
            
            // For medium data, use pooled buffer 
            1025..=65536 => {
                let mut buf = self.get_buffer(data.len());
                buf[..data.len()].copy_from_slice(data);
                buf.truncate(data.len());
                Bytes::from(buf)
            },
            
            // For large data, use direct allocation
            _ => Bytes::from(data.to_vec())
        }
    }

    /// Get pool statistics for monitoring
    #[allow(dead_code)]
    pub fn get_stats(&self) -> PoolStats {
        let small_count = self.small_buffers.lock().map(|s| s.len()).unwrap_or(0);
        let medium_count = self.medium_buffers.lock().map(|m| m.len()).unwrap_or(0);
        let large_count = self.large_buffers.lock().map(|l| l.len()).unwrap_or(0);

        let estimated_memory = 
            small_count * self.config.small_buffer_size +
            medium_count * self.config.medium_buffer_size +
            large_count * self.config.large_buffer_size;

        PoolStats {
            small_buffers_available: small_count,
            medium_buffers_available: medium_count,
            large_buffers_available: large_count,
            total_buffers_available: small_count + medium_count + large_count,
            estimated_memory_bytes: estimated_memory,
            max_capacity: self.config.max_small_buffers + 
                         self.config.max_medium_buffers + 
                         self.config.max_large_buffers,
        }
    }
}

/// Memory pool statistics
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct PoolStats {
    pub small_buffers_available: usize,
    pub medium_buffers_available: usize,
    pub large_buffers_available: usize,
    pub total_buffers_available: usize,
    pub estimated_memory_bytes: usize,
    pub max_capacity: usize,
}

/// Global memory pool instance for maximum performance
static GLOBAL_MEMORY_POOL: std::sync::OnceLock<ByteBufferPool> = std::sync::OnceLock::new();

/// Get global memory pool instance
#[inline(always)]  // Critical hot path - force inline
pub fn get_global_memory_pool() -> &'static ByteBufferPool {
    GLOBAL_MEMORY_POOL.get_or_init(|| {
        ByteBufferPool::new(PoolConfig::ultra()) // Use ULTRA config for A级 performance
    })
}

/// Pre-allocated string pool for common HTTP headers and values
#[derive(Clone)]
#[allow(dead_code)]
pub struct StringPool {
    /// Common header names
    common_headers: Arc<[&'static str; 32]>,
    /// Common header values  
    common_values: Arc<[&'static str; 16]>,
}

impl Default for StringPool {
    fn default() -> Self {
        Self::new()
    }
}

#[allow(dead_code)]
impl StringPool {
    pub fn new() -> Self {
        Self {
            common_headers: Arc::new([
                "Content-Type", "Content-Length", "Accept", "Authorization",
                "User-Agent", "Host", "Connection", "Cache-Control",
                "Accept-Encoding", "Accept-Language", "Cookie", "Set-Cookie",
                "Location", "Referer", "Origin", "X-Forwarded-For",
                "X-Real-IP", "X-Requested-With", "If-Modified-Since", "Last-Modified",
                "ETag", "If-None-Match", "Transfer-Encoding", "Upgrade",
                "Sec-WebSocket-Key", "Sec-WebSocket-Accept", "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods", "Access-Control-Allow-Headers", 
                "Access-Control-Max-Age", "Vary", "Server"
            ]),
            common_values: Arc::new([
                "application/json", "application/x-www-form-urlencoded", "text/html",
                "text/plain", "multipart/form-data", "gzip, deflate", "en-US,en;q=0.9",
                "keep-alive", "close", "no-cache", "max-age=0", "chunked",
                "*/*", "Mozilla/5.0", "GET", "POST"
            ]),
        }
    }

    /// Check if header name is commonly used (for optimization)
    #[inline(always)]
    pub fn is_common_header(&self, name: &str) -> bool {
        self.common_headers.contains(&name)
    }

    /// Check if header value is commonly used (for optimization)  
    #[inline(always)]
    pub fn is_common_value(&self, value: &str) -> bool {
        self.common_values.contains(&value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_memory_pool_creation() {
        let pool = ByteBufferPool::new(PoolConfig::balanced());
        let stats = pool.get_stats();
        
        // Pool should be initialized
        assert!(stats.max_capacity > 0);
    }

    #[test]
    fn test_buffer_allocation() {
        let pool = ByteBufferPool::new(PoolConfig::ultra());
        
        // Test small buffer
        let small_buf = pool.get_buffer(1024);
        assert_eq!(small_buf.len(), 1024);
        
        // Test medium buffer
        let medium_buf = pool.get_buffer(32768);
        assert_eq!(medium_buf.len(), 32768);
        
        // Return buffers
        pool.return_buffer(small_buf);
        pool.return_buffer(medium_buf);
    }

    #[test]
    fn test_bytes_creation() {
        let pool = ByteBufferPool::new(PoolConfig::ultra());
        let data = b"Hello, World!";
        
        let bytes = pool.create_bytes(data);
        assert_eq!(bytes.as_ref(), data);
    }

    #[test]
    fn test_string_pool() {
        let pool = StringPool::new();
        
        assert!(pool.is_common_header("Content-Type"));
        assert!(pool.is_common_value("application/json"));
        assert!(!pool.is_common_header("Custom-Header"));
    }
}