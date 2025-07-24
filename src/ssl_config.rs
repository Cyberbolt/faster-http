use pyo3::prelude::*;
use pyo3::types::{PyBool, PyString};
use reqwest::Identity;
use std::path::PathBuf;

/// SSL配置结构体 - 对应httpx的SSL配置选项
#[derive(Clone, Debug)]
pub struct SslConfig {
    /// SSL验证设置 - 对应httpx的verify参数
    pub verify: SslVerifyMode,
    /// 客户端证书配置 - 对应httpx的cert参数  
    pub client_cert: Option<ClientCertConfig>,
    /// 自定义CA bundle路径
    pub ca_bundle: Option<PathBuf>,
    /// 是否信任环境变量 (SSL_CERT_FILE等)
    pub trust_env: bool,
    /// SSL/TLS协议版本限制
    pub min_version: Option<SslVersion>,
    pub max_version: Option<SslVersion>,
    /// 是否验证主机名
    pub check_hostname: bool,
}

/// SSL验证模式
#[derive(Clone, Debug)]
pub enum SslVerifyMode {
    /// 启用SSL验证，使用默认CA bundle
    Enabled,
    /// 禁用SSL验证
    Disabled,
    /// 使用自定义CA bundle文件
    CustomCaFile(PathBuf),
    /// 使用自定义CA目录
    CustomCaDir(PathBuf),
}

/// 客户端证书配置
#[derive(Clone, Debug)]
pub struct ClientCertConfig {
    /// 证书文件路径
    pub cert_file: PathBuf,
    /// 私钥文件路径 (如果与证书文件分开)
    pub key_file: Option<PathBuf>,
    /// 私钥密码
    pub password: Option<String>,
}

/// SSL/TLS协议版本
#[derive(Clone, Debug)]
pub enum SslVersion {
    TlsV10,
    TlsV11, 
    TlsV12,
    TlsV13,
}

impl Default for SslConfig {
    fn default() -> Self {
        SslConfig {
            verify: SslVerifyMode::Enabled,
            client_cert: None,
            ca_bundle: None,
            trust_env: true,
            min_version: Some(SslVersion::TlsV12), // 默认最低TLS 1.2
            max_version: None,
            check_hostname: true,
        }
    }
}

impl SslConfig {
    /// 从Python对象创建SSL配置
    pub fn from_python_params(
        verify: Option<&PyAny>,
        cert: Option<&PyAny>,
        trust_env: Option<bool>,
    ) -> PyResult<Self> {
        let mut config = SslConfig::default();
        
        // 处理verify参数
        if let Some(verify_obj) = verify {
            config.verify = Self::parse_verify_param(verify_obj)?;
        }
        
        // 处理cert参数
        if let Some(cert_obj) = cert {
            config.client_cert = Some(Self::parse_cert_param(cert_obj)?);
        }
        
        // 处理trust_env参数
        if let Some(trust) = trust_env {
            config.trust_env = trust;
        }
        
        Ok(config)
    }
    
    /// 解析verify参数
    fn parse_verify_param(verify_obj: &PyAny) -> PyResult<SslVerifyMode> {
        // 尝试解析为bool
        if let Ok(verify_bool) = verify_obj.downcast::<PyBool>() {
            return Ok(if verify_bool.is_true() {
                SslVerifyMode::Enabled
            } else {
                SslVerifyMode::Disabled
            });
        }
        
        // 尝试解析为字符串路径
        if let Ok(verify_str) = verify_obj.downcast::<PyString>() {
            let path_str = verify_str.to_str()?;
            let path = PathBuf::from(path_str);
            
            // 检查是文件还是目录
            if path.is_file() {
                return Ok(SslVerifyMode::CustomCaFile(path));
            } else if path.is_dir() {
                return Ok(SslVerifyMode::CustomCaDir(path));
            } else {
                // 路径不存在，假设是文件
                return Ok(SslVerifyMode::CustomCaFile(path));
            }
        }
        
        // TODO: 处理ssl.SSLContext对象
        // 目前先返回启用验证
        Ok(SslVerifyMode::Enabled)
    }
    
