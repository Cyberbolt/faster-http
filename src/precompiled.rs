// ULTRA-OPTIMIZED: Precompiled HTTP methods and headers for A级 performance
// Eliminates runtime string parsing and provides O(1) lookups

use hyper::Method;
use std::collections::HashMap;
use std::sync::OnceLock;

/// EXTREME OPTIMIZATION: Precompiled HTTP methods with direct Method instances
#[allow(dead_code)]
pub struct PrecompiledMethods {
    /// Direct method mapping for O(1) lookup
    methods: HashMap<&'static str, Method>,
    /// Reverse lookup for method to string
    method_strings: HashMap<Method, &'static str>,
}

#[allow(dead_code)]
impl PrecompiledMethods {
    pub fn new() -> Self {
        let mut methods = HashMap::new();
        let mut method_strings = HashMap::new();

        // Pre-compile all common HTTP methods
        let method_pairs = [
            ("GET", Method::GET),
            ("POST", Method::POST), 
            ("PUT", Method::PUT),
            ("DELETE", Method::DELETE),
            ("PATCH", Method::PATCH),
            ("HEAD", Method::HEAD),
            ("OPTIONS", Method::OPTIONS),
            ("TRACE", Method::TRACE),
            ("CONNECT", Method::CONNECT),
        ];

        for (name, method) in method_pairs {
            methods.insert(name, method.clone());
            method_strings.insert(method, name);
        }

        Self { methods, method_strings }
    }

    /// ULTRA-FAST: Get Method from string with O(1) lookup
    #[inline(always)]
    pub fn get_method(&self, method_str: &str) -> Option<&Method> {
        self.methods.get(method_str)
    }

    /// ULTRA-FAST: Get string from Method with O(1) lookup  
    #[inline(always)]
    pub fn get_method_string(&self, method: &Method) -> Option<&'static str> {
        self.method_strings.get(method).copied()
    }

    /// Check if method is precompiled
    #[inline(always)]
    pub fn is_precompiled(&self, method_str: &str) -> bool {
        self.methods.contains_key(method_str)
    }
}

/// EXTREME OPTIMIZATION: Precompiled header names with case-insensitive lookup
#[allow(dead_code)]
pub struct PrecompiledHeaders {
    /// Canonical header names
    canonical_names: HashMap<&'static str, &'static str>,
    /// Lowercase to canonical mapping for case-insensitive lookup
    lowercase_map: HashMap<&'static str, &'static str>,
    /// Common header values
    common_values: HashMap<&'static str, &'static str>,
}

#[allow(dead_code)]
impl PrecompiledHeaders {
    pub fn new() -> Self {
        let header_pairs = [
            // Standard headers
            ("content-type", "Content-Type"),
            ("content-length", "Content-Length"),
            ("accept", "Accept"),
            ("accept-encoding", "Accept-Encoding"),
            ("accept-language", "Accept-Language"),
            ("authorization", "Authorization"),
            ("user-agent", "User-Agent"),
            ("host", "Host"),
            ("connection", "Connection"),
            ("cache-control", "Cache-Control"),
            ("cookie", "Cookie"),
            ("set-cookie", "Set-Cookie"),
            ("location", "Location"),
            ("referer", "Referer"),
            ("origin", "Origin"),
            ("x-forwarded-for", "X-Forwarded-For"),
            ("x-real-ip", "X-Real-IP"),
            ("x-requested-with", "X-Requested-With"),
            ("if-modified-since", "If-Modified-Since"),
            ("last-modified", "Last-Modified"),
            ("etag", "ETag"),
            ("if-none-match", "If-None-Match"),
            ("transfer-encoding", "Transfer-Encoding"),
            ("upgrade", "Upgrade"),
            ("sec-websocket-key", "Sec-WebSocket-Key"),
            ("sec-websocket-accept", "Sec-WebSocket-Accept"),
            ("access-control-allow-origin", "Access-Control-Allow-Origin"),
            ("access-control-allow-methods", "Access-Control-Allow-Methods"),
            ("access-control-allow-headers", "Access-Control-Allow-Headers"),
            ("access-control-max-age", "Access-Control-Max-Age"),
            ("vary", "Vary"),
            ("server", "Server"),
            ("date", "Date"),
            ("expires", "Expires"),
            ("pragma", "Pragma"),
        ];

        let value_pairs = [
            // Content-Type values
            ("application/json", "application/json"),
            ("application/x-www-form-urlencoded", "application/x-www-form-urlencoded"),
            ("text/html", "text/html"),
            ("text/plain", "text/plain"),
            ("text/xml", "text/xml"),
            ("application/xml", "application/xml"),
            ("application/octet-stream", "application/octet-stream"),
            ("multipart/form-data", "multipart/form-data"),
            ("image/jpeg", "image/jpeg"),
            ("image/png", "image/png"),
            ("image/gif", "image/gif"),
            
            // Accept-Encoding values
            ("gzip", "gzip"),
            ("deflate", "deflate"),
            ("br", "br"),
            ("gzip, deflate", "gzip, deflate"),
            ("gzip, deflate, br", "gzip, deflate, br"),
            
            // Connection values
            ("keep-alive", "keep-alive"),
            ("close", "close"),
            ("upgrade", "upgrade"),
            
            // Cache-Control values
            ("no-cache", "no-cache"),
            ("no-store", "no-store"),
            ("max-age=0", "max-age=0"),
            ("public", "public"),
            ("private", "private"),
            
            // Common values
            ("*/*", "*/*"),
            ("chunked", "chunked"),
            ("identity", "identity"),
        ];

        let mut canonical_names = HashMap::new();
        let mut lowercase_map = HashMap::new();
        let mut common_values = HashMap::new();

        // Build header name mappings
        for (lowercase, canonical) in header_pairs {
            canonical_names.insert(canonical, canonical);
            lowercase_map.insert(lowercase, canonical);
        }

        // Build value mappings
        for (value, canonical) in value_pairs {
            common_values.insert(value, canonical);
        }

        Self {
            canonical_names,
            lowercase_map,
            common_values,
        }
    }

