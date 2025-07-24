use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use std::collections::HashMap;
use url::Url;
use reqwest::Proxy;
use crate::error::RequestError;

/// 代理类型枚举
#[derive(Clone, Debug)]
pub enum ProxyType {
    Http,
    Https,
    Socks5,
    Socks4,
}

/// 代理认证信息
#[derive(Clone, Debug)]
pub struct ProxyAuth {
    pub username: String,
    pub password: String,
}

/// 单个代理配置
#[derive(Clone, Debug)]
pub struct ProxyConfig {
    /// 代理类型
    pub proxy_type: ProxyType,
    /// 代理服务器地址
    pub host: String,
    /// 代理服务器端口
    pub port: u16,
    /// 认证信息
    pub auth: Option<ProxyAuth>,
    /// 完整的代理URL
    pub url: String,
}

impl ProxyConfig {
    /// 从URL字符串创建代理配置
    pub fn from_url(proxy_url: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let url = Url::parse(proxy_url)?;
        
        let proxy_type = match url.scheme() {
            "http" => ProxyType::Http,
            "https" => ProxyType::Https,
            "socks5" => ProxyType::Socks5,
            "socks4" => ProxyType::Socks4,
            scheme => return Err(format!("Unsupported proxy scheme: {}", scheme).into()),
        };
        
        let host = url.host_str()
            .ok_or("Missing proxy host")?
            .to_string();
        
        let port = url.port()
            .unwrap_or(match proxy_type {
                ProxyType::Http => 80,
                ProxyType::Https => 443,
                ProxyType::Socks5 | ProxyType::Socks4 => 1080,
            });
        
        let auth = if let Some(password) = url.password() {
            Some(ProxyAuth {
                username: url.username().to_string(),
                password: password.to_string(),
            })
        } else if !url.username().is_empty() {
            Some(ProxyAuth {
                username: url.username().to_string(),
                password: String::new(),
            })
        } else {
            None
        };
        
        Ok(ProxyConfig {
            proxy_type,
            host,
            port,
            auth,
            url: proxy_url.to_string(),
        })
    }
    
    /// 将代理配置转换为reqwest::Proxy
    pub fn to_reqwest_proxy(&self) -> Result<Proxy, Box<dyn std::error::Error>> {
        let proxy = match self.proxy_type {
            ProxyType::Http | ProxyType::Https => {
                Proxy::http(&self.url)?
            },
            ProxyType::Socks5 => {
                // reqwest内置支持SOCKS5
                // 注意：这需要reqwest的socks feature
                Proxy::all(&self.url).map_err(|e| {
                    format!("SOCKS5 proxy error (ensure reqwest socks feature is enabled): {}", e)
                })?
            },
            ProxyType::Socks4 => {
                return Err("SOCKS4 proxy not supported by reqwest".into());
            },
        };
        
        Ok(proxy)
    }
}

/// 高级代理配置系统
#[derive(Clone, Debug)]
pub struct ProxySystem {
    /// 默认代理配置 (用于所有请求)
    pub default_proxy: Option<ProxyConfig>,
    /// 按scheme挂载的代理 (http://, https://)
    pub scheme_proxies: HashMap<String, ProxyConfig>,
    /// 按域名挂载的代理
    pub domain_proxies: HashMap<String, ProxyConfig>,
    /// 按完整URL模式挂载的代理
    pub url_proxies: HashMap<String, ProxyConfig>,
    /// 不使用代理的域名列表
    pub no_proxy: Vec<String>,
    /// 是否信任环境变量 (HTTP_PROXY, HTTPS_PROXY, NO_PROXY)
    pub trust_env: bool,
}

impl Default for ProxySystem {
    fn default() -> Self {
        ProxySystem {
            default_proxy: None,
            scheme_proxies: HashMap::new(),
            domain_proxies: HashMap::new(),
            url_proxies: HashMap::new(),
            no_proxy: Vec::new(),
            trust_env: true,
        }
    }
}

