# HTTPX Core API Interface Documentation

## 概述信息
- **HTTPX 版本**: 0.28.1
- **更新日期**: 2025-08-23
- **用途**: faster-http 项目开发指导文档

## 1. 顶级HTTP请求函数 (Top-Level Functions)

### 基础HTTP方法
- [ ] `httpx.get(url, *, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=False, verify=True, timeout=Timeout(5.0), trust_env=True) -> Response`
- [ ] `httpx.post(url, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=False, verify=True, timeout=Timeout(5.0), trust_env=True) -> Response`
- [ ] `httpx.put(url, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=False, verify=True, timeout=Timeout(5.0), trust_env=True) -> Response`
- [ ] `httpx.patch(url, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=False, verify=True, timeout=Timeout(5.0), trust_env=True) -> Response`
- [ ] `httpx.delete(url, *, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=False, verify=True, timeout=Timeout(5.0), trust_env=True) -> Response`
- [ ] `httpx.head(url, *, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=False, verify=True, timeout=Timeout(5.0), trust_env=True) -> Response`
- [ ] `httpx.options(url, *, params=None, headers=None, cookies=None, auth=None, proxy=None, follow_redirects=False, verify=True, timeout=Timeout(5.0), trust_env=True) -> Response`

### 通用请求函数
- [ ] `httpx.request(method, url, *, params=None, content=None, data=None, files=None, json=None, headers=None, cookies=None, auth=None, proxy=None, timeout=Timeout(5.0), follow_redirects=False, verify=True, trust_env=True) -> Response`

### 流式请求函数
- [ ] `httpx.stream(method, url, *, params=None, content=None, data=None, files=None, json=None, headers=None, cookies=None, auth=None, proxy=None, timeout=Timeout(5.0), follow_redirects=False, verify=True, trust_env=True) -> Iterator[Response]`

## 2. Client 类 (同步客户端)

### 初始化参数
```python
httpx.Client(
    *, 
    auth=None,                    # 认证信息
    params=None,                  # 默认查询参数
    headers=None,                 # 默认请求头
    cookies=None,                 # 默认cookies
    verify=True,                  # SSL验证
    cert=None,                    # 客户端证书
    trust_env=True,              # 信任环境变量
    http1=True,                  # HTTP/1.1支持
    http2=False,                 # HTTP/2支持
    proxy=None,                  # 代理设置
    mounts=None,                 # 传输挂载
    timeout=Timeout(5.0),        # 超时配置
    follow_redirects=False,      # 跟随重定向
    limits=Limits(...),          # 连接限制
    max_redirects=20,            # 最大重定向次数
    event_hooks=None,            # 事件钩子
    base_url='',                 # 基础URL
    transport=None,              # 自定义传输
    default_encoding='utf-8'     # 默认编码
) -> None
```

### HTTP请求方法
- [ ] `Client.get(url, *, params=None, headers=None, cookies=None, auth=UseClientDefault, follow_redirects=UseClientDefault, timeout=UseClientDefault, extensions=None) -> Response`
- [ ] `Client.post(url, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, auth=UseClientDefault, follow_redirects=UseClientDefault, timeout=UseClientDefault, extensions=None) -> Response`
- [ ] `Client.put(url, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, auth=UseClientDefault, follow_redirects=UseClientDefault, timeout=UseClientDefault, extensions=None) -> Response`
- [ ] `Client.patch(url, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, auth=UseClientDefault, follow_redirects=UseClientDefault, timeout=UseClientDefault, extensions=None) -> Response`
- [ ] `Client.delete(url, *, params=None, headers=None, cookies=None, auth=UseClientDefault, follow_redirects=UseClientDefault, timeout=UseClientDefault, extensions=None) -> Response`
- [ ] `Client.head(url, *, params=None, headers=None, cookies=None, auth=UseClientDefault, follow_redirects=UseClientDefault, timeout=UseClientDefault, extensions=None) -> Response`
- [ ] `Client.options(url, *, params=None, headers=None, cookies=None, auth=UseClientDefault, follow_redirects=UseClientDefault, timeout=UseClientDefault, extensions=None) -> Response`