    /// ULTRA-FAST: Get canonical header name with O(1) lookup
    #[inline(always)]
    pub fn get_canonical_name(&self, name: &str) -> &'static str {
        // Try direct lookup first
        if let Some(canonical) = self.canonical_names.get(name) {
            return canonical;
        }

        // Try lowercase lookup
        let lowercase = name.to_lowercase();
        self.lowercase_map.get(lowercase.as_str()).unwrap_or(&"Unknown-Header")
    }

    /// ULTRA-FAST: Get canonical header value with O(1) lookup
    #[inline(always)]
    pub fn get_canonical_value<'a>(&self, value: &'a str) -> &'a str {
        self.common_values.get(value).unwrap_or(&value)
    }

    /// Check if header name is precompiled
    #[inline(always)]
    pub fn is_precompiled_name(&self, name: &str) -> bool {
        self.canonical_names.contains_key(name) || 
        self.lowercase_map.contains_key(&name.to_lowercase().as_str())
    }

    /// Check if header value is precompiled
    #[inline(always)]  
    pub fn is_precompiled_value(&self, value: &str) -> bool {
        self.common_values.contains_key(value)
    }
}

/// EXTREME OPTIMIZATION: Precompiled URL schemes and ports
#[allow(dead_code)]
pub struct PrecompiledSchemes {
    /// Default ports for schemes
    default_ports: HashMap<&'static str, u16>,
    /// Secure schemes
    secure_schemes: &'static [&'static str],
}

#[allow(dead_code)]
impl PrecompiledSchemes {
    pub fn new() -> Self {
        let mut default_ports = HashMap::new();
        default_ports.insert("http", 80);
        default_ports.insert("https", 443);
        default_ports.insert("ftp", 21);
        default_ports.insert("ftps", 990);
        default_ports.insert("ssh", 22);
        default_ports.insert("telnet", 23);
        default_ports.insert("smtp", 25);
        default_ports.insert("dns", 53);
        default_ports.insert("tftp", 69);
        default_ports.insert("pop3", 110);
        default_ports.insert("imap", 143);
        default_ports.insert("snmp", 161);
        default_ports.insert("ldap", 389);
        default_ports.insert("smtps", 465);
        default_ports.insert("imaps", 993);
        default_ports.insert("pop3s", 995);

        Self {
            default_ports,
            secure_schemes: &["https", "ftps", "smtps", "imaps", "pop3s"],
        }
    }

    /// Get default port for scheme
    #[inline(always)]
    pub fn get_default_port(&self, scheme: &str) -> Option<u16> {
        self.default_ports.get(scheme).copied()
    }

    /// Check if scheme is secure
    #[inline(always)]
    pub fn is_secure_scheme(&self, scheme: &str) -> bool {
        self.secure_schemes.contains(&scheme)
    }
}

