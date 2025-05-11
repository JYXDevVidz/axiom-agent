# Axiom Agent API 🤖

[![GitHub stars](https://img.shields.io/github/stars/JYXDevVidz/axiom-agent?style=social)](https://github.com/JYXDevVidz/axiom-agent/stargazers)
[![GitHub license](https://img.shields.io/github/license/JYXDevVidz/axiom-agent)](https://github.com/JYXDevVidz/axiom-agent/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)

> 一个模块化的智能代理 API 系统，让 AI 为您执行实际任务 🔥

## 📖 简介

Axiom Agent API 是一个通过 RESTful 接口与大型语言模型 (LLM) 交互的智能代理系统。它设计为高度模块化和可扩展，通过插件式工具架构使 AI 能够执行实际任务，如文件操作、命令执行、用户交互等。

## ✨ 主要特性

- 🔌 **完全模块化** - 所有功能通过工具模块实现，易于扩展
- 🌐 **RESTful API** - 简单的 HTTP 接口，易于集成到任何应用
- 💬 **会话管理** - 支持多用户、多会话并行处理
- ⚙️ **工具丰富** - 文件读写、命令执行、交互式输入等
- 🔒 **安全机制** - 敏感操作确认，防止危险命令执行
- 🧠 **上下文记忆** - 会话中保持对话历史和上下文
- 🚀 **易于部署** - 简单配置，支持 Docker 部署

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/JYXDevVidz/axiom-agent.git
cd axiom-agent

# 安装依赖
pip install -r requirements.txt
```

### 配置

创建 `config.json` 文件:

```json
{
  "base_url": "https://api.openai.com/v1",
  "api_key": "YOUR_API_KEY",
  "model_name": "gpt-4o",
  "max_retries": 3,
  "timeout": 90
}
```

### 启动服务

```bash
python app.py
```

服务默认在 http://localhost:5000 上运行。

## 📝 API 使用示例

### 发送消息

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "列出当前目录中的文件"}'
```

响应示例:

```json
{
  "type": "tool_result",
  "tool": "execute",
  "success": true,
  "result": "file1.txt\nfile2.txt\nREADME.md",
  "session_id": "12345678-1234-5678-1234-567812345678"
}
```

### 用户交互

当代理需要更多信息时，您将收到交互请求:

```json
{
  "type": "interaction_required",
  "interaction_id": "87654321-4321-8765-4321-876543210987",
  "content": "请问您想创建什么内容的文件?",
  "prompt": "文件内容: ",
  "session_id": "12345678-1234-5678-1234-567812345678"
}
```

回复交互:

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "12345678-1234-5678-1234-567812345678",
    "message": "这是示例文件内容",
    "interaction_id": "87654321-4321-8765-4321-876543210987"
  }'
```

## 🔧 工具列表

Axiom Agent 预装了多种实用工具:

- 📄 **read** - 读取文件内容
- ✏️ **write** - 写入文件内容
- 🖥️ **execute** - 执行系统命令
- 📢 **info** - 显示信息给用户
- 💬 **interact** - 请求用户输入
- 🚪 **exit** - 结束当前任务

## 🛠️ 开发自定义工具

创建新工具只需三步:

1. 在 `tools/` 目录创建工具模块文件 (例如 `my_tool.py`)
2. 实现 `execute()` 函数作为入口点
3. 在 `tools.json` 中注册工具

示例工具:

```python
# tools/my_tool.py
def execute(param1: str, param2: int = 0) -> dict:
    """示例工具函数"""
    try:
        result = f"处理了 {param1} 和 {param2}"
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "result": f"工具执行失败: {str(e)}"
        }
```

## 📚 完整文档

获取详细 API 参考、工具开发规范和高级配置，请参阅[完整文档](docs/full_documentation.md)。

## 🔐 安全注意事项

Axiom Agent 可以执行系统命令，因此在生产环境中部署时应:

- 实现适当的 API 认证和授权
- 限制文件操作访问路径
- 使用 `security.json` 定义敏感命令
- 在公开网络上运行时使用 HTTPS

## 🤝 贡献

欢迎贡献新工具、功能和改进！请确保遵循项目的代码规范，并为重要更改提供测试案例。

## 📜 许可证

[MIT License](LICENSE)

## 📧 联系方式

有问题或建议? [创建 Issue](https://github.com/JYXDevVidz/axiom-agent/issues) 

---

⭐ 如果您喜欢这个项目，请考虑给它点赞! ⭐