### 通用请求和流式请求
- [ ] `Client.request(method, url, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, auth=UseClientDefault, follow_redirects=UseClientDefault, timeout=UseClientDefault, extensions=None) -> Response`
- [ ] `Client.stream(method, url, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, auth=UseClientDefault, follow_redirects=UseClientDefault, timeout=UseClientDefault, extensions=None) -> Iterator[Response]`

### 请求构建和发送
- [ ] `Client.build_request(method, url, *, content=None, data=None, files=None, json=None, params=None, headers=None, cookies=None, timeout=UseClientDefault, extensions=None) -> Request`
- [ ] `Client.send(request, *, stream=False, auth=UseClientDefault, follow_redirects=UseClientDefault) -> Response`

### 资源管理
- [ ] `Client.close() -> None`

## 3. AsyncClient 类 (异步客户端)

### 初始化参数
```python
httpx.AsyncClient(
    *, 
    auth=None,                    # 认证信息
    params=None,                  # 默认查询参数
    headers=None,                 # 默认请求头
    cookies=None,                 # 默认cookies
    verify=True,                  # SSL验证
    cert=None,                    # 客户端证书
    http1=True,                  # HTTP/1.1支持
    http2=False,                 # HTTP/2支持
    proxy=None,                  # 代理设置
    mounts=None,                 # 传输挂载 (AsyncBaseTransport)
    timeout=Timeout(5.0),        # 超时配置
    follow_redirects=False,      # 跟随重定向
    limits=Limits(...),          # 连接限制
    max_redirects=20,            # 最大重定向次数
    event_hooks=None,            # 事件钩子
    base_url='',                 # 基础URL
    transport=None,              # 自定义传输 (AsyncBaseTransport)
    trust_env=True,              # 信任环境变量
    default_encoding='utf-8'     # 默认编码
) -> None
```

### HTTP请求方法 (异步，需要 await)
- [ ] `AsyncClient.get(url, **kwargs) -> Response` (需要 await)
- [ ] `AsyncClient.post(url, **kwargs) -> Response` (需要 await)
- [ ] `AsyncClient.put(url, **kwargs) -> Response` (需要 await)
- [ ] `AsyncClient.patch(url, **kwargs) -> Response` (需要 await)
- [ ] `AsyncClient.delete(url, **kwargs) -> Response` (需要 await)
- [ ] `AsyncClient.head(url, **kwargs) -> Response` (需要 await)
- [ ] `AsyncClient.options(url, **kwargs) -> Response` (需要 await)
- [ ] `AsyncClient.request(method, url, **kwargs) -> Response` (需要 await)

### 异步流式请求
- [ ] `AsyncClient.stream(method, url, **kwargs) -> AsyncIterator[Response]` (需要 async with)

### 异步请求构建和发送
- [ ] `AsyncClient.build_request(method, url, **kwargs) -> Request`
- [ ] `AsyncClient.send(request, **kwargs) -> Response` (需要 await)

### 异步资源管理
- [ ] `AsyncClient.aclose() -> None` (需要 await)

## 4. Response 对象

### 状态属性
- [x] `Response.status_code: int` - HTTP状态码
- [ ] `Response.reason_phrase: str` - 状态原因短语
- [ ] `Response.http_version: str` - HTTP版本号 (如 'HTTP/1.1')
- [x] `Response.url: httpx.URL` - 请求的URL
- [x] `Response.headers: httpx.Headers` - 响应头 (不区分大小写)
- [ ] `Response.cookies: httpx.Cookies` - 响应中的cookies
- [x] `Response.request: httpx.Request` - 原始请求对象

### 内容相关属性
- [x] `Response.content: bytes` - 响应内容的原始字节
- [x] `Response.text: str` - 响应内容的文本形式 (解码后)
- [ ] `Response.encoding: str` - 文本编码
- [ ] `Response.charset_encoding: str | None` - 字符集编码

### 状态判断属性
- [x] `Response.is_success: bool` - 是否成功 (2xx状态码)
- [ ] `Response.is_redirect: bool` - 是否重定向
- [ ] `Response.is_client_error: bool` - 是否客户端错误 (4xx)
- [ ] `Response.is_server_error: bool` - 是否服务端错误 (5xx)
- [x] `Response.is_error: bool` - 是否错误 (4xx或5xx)
- [ ] `Response.is_informational: bool` - 是否信息性响应 (1xx)

