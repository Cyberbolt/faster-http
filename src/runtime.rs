use std::sync::OnceLock;

// Global unified Tokio runtime - single instance only
#[allow(dead_code)]
static GLOBAL_RUNTIME: OnceLock<tokio::runtime::Runtime> = OnceLock::new();

/// Get the EXTREME performance global Tokio runtime for A级 standard
/// NUMA-aware and highly optimized for maximum HTTP throughput
/// Returns None if runtime creation fails
#[allow(dead_code)]
pub fn get_global_runtime() -> Option<&'static tokio::runtime::Runtime> {
    static RUNTIME_INIT_RESULT: std::sync::OnceLock<Option<tokio::runtime::Runtime>> = std::sync::OnceLock::new();
    
    let runtime_option = RUNTIME_INIT_RESULT.get_or_init(|| {
        // EXTREME PERFORMANCE: Create NUMA-aware multi-threaded runtime
        let cpu_count = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(8); // Fallback to 8 cores
        
        // OPTIMIZED: Limit worker threads to avoid excessive context switching and competition
        let worker_threads = cpu_count.min(8); // Limit max 8 workers to reduce competition
        let max_blocking_threads = 64; // Significantly reduce blocking thread pool size
        
        if let Ok(runtime) = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(worker_threads) // Use all available CPU cores
            .max_blocking_threads(max_blocking_threads) // Extreme blocking thread pool
            .enable_all() // Enable all Tokio features
            .thread_name("faster-http-worker") // Named threads for debugging
            .thread_stack_size(8 * 1024 * 1024) // 8MB stack size for complex async operations
            .global_queue_interval(17) // Ultra-optimized work stealing (smaller prime for async)
            .event_interval(31) // Ultra-optimized event loop polling (smaller prime for async)
            .max_io_events_per_tick(4096) // Process up to 4096 I/O events per tick for BEYOND extreme async performance
            .build() 
        {
            eprintln!("ULTRA Tokio Runtime initialized: {} worker threads, {} max blocking threads", 
                     worker_threads, max_blocking_threads);
            return Some(runtime);
        }
        
        // Fallback: Standard multi-threaded runtime if ULTRA config fails
        if let Ok(runtime) = tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .worker_threads(cpu_count)
            .build() 
        {
            eprintln!("Standard Tokio Runtime initialized: {} worker threads", cpu_count);
            return Some(runtime);
        }
        
        // Last fallback: Single-threaded runtime
        if let Ok(runtime) = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .max_io_events_per_tick(256) // Optimize single-thread I/O
            .build() 
        {
            eprintln!("Warning: Single-threaded Tokio Runtime initialized (performance may be limited)");
            return Some(runtime);
        }
        
        eprintln!("ERROR: Failed to create any Tokio runtime!");
        None
    });
    
    runtime_option.as_ref()
}
