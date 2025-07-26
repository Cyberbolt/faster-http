项目规则 @prompts/project-rules.md

你应该遵循：

- 你应该合理安排 软件开发工程师 sub agent 和 测试工程师 sub agent 来完成任务，暂时不需要请 技术文档工程师 sub agent 编写文档

- 开发(编写或修改代码)和测试应该安排给相应的 sub agent，你不应该自己来做，应该安排给别的 sub agent

- 安排软件开发工程师 sub agent 编写或修改了代码，如果没有测试，还需要安排 测试工程师 sub agent 来测试。除了测试当前功能以外，还需要运行全部测试确保其他功能没有受到破坏
