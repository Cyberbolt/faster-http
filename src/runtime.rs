use std::sync::OnceLock;

// Global unified Tokio runtime - single instance only
static GLOBAL_RUNTIME: OnceLock<tokio::runtime::Runtime> = OnceLock::new();

/// Get the global unified Tokio runtime
/// This is the only runtime instance in the library, avoiding cleanup issues caused by multiple runtimes
pub fn get_global_runtime() -> &'static tokio::runtime::Runtime {
    GLOBAL_RUNTIME.get_or_init(|| {
        tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .build()
            .expect("Failed to create global tokio runtime")
    })
}
