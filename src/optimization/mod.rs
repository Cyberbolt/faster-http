// Performance optimization module
pub mod batch;
pub mod gil_optimized;
pub mod precompiled;

pub use batch::*;
pub use gil_optimized::*;