impl ProxySystem {
    /// 从Python参数创建代理系统
    pub fn from_python_params(
        proxy: Option<&PyAny>,
        proxies: Option<&PyDict>,
        trust_env: Option<bool>,
    ) -> PyResult<Self> {
        let mut system = ProxySystem::default();
        
        if let Some(trust) = trust_env {
            system.trust_env = trust;
        }
        
        // 处理单个代理配置
        if let Some(proxy_obj) = proxy {
            let proxy_url = if let Ok(proxy_str) = proxy_obj.downcast::<PyString>() {
                proxy_str.to_str()?.to_string()
            } else {
                return Err(pyo3::exceptions::PyTypeError::new_err(
                    "proxy must be a string URL"
                ));
            };
            
            let proxy_config = ProxyConfig::from_url(&proxy_url)
                .map_err(|e| RequestError::new_err(format!("Invalid proxy URL: {}", e)))?;
                
            system.default_proxy = Some(proxy_config);
        }
        
        // 处理代理字典 (scheme/domain -> proxy)
        if let Some(proxies_dict) = proxies {
            for (key, value) in proxies_dict.iter() {
                let key_str = key.downcast::<PyString>()?.to_str()?;
                let proxy_url = value.downcast::<PyString>()?.to_str()?;
                
                let proxy_config = ProxyConfig::from_url(proxy_url)
                    .map_err(|e| RequestError::new_err(format!("Invalid proxy URL for '{}': {}", key_str, e)))?;
                
                if key_str.ends_with("://") {
                    // scheme proxy (e.g., "http://", "https://")
                    system.scheme_proxies.insert(key_str.to_string(), proxy_config);
                } else if key_str.starts_with("http://") || key_str.starts_with("https://") {
                    // URL pattern proxy
                    system.url_proxies.insert(key_str.to_string(), proxy_config);
                } else {
                    // domain proxy
                    system.domain_proxies.insert(key_str.to_string(), proxy_config);
                }
            }
        }
        
        // 加载环境变量
        if system.trust_env {
            system.load_from_environment();
        }
        
        Ok(system)
    }
    
    /// 从环境变量加载代理配置
    pub fn load_from_environment(&mut self) {
        // HTTP_PROXY
        if let Ok(http_proxy) = std::env::var("HTTP_PROXY") {
            if !http_proxy.is_empty() {
                if let Ok(config) = ProxyConfig::from_url(&http_proxy) {
                    self.scheme_proxies.insert("http://".to_string(), config);
                }
            }
        }
        
        // HTTPS_PROXY
        if let Ok(https_proxy) = std::env::var("HTTPS_PROXY") {
            if !https_proxy.is_empty() {
                if let Ok(config) = ProxyConfig::from_url(&https_proxy) {
                    self.scheme_proxies.insert("https://".to_string(), config);
                }
            }
        }
        
        // ALL_PROXY (fallback for all schemes)
        if let Ok(all_proxy) = std::env::var("ALL_PROXY") {
            if !all_proxy.is_empty() && self.default_proxy.is_none() {
                if let Ok(config) = ProxyConfig::from_url(&all_proxy) {
                    self.default_proxy = Some(config);
                }
            }
        }
        
        // NO_PROXY
        if let Ok(no_proxy) = std::env::var("NO_PROXY") {
            if !no_proxy.is_empty() {
                self.no_proxy = no_proxy.split(',')
                    .map(|s| s.trim().to_string())
                    .filter(|s| !s.is_empty())
                    .collect();
            }
        }
    }
    
    /// 为指定URL选择合适的代理
    pub fn select_proxy_for_url(&self, url: &str) -> Option<&ProxyConfig> {
        // 检查NO_PROXY列表
        if let Ok(parsed_url) = Url::parse(url) {
            if let Some(host) = parsed_url.host_str() {
                for no_proxy_pattern in &self.no_proxy {
                    if no_proxy_pattern == "*" || 
                       host == no_proxy_pattern ||
                       host.ends_with(&format!(".{}", no_proxy_pattern)) {
                        return None; // 不使用代理
                    }
                }
            }
            
            // 1. 检查完整URL匹配
            if let Some(proxy) = self.url_proxies.get(url) {
                return Some(proxy);
            }
            
            // 2. 检查域名匹配
            if let Some(host) = parsed_url.host_str() {
                if let Some(proxy) = self.domain_proxies.get(host) {
                    return Some(proxy);
                }
            }
            
            // 3. 检查scheme匹配
            let scheme_pattern = format!("{}://", parsed_url.scheme());
            if let Some(proxy) = self.scheme_proxies.get(&scheme_pattern) {
                return Some(proxy);
            }
        }
        
        // 4. 返回默认代理
        self.default_proxy.as_ref()
    }
    
    /// 检查URL是否应该使用代理
    pub fn should_use_proxy(&self, url: &str) -> bool {
        self.select_proxy_for_url(url).is_some()
    }
    
