// Simplified utils for hyper migration - multipart upload temporarily disabled
use pyo3::prelude::*;
use serde_json::Value;
use std::collections::HashMap;

/// Convert Python object to string for URL parameters
pub fn python_object_to_string(py: Python, obj: &PyObject) -> PyResult<String> {
    if let Ok(s) = obj.extract::<String>(py) {
        Ok(s)
    } else if let Ok(i) = obj.extract::<i64>(py) {
        Ok(i.to_string())
    } else if let Ok(f) = obj.extract::<f64>(py) {
        Ok(f.to_string())
    } else if let Ok(b) = obj.extract::<bool>(py) {
        Ok(b.to_string())
    } else if obj.is_none(py) {
        Ok("None".to_string())
    } else {
        // Use Python's str() representation as fallback
        obj.call_method0(py, "__str__")?.extract::<String>(py)
    }
}

/// Convert Python params dict to string params dict
pub fn convert_params_to_strings(params: &HashMap<String, PyObject>) -> PyResult<HashMap<String, String>> {
    Python::with_gil(|py| {
        let mut string_params = HashMap::new();
        for (key, value) in params {
            let value_str = python_object_to_string(py, value)?;
            string_params.insert(key.clone(), value_str);
        }
        Ok(string_params)
    })
}

/// Build a URL with query parameters (legacy version for String params)
pub fn build_url(
    base_path: &str,
    base_url: Option<&String>,
    params: Option<&HashMap<String, String>>,
) -> Result<String, String> {
    let mut final_url = if let Some(base) = base_url {
        if base_path.starts_with("http://") || base_path.starts_with("https://") {
            base_path.to_string()
        } else {
            format!(
                "{}/{}",
                base.trim_end_matches('/'),
                base_path.trim_start_matches('/')
            )
        }
    } else {
        base_path.to_string()
    };

    // Add query parameters
    if let Some(params_map) = params {
        if !params_map.is_empty() {
            let query_string: Vec<String> = params_map
                .iter()
                .map(|(key, value)| format!("{}={}", urlencoding::encode(key), urlencoding::encode(value)))
                .collect();

            if final_url.contains('?') {
                final_url.push('&');
            } else {
                final_url.push('?');
            }
            final_url.push_str(&query_string.join("&"));
        }
    }

    Ok(final_url)
}

/// Build a URL with query parameters (Python object version)
pub fn build_url_with_python_params(
    base_path: &str,
    base_url: Option<&String>,
    params: Option<&HashMap<String, PyObject>>,
) -> PyResult<String> {
    if let Some(python_params) = params {
        let string_params = convert_params_to_strings(python_params)?;
        build_url(base_path, base_url, Some(&string_params))
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
    } else {
        build_url(base_path, base_url, None)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
    }
}

/// Build multipart form data from Python files and data
pub fn build_multipart_body(
    files_data: Option<HashMap<String, PyObject>>,
    form_data: Option<HashMap<String, PyObject>>,
) -> PyResult<(Vec<u8>, String)> {
    use uuid::Uuid;
    
    // Generate a random boundary
    let boundary = format!("----formdata-{}", Uuid::new_v4().simple());
    let boundary_bytes = format!("--{}", boundary);
    let end_boundary_bytes = format!("--{}--", boundary);
    
    let mut body = Vec::new();
    
    Python::with_gil(|py| -> PyResult<()> {
        // Add form data fields first if any
        if let Some(data) = form_data {
            for (name, value) in data {
                // Write boundary
                body.extend_from_slice(boundary_bytes.as_bytes());
                body.extend_from_slice(b"\r\n");
                
                // Write Content-Disposition header
                body.extend_from_slice(
                    format!("Content-Disposition: form-data; name=\"{}\"\r\n\r\n", name).as_bytes()
                );
                
                // Convert Python value to string and write it
                // NOTE: Check bool before i64 because bool is a subclass of int in Python
                let value_str = if let Ok(s) = value.extract::<String>(py) {
                    s
                } else if let Ok(b) = value.extract::<bool>(py) {
                    if b { "true".to_string() } else { "false".to_string() }
                } else if let Ok(i) = value.extract::<i64>(py) {
                    i.to_string()
                } else if let Ok(f) = value.extract::<f64>(py) {
                    f.to_string()
                } else {
                    // Use Python's str() representation as fallback
                    value.call_method0(py, "__str__")?.extract::<String>(py)?
                };
                
                body.extend_from_slice(value_str.as_bytes());
                body.extend_from_slice(b"\r\n");
            }
        }
        
        // Add file uploads if any
        if let Some(files) = files_data {
            for (field_name, file_spec) in files {
                // Write boundary
                body.extend_from_slice(boundary_bytes.as_bytes());
                body.extend_from_slice(b"\r\n");
                
                // Parse file specification - support multiple formats:
                // 1. Direct file object: file_obj
                // 2. Tuple with filename: (filename, file_obj)  
                // 3. Tuple with content type: (filename, file_obj, content_type)
                let (filename, file_obj, mime_type) = if let Ok(tuple) = file_spec.extract::<(String, PyObject, String)>(py) {
                    // Format: (filename, file_obj, content_type)
                    let (fname, fobj, ctype) = tuple;
                    (fname, fobj, ctype)
                } else if let Ok(tuple) = file_spec.extract::<(String, PyObject)>(py) {
                    // Format: (filename, file_obj)
                    let (fname, fobj) = tuple;
                    let mime_type = mime_guess::from_path(&fname)
                        .first_or_octet_stream()
                        .as_ref()
                        .to_string();
                    (fname, fobj, mime_type)
                } else {
                    // Format: Direct file object
                    let file_obj = file_spec.clone();
                    
                    // Get filename from file object if possible
                    let filename = if let Ok(name) = file_obj.getattr(py, "name") {
                        if let Ok(name_str) = name.extract::<String>(py) {
                            // Extract just the filename from full path
                            std::path::Path::new(&name_str)
                                .file_name()
                                .and_then(|s| s.to_str())
                                .unwrap_or("file")
                                .to_string()
                        } else {
                            "file".to_string()
                        }
                    } else {
                        "file".to_string()
                    };
                    
                    // Guess MIME type from filename
                    let mime_type = mime_guess::from_path(&filename)
                        .first_or_octet_stream()
                        .as_ref()
                        .to_string();
                    
                    (filename, file_obj, mime_type)
                };
                
                // Write Content-Disposition and Content-Type headers
                body.extend_from_slice(
                    format!(
                        "Content-Disposition: form-data; name=\"{}\"; filename=\"{}\"\r\n",
                        field_name, filename
                    ).as_bytes()
                );
                body.extend_from_slice(
                    format!("Content-Type: {}\r\n\r\n", mime_type).as_bytes()
                );
                
                // Read file content - support both file objects and direct content
                let file_content = if let Ok(read_method) = file_obj.getattr(py, "read") {
                    // Case 1: File object with read() method
                    let content = read_method.call0(py)?;
                    if let Ok(bytes) = content.extract::<Vec<u8>>(py) {
                        bytes
                    } else if let Ok(string) = content.extract::<String>(py) {
                        string.into_bytes()
                    } else {
                        return Err(crate::error::RequestError::new_err(
                            "File content must be bytes or string"
                        ));
                    }
                } else if let Ok(string_content) = file_obj.extract::<String>(py) {
                    // Case 2: Direct string content (httpx compatibility)
                    string_content.into_bytes()
                } else if let Ok(bytes_content) = file_obj.extract::<Vec<u8>>(py) {
                    // Case 3: Direct bytes content (httpx compatibility)
                    bytes_content
                } else {
                    return Err(crate::error::RequestError::new_err(
                        format!("File object must be a file-like object with read() method, string, or bytes. Got object type: {}", file_obj.as_ref(py).get_type().name()?)
                    ));
                };
                
                // Write file content
                body.extend_from_slice(&file_content);
                body.extend_from_slice(b"\r\n");
            }
        }
        
        Ok(())
    })?;
    
    // Add final boundary
    body.extend_from_slice(end_boundary_bytes.as_bytes());
    body.extend_from_slice(b"\r\n");
    
    let content_type = format!("multipart/form-data; boundary={}", boundary);
    
    Ok((body, content_type))
}