### 流和重定向相关属性
- [ ] `Response.is_closed: bool` - 响应是否已关闭
- [ ] `Response.is_stream_consumed: bool` - 流是否已消费
- [ ] `Response.next_request: httpx.Request | None` - 下一个重定向请求
- [ ] `Response.history: list[httpx.Response]` - 重定向历史
- [ ] `Response.has_redirect_location: bool` - 是否有重定向位置

### 其他属性
- [ ] `Response.elapsed: timedelta` - 请求耗时 (从发送到响应)
- [ ] `Response.extensions: dict` - 扩展信息
- [ ] `Response.links: dict` - Link头的解析结果
- [ ] `Response.num_bytes_downloaded: int` - 下载字节数
- [ ] `Response.default_encoding: str` - 默认编码

### 同步方法
- [x] `Response.json() -> Any` - 解析JSON响应
- [x] `Response.raise_for_status() -> Response` - 状态码异常检查
- [ ] `Response.read() -> bytes` - 读取完整响应内容
- [ ] `Response.close() -> None` - 关闭响应

### 同步流式方法
- [ ] `Response.iter_bytes(chunk_size=1024) -> Iterator[bytes]` - 迭代字节块
- [ ] `Response.iter_text(chunk_size=1024) -> Iterator[str]` - 迭代文本块
- [ ] `Response.iter_lines() -> Iterator[str]` - 迭代文本行
- [ ] `Response.iter_raw(chunk_size=1024) -> Iterator[bytes]` - 迭代原始字节

### 异步方法
- [ ] `Response.aread() -> bytes` - 异步读取完整响应内容
- [ ] `Response.aclose() -> None` - 异步关闭响应

### 异步流式方法
- [ ] `Response.aiter_bytes(chunk_size=1024) -> AsyncIterator[bytes]` - 异步迭代字节块
- [ ] `Response.aiter_text(chunk_size=1024) -> AsyncIterator[str]` - 异步迭代文本块
- [ ] `Response.aiter_lines() -> AsyncIterator[str]` - 异步迭代文本行
- [ ] `Response.aiter_raw(chunk_size=1024) -> AsyncIterator[bytes]` - 异步迭代原始字节

## 5. Request 对象

### 初始化参数
```python
httpx.Request(
    method: str,                  # HTTP方法
    url: str | httpx.URL,        # 请求URL
    *, 
    params=None,                 # URL查询参数
    headers=None,                # 请求头
    cookies=None,                # cookies
    content=None,                # 请求内容 (bytes/str)
    data=None,                   # 表单数据
    files=None,                  # 文件上传
    json=None,                   # JSON数据
    stream=None                  # 流对象
    extensions=None              # 扩展信息
) -> None
```

### 属性
- [ ] `Request.method: str` - HTTP方法
- [ ] `Request.url: httpx.URL` - 请求URL
- [ ] `Request.headers: httpx.Headers` - 请求头
- [ ] `Request.content: bytes` - 请求内容
- [ ] `Request.extensions: dict` - 扩展信息

### 方法
- [ ] `Request.read() -> bytes` - 读取请求内容
- [ ] `Request.aread() -> bytes` - 异步读取请求内容

## 6. 配置类

### Timeout 超时配置
```python
httpx.Timeout(
    timeout=5.0,          # 总超时时间
    *, 
    connect=None,         # 连接超时
    read=None,            # 读取超时
    write=None,           # 写入超时
    pool=None            # 连接池超时
) -> None
```
- [ ] `Timeout` 类 (超时配置的数据类)

### Limits 连接限制
```python
httpx.Limits(
    *, 
    max_connections=None,          # 最大连接数
    max_keepalive_connections=None, # 最大保活连接数
    keepalive_expiry=5.0          # 保活连接过期时间
) -> None
```
- [ ] `Limits` 类 (配置连接池限制)

## 7. 认证类

### BasicAuth 基础认证
```python
httpx.BasicAuth(
    username: str | bytes,  # 用户名
    password: str | bytes   # 密码
) -> None
```
- [ ] `BasicAuth` 类 (实现HTTP基础认证)

### DigestAuth 摘要认证
```python
httpx.DigestAuth(
    username: str | bytes,  # 用户名
    password: str | bytes   # 密码
) -> None
```
- [ ] `DigestAuth` 类 (实现HTTP摘要认证)

### Auth 基类
- [ ] `httpx.Auth` - 自定义认证的基类

