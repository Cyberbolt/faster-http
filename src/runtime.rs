use std::sync::OnceLock;

// Global unified Tokio runtime - single instance only
#[allow(dead_code)]
static GLOBAL_RUNTIME: OnceLock<tokio::runtime::Runtime> = OnceLock::new();

/// Get the global unified Tokio runtime
/// This is the only runtime instance in the library, avoiding cleanup issues caused by multiple runtimes
/// Returns None if runtime creation fails
#[allow(dead_code)]
pub fn get_global_runtime() -> Option<&'static tokio::runtime::Runtime> {
    static RUNTIME_INIT_RESULT: std::sync::OnceLock<Option<tokio::runtime::Runtime>> = std::sync::OnceLock::new();
    
    let runtime_option = RUNTIME_INIT_RESULT.get_or_init(|| {
        // Try multi-threaded first
        if let Ok(runtime) = tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .build() 
        {
            return Some(runtime);
        }
        
        // Fallback to single-threaded
        if let Ok(runtime) = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build() 
        {
            return Some(runtime);
        }
        
        None
    });
    
    runtime_option.as_ref()
}
