use crate::core::error::InternalError;
use crate::models::{HttpRequest, HttpResponse};
use pyo3::prelude::*;
use pyo3::PyCell;
use std::collections::HashMap;

/// Event hook types supported by faster-http
#[derive(Clone, Debug)]
pub enum HookType {
    Request,
    Response,
    /// Hook called before request is prepared
    PreRequest,
    /// Hook called after response is processed
    PostResponse,
    /// Hook called on request/response errors
    Error,
}

/// Container for event hooks - stores Python callable objects
#[derive(Clone)]
pub struct EventHooks {
    pub request_hooks: Vec<PyObject>,
    pub response_hooks: Vec<PyObject>,
    pub pre_request_hooks: Vec<PyObject>,
    pub post_response_hooks: Vec<PyObject>,
    pub error_hooks: Vec<PyObject>,
}

impl EventHooks {
    pub fn new() -> Self {
        Self {
            request_hooks: Vec::new(),
            response_hooks: Vec::new(),
            pre_request_hooks: Vec::new(),
            post_response_hooks: Vec::new(),
            error_hooks: Vec::new(),
        }
    }

    /// Create EventHooks from Python dict like {'request': [hook1, hook2], 'response': [hook3]}
    pub fn from_python_dict(py: Python, hooks_dict: &PyObject) -> PyResult<Self> {
        let mut event_hooks = Self::new();

        if hooks_dict.is_none(py) {
            return Ok(event_hooks);
        }

        // Try to extract as dictionary
        if let Ok(dict) = hooks_dict.extract::<HashMap<String, PyObject>>(py) {
            for (hook_type, hooks_obj) in dict {
                match hook_type.as_str() {
                    "request" => {
                        event_hooks.request_hooks = Self::extract_hook_list(py, &hooks_obj)?;
                    }
                    "response" => {
                        event_hooks.response_hooks = Self::extract_hook_list(py, &hooks_obj)?;
                    }
                    "pre_request" => {
                        event_hooks.pre_request_hooks = Self::extract_hook_list(py, &hooks_obj)?;
                    }
                    "post_response" => {
                        event_hooks.post_response_hooks = Self::extract_hook_list(py, &hooks_obj)?;
                    }
                    "error" => {
                        event_hooks.error_hooks = Self::extract_hook_list(py, &hooks_obj)?;
                    }
                    _ => {
                        // Ignore unknown hook types for forward compatibility
                        continue;
                    }
                }
            }
        }

        Ok(event_hooks)
    }

    /// Extract a list of hooks from Python object (must be list/iterable, not single callable)
    fn extract_hook_list(py: Python, hooks_obj: &PyObject) -> PyResult<Vec<PyObject>> {
        let mut hooks = Vec::new();

        // Only accept list/iterable, not single callable (to match httpx behavior)
        if let Ok(hook_list) = hooks_obj.extract::<Vec<PyObject>>(py) {
            for hook in hook_list {
                if hook.as_ref(py).hasattr("__call__")? {
                    hooks.push(hook);
                }
            }
        } else {
            // If not a list, return error like httpx does
            return Err(pyo3::exceptions::PyTypeError::new_err(
                "object is not iterable",
            ));
        }

        Ok(hooks)
    }

    /// Execute request hooks
    pub fn execute_request_hooks(&self, py: Python, request: &HttpRequest) -> PyResult<()> {
        for hook in &self.request_hooks {
            // Create Python object from HttpRequest
            let py_request = PyCell::new(py, request.clone())?;
            let result = hook.call1(py, (py_request,))?;

            // For now, only handle sync hooks to avoid spawn_blocking conflicts
            // Async hooks would require a different architecture
            if let Ok(inspect_module) = py.import("inspect") {
                if let Ok(is_coroutine) =
                    inspect_module.call_method1("iscoroutine", (result.clone(),))
                {
                    if is_coroutine.is_true()? {
                        // Skip async hooks silently in spawn_blocking context
                        // Async hooks are not supported in synchronous execution context
                    }
                }
            }
        }
        Ok(())
    }

