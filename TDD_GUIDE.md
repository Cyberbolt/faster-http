# TDD 开发指南 - faster-http

## 🚀 TDD框架已就绪

TDD（测试驱动开发）框架已经完全重建并可用于开发。

## 📁 测试结构

```
tests/
├── tdd_basic.py     # TDD框架验证测试
├── tdd_demo.py      # TDD工作流程演示
├── utils/
│   └── tdd_framework.py  # 简化的TDD测试工具
└── conftest.py      # pytest配置和fixtures
```

## 🔄 TDD 开发流程

### 1. Red Phase (红灯阶段)
创建失败的测试：

```python
from tests.utils.tdd_framework import tdd_test

class TestNewFeature:
    @tdd_test
    def test_new_functionality(self, tdd_client):
        # 测试尚未实现的功能
        response = tdd_client.get("http://mock-server/get")
        assert hasattr(response, 'new_attribute')  # 这会失败
```

### 2. Green Phase (绿灯阶段)
编写最少代码让测试通过：

```python
# 在 faster_http 代码中添加最小实现
class Response:
    def __init__(self):
        self.new_attribute = "minimal_implementation"
```

### 3. Refactor Phase (重构阶段)
改进代码质量，保持测试通过：

```python
# 改进实现质量
class Response:
    @property
    def new_attribute(self):
        return self._compute_attribute()
    
    def _compute_attribute(self):
        # 更好的实现逻辑
        return "improved_implementation"
```

## 🛠️ 使用指南

### 基本测试运行

```bash
# 运行TDD相关测试
timeout 30s uv run -m pytest tests/tdd_basic.py tests/tdd_demo.py -v --no-cov

# 运行单个测试文件
timeout 30s uv run -m pytest tests/tdd_basic.py -v --no-cov --tb=short

# 快速验证TDD框架就绪
timeout 10s uv run -m pytest tests/tdd_basic.py::TestTDDFramework::test_tdd_framework_ready -v
```

### TDD开发示例

```python
from tests.utils.tdd_framework import tdd_test

class TestMyNewFeature:
    @tdd_test
    def test_feature_works(self, tdd_client):
        """TDD: 新功能测试."""
        # 第一阶段：编写失败测试（Red）
        client = tdd_client()
        response = client.get("http://mock-server/get", timeout=5.0)
        
        # 测试期望的行为
        assert response.status_code == 200
        assert response.text is not None
```

## ✅ 关键优势

1. **快速启动**: 测试在 5 秒内完成
2. **简化架构**: 移除了复杂的httpx比较装饰器 
3. **专注TDD**: 专为Red-Green-Refactor循环优化
4. **稳定可靠**: 无signal处理或复杂超时机制
5. **本地测试**: 使用Mock响应，无需外部服务器

## 🔧 框架组件

### tdd_framework.py
- `@tdd_test`: 简化的测试装饰器
- `SimpleClientFactory`: 轻量级客户端工厂
- `tdd_client` fixture: 用于测试的客户端

### pytest配置
- 移除了 `-x` 选项（允许测试在Red阶段失败）
- 移除了并发执行（避免干扰）
- 设置30秒超时限制
- 简化的测试报告

## 🎯 验证清单

- ✅ TDD框架可以启动
- ✅ 能够创建失败测试（Red阶段）
- ✅ 能够编写通过测试（Green阶段）
- ✅ 支持重构阶段
- ✅ 测试执行快速（<5秒）
- ✅ 符合CLAUDE.md时间要求

## 📝 下一步

TDD框架现已完全就绪，可以开始：

1. 为新功能编写TDD测试
2. 实现httpx兼容接口
3. 进行性能优化
4. 添加完整的功能覆盖

开始TDD开发！🚀