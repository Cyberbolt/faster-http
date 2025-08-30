use std::sync::OnceLock;

// Global unified Tokio runtime - single instance only
#[allow(dead_code)]
static GLOBAL_RUNTIME: OnceLock<tokio::runtime::Runtime> = OnceLock::new();

/// Get the global Tokio runtime for async processing  
/// Configured specifically for HTTP client async workloads
/// Returns None if runtime creation fails
#[allow(dead_code)]
pub fn get_global_runtime() -> Option<&'static tokio::runtime::Runtime> {
    static RUNTIME_INIT_RESULT: std::sync::OnceLock<Option<tokio::runtime::Runtime>> = std::sync::OnceLock::new();
    
    let runtime_option = RUNTIME_INIT_RESULT.get_or_init(|| {
        // Create async runtime
        let cpu_count = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(8); // Fallback to 8 cores
        
        // OPTIMIZED: Use CPU count for optimal async/await performance
        // Avoid over-allocation which can hurt performance
        let worker_threads = cpu_count.max(4).min(12); // Better balance for high-core systems
        let max_blocking_threads = 16; // Reasonable blocking thread pool
        
        if let Ok(runtime) = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(worker_threads) // Optimal worker count
            .max_blocking_threads(max_blocking_threads)
            .enable_all() // Enable all Tokio features
            .thread_name("faster-http") // Simple thread naming
            .build() 
        {
            eprintln!("Tokio Runtime initialized: {} worker threads, {} max blocking threads (optimized)", 
                     worker_threads, max_blocking_threads);
            return Some(runtime);
        }
        
        // Fallback: Simple runtime
        if let Ok(runtime) = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(cpu_count.max(2).min(4))
            .enable_all()
            .build() 
        {
            eprintln!("Simple Tokio Runtime initialized: {} worker threads", cpu_count.max(2).min(4));
            return Some(runtime);
        }
        
        // Default fallback
        if let Ok(runtime) = tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .build() // Use default configuration
        {
            eprintln!("Default Tokio Runtime initialized");
            return Some(runtime);
        }
        
        // Last fallback: Single-threaded runtime
        if let Ok(runtime) = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .max_io_events_per_tick(512) // Higher I/O events for single-thread
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
