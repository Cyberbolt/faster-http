你应该使用中文来回答我问题，但是写代码的注释要用英文注释

## 项目规则

这个项目的目的是作为 httpx 的高性能替代

因为需要随时确认 httpx 的文档，如果你不清楚请使用 context7

Python 部分，这个项目只应该对外暴露 httpx 的接口，而不应该实现任何 Python 的逻辑（除非必要），将逻辑交给 Rust 部分，这个项目只应该对外暴露

Rust 部分，应该把 Python 部分的输入转为 reqwest 的输入，然后用 reqwest 来处理请求，将返回的 reqwest 的 Response 转为 Python httpx 的 Response 对象，并返回给 Python 部分。除非必要，Rust 部分的逻辑应该尽可能交给 reqwest 来处理，而不是自己实现。

综上，这个项目 Python 和 Rust 的作用只是作 httpx 接口和 reqwest 的接口的转换，仅此而已。

Python 调用 Rust 应该尽可能高效，追求极致性能。

当你修改了代码，应该执行 tests 目录下的测试，确保没有破坏原有功能。如果你修改了 Rust 代码，应该先运行 `uv run maturin develop` 重新编译。