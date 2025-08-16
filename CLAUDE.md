# 项目规则

- 使用中文来回答问题，但是写代码的注释要用英文注释

- 如果有不明确用法的库，擅于用 context7 查询文档，context7 查询的优先级应该高于互联网搜索

- 如果一件事确实超过了你的能力范围：能用 context7 查询文档解决的问题，就先查文档；还是无法解决的，就查询互联网

- 使用 uv 来管理项目，用 `uv run -m` 替代 `python -m`，用 `uv add` 来添加相关依赖。如果你不清楚 uv 的使用方法，可以用 context7 查询

- 你如果只想临时执行一段代码来验证你的想法，应该用 `uv run python -c` 来执行，千万不要污染项目根目录的文件

- 这个项目的目的是作为 httpx 的高性能替代。
因为需要随时确认 httpx 或 reqwest 的文档，如果你不清楚请使用 context7 查询(同时结合 `uv run python -c` 来查询 httpx 的真实接口)。
Python 部分，这个项目只应该对外暴露 httpx 的接口，而不应该实现任何 Python 的逻辑（除非必要），将逻辑交给 Rust 部分，这个项目只应该对外暴露。
Rust 部分，应该把 Python 部分的输入转为 reqwest 的输入，然后用 reqwest 来处理请求，将返回的 reqwest 的 Response 转为 Python httpx 的 Response 对象，并返回给 Python 部分。除非必要，Rust 部分的逻辑应该尽可能交给 reqwest 来处理，而不是自己实现。
综上，这个项目 Python 和 Rust 的作用只是作 httpx 接口和 reqwest 的接口的转换，仅此而已。

- Python 调用 Rust 应该尽可能高效，追求极致性能

- CI/CD 中不应该跑 benchmark

- 如果需要运行 benchmark，为避免阻塞，一定要加一个超时时间，示例运行 `timeout 60s uv run -m benchmark.faster_http_test`

- 禁止运行任何无限阻塞的任务（如 server 等），如果必须运行，请用 timeout 来限制时间
