use pyo3::prelude::*;
use serde_json::Value;
use std::collections::HashMap;
use crate::error::RequestError;


// Minimal utility functions - most URL/header processing delegated to reqwest
// Only keep essential interface conversion utilities

// 统一的 URL 构建函数，避免重复代码
pub fn build_url(
    url: &str, 
    base_url: Option<&String>, 
    params: Option<&HashMap<String, String>>
) -> Result<String, String> {
    let mut final_url = url.to_string();
    
    // Handle base URL if provided
    if let Some(base) = base_url {
        if !url.starts_with("http://") && !url.starts_with("https://") {
            final_url = format!("{}/{}", base.trim_end_matches('/'), url.trim_start_matches('/'));
        }
    }
    
    // Handle query parameters
    if let Some(params) = params {
        let mut parsed_url = reqwest::Url::parse(&final_url)
            .map_err(|e| format!("Invalid URL: {}", e))?;
        
        for (key, value) in params {
            parsed_url.query_pairs_mut().append_pair(key, value);
        }
        final_url = parsed_url.to_string();
    }
    
    Ok(final_url)
}

// File upload processing - delegate to reqwest multipart
pub fn build_multipart_form(files_data: HashMap<String, PyObject>) -> PyResult<reqwest::multipart::Form> {
    Python::with_gil(|py| {
        let mut form = reqwest::multipart::Form::new();
        
        for (field_name, file_obj) in files_data {
            let part = process_file_upload(py, &file_obj, &field_name)?;
            form = form.part(field_name, part);
        }
        
        Ok(form)
    })
}

fn process_file_upload(py: Python, file_obj: &PyObject, field_name: &str) -> PyResult<reqwest::multipart::Part> {
    // Process byte data
    if let Ok(bytes_data) = file_obj.extract::<Vec<u8>>(py) {
        return Ok(reqwest::multipart::Part::bytes(bytes_data)
            .file_name(format!("{}.bin", field_name))
            .mime_str("application/octet-stream")
            .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?);
    }
    
    // Process string data
    if let Ok(string_data) = file_obj.extract::<String>(py) {
        return Ok(reqwest::multipart::Part::text(string_data)
            .file_name(format!("{}.txt", field_name))
            .mime_str("text/plain")
            .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?);
    }
    
    // Process tuple format
    if let Ok((filename, content_obj)) = file_obj.extract::<(Option<String>, PyObject)>(py) {
        return process_tuple_upload(py, filename, content_obj);
    }
    
    if let Ok((filename, content_obj, content_type)) = file_obj.extract::<(Option<String>, PyObject, String)>(py) {
        return process_tuple_upload_with_type(py, filename, content_obj, content_type);
    }
    
    // Process FileUpload object
    if let Ok(bytes_data) = file_obj.call_method0(py, "to_bytes")?.extract::<Vec<u8>>(py) {
        let mut part = reqwest::multipart::Part::bytes(bytes_data);
        
        if let Ok(Some(filename)) = file_obj.getattr(py, "filename")?.extract::<Option<String>>(py) {
            part = part.file_name(filename);
        }
        
        if let Ok(content_type) = file_obj.call_method0(py, "get_content_type")?.extract::<String>(py) {
            part = part.mime_str(&content_type)
                .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?;
        }
        
        return Ok(part);
    }
    
    Err(RequestError::new_err(format!(
        "Unsupported file format for field '{}'. Expected bytes, string, tuple, or FileUpload object.",
        field_name
    )))
}

fn process_tuple_upload(py: Python, filename: Option<String>, content_obj: PyObject) -> PyResult<reqwest::multipart::Part> {
    if let Ok(bytes_content) = content_obj.extract::<Vec<u8>>(py) {
        let mut part = reqwest::multipart::Part::bytes(bytes_content);
        
        if let Some(fname) = filename {
            if let Some(mime_type) = guess_mime_type(&fname) {
                part = part.mime_str(&mime_type)
                    .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?;
            }
            part = part.file_name(fname);
        }
        
        Ok(part)
    } else if let Ok(string_content) = content_obj.extract::<String>(py) {
        let mut part = reqwest::multipart::Part::text(string_content);
        
        if let Some(fname) = filename {
            part = part.file_name(fname);
        }
        
        Ok(part)
    } else {
        Err(RequestError::new_err("Invalid content type in tuple format".to_string()))
    }
}

