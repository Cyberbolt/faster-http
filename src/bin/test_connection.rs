use std::collections::HashMap;
use std::time::Duration;

// Test connection to test server using different HTTP clients
// This helps diagnose connection issues between Rust clients and test server

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Testing Rust HTTP client connections to test server...\n");
    
    // Start test server
    println!("Starting test server...");
    let server = start_test_server().await?;
    let base_url = &server.base_url;
    println!("Test server started at: {}\n", base_url);
    
    // Test with curl first
    test_with_curl(base_url).await?;
    
    // Test with different Rust HTTP clients
    test_with_hyper(base_url).await?;
    test_with_ureq(base_url).await?;
    test_with_reqwest(base_url).await?;
    
    println!("\nAll tests completed!");
    Ok(())
}

// Test with system curl to verify server is working
async fn test_with_curl(base_url: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Testing with curl ===");
    
    let output = tokio::process::Command::new("curl")
        .args(&["-s", "-w", "HTTP %{http_code}", &format!("{}/get", base_url)])
        .output()
        .await?;
    
    if output.status.success() {
        println!("curl SUCCESS: {}", String::from_utf8_lossy(&output.stdout));
    } else {
        println!("curl FAILED: {}", String::from_utf8_lossy(&output.stderr));
    }
    println!();
    Ok(())
}

// Test with hyper directly
async fn test_with_hyper(base_url: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Testing with hyper ===");
    
    let uri = format!("{}/get", base_url).parse::<hyper::Uri>()?;
    let request = hyper::Request::builder()
        .method("GET")
        .uri(&uri)
        .header("User-Agent", "Rust-Hyper/1.0")
        .body(http_body_util::Empty::<bytes::Bytes>::new())?;
    
    // Create a simple HTTP connector
    let connector = hyper_util::client::legacy::connect::HttpConnector::new();
    let client = hyper_util::client::legacy::Client::builder(hyper_util::rt::TokioExecutor::new())
        .build(connector);
    
    match tokio::time::timeout(Duration::from_secs(10), client.request(request)).await {
        Ok(Ok(response)) => {
            println!("hyper SUCCESS: HTTP {}", response.status().as_u16());
        },
        Ok(Err(e)) => {
            println!("hyper ERROR: {}", e);
        },
        Err(_) => {
            println!("hyper TIMEOUT after 10 seconds");
        }
    }
    println!();
    Ok(())
}

// Test with ureq
async fn test_with_ureq(base_url: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Testing with ureq ===");
    
    let url = format!("{}/get", base_url);
    
    // Run ureq in blocking task since it's synchronous
    let result = tokio::task::spawn_blocking(move || {
        let agent = ureq::AgentBuilder::new()
            .timeout(Duration::from_secs(10))
            .build();
        
        agent.get(&url)
            .set("User-Agent", "Rust-Ureq/1.0")
            .call()
    }).await;
    
    match result {
        Ok(Ok(response)) => {
            println!("ureq SUCCESS: HTTP {}", response.status());
        },
        Ok(Err(e)) => {
            println!("ureq ERROR: {}", e);
        },
        Err(e) => {
            println!("ureq TASK ERROR: {}", e);
        }
    }
    println!();
    Ok(())
}

// Test with reqwest
async fn test_with_reqwest(base_url: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Testing with reqwest ===");
    
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(10))
        .build()?;
    
    let url = format!("{}/get", base_url);
    
    match client.get(&url)
        .header("User-Agent", "Rust-Reqwest/1.0")
        .send()
        .await 
    {
        Ok(response) => {
            println!("reqwest SUCCESS: HTTP {}", response.status().as_u16());
        },
        Err(e) => {
            println!("reqwest ERROR: {}", e);
        }
    }
    println!();
    Ok(())
}

// Test server helper
struct TestServer {
    pub base_url: String,
}

async fn start_test_server() -> Result<TestServer, Box<dyn std::error::Error>> {
    // Import test server
    use std::process::Stdio;
    use std::time::Duration;
    use tokio::io::{AsyncBufReadExt, BufReader};
    
    // Start Python test server in background
    let mut child = tokio::process::Command::new("python")
        .args(&["-c", r#"
import sys
sys.path.insert(0, 'tests')
from utils.test_server import HTTPTestServer
import time

server = HTTPTestServer()
server.start()
print(f"SERVER_URL:{server.base_url}")
sys.stdout.flush()

# Keep server alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    server.stop()
"#])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;
    
    let stdout = child.stdout.take().unwrap();
    let mut reader = BufReader::new(stdout);
    let mut line = String::new();
    
    // Wait for server to start and get URL
    tokio::time::timeout(Duration::from_secs(30), reader.read_line(&mut line)).await??;
    
    if let Some(url_part) = line.strip_prefix("SERVER_URL:") {
        let base_url = url_part.trim().to_string();
        
        // Give server a moment to fully initialize
        tokio::time::sleep(Duration::from_millis(100)).await;
        
        Ok(TestServer { base_url })
    } else {
        Err(format!("Failed to parse server URL from: {}", line).into())
    }
}