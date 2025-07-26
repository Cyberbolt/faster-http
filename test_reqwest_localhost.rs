// Pure Rust test to check if reqwest can connect to localhost
use tokio;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Testing pure reqwest with localhost...");
    
    // Test multiple client configurations including extreme settings
    let configs = vec![
        ("Default", reqwest::Client::builder().timeout(std::time::Duration::from_secs(10)).build()?),
        ("No Proxy", reqwest::Client::builder().timeout(std::time::Duration::from_secs(10)).no_proxy().build()?),
        ("HTTP1 Only", reqwest::Client::builder().timeout(std::time::Duration::from_secs(10)).http1_only().build()?),
        ("Minimal Config", reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(10))
            .no_proxy()
            .http1_only()
            .http1_title_case_headers()
            .tcp_nodelay(false)
            .tcp_keepalive(None)
            .pool_idle_timeout(None)
            .pool_max_idle_per_host(0)
            .build()?),
    ];
    
    // Test URLs that should work
    let test_urls = vec![
        "https://httpbin.org/get",      // External (should work)
        "http://127.0.0.1:41539/get",   // Local test server (test if this works)
    ];
    
    for (config_name, client) in configs {
        println!("\n========== Testing with {} client ==========", config_name);
        
        for url in &test_urls {
            println!("\n=== Testing {} ===", url);
            
            match client.get(*url).send().await {
                Ok(response) => {
                    println!("✅ SUCCESS: {} - Status: {}", url, response.status());
                    let text = response.text().await.unwrap_or_else(|_| "Failed to read body".to_string());
                    println!("Response length: {} bytes", text.len());
                }
                Err(e) => {
                    println!("❌ FAILED: {} - Error: {}", url, e);
                }  
            }
        }
    }
    
    Ok(())
}