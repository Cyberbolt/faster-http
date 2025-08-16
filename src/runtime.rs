use std::sync::OnceLock;

// 全局统一的 Tokio runtime - 只有一个实例
static GLOBAL_RUNTIME: OnceLock<tokio::runtime::Runtime> = OnceLock::new();

/// 获取全局统一的 Tokio runtime
/// 这是库中唯一的 runtime 实例，避免多个 runtime 导致的清理问题
pub fn get_global_runtime() -> &'static tokio::runtime::Runtime {
    GLOBAL_RUNTIME.get_or_init(|| {
        tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .build()
            .expect("Failed to create global tokio runtime")
    })
}
