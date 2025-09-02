// Simplified authentication types - pure conversion layer
use pyo3::prelude::*;

/// Simplified auth types enum for format conversion
#[derive(Clone)]
pub enum AuthType {
    Basic { username: String, password: String },
    Bearer { token: String },
}

// SECURITY: Custom Debug implementation to prevent credential leakage
impl std::fmt::Debug for AuthType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AuthType::Basic { username, .. } => f
                .debug_struct("Basic")
                .field("username", username)
                .field("password", &"***REDACTED***")
                .finish(),
            AuthType::Bearer { .. } => f
                .debug_struct("Bearer")
                .field("token", &"***REDACTED***")
                .finish(),
        }
    }
}

/// Simple auth extraction from Python objects - minimal processing
pub fn extract_auth_from_object(auth_obj: &PyObject) -> PyResult<Option<AuthType>> {
    Python::with_gil(|py| {
        // Try to extract as basic tuple (username, password)
        if let Ok((username, password)) = auth_obj.extract::<(String, String)>(py) {
            return Ok(Some(AuthType::Basic { username, password }));
        }

        // Try to extract as bearer token string
        if let Ok(token) = auth_obj.extract::<String>(py) {
            return Ok(Some(AuthType::Bearer { token }));
        }

        // Default to None if extraction fails
        Ok(None)
    })
}

/// Extract auth credentials as tuple - simple conversion
pub fn extract_auth(auth: &Option<AuthType>) -> Option<(String, String)> {
    match auth {
        Some(AuthType::Basic { username, password }) => Some((username.clone(), password.clone())),
        _ => None,
    }
}
