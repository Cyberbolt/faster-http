// Core functionality module
pub mod api;
pub mod core;
pub mod error;
pub mod sync_core;

pub use error::*;
pub use sync_core::SyncHttpClient;

use pyo3::prelude::*;

/// Main entry point function for httpx compatibility
///
/// This function provides the same signature as httpx.main()
/// It's primarily used for CLI functionality but can be called directly
#[pyfunction]
pub fn main() -> PyResult<()> {
    // For now, this is a placeholder that matches httpx.main() behavior
    // httpx.main() typically handles CLI arguments and runs the HTTP client
    // Since faster-http focuses on library usage, we'll just provide a no-op implementation
    // that's compatible with httpx API

    Python::with_gil(|py| {
        // Check if we're being called from command line
        let sys = py.import("sys")?;
        let argv = sys.getattr("argv")?;
        let argv_list: Vec<String> = argv.extract()?;

        if argv_list.len() > 1 {
            // If arguments provided, show a simple message
            let message = "faster-http: High-performance HTTP client compatible with httpx API\n";
            print!("{}", message);
        }

        Ok(())
    })
}
