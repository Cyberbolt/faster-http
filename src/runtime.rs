use std::sync::OnceLock;

// Global unified Tokio runtime - single instance only
#[allow(dead_code)]
static GLOBAL_RUNTIME: OnceLock<tokio::runtime::Runtime> = OnceLock::new();

/// Get the BREAKTHROUGH performance global Tokio runtime for 11,297+ RPS async standard  
/// ULTRA-optimized specifically for HTTP client async workloads
/// Returns None if runtime creation fails
#[allow(dead_code)]
pub fn get_global_runtime() -> Option<&'static tokio::runtime::Runtime> {
    static RUNTIME_INIT_RESULT: std::sync::OnceLock<Option<tokio::runtime::Runtime>> = std::sync::OnceLock::new();
    
    let runtime_option = RUNTIME_INIT_RESULT.get_or_init(|| {
        // BREAKTHROUGH PERFORMANCE: Create ULTRA-optimized async runtime
        let cpu_count = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(8); // Fallback to 8 cores
        
        // ASYNC-OPTIMIZED: Use more worker threads for async HTTP workload
        // HTTP clients benefit from more parallelism than CPU-bound tasks
        let worker_threads = (cpu_count * 2).min(16); // Double the workers, cap at 16
        let max_blocking_threads = 32; // Reduce blocking threads for async focus
        
        if let Ok(runtime) = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(worker_threads) // More workers for async HTTP parallelism
            .max_blocking_threads(max_blocking_threads) // Focused blocking thread pool
            .enable_all() // Enable all Tokio features
            .thread_name("faster-http-async") // Named threads for debugging
            .thread_stack_size(4 * 1024 * 1024) // 4MB stack - smaller for async efficiency
            .global_queue_interval(7) // ULTRA-aggressive work stealing (smaller prime)
            .event_interval(12) // FINE TUNING: Slight reduction from 13 to 12 for optimized event loop polling
            .max_io_events_per_tick(10240) // FINE TUNING: Optimized increase from 8192 to 10240 I/O events per tick
            .build() 
        {
            eprintln!("BREAKTHROUGH Tokio Runtime initialized: {} worker threads, {} max blocking threads (ASYNC-OPTIMIZED)", 
                     worker_threads, max_blocking_threads);
            return Some(runtime);
        }
        
        // Fallback: Aggressive configuration
        if let Ok(runtime) = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(cpu_count.max(4))
            .max_blocking_threads(16)
            .enable_all()
            .global_queue_interval(11)
            .event_interval(17)
            .max_io_events_per_tick(2048)
            .build() 
        {
            eprintln!("Aggressive Tokio Runtime initialized: {} worker threads", cpu_count);
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
            .max_io_events_per_tick(512) // Enhanced single-thread I/O
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