// Legacy function for compatibility - now redirects to new implementation
#[allow(dead_code)]
pub fn build_multipart_form(
    files_data: HashMap<String, PyObject>,
) -> PyResult<String> {
    let (_, content_type) = build_multipart_body(Some(files_data), None)?;
    Ok(content_type)
}

/// Convert Python dict to URL-encoded form string
pub fn python_dict_to_form_string(data: HashMap<String, PyObject>) -> PyResult<String> {
    Python::with_gil(|py| {
        let mut form_parts = Vec::new();
        
        for (key, value) in data {
            // Convert Python value to string
            // NOTE: Check bool before i64 because bool is a subclass of int in Python
            let value_str = if let Ok(s) = value.extract::<String>(py) {
                s
            } else if let Ok(b) = value.extract::<bool>(py) {
                if b { "true".to_string() } else { "false".to_string() }
            } else if let Ok(i) = value.extract::<i64>(py) {
                i.to_string()
            } else if let Ok(f) = value.extract::<f64>(py) {
                f.to_string()
            } else {
                // Use Python's str() representation as fallback
                value.call_method0(py, "__str__")?.extract::<String>(py)?
            };
            
            form_parts.push(format!("{}={}", 
                urlencoding::encode(&key), 
                urlencoding::encode(&value_str)
            ));
        }
        
        Ok(form_parts.join("&"))
    })
}

/// Convert Python dict to JSON value
pub fn python_dict_to_json_value(data: HashMap<String, PyObject>) -> PyResult<Value> {
    Python::with_gil(|py| {
        let mut json_map = serde_json::Map::new();
        
        for (key, value) in data {
            let json_value = python_object_to_json_value(py, &value)?;
            json_map.insert(key, json_value);
        }
        
        Ok(Value::Object(json_map))
    })
}

/// Convert Python object to JSON value recursively
fn python_object_to_json_value(py: Python, obj: &PyObject) -> PyResult<Value> {
    // Try different Python types
    if let Ok(s) = obj.extract::<String>(py) {
        Ok(Value::String(s))
    } else if let Ok(i) = obj.extract::<i64>(py) {
        Ok(Value::Number(serde_json::Number::from(i)))
    } else if let Ok(f) = obj.extract::<f64>(py) {
        if let Some(num) = serde_json::Number::from_f64(f) {
            Ok(Value::Number(num))
        } else {
            Ok(Value::Null)
        }
    } else if let Ok(b) = obj.extract::<bool>(py) {
        Ok(Value::Bool(b))
    } else if obj.is_none(py) {
        Ok(Value::Null)
    } else if let Ok(list) = obj.extract::<Vec<PyObject>>(py) {
        let mut json_array = Vec::new();
        for item in list {
            json_array.push(python_object_to_json_value(py, &item)?);
        }
        Ok(Value::Array(json_array))
    } else if let Ok(dict) = obj.extract::<HashMap<String, PyObject>>(py) {
        let mut json_map = serde_json::Map::new();
        for (key, value) in dict {
            json_map.insert(key, python_object_to_json_value(py, &value)?);
        }
        Ok(Value::Object(json_map))
    } else {
        // Fallback: convert to string
        let s = obj.call_method0(py, "__str__")?.extract::<String>(py)?;
        Ok(Value::String(s))
    }
}