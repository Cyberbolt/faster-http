// 允许 PyO3 宏产生的警告
#![allow(non_local_definitions)]

use pyo3::prelude::*;

// 模块声明
mod error;
mod auth;
mod request;
mod response;
mod config;
mod utils;
mod core;
mod client;
mod async_client;
mod global;

// 重新导出主要类型和函数
pub use error::*;
pub use auth::*;
pub use request::HttpRequest;
pub use response::HttpResponse;
pub use config::ClientConfig;
pub use client::HttpClient;
pub use async_client::AsyncHttpClient;
pub use global::*;

// Python 模块定义
#[pymodule]
fn _core(py: Python, m: &PyModule) -> PyResult<()> {
    // 添加类
    m.add_class::<HttpRequest>()?;
    m.add_class::<HttpResponse>()?;
    m.add_class::<HttpClient>()?;
    m.add_class::<AsyncHttpClient>()?;
    
    // 添加全局函数
    m.add_function(wrap_pyfunction!(global::get, m)?)?;
    m.add_function(wrap_pyfunction!(global::post, m)?)?;
    m.add_function(wrap_pyfunction!(global::put, m)?)?;
    m.add_function(wrap_pyfunction!(global::patch, m)?)?;
    m.add_function(wrap_pyfunction!(global::delete, m)?)?;
    m.add_function(wrap_pyfunction!(global::head, m)?)?;
    m.add_function(wrap_pyfunction!(global::options, m)?)?;
    
    // 添加异常类型
    m.add("HTTPError", py.get_type::<HTTPError>())?;
    m.add("ConnectTimeout", py.get_type::<ConnectTimeout>())?;
    m.add("ReadTimeout", py.get_type::<ReadTimeout>())?;
    m.add("RequestError", py.get_type::<RequestError>())?;
    
    Ok(())
} 