/// ULTRA-PERFORMANCE: Global precompiled instances for maximum speed
static PRECOMPILED_METHODS: OnceLock<PrecompiledMethods> = OnceLock::new();
static PRECOMPILED_HEADERS: OnceLock<PrecompiledHeaders> = OnceLock::new();
#[allow(dead_code)]
static PRECOMPILED_SCHEMES: OnceLock<PrecompiledSchemes> = OnceLock::new();

/// Get global precompiled methods instance
#[inline(always)]
pub fn get_precompiled_methods() -> &'static PrecompiledMethods {
    PRECOMPILED_METHODS.get_or_init(PrecompiledMethods::new)
}

/// Get global precompiled headers instance  
#[inline(always)]
pub fn get_precompiled_headers() -> &'static PrecompiledHeaders {
    PRECOMPILED_HEADERS.get_or_init(PrecompiledHeaders::new)
}

/// Get global precompiled schemes instance
#[inline(always)]
#[allow(dead_code)]
pub fn get_precompiled_schemes() -> &'static PrecompiledSchemes {
    PRECOMPILED_SCHEMES.get_or_init(PrecompiledSchemes::new)
}

/// ULTRA-OPTIMIZED: Parse HTTP method with precompiled lookup
#[inline(always)]
pub fn parse_method_optimized(method_str: &str) -> Result<Method, String> {
    let precompiled = get_precompiled_methods();
    
    if let Some(method) = precompiled.get_method(method_str) {
        Ok(method.clone())
    } else {
        // Fallback to standard parsing for uncommon methods
        method_str.parse::<Method>()
            .map_err(|e| format!("Invalid HTTP method: {}", e))
    }
}

/// ULTRA-OPTIMIZED: Normalize header name with precompiled lookup
#[inline(always)]
pub fn normalize_header_name(name: &str) -> &'static str {
    get_precompiled_headers().get_canonical_name(name)
}

/// ULTRA-OPTIMIZED: Normalize header value with precompiled lookup
#[inline(always)]
pub fn normalize_header_value(value: &str) -> &str {
    get_precompiled_headers().get_canonical_value(value)
}

/// EXTREME OPTIMIZATION: Batch header processing for maximum performance
pub fn process_headers_optimized(
    headers: &HashMap<String, String>
) -> HashMap<&'static str, String> {
    let mut optimized_headers = HashMap::with_capacity(headers.len());
    let precompiled = get_precompiled_headers();
    
    for (name, value) in headers {
        let canonical_name = precompiled.get_canonical_name(name);
        let canonical_value = if precompiled.is_precompiled_value(value) {
            precompiled.get_canonical_value(value).to_string()
        } else {
            value.clone()
        };
        
        optimized_headers.insert(canonical_name, canonical_value);
    }
    
    optimized_headers
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_precompiled_methods() {
        let methods = PrecompiledMethods::new();
        
        assert!(methods.get_method("GET").is_some());
        assert!(methods.get_method("POST").is_some());
        assert!(methods.get_method("INVALID").is_none());
        
        assert!(methods.is_precompiled("GET"));
        assert!(!methods.is_precompiled("CUSTOM"));
    }

    #[test]
    fn test_precompiled_headers() {
        let headers = PrecompiledHeaders::new();
        
        assert_eq!(headers.get_canonical_name("content-type"), "Content-Type");
        assert_eq!(headers.get_canonical_name("Content-Type"), "Content-Type");
        
        assert!(headers.is_precompiled_name("content-type"));
        assert!(headers.is_precompiled_value("application/json"));
    }

    #[test]
    fn test_method_parsing() {
        let method = parse_method_optimized("GET").unwrap();
        assert_eq!(method, Method::GET);
        
        let method = parse_method_optimized("POST").unwrap();
        assert_eq!(method, Method::POST);
    }

    #[test]
    fn test_header_normalization() {
        assert_eq!(normalize_header_name("content-type"), "Content-Type");
        assert_eq!(normalize_header_value("application/json"), "application/json");
    }

    #[test]
    fn test_schemes() {
        let schemes = PrecompiledSchemes::new();
        
        assert_eq!(schemes.get_default_port("http"), Some(80));
        assert_eq!(schemes.get_default_port("https"), Some(443));
        
        assert!(schemes.is_secure_scheme("https"));
        assert!(!schemes.is_secure_scheme("http"));
    }
}