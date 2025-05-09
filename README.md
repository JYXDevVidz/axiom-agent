
# Axiom Agent

Axiom Agent 是一个强大的可自定义工具智能助手，基于大语言模型构建，能够处理各种任务并让您轻松添加自定义工具。

## 🌟 主要特点

- **可自定义工具系统** - 轻松添加自己的工具
- **对话式交互** - 自然的对话流程
- **内置核心工具** - 文件操作、命令执行等
- **灵活的工具调用格式** - 支持多种调用格式
- **健壮的错误处理** - 自动重试和清晰的错误信息
- **自动上下文管理** - 优化令牌使用

## 📁 项目结构

```
axiom-agent/
  ├── main.py          # 主程序
  ├── config.json      # 配置文件
  ├── tools.json       # 工具定义
  └── tools/           # 工具实现文件夹
      └── example_tool.py  # 示例自定义工具
```

## 🚀 快速开始

### 安装依赖

```bash
pip install requests psutil
```

### 配置

1. 编辑 `config.json`：

```json
{
  "base_url": "https://api.openai.com/v1",
  "api_key": "YOUR_API_KEY_HERE",
  "model_name": "gpt-4o",
  "max_retries": 3,
  "retry_delay": 5,
  "timeout": 90,
  "max_tokens": 16000,
  "max_content_size": 10240
}
```

2. 运行助手：

```bash
python main.py
```

## 🛠️ 内置工具

Axiom Agent 内置了六个核心工具：

| 工具名 | 描述 | 主要参数 |
|-------|------|---------|
| read | 读取文件内容 | file_path |
| write | 写入文件内容 | file_path, content, mode |
| execute | 执行系统命令 | command |
| info | 显示重要信息 | content |
| interact | 与用户交互 | content, prompt |
| exit | 结束当前任务 | message |

## ✨ 添加自定义工具

### 步骤 1: 创建工具实现

在 `tools` 目录下创建一个 Python 文件 (例如 `my_tool.py`):

```python
def execute(**kwargs):
    """
    工具执行函数
    """
    try:
        # 从kwargs获取参数
        param1 = kwargs.get('param1', 'default_value')
        
        # 执行工具功能
        result = f"自定义工具结果: {param1}"
        
        # 返回结果
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

### 步骤 2: 在tools.json中注册工具

```json
"my_tool": {
  "description": "我的自定义工具，用于...",
  "implementation": "my_tool.py",
  "args": {
    "param1": "参数1的描述",
    "param2": "参数2的描述"
  }
}
```

## 🔄 工具调用格式

Axiom Agent 支持多种工具调用格式：

### 1. 标准JSON格式

```json
{
  "name": "tool_name",
  "args": {
    "arg1": "value1",
    "arg2": "value2"
  }
}
```

### 2. 函数调用样式

```
tool_name(arg1="value1", arg2="value2")
```

### 3. 自然语言描述

```
使用read工具读取文件"example.txt"
```

## 📝 示例使用场景

### 文件分析

```
> 分析当前目录下的Python文件并统计行数

[工具执行过程...]

总共发现5个Python文件，共1250行代码
```

### 数据处理

```
> 读取sales.csv，计算总销售额并生成报告

[工具执行过程...]

已生成销售报告report.md，总销售额: $12,536.42
```

## 🔒 注意事项

- 始终验证外部输入以防安全风险
- 工具的execute函数必须处理所有可能的异常
- 确保您有权限执行所请求的操作

## 📄 许可证

MIT

## 🙏 贡献

欢迎提交问题和改进建议！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request