    /// Execute response hooks  
    pub fn execute_response_hooks(&self, py: Python, response: &HttpResponse) -> PyResult<()> {
        for hook in &self.response_hooks {
            // Create Python object from HttpResponse
            let cloned_response = response.clone();
            let py_response = PyCell::new(py, cloned_response)?;
            let result = hook.call1(py, (py_response,))?;

            // For now, only handle sync hooks to avoid spawn_blocking conflicts
            // Async hooks would require a different architecture
            if let Ok(inspect_module) = py.import("inspect") {
                if let Ok(is_coroutine) =
                    inspect_module.call_method1("iscoroutine", (result.clone(),))
                {
                    if is_coroutine.is_true()? {
                        // Skip async hooks silently in spawn_blocking context
                        // Async hooks are not supported in synchronous execution context
                    }
                }
            }
        }
        Ok(())
    }

    /// Check if any hooks are registered
    pub fn has_hooks(&self) -> bool {
        !self.request_hooks.is_empty() || !self.response_hooks.is_empty()
    }

    /// Check if request hooks are registered
    pub fn has_request_hooks(&self) -> bool {
        !self.request_hooks.is_empty()
    }

    /// Check if response hooks are registered
    pub fn has_response_hooks(&self) -> bool {
        !self.response_hooks.is_empty()
    }

    /// Execute pre-request hooks
    pub fn execute_pre_request_hooks(
        &self,
        py: Python,
        url: &str,
        method: &str,
        headers: &HashMap<String, String>,
    ) -> PyResult<()> {
        for hook in &self.pre_request_hooks {
            // Create a simple dict with basic request info using PyDict instead of eval
            use pyo3::types::PyDict;
            let request_info = PyDict::new(py);
            request_info.set_item("method", method)?;
            request_info.set_item("url", url)?;
            request_info.set_item("headers", headers)?;
            hook.call1(py, (request_info,))?;
        }
        Ok(())
    }

    /// Execute post-response hooks  
    pub fn execute_post_response_hooks(&self, py: Python, response: &HttpResponse) -> PyResult<()> {
        for hook in &self.post_response_hooks {
            let py_response = PyCell::new(py, response.clone())?;
            hook.call1(py, (py_response,))?;
        }
        Ok(())
    }

    /// Execute error hooks
    pub fn execute_error_hooks(
        &self,
        py: Python,
        error: &str,
        context: Option<&str>,
    ) -> PyResult<()> {
        for hook in &self.error_hooks {
            // Create error info dict using PyDict instead of eval
            use pyo3::types::PyDict;
            let error_info = PyDict::new(py);
            error_info.set_item("error", error)?;
            if let Some(ctx) = context {
                error_info.set_item("context", ctx)?;
            }
            hook.call1(py, (error_info,))?;
        }
        Ok(())
    }

    /// Check if any pre-request hooks are registered
    pub fn has_pre_request_hooks(&self) -> bool {
        !self.pre_request_hooks.is_empty()
    }

    /// Check if any post-response hooks are registered
    pub fn has_post_response_hooks(&self) -> bool {
        !self.post_response_hooks.is_empty()
    }

    /// Check if any error hooks are registered
    pub fn has_error_hooks(&self) -> bool {
        !self.error_hooks.is_empty()
    }

    /// Add hooks dynamically
    pub fn add_hook(&mut self, hook_type: HookType, hook: PyObject) {
        match hook_type {
            HookType::Request => self.request_hooks.push(hook),
            HookType::Response => self.response_hooks.push(hook),
            HookType::PreRequest => self.pre_request_hooks.push(hook),
            HookType::PostResponse => self.post_response_hooks.push(hook),
            HookType::Error => self.error_hooks.push(hook),
        }
    }

