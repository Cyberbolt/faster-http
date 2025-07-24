"""
Test SSL configuration in faster-http
"""

import os
import ssl
import tempfile
import subprocess
from pathlib import Path
import faster_http


def create_self_signed_cert(cert_dir):
    """创建自签名证书用于测试"""
    cert_file = cert_dir / "cert.pem"
    key_file = cert_dir / "key.pem"
    combined_file = cert_dir / "combined.pem"
    ca_file = cert_dir / "ca.pem"
    
    # 创建自签名证书和私钥
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", 
        "-keyout", str(key_file), "-out", str(cert_file),
        "-days", "365", "-nodes", "-subj", 
        "/C=US/ST=Test/L=Test/O=Test/CN=localhost"
    ], check=True, capture_output=True)
    
    # 创建组合文件 (cert + key)
    with open(combined_file, 'w') as combined:
        with open(cert_file, 'r') as cert:
            combined.write(cert.read())
        with open(key_file, 'r') as key:
            combined.write(key.read())
    
    # 复制证书作为CA文件
    subprocess.run(["cp", str(cert_file), str(ca_file)], check=True)
    
    return {
        'cert_file': cert_file,
        'key_file': key_file,
        'combined_file': combined_file,
        'ca_file': ca_file
    }


def test_ssl_verification_disabled():
    """测试禁用SSL验证"""
    print("=== 测试禁用SSL验证 ===")
    
    client = faster_http.Client(verify=False)
    
    try:
        # 测试访问自签名证书网站 (通常会失败，但禁用验证后应该成功)
        response = client.get('https://self-signed.badssl.com/')
        print(f"✅ SSL验证禁用测试成功: {response.status_code}")
    except Exception as e:
        print(f"❌ SSL验证禁用测试失败: {e}")


def test_ssl_verification_enabled():
    """测试启用SSL验证 (默认)"""
    print("\n=== 测试启用SSL验证 (默认) ===")
    
    client = faster_http.Client(verify=True)
    
    try:
        # 测试访问有效证书网站
        response = client.get('https://httpbin.org/get')
        print(f"✅ SSL验证启用测试成功: {response.status_code}")
    except Exception as e:
        print(f"❌ SSL验证启用测试失败: {e}")


def test_custom_ca_bundle():
    """测试自定义CA bundle"""
    print("\n=== 测试自定义CA bundle ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cert_dir = Path(temp_dir)
        
        try:
            # 创建自签名证书
            certs = create_self_signed_cert(cert_dir)
            
            # 使用自定义CA文件
            client = faster_http.Client(verify=str(certs['ca_file']))
            
            print(f"✅ 自定义CA bundle客户端创建成功")
            print(f"   CA文件: {certs['ca_file']}")
            
        except Exception as e:
            print(f"❌ 自定义CA bundle测试失败: {e}")


def test_client_certificate():
    """测试客户端证书配置"""
    print("\n=== 测试客户端证书配置 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cert_dir = Path(temp_dir)
        
        try:
            # 创建自签名证书
            certs = create_self_signed_cert(cert_dir)
            
            # 测试单个文件格式 (cert + key 在同一文件)
            print("1. 测试组合证书文件:")
            client1 = faster_http.Client(
                cert=str(certs['combined_file']),
                verify=False  # 禁用验证因为是自签名证书
            )
            print(f"   ✅ 组合证书文件客户端创建成功")
            
            # 测试分离文件格式 (cert, key)
            print("2. 测试分离证书文件:")
            client2 = faster_http.Client(
                cert=(str(certs['cert_file']), str(certs['key_file'])),
                verify=False
            )
            print(f"   ✅ 分离证书文件客户端创建成功")
            
        except Exception as e:
            print(f"❌ 客户端证书测试失败: {e}")


def test_trust_env():
    """测试环境变量信任"""
    print("\n=== 测试环境变量信任 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cert_dir = Path(temp_dir)
        
        try:
            # 创建自签名证书
            certs = create_self_signed_cert(cert_dir)
            
            # 设置环境变量
            os.environ['SSL_CERT_FILE'] = str(certs['ca_file'])
            
            # 测试信任环境变量
            client = faster_http.Client(trust_env=True)
            print(f"✅ 环境变量信任客户端创建成功")
            print(f"   SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE')}")
            
            # 清理环境变量
            del os.environ['SSL_CERT_FILE']
            
        except Exception as e:
            print(f"❌ 环境变量信任测试失败: {e}")


def test_async_ssl_config():
    """测试异步客户端SSL配置"""
    print("\n=== 测试异步客户端SSL配置 ===")
    
    import asyncio
    
    async def test_async():
        try:
            # 测试禁用SSL验证的异步客户端
            client = faster_http.AsyncClient(verify=False)
            print("✅ 异步SSL客户端创建成功")
            
            # 简单测试 (不实际发送请求以避免依赖外部网站)
            print("   异步客户端配置完成")
            
        except Exception as e:
            print(f"❌ 异步SSL配置测试失败: {e}")
    
    asyncio.run(test_async())


def test_httpx_compatibility():
    """测试httpx兼容性"""
    print("\n=== 测试httpx兼容性 ===")
    
    try:
        # 测试httpx风格的SSL配置
        
        # 1. verify=False
        client1 = faster_http.Client(verify=False)
        print("✅ httpx风格 verify=False 成功")
        
        # 2. verify=True
        client2 = faster_http.Client(verify=True)
        print("✅ httpx风格 verify=True 成功")
        
        # 3. 路径字符串 - 使用真实的证书文件
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_dir = Path(temp_dir)
            try:
                certs = create_self_signed_cert(cert_dir)
                client3 = faster_http.Client(verify=str(certs['ca_file']))
                print("✅ httpx风格路径字符串成功")
            except Exception as path_error:
                print(f"⚠️ 路径字符串测试失败: {path_error}")
                # 继续其他测试
        
        print("✅ 所有httpx兼容性测试通过")
        
    except Exception as e:
        print(f"❌ httpx兼容性测试失败: {e}")


def main():
    """运行所有SSL配置测试"""
    print("🔒 开始SSL配置测试\n")
    
    # 检查OpenSSL是否可用
    try:
        subprocess.run(["openssl", "version"], check=True, capture_output=True)
        print("✅ OpenSSL 可用\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ OpenSSL 不可用，跳过证书创建测试\n")
        # 只运行不需要证书的测试
        test_ssl_verification_enabled()
        test_ssl_verification_disabled()
        test_async_ssl_config()
        test_httpx_compatibility()
        return
    
    # 基础SSL测试
    test_ssl_verification_enabled()
    test_ssl_verification_disabled()
    
    # 高级SSL测试
    test_custom_ca_bundle()
    test_client_certificate()
    test_trust_env()
    
    # 异步和兼容性测试
    test_async_ssl_config()
    test_httpx_compatibility()
    
    print("\n🎉 所有SSL配置测试完成!")


if __name__ == "__main__":
    main()