    /// 解析cert参数
    fn parse_cert_param(cert_obj: &PyAny) -> PyResult<ClientCertConfig> {
        // 尝试解析为字符串 (单个证书文件)
        if let Ok(cert_str) = cert_obj.downcast::<PyString>() {
            let cert_path = PathBuf::from(cert_str.to_str()?);
            return Ok(ClientCertConfig {
                cert_file: cert_path,
                key_file: None,
                password: None,
            });
        }
        
        // 尝试解析为元组 (cert_file, key_file)
        if let Ok(cert_tuple) = cert_obj.extract::<(String, String)>() {
            return Ok(ClientCertConfig {
                cert_file: PathBuf::from(cert_tuple.0),
                key_file: Some(PathBuf::from(cert_tuple.1)),
                password: None,
            });
        }
        
        // 尝试解析为三元组 (cert_file, key_file, password)
        if let Ok(cert_triple) = cert_obj.extract::<(String, String, String)>() {
            return Ok(ClientCertConfig {
                cert_file: PathBuf::from(cert_triple.0),
                key_file: Some(PathBuf::from(cert_triple.1)),
                password: Some(cert_triple.2),
            });
        }
        
        Err(pyo3::exceptions::PyValueError::new_err(
            "cert parameter must be a string path, (cert_file, key_file) tuple, or (cert_file, key_file, password) tuple"
        ))
    }
    
    /// 将SSL配置应用到reqwest客户端构建器
    pub fn apply_to_client_builder(
        &self,
        builder: reqwest::ClientBuilder,
    ) -> Result<reqwest::ClientBuilder, Box<dyn std::error::Error>> {
        let mut builder = builder;
        
        // 配置SSL验证
        match &self.verify {
            SslVerifyMode::Enabled => {
                builder = builder.tls_built_in_root_certs(true);
            }
            SslVerifyMode::Disabled => {
                builder = builder
                    .danger_accept_invalid_certs(true)
                    .danger_accept_invalid_hostnames(true);
            }
            SslVerifyMode::CustomCaFile(ca_file) => {
                let ca_cert = std::fs::read(ca_file)?;
                let cert = reqwest::Certificate::from_pem(&ca_cert)?;
                builder = builder.add_root_certificate(cert);
            }
            SslVerifyMode::CustomCaDir(_ca_dir) => {
                // reqwest不直接支持CA目录，需要遍历目录加载证书
                // 这里先使用默认设置，后续可以扩展
                builder = builder.tls_built_in_root_certs(true);
            }
        }
        
        // 配置客户端证书
        if let Some(client_cert) = &self.client_cert {
            let identity = self.load_client_identity(client_cert)?;
            builder = builder.identity(identity);
        }
        
        // 配置TLS版本
        if let Some(min_version) = &self.min_version {
            builder = builder.min_tls_version(self.ssl_version_to_reqwest(min_version));
        }
        if let Some(max_version) = &self.max_version {
            builder = builder.max_tls_version(self.ssl_version_to_reqwest(max_version));
        }
        
        // 配置主机名验证
        if !self.check_hostname {
            builder = builder.danger_accept_invalid_hostnames(true);
        }
        
        Ok(builder)
    }
    
    /// 加载客户端证书身份
    fn load_client_identity(&self, cert_config: &ClientCertConfig) -> Result<Identity, Box<dyn std::error::Error>> {
        if let Some(key_file) = &cert_config.key_file {
            // 分别读取证书和私钥文件
            let cert_pem = std::fs::read(&cert_config.cert_file)?;
            let key_pem = std::fs::read(key_file)?;
            
            if let Some(password) = &cert_config.password {
                // PKCS#12格式证书 (通常是.p12或.pfx文件)
                Ok(Identity::from_pkcs12_der(&cert_pem, password)?)
            } else {
                // PKCS#8格式的PEM证书和私钥
                Ok(Identity::from_pkcs8_pem(&cert_pem, &key_pem)?)
            }
        } else {
            // 证书和私钥在同一个文件中
            let cert_pem = std::fs::read(&cert_config.cert_file)?;
            
            if let Some(password) = &cert_config.password {
                // PKCS#12格式证书
                Ok(Identity::from_pkcs12_der(&cert_pem, password)?)
            } else {
                // 从单个PEM文件中提取证书和私钥
                // 这需要我们解析PEM文件分离证书和私钥
                let pem_str = String::from_utf8_lossy(&cert_pem);
                let (cert_part, key_part) = self.split_pem_cert_and_key(&pem_str)?;
                Ok(Identity::from_pkcs8_pem(cert_part.as_bytes(), key_part.as_bytes())?)
            }
        }
    }
    