fn process_tuple_upload_with_type(py: Python, filename: Option<String>, content_obj: PyObject, content_type: String) -> PyResult<reqwest::multipart::Part> {
    if let Ok(bytes_content) = content_obj.extract::<Vec<u8>>(py) {
        let mut part = reqwest::multipart::Part::bytes(bytes_content)
            .mime_str(&content_type)
            .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?;
        
        if let Some(fname) = filename {
            part = part.file_name(fname);
        }
        
        Ok(part)
    } else if let Ok(string_content) = content_obj.extract::<String>(py) {
        let mut part = reqwest::multipart::Part::text(string_content)
            .mime_str(&content_type)
            .map_err(|e| RequestError::new_err(format!("Invalid mime type: {}", e)))?;
        
        if let Some(fname) = filename {
            part = part.file_name(fname);
        }
        
        Ok(part)
    } else {
        Err(RequestError::new_err("Invalid content type in tuple format".to_string()))
    }
}

fn guess_mime_type(filename: &str) -> Option<String> {
    let extension = std::path::Path::new(filename)
        .extension()?
        .to_str()?
        .to_lowercase();
    
    match extension.as_str() {
        "txt" => Some("text/plain".to_string()),
        "html" | "htm" => Some("text/html".to_string()),
        "css" => Some("text/css".to_string()),
        "js" => Some("application/javascript".to_string()),
        "json" => Some("application/json".to_string()),
        "xml" => Some("application/xml".to_string()),
        "pdf" => Some("application/pdf".to_string()),
        "png" => Some("image/png".to_string()),
        "jpg" | "jpeg" => Some("image/jpeg".to_string()),
        "gif" => Some("image/gif".to_string()),
        "svg" => Some("image/svg+xml".to_string()),
        "mp4" => Some("video/mp4".to_string()),
        "mp3" => Some("audio/mpeg".to_string()),
        "zip" => Some("application/zip".to_string()),
        "csv" => Some("text/csv".to_string()),
        "xlsx" => Some("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet".to_string()),
        "docx" => Some("application/vnd.openxmlformats-officedocument.wordprocessingml.document".to_string()),
        _ => Some("application/octet-stream".to_string()),
    }
}

// Python data conversion tools
pub fn python_dict_to_json_value(data: HashMap<String, PyObject>) -> PyResult<Value> {
    let mut map = serde_json::Map::new();
    
    Python::with_gil(|py| {
        for (key, value) in data {
            let json_value = python_to_json_value(py, &value)?;
            map.insert(key, json_value);
        }
        Ok(Value::Object(map))
    })
}

pub fn python_dict_to_form_string(data: HashMap<String, PyObject>) -> PyResult<String> {
    let mut form_pairs = Vec::new();
    
    Python::with_gil(|py| {
        for (key, value) in data {
            let value_str = if value.is_none(py) {
                "".to_string()
            } else {
                format!("{}", value.as_ref(py))
            };
            form_pairs.push(format!("{}={}", 
                urlencoding::encode(&key), 
                urlencoding::encode(&value_str)
            ));
        }
        Ok(form_pairs.join("&"))
    })
}

fn python_to_json_value(py: Python, obj: &PyObject) -> PyResult<Value> {
    if obj.is_none(py) {
        Ok(Value::Null)
    } else if let Ok(b) = obj.extract::<bool>(py) {
        Ok(Value::Bool(b))
    } else if let Ok(i) = obj.extract::<i64>(py) {
        Ok(Value::Number(serde_json::Number::from(i)))
    } else if let Ok(f) = obj.extract::<f64>(py) {
        Ok(Value::Number(serde_json::Number::from_f64(f).unwrap_or_else(|| serde_json::Number::from(0))))
    } else if let Ok(s) = obj.extract::<String>(py) {
        Ok(Value::String(s))
    } else {
        Ok(Value::String(format!("{}", obj.as_ref(py))))
    }
} 