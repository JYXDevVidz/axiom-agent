# Axiom Agent API 完整文档

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [API 参考文档](#3-api-参考文档)
4. [核心模块文档](#4-核心模块文档)
5. [工具开发规范](#5-工具开发规范)
6. [配置文件说明](#6-配置文件说明)
7. [部署指南](#7-部署指南)
8. [安全考虑](#8-安全考虑)
9. [示例和使用案例](#9-示例和使用案例)
10. [常见问题解答](#10-常见问题解答)

## 1. 项目概述

Axiom Agent API 是一个模块化的智能代理系统，通过 RESTful API 提供与大型语言模型（LLM）的交互能力。系统设计为高度可扩展和灵活，允许用户通过开发自定义工具来扩展其功能。

### 主要特性

- **API 驱动**：通过简单的 HTTP 请求与代理交互
- **会话管理**：支持多用户、多会话并行处理
- **工具模块化**：所有功能通过模块化工具实现，易于扩展
- **异步交互**：支持需要用户输入的情景，如确认敏感操作
- **状态持久化**：对话历史和上下文在会话中持续保持
- **敏感操作保护**：对潜在危险操作提供安全确认机制

## 2. 系统架构

Axiom Agent API 由以下核心组件构成：

```
┌─────────────────────┐     ┌──────────────────┐
│   客户端应用         │◄───►│   Flask API 服务  │
└─────────────────────┘     └────────┬─────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────┐
│                    AIAgent                          │
├─────────────┬──────────────┬─────────────┬──────────┤
│ConfigManager│ToolManager   │DialogueManager│ModelCom.│
└─────────────┴──────────────┴─────────────┴──────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│                     工具模块                         │
├─────────┬─────────┬─────────┬──────────┬────────────┤
│  read   │  write  │ execute │  info    │  interact  │
└─────────┴─────────┴─────────┴──────────┴────────────┘
```

### 核心组件说明

- **Flask API 服务**：提供 RESTful API 接口，管理会话和请求路由
- **AIAgent**：智能代理核心，协调各组件工作
- **ConfigManager**：管理系统配置
- **ToolManager**：加载和管理工具模块
- **DialogueManager**：管理会话历史和对话上下文
- **ModelCommunicator**：与 LLM API 通信

## 3. API 参考文档

### 3.1 基本信息

- **Base URL**: `http://localhost:5000/api`
- **Content-Type**: `application/json`
- **响应格式**: 所有响应都使用 JSON 格式

### 3.2 API 端点

#### 3.2.1 发送消息

**请求**:

```
POST /chat
```

**请求体**:

```json
{
  "session_id": "string (可选，如果不提供则创建新会话)",
  "message": "string (必须, 用户消息内容)",
  "interaction_id": "string (可选，仅当响应交互请求时需要)"
}
```

**响应**:

根据不同情况，响应格式会有所不同：

1. **工具调用结果**:

```json
{
  "type": "tool_result",
  "tool": "string (工具名称)",
  "success": boolean,
  "result": "string (工具执行结果)",
  "session_id": "string (会话ID)"
}
```

2. **需要用户交互**:

```json
{
  "type": "interaction_required",
  "interaction_id": "string (交互ID)",
  "content": "string (向用户展示的内容)",
  "prompt": "string (输入提示)",
  "session_id": "string (会话ID)"
}
```

3. **任务结束**:

```json
{
  "type": "exit",
  "message": "string (结束消息)",
  "session_id": "string (会话ID)"
}
```

4. **错误响应**:

```json
{
  "type": "error",
  "message": "string (错误描述)",
  "content": "string (可选，原始错误内容)",
  "session_id": "string (会话ID, 如果有)"
}
```

5. **警告响应**:

```json
{
  "type": "warning",
  "message": "string (警告描述)",
  "result": "string (警告详情)",
  "next_action": "string (建议的下一步操作)",
  "session_id": "string (会话ID)"
}
```

#### 3.2.2 删除会话

**请求**:

```
DELETE /sessions/{session_id}
```

**响应**:

```json
{
  "success": boolean,
  "message": "string (操作结果描述)"
}
```

### 3.3 错误码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 400 | 错误请求 (缺少必要参数或参数无效) |
| 404 | 资源不存在 (会话ID无效) |
| 500 | 服务器内部错误 |

## 4. 核心模块文档

### 4.1 agent.py

`agent.py` 是系统的核心模块，包含以下主要类：

#### 4.1.1 AIAgent 类

AI代理主类，协调所有组件工作。

**主要方法**:

- `__init__()`: 初始化代理实例
- `get_system_prompt()`: 获取系统提示词
- `process_message(message)`: 处理用户消息并返回结果
- `complete_interaction(interaction_id, user_input)`: 完成交互操作

#### 4.1.2 ConfigManager 类

配置管理器，负责加载和管理配置。

**主要方法**:

- `load_config()`: 加载配置文件
- `get_config()`: 获取当前配置

#### 4.1.3 SecurityManager 类

安全管理器，处理敏感命令检查。

**主要方法**:

- `load_security_config()`: 加载安全配置
- `is_sensitive_command(command)`: 检查命令是否敏感

#### 4.1.4 ToolManager 类

工具管理器，负责加载和管理工具。

**主要方法**:

- `load_tools()`: 加载所有工具
- `load_custom_tool(tool_name, module_path)`: 加载自定义工具
- `get_tool_function(tool_name)`: 获取工具函数

#### 4.1.5 DialogueManager 类

对话管理器，管理会话历史。

**主要方法**:

- `add_user_message(content)`: 添加用户消息
- `add_assistant_message(content)`: 添加助手消息
- `add_tool_result(tool_call, result)`: 添加工具调用结果
- `get_messages()`: 获取对话历史

#### 4.1.6 ModelCommunicator 类

模型通信器，与LLM API通信。

**主要方法**:

- `send_request(messages)`: 发送请求到模型
- `parse_response(response, available_tools)`: 解析模型响应

## 5. 工具开发规范

### 5.1 工具结构

每个工具都应遵循以下结构：

1. 放置在 `tools/` 目录下
2. 实现 `execute()` 函数作为入口点
3. 返回标准格式的结果

### 5.2 工具函数规范

工具的 `execute()` 函数必须遵循以下规范：

**函数签名**:

```python
def execute(*args, **kwargs) -> dict:
    """工具执行入口点
    
    Args:
        根据工具需要的参数定义
        
    Returns:
        dict: 包含以下键的字典
            - success (bool): 执行是否成功
            - result (str): 执行结果或错误消息
            - 可选的其他特殊字段
    """
```

**标准返回格式**:

```python
{
    "success": True/False,  # 必须
    "result": "执行结果或错误消息",  # 必须
    # 可选字段
    "exit": True,  # 仅用于exit工具
    "awaiting_user_input": True,  # 仅用于interact工具
    "content": "交互内容",  # 仅用于interact工具
    "prompt": "输入提示",  # 仅用于interact工具
    "sensitive_command": True,  # 标记敏感命令
    "needs_confirmation": True  # 需要确认的操作
}
```

### 5.3 工具定义

工具需要在 `tools.json` 文件中定义:

```json
{
  "tool_name": {
    "description": "工具描述",
    "implementation": "file_name.py",
    "args": {
      "arg1": "参数1描述",
      "arg2": "参数2描述"
    }
  }
}
```

### 5.4 工具开发示例

```python
# tools/example_tool.py

def execute(param1: str, param2: int = 0) -> dict:
    """示例工具函数
    
    Args:
        param1: 第一个参数
        param2: 第二个参数，默认为0
        
    Returns:
        执行结果
    """
    try:
        # 执行工具逻辑
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

## 6. 配置文件说明

### 6.1 config.json

主配置文件，定义系统核心设置：

```json
{
  "base_url": "https://api.openai.com/v1",
  "api_key": "YOUR_API_KEY",
  "model_name": "gpt-4o",
  "max_retries": 3,
  "retry_delay": 5,
  "timeout": 90,
  "max_tokens": 16000,
  "max_content_size": 10240
}
```

| 参数 | 类型 | 描述 | 默认值 |
|------|------|------|--------|
| base_url | string | LLM API基础URL | https://api.openai.com/v1 |
| api_key | string | LLM API密钥 | - |
| model_name | string | 使用的模型名称 | gpt-4o |
| max_retries | integer | API请求最大重试次数 | 3 |
| retry_delay | integer | 重试间隔(秒) | 5 |
| timeout | integer | API请求超时(秒) | 90 |
| max_tokens | integer | 对话历史最大token数 | 16000 |
| max_content_size | integer | 内容最大字节数 | 10240 |

### 6.2 tools.json

工具定义文件，配置系统可用工具：

```json
{
  "read": {
    "description": "读取文件内容",
    "implementation": "read.py",
    "args": {
      "file_path": "要读取的文件路径"
    }
  },
  "write": {
    "description": "写入文件内容",
    "implementation": "write.py",
    "args": {
      "file_path": "要写入的文件路径",
      "content": "要写入的内容",
      "mode": "写入模式：w(覆盖)或a(追加)"
    }
  }
}
```

### 6.3 security.json

安全配置文件，定义敏感命令：

```json
{
  "sensitive_commands": [
    {
      "pattern": "rm",
      "description": "删除文件或目录命令",
      "os": ["linux", "darwin"]
    },
    {
      "pattern": "del",
      "description": "删除文件命令",
      "os": ["windows"]
    }
  ]
}
```

## 7. 部署指南

### 7.1 系统要求

- Python 3.8+
- Flask
- requests
- psutil

### 7.2 安装步骤

1. 克隆或下载项目代码

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 配置文件：
   - 创建 `config.json` 配置文件
   - 创建 `tools.json` 工具定义文件
   - 可选：创建 `security.json` 安全配置文件

4. 启动服务：

```bash
python app.py
```

默认服务运行在 `http://localhost:5000`

### 7.3 Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

构建和运行：

```bash
docker build -t axiom-agent-api .
docker run -p 5000:5000 axiom-agent-api
```

## 8. 安全考虑

### 8.1 API安全

- **身份验证**: 在生产环境中应实现API密钥或OAuth等身份验证
- **输入验证**: 所有API输入都应进行验证和消毒
- **限速**: 实现API速率限制以防止滥用

### 8.2 敏感命令处理

敏感命令通过 `security.json` 定义，执行前会要求确认。对于API版本，敏感命令会返回需要确认的响应，而不是直接执行。

### 8.3 文件安全

- 限制文件操作在特定目录
- 对写入操作进行额外验证
- 防止路径遍历攻击

### 8.4 模型安全

- 使用提示词工程技术防止提示注入
- 对模型输出进行安全过滤
- 限制模型访问敏感系统功能

## 9. 示例和使用案例

### 9.1 基本用法：文件操作

**客户端请求**:

```json
// POST /api/chat
{
  "message": "请列出当前目录下的文件"
}
```

**服务器响应**:

```json
{
  "type": "tool_result",
  "tool": "execute",
  "success": true,
  "result": "file1.txt\nfile2.txt\nREADME.md",
  "session_id": "12345678-1234-5678-1234-567812345678"
}
```

### 9.2 用户交互

**客户端请求**:

```json
// POST /api/chat
{
  "session_id": "12345678-1234-5678-1234-567812345678",
  "message": "请帮我创建一个名为 example.txt 的文件"
}
```

**服务器响应** (需要用户输入):

```json
{
  "type": "interaction_required",
  "interaction_id": "87654321-4321-8765-4321-876543210987",
  "content": "请提供要写入 example.txt 的内容",
  "prompt": "文件内容: ",
  "session_id": "12345678-1234-5678-1234-567812345678"
}
```

**客户端继续请求** (提供交互内容):

```json
// POST /api/chat
{
  "session_id": "12345678-1234-5678-1234-567812345678",
  "message": "这是一个示例文件内容",
  "interaction_id": "87654321-4321-8765-4321-876543210987"
}
```

**服务器响应**:

```json
{
  "type": "tool_result",
  "tool": "write",
  "success": true,
  "result": "文件写入成功: example.txt",
  "session_id": "12345678-1234-5678-1234-567812345678"
}
```

### 9.3 敏感操作确认

**客户端请求**:

```json
// POST /api/chat
{
  "session_id": "12345678-1234-5678-1234-567812345678",
  "message": "删除 example.txt 文件"
}
```

**服务器响应** (敏感操作需要确认):

```json
{
  "type": "interaction_required",
  "interaction_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "content": "检测到敏感命令: rm example.txt\n描述: 删除文件命令\n请确认是否要执行此操作？",
  "prompt": "输入 'yes' 确认或 'no' 取消: ",
  "session_id": "12345678-1234-5678-1234-567812345678"
}
```

## 10. 常见问题解答

### 10.1 技术问题

**Q: 如何更改服务端口？**  
A: 在 `app.py` 中修改 `app.run()` 的 `port` 参数。

**Q: 如何处理大型文件？**  
A: 大文件会自动截断以防止内存溢出。可以通过 `config.json` 中的 `max_content_size` 调整截断大小。

**Q: 会话数据存储在哪里？**  
A: 当前会话数据存储在内存中。如需持久化，应实现数据库存储。

### 10.2 开发问题

**Q: 如何调试工具？**  
A: 工具可以通过返回详细的 `result` 字段来提供调试信息。还可以在工具中使用 `print()` 打印调试信息，这些信息会显示在服务器控制台。

**Q: 如何添加新工具类型？**  
A: 创建新的工具模块文件放入 `tools/` 目录，然后在 `tools.json` 中注册。

**Q: 如何替换底层LLM？**  
A: 修改 `config.json` 中的 `base_url` 和 `model_name`，并在必要时修改 `ModelCommunicator` 类以适应新API的请求/响应格式。

---

## 开发者贡献

欢迎贡献新工具、功能和改进！请确保遵循项目的代码规范，并为重要更改提供测试案例。

## 许可证

MIT License

---

*文档最后更新: 2025年5月11日*
