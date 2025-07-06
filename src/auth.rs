// Authentication types enum - minimal interface for reqwest delegation
use pyo3::prelude::*;
use crate::models::{HttpBasicAuth, HttpDigestAuth, HttpNetRCAuth};

#[derive(Clone)]
pub enum AuthType {
    Basic { username: String, password: String },
    Digest { username: String, password: String },
    NetRC { file: Option<String> },
    Bearer { token: String },
}

// Convert Python auth objects to AuthType enum for reqwest processing
pub fn extract_auth_from_object(auth_obj: &PyObject) -> PyResult<Option<AuthType>> {
    Python::with_gil(|py| {
        // Try to extract as BasicAuth
        if let Ok(basic_auth) = auth_obj.extract::<HttpBasicAuth>(py) {
            return Ok(Some(AuthType::Basic {
                username: basic_auth.username(),
                password: basic_auth.password(),
            }));
        }
        
        // Try to extract as DigestAuth
        if let Ok(digest_auth) = auth_obj.extract::<HttpDigestAuth>(py) {
            return Ok(Some(AuthType::Digest {
                username: digest_auth.username(),
                password: digest_auth.password(),
            }));
        }
        
        // Try to extract as NetRCAuth
        if let Ok(netrc_auth) = auth_obj.extract::<HttpNetRCAuth>(py) {
            return Ok(Some(AuthType::NetRC {
                file: Some(netrc_auth.file()),
            }));
        }
        
        // If none of the above, return None
        Ok(None)
    })
}

pub fn extract_auth(auth: &Option<AuthType>) -> Option<(String, String)> {
    match auth {
        Some(AuthType::Basic { username, password }) => Some((username.clone(), password.clone())),
        Some(AuthType::Digest { username, password }) => Some((username.clone(), password.clone())),
        _ => None,
    }
} 