    /// Remove all hooks of a specific type
    pub fn clear_hooks(&mut self, hook_type: HookType) {
        match hook_type {
            HookType::Request => self.request_hooks.clear(),
            HookType::Response => self.response_hooks.clear(),
            HookType::PreRequest => self.pre_request_hooks.clear(),
            HookType::PostResponse => self.post_response_hooks.clear(),
            HookType::Error => self.error_hooks.clear(),
        }
    }

    /// Clear all hooks
    pub fn clear_all_hooks(&mut self) {
        self.request_hooks.clear();
        self.response_hooks.clear();
        self.pre_request_hooks.clear();
        self.post_response_hooks.clear();
        self.error_hooks.clear();
    }

    /// Update hooks from Python dict
    pub fn update_from_python_dict(&mut self, py: Python, hooks_dict: &PyObject) -> PyResult<()> {
        // Clear existing hooks
        self.clear_all_hooks();

        // Extract new hooks from dict
        if let Ok(dict) = hooks_dict.extract::<HashMap<String, PyObject>>(py) {
            for (hook_type, hooks_obj) in dict {
                match hook_type.as_str() {
                    "request" => {
                        self.request_hooks = Self::extract_hook_list(py, &hooks_obj)?;
                    }
                    "response" => {
                        self.response_hooks = Self::extract_hook_list(py, &hooks_obj)?;
                    }
                    "pre_request" => {
                        self.pre_request_hooks = Self::extract_hook_list(py, &hooks_obj)?;
                    }
                    "post_response" => {
                        self.post_response_hooks = Self::extract_hook_list(py, &hooks_obj)?;
                    }
                    "error" => {
                        self.error_hooks = Self::extract_hook_list(py, &hooks_obj)?;
                    }
                    _ => {
                        // Ignore unknown hook types for forward compatibility
                        continue;
                    }
                }
            }
        }

        Ok(())
    }

    /// Convert EventHooks back to Python dict format for httpx compatibility
    /// Only includes standard httpx hook types: 'request' and 'response'
    pub fn to_python_dict(&self, py: Python) -> PyResult<PyObject> {
        use pyo3::types::PyDict;

        let dict = PyDict::new(py);

        // Only include standard httpx hook types to ensure 100% compatibility
        dict.set_item("request", self.request_hooks.clone())?;
        dict.set_item("response", self.response_hooks.clone())?;

        Ok(dict.to_object(py))
    }
}

/// EventHooksProxy provides a dict-like interface that synchronizes with the underlying EventHooks
#[pyclass]
pub struct EventHooksProxy {
    hooks: std::sync::Arc<std::sync::Mutex<EventHooks>>,
}

impl EventHooksProxy {
    pub fn new(hooks: std::sync::Arc<std::sync::Mutex<EventHooks>>) -> Self {
        Self { hooks }
    }
}

