// 认证类型枚举
#[derive(Clone)]
pub enum AuthType {
    Basic { username: String, password: String },
    Bearer { token: String },
}

pub fn extract_auth(auth: &Option<AuthType>) -> Option<(String, String)> {
    match auth {
        Some(AuthType::Basic { username, password }) => Some((username.clone(), password.clone())),
        _ => None,
    }
} 