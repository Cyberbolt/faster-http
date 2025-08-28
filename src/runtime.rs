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
        
        // ASYNC-CONFIGURED: Use more worker threads for async HTTP workload
        // HTTP clients benefit from more parallelism than CPU-bound tasks
        let worker_threads = (cpu_count * 2).min(16); // Double the workers, cap at 16
        let max_blocking_threads = 32; // Reduce blocking threads for async focus
        
        if let Ok(runtime) = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(worker_threads) // More workers for async HTTP parallelism
            .max_blocking_threads(max_blocking_threads) // Focused blocking thread pool
            .enable_all() // Enable all Tokio features
            .thread_name("faster-http-async") // Named threads for debugging
            .thread_stack_size(4 * 1024 * 1024) // 4MB stack - smaller for async efficiency
            .global_queue_interval(7) // Work stealing with small prime interval
            .event_interval(12) // Tuned event loop polling interval
            .max_io_events_per_tick(10240) // High I/O events per tick for async workloads
            .build() 
        {
            eprintln!("Tokio Runtime initialized: {} worker threads, {} max blocking threads (async-tuned)", 
                     worker_threads, max_blocking_threads);
            return Some(runtime);
        }
        
        // Fallback: Configured runtime
        if let Ok(runtime) = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(cpu_count.max(4))
            .max_blocking_threads(16)
            .enable_all()
            .global_queue_interval(11)
            .event_interval(17)
            .max_io_events_per_tick(2048)
            .build() 
        {
            eprintln!("Configured Tokio Runtime initialized: {} worker threads", cpu_count);
            return Some(runtime);
        }
        
        // Standard fallback
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
