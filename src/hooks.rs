use pyo3::prelude::*;
use pyo3::PyCell;
use std::collections::HashMap;
use crate::request::HttpRequest;
use crate::response::HttpResponse;

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

    /// Extract a list of hooks from Python object (can be single callable or list of callables)
    fn extract_hook_list(py: Python, hooks_obj: &PyObject) -> PyResult<Vec<PyObject>> {
        let mut hooks = Vec::new();

        // Check if it's a single callable
        if hooks_obj.as_ref(py).hasattr("__call__")? {
            hooks.push(hooks_obj.clone());
        } else {
            // Try to extract as list/iterable
            if let Ok(hook_list) = hooks_obj.extract::<Vec<PyObject>>(py) {
                for hook in hook_list {
                    if hook.as_ref(py).hasattr("__call__")? {
                        hooks.push(hook);
                    }
                }
            }
        }

        Ok(hooks)
    }

    /// Execute request hooks
    pub fn execute_request_hooks(&self, py: Python, request: &HttpRequest) -> PyResult<()> {
        for hook in &self.request_hooks {
            // Create Python object from HttpRequest
            let py_request = PyCell::new(py, request.clone())?;
            hook.call1(py, (py_request,))?;
        }
        Ok(())
    }

    /// Execute response hooks  
    pub fn execute_response_hooks(&self, py: Python, response: &HttpResponse) -> PyResult<()> {
        for hook in &self.response_hooks {
            // Create Python object from HttpResponse
            let cloned_response = response.clone();
            let py_response = PyCell::new(py, cloned_response)?;
            hook.call1(py, (py_response,))?;
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
    pub fn execute_pre_request_hooks(&self, py: Python, url: &str, method: &str, headers: &HashMap<String, String>) -> PyResult<()> {
        for hook in &self.pre_request_hooks {
            // Create a simple dict with basic request info
            let request_info = py.eval(&format!(
                "{{'method': '{}', 'url': '{}', 'headers': {}}}",
                method,
                url,
                format!("{:?}", headers)
            ), None, None)?;
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
    pub fn execute_error_hooks(&self, py: Python, error: &str, context: Option<&str>) -> PyResult<()> {
        for hook in &self.error_hooks {
            let error_info = match context {
                Some(ctx) => py.eval(&format!(
                    "{{'error': '{}', 'context': '{}'}}",
                    error,
                    ctx
                ), None, None)?,
                None => py.eval(&format!(
                    "{{'error': '{}'}}",
                    error
                ), None, None)?,
            };
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
}

impl Default for EventHooks {
    fn default() -> Self {
        Self::new()
    }
}