    /// 为reqwest客户端构建器应用代理配置
    pub fn apply_to_client_builder(
        &self,
        builder: reqwest::ClientBuilder,
        url: &str,
    ) -> Result<reqwest::ClientBuilder, Box<dyn std::error::Error>> {
        if let Some(proxy_config) = self.select_proxy_for_url(url) {
            let reqwest_proxy = proxy_config.to_reqwest_proxy()?;
            Ok(builder.proxy(reqwest_proxy))
        } else {
            Ok(builder)
        }
    }
    
    /// 获取代理统计信息
    pub fn get_proxy_stats(&self) -> HashMap<String, usize> {
        let mut stats = HashMap::new();
        
        if self.default_proxy.is_some() {
            stats.insert("default".to_string(), 1);
        }
        
        stats.insert("scheme_proxies".to_string(), self.scheme_proxies.len());
        stats.insert("domain_proxies".to_string(), self.domain_proxies.len());
        stats.insert("url_proxies".to_string(), self.url_proxies.len());
        stats.insert("no_proxy_patterns".to_string(), self.no_proxy.len());
        
        stats
    }
    
    /// 验证所有代理配置
    pub fn validate_all_proxies(&self) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();
        
        // 验证默认代理
        if let Some(proxy) = &self.default_proxy {
            if let Err(e) = proxy.to_reqwest_proxy() {
                errors.push(format!("Default proxy error: {}", e));
            }
        }
        
        // 验证scheme代理
        for (scheme, proxy) in &self.scheme_proxies {
            if let Err(e) = proxy.to_reqwest_proxy() {
                errors.push(format!("Scheme proxy '{}' error: {}", scheme, e));
            }
        }
        
        // 验证域名代理
        for (domain, proxy) in &self.domain_proxies {
            if let Err(e) = proxy.to_reqwest_proxy() {
                errors.push(format!("Domain proxy '{}' error: {}", domain, e));
            }
        }
        
        // 验证URL代理
        for (url_pattern, proxy) in &self.url_proxies {
            if let Err(e) = proxy.to_reqwest_proxy() {
                errors.push(format!("URL proxy '{}' error: {}", url_pattern, e));
            }
        }
        
        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_proxy_config_from_url() {
        // HTTP代理
        let config = ProxyConfig::from_url("http://proxy.example.com:8080").unwrap();
        assert!(matches!(config.proxy_type, ProxyType::Http));
        assert_eq!(config.host, "proxy.example.com");
        assert_eq!(config.port, 8080);
        assert!(config.auth.is_none());
        
        // 带认证的HTTPS代理
        let config = ProxyConfig::from_url("https://user:pass@proxy.example.com:3128").unwrap();
        assert!(matches!(config.proxy_type, ProxyType::Https));
        assert_eq!(config.host, "proxy.example.com");
        assert_eq!(config.port, 3128);
        assert!(config.auth.is_some());
        let auth = config.auth.unwrap();
        assert_eq!(auth.username, "user");
        assert_eq!(auth.password, "pass");
    }
    
    #[test]
    fn test_proxy_system_url_selection() {
        let mut system = ProxySystem::default();
        
        // 添加scheme代理
        let http_proxy = ProxyConfig::from_url("http://http-proxy.com:8080").unwrap();
        system.scheme_proxies.insert("http://".to_string(), http_proxy);
        
        // 测试HTTP URL
        let proxy = system.select_proxy_for_url("http://example.com/test");
        assert!(proxy.is_some());
        assert_eq!(proxy.unwrap().host, "http-proxy.com");
        
        // 测试HTTPS URL (没有配置，应该返回None)
        let proxy = system.select_proxy_for_url("https://example.com/test");
        assert!(proxy.is_none());
    }
    
    #[test]
    fn test_no_proxy_patterns() {
        let mut system = ProxySystem::default();
        system.default_proxy = Some(ProxyConfig::from_url("http://proxy.com:8080").unwrap());
        system.no_proxy = vec!["localhost".to_string(), "example.com".to_string()];
        
        // 应该使用代理
        assert!(system.should_use_proxy("http://other.com/test"));
        
        // 不应该使用代理
        assert!(!system.should_use_proxy("http://localhost/test"));
        assert!(!system.should_use_proxy("http://example.com/test"));
        assert!(!system.should_use_proxy("http://sub.example.com/test"));
    }
}