    /// 从PEM文件中分离证书和私钥
    fn split_pem_cert_and_key(&self, pem_content: &str) -> Result<(String, String), Box<dyn std::error::Error>> {
        let mut cert_lines = Vec::new();
        let mut key_lines = Vec::new();
        let mut in_cert = false;
        let mut in_key = false;
        
        for line in pem_content.lines() {
            if line.contains("-----BEGIN CERTIFICATE-----") {
                in_cert = true;
                cert_lines.push(line);
            } else if line.contains("-----END CERTIFICATE-----") {
                cert_lines.push(line);
                in_cert = false;
            } else if line.contains("-----BEGIN PRIVATE KEY-----") || line.contains("-----BEGIN RSA PRIVATE KEY-----") {
                in_key = true;
                key_lines.push(line);
            } else if line.contains("-----END PRIVATE KEY-----") || line.contains("-----END RSA PRIVATE KEY-----") {
                key_lines.push(line);
                in_key = false;
            } else if in_cert {
                cert_lines.push(line);
            } else if in_key {
                key_lines.push(line);
            }
        }
        
        if cert_lines.is_empty() {
            return Err("No certificate found in PEM file".into());
        }
        if key_lines.is_empty() {
            return Err("No private key found in PEM file".into());
        }
        
        Ok((cert_lines.join("\n"), key_lines.join("\n")))
    }
    
    /// 转换SSL版本到reqwest格式
    fn ssl_version_to_reqwest(&self, version: &SslVersion) -> reqwest::tls::Version {
        match version {
            SslVersion::TlsV10 => reqwest::tls::Version::TLS_1_0,
            SslVersion::TlsV11 => reqwest::tls::Version::TLS_1_1,
            SslVersion::TlsV12 => reqwest::tls::Version::TLS_1_2,
            SslVersion::TlsV13 => reqwest::tls::Version::TLS_1_3,
        }
    }
    
    /// 从环境变量加载CA bundle
    pub fn load_ca_bundle_from_env(&mut self) {
        if !self.trust_env {
            return;
        }
        
        // 按优先级检查环境变量
        let env_vars = ["SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"];
        
        for var in &env_vars {
            if let Ok(ca_file) = std::env::var(var) {
                let path = PathBuf::from(ca_file);
                if path.exists() {
                    self.ca_bundle = Some(path.clone());
                    self.verify = SslVerifyMode::CustomCaFile(path);
                    break;
                }
            }
        }
        
        // 检查SSL_CERT_DIR
        if let Ok(ca_dir) = std::env::var("SSL_CERT_DIR") {
            let path = PathBuf::from(ca_dir);
            if path.exists() && path.is_dir() {
                self.verify = SslVerifyMode::CustomCaDir(path);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_default_ssl_config() {
        let config = SslConfig::default();
        assert!(matches!(config.verify, SslVerifyMode::Enabled));
        assert!(config.client_cert.is_none());
        assert!(config.trust_env);
        assert!(config.check_hostname);
    }
    
    #[test]
    fn test_ssl_config_with_disabled_verify() {
        let mut config = SslConfig::default();
        config.verify = SslVerifyMode::Disabled;
        
        let builder = reqwest::ClientBuilder::new();
        let result = config.apply_to_client_builder(builder);
        assert!(result.is_ok());
    }
}