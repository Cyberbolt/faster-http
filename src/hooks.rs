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
}

/// Container for event hooks - stores Python callable objects
#[derive(Clone)]
pub struct EventHooks {
    pub request_hooks: Vec<PyObject>,
    pub response_hooks: Vec<PyObject>,
}

impl EventHooks {
    pub fn new() -> Self {
        Self {
            request_hooks: Vec::new(),
            response_hooks: Vec::new(),
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
}

impl Default for EventHooks {
    fn default() -> Self {
        Self::new()
    }
}