#[pymethods]
impl EventHooksProxy {
    fn __getitem__(&self, key: &str) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let hooks = self
                .hooks
                .lock()
                .map_err(|_| InternalError::new_err("Failed to acquire hooks lock"))?;
            match key {
                "request" => Ok(hooks.request_hooks.to_object(py)),
                "response" => Ok(hooks.response_hooks.to_object(py)),
                "pre_request" => Ok(hooks.pre_request_hooks.to_object(py)),
                "post_response" => Ok(hooks.post_response_hooks.to_object(py)),
                "error" => Ok(hooks.error_hooks.to_object(py)),
                _ => Err(pyo3::exceptions::PyKeyError::new_err(format!(
                    "Unknown hook type: {}",
                    key
                ))),
            }
        })
    }

    fn __setitem__(&self, key: &str, value: PyObject) -> PyResult<()> {
        Python::with_gil(|py| {
            let mut hooks = self
                .hooks
                .lock()
                .map_err(|_| InternalError::new_err("Failed to acquire hooks lock"))?;
            let hook_list = EventHooks::extract_hook_list(py, &value)?;

            match key {
                "request" => hooks.request_hooks = hook_list,
                "response" => hooks.response_hooks = hook_list,
                "pre_request" => hooks.pre_request_hooks = hook_list,
                "post_response" => hooks.post_response_hooks = hook_list,
                "error" => hooks.error_hooks = hook_list,
                _ => {
                    return Err(pyo3::exceptions::PyKeyError::new_err(format!(
                        "Unknown hook type: {}",
                        key
                    )))
                }
            }
            Ok(())
        })
    }

    fn __delitem__(&self, key: &str) -> PyResult<()> {
        Python::with_gil(|_py| {
            let mut hooks = self
                .hooks
                .lock()
                .map_err(|_| InternalError::new_err("Failed to acquire hooks lock"))?;
            match key {
                "request" => hooks.request_hooks.clear(),
                "response" => hooks.response_hooks.clear(),
                "pre_request" => hooks.pre_request_hooks.clear(),
                "post_response" => hooks.post_response_hooks.clear(),
                "error" => hooks.error_hooks.clear(),
                _ => {
                    return Err(pyo3::exceptions::PyKeyError::new_err(format!(
                        "Unknown hook type: {}",
                        key
                    )))
                }
            }
            Ok(())
        })
    }

    fn __len__(&self) -> usize {
        5 // Always return 5 standard hook types like httpx
    }

    fn __iter__(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let keys = vec![
                "request",
                "response",
                "pre_request",
                "post_response",
                "error",
            ];
            keys.to_object(py).call_method0(py, "__iter__")
        })
    }

    fn keys(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let keys = vec![
                "request",
                "response",
                "pre_request",
                "post_response",
                "error",
            ];
            Ok(keys.to_object(py))
        })
    }

    fn values(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let hooks = self
                .hooks
                .lock()
                .map_err(|_| InternalError::new_err("Failed to acquire hooks lock"))?;
            let values = vec![
                hooks.request_hooks.to_object(py),
                hooks.response_hooks.to_object(py),
                hooks.pre_request_hooks.to_object(py),
                hooks.post_response_hooks.to_object(py),
                hooks.error_hooks.to_object(py),
            ];
            Ok(values.to_object(py))
        })
    }

    fn items(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let hooks = self
                .hooks
                .lock()
                .map_err(|_| InternalError::new_err("Failed to acquire hooks lock"))?;
            let items = vec![
                ("request", hooks.request_hooks.to_object(py)),
                ("response", hooks.response_hooks.to_object(py)),
                ("pre_request", hooks.pre_request_hooks.to_object(py)),
                ("post_response", hooks.post_response_hooks.to_object(py)),
                ("error", hooks.error_hooks.to_object(py)),
            ];
            Ok(items.to_object(py))
        })
    }

    fn get(&self, key: &str, default: Option<PyObject>) -> PyResult<PyObject> {
        match self.__getitem__(key) {
            Ok(value) => Ok(value),
            Err(_) => {
                if let Some(default_value) = default {
                    Ok(default_value)
                } else {
                    Python::with_gil(|py| Ok(py.None()))
                }
            }
        }
    }

    fn __contains__(&self, key: &str) -> bool {
        matches!(
            key,
            "request" | "response" | "pre_request" | "post_response" | "error"
        )
    }

    fn __repr__(&self) -> PyResult<String> {
        Python::with_gil(|_py| {
            let hooks = self
                .hooks
                .lock()
                .map_err(|_| InternalError::new_err("Failed to acquire hooks lock"))?;
            Ok(format!(
                "EventHooksProxy({{'request': {}, 'response': {}, 'pre_request': {}, 'post_response': {}, 'error': {}}})",
                hooks.request_hooks.len(),
                hooks.response_hooks.len(),
                hooks.pre_request_hooks.len(),
                hooks.post_response_hooks.len(),
                hooks.error_hooks.len()
            ))
        })
    }
}

impl Default for EventHooks {
    fn default() -> Self {
        Self::new()
    }
}
