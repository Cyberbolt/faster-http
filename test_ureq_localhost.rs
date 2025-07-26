// Test ureq (sync HTTP client) with localhost
use ureq;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Testing ureq with localhost...");
    
    // Test URLs
    let test_urls = [
        "https://httpbin.org/get",      // External (should work)
        "http://127.0.0.1:44839/get",   // Local test server (test if this works)
    ];
    
    // Create ureq agent with minimal config
    let agent = ureq::AgentBuilder::new()
        .timeout_connect(std::time::Duration::from_secs(5))
        .timeout_read(std::time::Duration::from_secs(10))
        .build();
    
    for url in &test_urls {
        println!("\n=== Testing {} ===", url);
        
        match agent.get(url).call() {
            Ok(response) => {
                println!("✅ SUCCESS: {} - Status: {}", url, response.status());
                let text = response.into_string().unwrap_or_else(|_| "Failed to read body".to_string());
                println!("Response length: {} bytes", text.len());
            }
            Err(e) => {
                println!("❌ FAILED: {} - Error: {}", url, e);
            }
        }
    }
    
    Ok(())
}