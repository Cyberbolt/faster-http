use pyo3::prelude::*;
use pyo3::exceptions::PyException;

// 创建自定义异常类型
pyo3::create_exception!(faster_http, HTTPError, PyException);
pyo3::create_exception!(faster_http, ConnectTimeout, HTTPError);
pyo3::create_exception!(faster_http, ReadTimeout, HTTPError);
pyo3::create_exception!(faster_http, RequestError, HTTPError);

// 错误处理工具
pub fn map_reqwest_error(error: reqwest::Error) -> PyErr {
    if error.is_timeout() {
        ReadTimeout::new_err(format!("Request timeout: {error}"))
    } else if error.is_connect() {
        ConnectTimeout::new_err(format!("Connection timeout: {error}"))
    } else {
        RequestError::new_err(format!("Request failed: {error}"))
    }
} 