## 8. 异常类

### 基本异常
- [ ] `httpx.HTTPError` - HTTP相关异常的基类
- [ ] `httpx.RequestError` - 请求相关异常
- [x] `httpx.HTTPStatusError` - HTTP状态码异常
- [ ] `httpx.ConnectError` - 连接异常
- [ ] `httpx.TimeoutException` - 超时异常

## 9. 工具类和辅助类

### URL 类
- [ ] `httpx.URL` - URL对象 (不可变URL表示和操作)
  - 支持 `copy_with(params=...)` 等方法

### Headers 类
- [ ] `httpx.Headers` - 请求/响应头对象 (不区分大小写)
  - 支持dict操作接口

### Cookies 类
- [ ] `httpx.Cookies` - Cookie管理对象
  - 支持添加和读取cookie的操作

### 状态码常量
- [ ] `httpx.codes` - 状态码常量
  - 如: `codes.OK` (200), `codes.NOT_FOUND` (404) 等

### MockTransport 测试工具类
- [ ] `httpx.MockTransport` - 用于单元测试的模拟传输

## 10. 参数类型详解

### 请求参数类型
- `params`: URL查询参数 - `dict` 或 `list[tuple]`
- `headers`: 请求头 - `dict` 或 `httpx.Headers`
- `cookies`: Cookie - `dict` 或 `httpx.Cookies`
- `data`: 表单数据 - `dict` 或 `bytes` 或 `str`
- `files`: 文件上传
  - `dict`
- `json`: JSON数据 - 任意可序列化对象
- `content`: 原始请求内容 - `bytes` 或 `str`

### 认证参数
- `auth`: 认证 - `tuple[str, str]` 或 `httpx.Auth`

### 其他配置参数
- `verify`: SSL验证 - `bool` 或 `ssl.SSLContext` 或 `str`
- `cert`: 客户端证书 - `str` 或 `tuple[str, str]`
- `proxy`: 代理 - `str` 代理地址
- `timeout`: 超时 - `float` 或 `httpx.Timeout`
- `follow_redirects`: 跟随重定向 - `bool`
- `trust_env`: 信任环境变量 - `bool`

## 11. 优先级分类

### 核心必需功能 (第一批实现)
1. **基本HTTP方法**: `get()`, `post()`, `put()`, `patch()`, `delete()`, `head()`, `options()`
2. **Client类**: 初始化和基本HTTP方法，`close()`
3. **Response对象**: `status_code`, `headers`, `content`, `text`, `json()`, `url`
4. **基本参数**: `params`, `headers`, `data`, `json`, `timeout`

### 重要功能 (第二批实现)
1. **AsyncClient类**: 异步支持
2. **Request对象**: 请求构建和操作
3. **流式处理**: `stream()`, `iter_bytes()`, `iter_text()`
4. **异常处理**: `HTTPStatusError`, `raise_for_status()`
5. **配置类**: `Timeout`, `Limits`

### 高级功能 (第三批实现)
1. **认证**: `BasicAuth`, `DigestAuth`
2. **代理**: `proxy` 参数
3. **SSL配置**: `verify`, `cert`
4. **事件钩子**: `event_hooks`
5. **自定义传输**: `transport`, `mounts`

### 工具和辅助 (第四批实现)
1. **URL工具**: `httpx.URL`
2. **Headers工具**: `httpx.Headers`
3. **Cookies工具**: `httpx.Cookies`
4. **状态码常量**: `httpx.codes`
5. **测试工具**: `MockTransport`

## 12. 与 requests 的主要差异

1. **重定向**: httpx默认不跟随重定向，需要 `follow_redirects=True`
2. **超时**: httpx默认超时5秒，requests默认无超时
3. **环境变量**: httpx通过 `trust_env=True` 参数控制是否读取环境变量
4. **响应状态**: httpx使用 `is_success`，requests使用 `ok`
5. **流式处理**: httpx使用 `with httpx.stream()` 而不是 `stream=True`
6. **参数处理**: httpx将 `None` 视为未提供参数，不会序列化
7. **异步支持**: httpx原生支持异步，requests 需要第三方库

---

**总接口数量参考**: 约120个属性、方法和类
**备注**: 此文档为 faster-http 项目的 Python 开发工程师的权威参考文档