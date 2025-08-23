# 项目规则

## 基本规范
- **语言使用**：用中文回答问题，代码注释使用英文
- **文档查询优先级**：context7 文档查询 > 互联网搜索
- **问题解决流程**：不明确时先查 context7 文档 → 仍无法解决再搜索互联网

## 项目架构原则
**目标**：构建 httpx 的高性能 Rust 替代方案

### Python 层职责
- **仅作接口层**：对外暴露完整的 httpx 兼容接口
- **最小化逻辑**：除必要情况外，不实现业务逻辑
- **接口验证**：使用 `uv run python -c` 验证 httpx 真实接口行为

### Rust 层职责  
- **接口转换**：Python 请求参数 → hyper 请求格式
- **请求处理**：委托 hyper 执行 HTTP 操作
- **响应转换**：hyper Response → httpx 兼容的 Python Response 对象
- **最小化实现**：除必要情况外，将逻辑交给 hyper 处理

### 性能要求
- Python-Rust 调用追求极致性能优化
- 减少不必要的数据转换和内存拷贝

## 文档依赖
- 开发标准：@prompts/development-standards.md
- 文档规范：@prompts/documentation-standards.md

## 技术栈文档查询
- **httpx**：不确定时使用 context7 查询 + 实际验证
- **hyper**：不确定时使用 context7 查询相关文档