import os
import json
import sys
import platform
import psutil
import requests
import importlib.util
import re
import time
import uuid
import shlex
from typing import Dict, List, Union, Optional, Any, Tuple

class ConfigManager:
    """配置管理器：处理config.json文件"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"读取配置文件失败: {e}")
                return {}
        else:
            print(f"错误: 配置文件 {self.config_path} 不存在。")
            return {}
    
    def get_config(self) -> Dict:
        """获取当前配置"""
        return self.config


class SecurityManager:
    """安全管理器：处理敏感命令检查和确认"""
    
    def __init__(self, security_config_path: str = "security.json"):
        self.security_config_path = security_config_path
        self.sensitive_commands = []
        self.load_security_config()
    
    def load_security_config(self) -> None:
        """加载安全配置文件"""
        if os.path.exists(self.security_config_path):
            try:
                with open(self.security_config_path, 'r', encoding='utf-8') as f:
                    security_config = json.load(f)
                    self.sensitive_commands = security_config.get("sensitive_commands", [])
                    print(f"已加载 {len(self.sensitive_commands)} 个敏感命令定义")
            except Exception as e:
                print(f"加载安全配置失败: {e}")
                self.sensitive_commands = []
        else:
            print(f"警告: 未找到安全配置文件 {self.security_config_path}。敏感命令检查已禁用。")
            self.sensitive_commands = []
    
    def is_sensitive_command(self, command: str) -> Tuple[bool, str]:
        """检查命令是否为敏感命令
        
        Args:
            command: 要检查的命令
            
        Returns:
            (是否敏感, 敏感描述)
        """
        if not self.sensitive_commands:
            return False, ""
            
        current_os = platform.system().lower()
        # 解析命令获取第一个部分（命令名）
        try:
            cmd_parts = shlex.split(command)
            if not cmd_parts:
                return False, ""
            
            base_cmd = cmd_parts[0].lower()
            
            # 检查是否为定义的敏感命令
            for sensitive_cmd in self.sensitive_commands:
                pattern = sensitive_cmd.get("pattern", "").lower()
                # 检查操作系统兼容性
                cmd_os = sensitive_cmd.get("os", [])
                
                # 如果该命令适用于当前操作系统
                if not cmd_os or current_os in cmd_os:
                    # 精确匹配命令开头
                    if base_cmd == pattern or base_cmd.startswith(pattern + " "):
                        return True, sensitive_cmd.get("description", "敏感命令")
                    
                    # 检查命令选项中的敏感模式
                    if pattern in command:
                        return True, sensitive_cmd.get("description", "敏感命令")
            
            return False, ""
            
        except Exception as e:
            print(f"检查敏感命令异常: {e}")
            return False, ""


class ToolManager:
    """工具管理器：加载和管理工具"""
    
    def __init__(self, tools_path: str = "tools.json", tools_dir: str = "tools"):
        self.tools_path = tools_path
        self.tools_dir = tools_dir
        self.tools = {}
        self.tool_descriptions = {}
        self.security_manager = SecurityManager()
        self.load_tools()
    
    def load_tools(self) -> None:
        """加载工具定义和实现"""
        # 确保工具目录存在
        if not os.path.exists(self.tools_dir):
            os.makedirs(self.tools_dir)
            print(f"已创建工具目录: {self.tools_dir}")
        
        # 加载工具定义
        if os.path.exists(self.tools_path):
            try:
                with open(self.tools_path, 'r', encoding='utf-8') as f:
                    tool_definitions = json.load(f)
                    print(f"已加载工具定义: {self.tools_path}")
            except Exception as e:
                print(f"加载工具定义失败: {e}")
                tool_definitions = {}
        else:
            print(f"错误: 工具定义文件 {self.tools_path} 不存在")
            tool_definitions = {}
        
        # 内置exit工具
        self.tools["exit"] = self.exit_program
        self.tool_descriptions["exit"] = "结束当前任务"
        
        # 逐个加载工具
        for tool_name, tool_info in tool_definitions.items():
            # 跳过exit工具（已内置）
            if tool_name == "exit":
                continue
                
            # 获取工具描述
            self.tool_descriptions[tool_name] = tool_info.get("description", "")
            
            # 获取工具实现路径
            implementation = tool_info.get("implementation", "")
            if not implementation:
                print(f"警告: 工具 {tool_name} 未指定实现文件，已跳过")
                continue
            
            # 加载自定义工具
            full_path = os.path.join(self.tools_dir, implementation)
            try:
                self.load_custom_tool(tool_name, full_path)
            except Exception as e:
                print(f"加载工具 {tool_name} 失败: {e}")
    
    def load_custom_tool(self, tool_name: str, module_path: str) -> None:
        """动态加载自定义工具模块"""
        if not os.path.exists(module_path):
            print(f"找不到工具模块: {module_path}")
            return
        
        # 从文件加载模块
        spec = importlib.util.spec_from_file_location(tool_name, module_path)
        if spec is None or spec.loader is None:
            print(f"无法从 {module_path} 加载模块规范")
            return
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 检查模块是否有execute函数
        if hasattr(module, 'execute'):
            self.tools[tool_name] = module.execute
        else:
            print(f"工具模块 {module_path} 缺少execute函数")
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """获取所有工具的描述"""
        return self.tool_descriptions
    
    def get_tool_function(self, tool_name: str):
        """获取指定工具的函数"""
        return self.tools.get(tool_name)
    
    def has_tool(self, tool_name: str) -> bool:
        """检查是否存在指定工具"""
        return tool_name in self.tools
    
    @staticmethod
    def exit_program(message: str = "任务已完成") -> Dict:
        """结束当前任务"""
        try:
            print(f"任务已完成", flush=True)
            return {
                "success": True,
                "result": message,
                "exit": True
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"退出失败: {str(e)}"
            }


class DialogueManager:
    """对话管理器: 管理与模型的对话历史"""
    
    def __init__(self, max_tokens: int = 16000):
        self.max_tokens = max_tokens
        self.messages = []  # 对话历史
        self.last_tool_was_info = False  # 跟踪上一个工具是否为info
    
    def add_system_message(self, content: str) -> None:
        """添加系统消息"""
        self.messages.append({"role": "system", "content": content})
    
    def add_user_message(self, content: str) -> None:
        """添加用户消息"""
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: str) -> None:
        """添加助手消息"""
        self.messages.append({"role": "assistant", "content": content})
    
    def add_tool_result(self, tool_call: Dict, result: Dict) -> None:
        """添加工具调用结果作为用户消息
        
        Args:
            tool_call: 工具调用信息
            result: 工具执行结果
        """
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        
        # 记录当前工具是否为info
        self.last_tool_was_info = (tool_name == "info")
        
        # 构建工具结果消息
        message = f"工具调用结果 ({tool_name})\n"
        message += f"参数: {json.dumps(tool_args, ensure_ascii=False)}\n"
        message += f"成功: {result['success']}\n"
        
        if result.get("result") is not None:
            # 截断过长结果
            result_text = str(result["result"])
            if len(result_text) > 4000:
                result_text = result_text[:4000] + f"\n... [内容已截断，共 {len(result_text)} 字符]"
            message += f"结果:\n{result_text}"
        else:
            message += "结果: 无内容"
        
        # 如果是交互工具，添加用户输入
        if tool_name == "interact" and "user_input" in result:
            message += f"\n用户输入: {result['user_input']}"
        
        self.add_user_message(message)
        self._trim_history()
    
    def _trim_history(self) -> None:
        """修剪对话历史以保持在令牌限制内"""
        # 保留system消息
        system_message = None
        for msg in self.messages:
            if msg["role"] == "system":
                system_message = msg
                break
        
        # 估算当前对话历史的令牌数量
        total_tokens = sum(len(str(msg.get("content", ""))) for msg in self.messages) // 4  # 粗略估计
        
        # 如果超过最大令牌数，删除最早的消息，但保留系统消息
        while total_tokens > self.max_tokens and len(self.messages) > 2:  # 保留至少system和最新user
            # 找到第一个非系统消息删除
            for i, msg in enumerate(self.messages):
                if msg["role"] != "system":
                    self.messages.pop(i)
                    # 重新计算令牌数
                    total_tokens = sum(len(str(msg.get("content", ""))) for msg in self.messages) // 4
                    break
    
    def get_messages(self) -> List[Dict]:
        """获取当前对话历史"""
        return self.messages
    
    def was_last_tool_info(self) -> bool:
        """检查上一个使用的工具是否为info工具"""
        return self.last_tool_was_info


class ModelCommunicator:
    """模型通信器：处理与AI模型的通信，使用HTTP请求"""
    
    def __init__(self, config: Dict):
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.api_key = config.get("api_key", "")
        self.model_name = config.get("model_name", "gpt-4o")
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 5)
        self.timeout = config.get("timeout", 90)
    
    def send_request(self, messages: List[Dict]) -> Dict:
        """向模型发送请求，自动重试
        
        Args:
            messages: 消息历史
            
        Returns:
            模型响应
        """
        retries = 0
        
        # 准备请求头和请求体
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "stream": False  # 禁用流式输出
        }
        
        while retries <= self.max_retries:
            try:
                print({"type": "system", "timestamp": time.time(), "content": {"message": "向模型发送请求", "retry": retries, "max_retries": self.max_retries}}, flush=True)
                
                # 使用requests发送请求
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                # 检查响应状态码
                if response.status_code == 200:
                    # 检查内容是否为JSON
                    try:
                        return response.json()
                    except json.JSONDecodeError as e:
                        print({"type": "error", "timestamp": time.time(), "content": {"message": f"JSON解析失败: {str(e)}"}}, flush=True)
                        # 如果不是有效的JSON，我们可以尝试重试
                        retries += 1
                        if retries <= self.max_retries:
                            print(f"响应不是有效的JSON，将在{self.retry_delay}秒后重试...", flush=True)
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            return {"error": f"服务器返回了无效的JSON响应: {response.text[:200]}..."}
                else:
                    # 某些错误可能需要重试
                    if 500 <= response.status_code < 600:  # 服务器错误
                        retries += 1
                        if retries <= self.max_retries:
                            print(f"API请求返回错误状态码: {response.status_code}，将在{self.retry_delay}秒后重试...", flush=True)
                            time.sleep(self.retry_delay)
                            continue
                    
                    # 其他错误直接返回，不重试
                    print(f"API请求失败: {response.status_code}", flush=True)
                    error_text = response.text
                    try:
                        error_json = response.json()
                        error_text = json.dumps(error_json, ensure_ascii=False)
                    except:
                        pass
                    print(error_text, flush=True)
                    return {"error": f"API请求失败: {response.status_code}", "details": error_text}
                    
            except requests.exceptions.Timeout:
                # 超时错误，尝试重试
                retries += 1
                if retries <= self.max_retries:
                    print(f"API请求超时，将在{self.retry_delay}秒后重试 ({retries}/{self.max_retries})...", flush=True)
                    time.sleep(self.retry_delay)
                else:
                    print(f"API请求在{self.max_retries}次重试后仍然超时", flush=True)
                    return {"error": "API请求多次超时，请检查网络连接或稍后再试"}
            
            except requests.exceptions.ConnectionError:
                # 连接错误，尝试重试
                retries += 1
                if retries <= self.max_retries:
                    print(f"API连接错误，将在{self.retry_delay}秒后重试 ({retries}/{self.max_retries})...", flush=True)
                    time.sleep(self.retry_delay)
                else:
                    print(f"API连接在{self.max_retries}次重试后仍然失败", flush=True)
                    return {"error": "API连接多次失败，请检查网络连接或API服务是否可用"}
                
            except Exception as e:
                # 其他异常
                print(f"API请求异常: {e}", flush=True)
                retries += 1
                if retries <= self.max_retries:
                    print(f"将在{self.retry_delay}秒后重试 ({retries}/{self.max_retries})...", flush=True)
                    time.sleep(self.retry_delay)
                else:
                    return {"error": f"API请求异常: {str(e)}"}
        
        return {"error": f"API请求在{self.max_retries}次重试后失败"}
    
    def parse_response(self, response: Dict, available_tools: List[str]) -> Union[Dict, str]:
        """解析模型响应
        
        Args:
            response: 模型响应
            available_tools: 可用工具列表
            
        Returns:
            工具调用信息或EOF标记
        """
        try:
            # 检查是否有错误
            if "error" in response:
                print(f"模型响应错误: {response['error']}", flush=True)
                return {"type": "error", "message": response.get("error")}
            
            # 获取实际内容
            if not response.get("choices"):
                return {"type": "error", "message": "模型响应中没有choices字段"}
                
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not content:
                return {"type": "error", "message": "模型响应内容为空"}
            
            # 检查是否包含EOF标记（如果EOF单独出现或在最后）
            if content.strip() == "EOF" or content.strip().endswith("EOF"):
                return "EOF"
            
            # 1. 首先尝试查找JSON代码块
            json_pattern = re.search(r'```(?:json|python)?\s*([\s\S]*?)```', content)
            if json_pattern:
                try:
                    # 提取JSON块内容
                    json_text = json_pattern.group(1).strip()
                    
                    # 处理多行JSON文本
                    lines = [line.strip() for line in json_text.split('\n')]
                    lines = [line for line in lines if line]
                    json_text = ' '.join(lines)
                    
                    # 查找包含{...}的部分
                    json_obj_match = re.search(r'({[\s\S]*})', json_text)
                    if json_obj_match:
                        json_text = json_obj_match.group(1)
                    
                    # 尝试解析JSON
                    tool_json = json.loads(json_text)
                    
                    # 检查是否是标准工具调用格式
                    if "name" in tool_json and "args" in tool_json:
                        tool_name = tool_json["name"]
                        if tool_name in available_tools:
                            return tool_json  # 直接返回使用标准格式的工具调用
                except json.JSONDecodeError as e:
                    print({"type": "error", "timestamp": time.time(), "content": {"message": f"JSON解析失败: {str(e)}"}}, flush=True)
            
            # 2. 如果没有找到标准格式的JSON工具调用，尝试解析其他格式
            
            # 2.1 查找类似 tool_name(arg1="value", arg2="value") 的模式
            tool_call_match = re.search(r'([a-zA-Z_]+)\s*\(([\s\S]*?)\)', content)
            if tool_call_match:
                tool_name = tool_call_match.group(1).strip()
                args_text = tool_call_match.group(2).strip()
                
                if tool_name in available_tools:
                    # 解析参数
                    args = {}
                    for arg_match in re.finditer(r'([a-zA-Z_]+)\s*=\s*(?:"([^"]*?)"|\'([^\']*?)\'|([^,\s]+))', args_text):
                        arg_name = arg_match.group(1)
                        # 找到第一个非None的组
                        arg_value = next((g for g in arg_match.groups()[1:] if g is not None), "")
                        args[arg_name] = arg_value
                    
                    return {
                        "name": tool_name,
                        "args": args
                    }
            
            # 2.2 查找显式提到工具名及其参数的模式
            for tool_name in available_tools:
                tool_match = re.search(rf'{tool_name}\s*[:：]?\s*(.*)', content, re.IGNORECASE)
                if tool_match:
                    # 找到工具名，解析参数
                    rest_of_content = tool_match.group(1).strip()
                    
                    # 如果是exit工具，简单处理
                    if tool_name == "exit":
                        return {
                            "name": "exit",
                            "args": {"message": rest_of_content or "任务已完成"}
                        }
                    
                    # 尝试从内容中提取参数
                    args = {}
                    
                    # 查找引号括起来的参数
                    param_matches = re.finditer(r'([a-zA-Z_]+)\s*[:：]\s*[\'"]([^\'"]+)[\'"]', rest_of_content)
                    for param_match in param_matches:
                        param_name = param_match.group(1)
                        param_value = param_match.group(2)
                        args[param_name] = param_value
                    
                    # 如果没有找到参数，使用整个内容
                    if not args:
                        # 查找文件路径参数（针对read/write工具）
                        if tool_name in ["read", "write"]:
                            file_path_match = re.search(r'[\'"]([^\'"]+)[\'"]|文件\s*[:：]?\s*([^\s,]+)|路径\s*[:：]?\s*([^\s,]+)', rest_of_content)
                            if file_path_match:
                                # 选择第一个非None的组作为文件路径
                                file_path = next((g for g in file_path_match.groups() if g), "")
                                args["file_path"] = file_path
                        
                        # 针对命令工具，整个内容可能就是命令
                        if tool_name == "execute" and not args:
                            args["command"] = rest_of_content
                        
                        # 针对info和interact工具，整个内容可能就是内容
                        if tool_name in ["info", "interact"] and not args:
                            args["content"] = rest_of_content
                    
                    return {
                        "name": tool_name,
                        "args": args
                    }
            
            # 3. 最后，尝试根据内容猜测最可能的工具
            
            # 3.1 内容包含"退出"、"结束"等关键词
            if re.search(r'退出|结束|完成|exit|quit', content, re.IGNORECASE):
                return {
                    "name": "exit",
                    "args": {"message": content.strip() or "任务已完成"}
                }
            
            # 3.2 内容看起来像是提供信息
            if len(content.strip().split()) > 3 and "info" in available_tools:
                return {
                    "name": "info",
                    "args": {"content": content.strip()}
                }
            
            # 如果无法识别为任何工具调用，返回错误
            print(f"无法解析模型响应为工具调用:\n{content}", flush=True)
            return {"type": "error", "message": "无法解析响应为工具调用", "content": content}
            
        except Exception as e:
            print(f"解析模型响应异常: {e}", flush=True)
            print(f"异常详情: {str(e)}", flush=True)
            return {"type": "error", "message": f"解析响应异常: {str(e)}"}


class AIAgent:
    """AI Agent主类：协调所有组件工作"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.tool_manager = ToolManager()
        self.dialogue_manager = DialogueManager(self.config.get("max_tokens", 16000))
        self.model_communicator = ModelCommunicator(self.config)
        
        # 添加大文件处理的配置
        self.max_content_size = self.config.get("max_content_size", 10 * 1024)  # 默认10KB
        
        # 挂起的交互请求
        self.pending_interactions = {}
        
        # 初始化系统消息
        system_prompt = self.get_system_prompt()
        self.dialogue_manager.add_system_message(system_prompt)
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        try:
            system_info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "python_version": sys.version,
                "cpu_cores": psutil.cpu_count(logical=True),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "current_directory": os.getcwd()
            }
            
            # 获取所有可用工具的描述
            tool_descriptions = self.tool_manager.get_tool_descriptions()
            
            # 构建工具使用指南
            tools_info = "你将作为Axiom Agent为用户服务!\n\n【工具使用指南】\n你有以下工具可用，请按需选择最合适的工具:\n\n"
            
            for tool_name, description in tool_descriptions.items():
                tools_info += f"{tool_name}: {description}\n"
                
                # 添加工具调用格式示例
                tools_info += "调用格式: \n```json\n"  
                tools_info += f'{{\n  "name": "{tool_name}",\n  "args": {{\n'  
                
                # 读取tools.json获取参数信息  
                try:  
                    with open("tools.json", 'r', encoding='utf-8') as f:  
                        tool_defs = json.load(f)  
                    
                    args = tool_defs.get(tool_name, {}).get("args", {})  
                    for arg_name, arg_desc in args.items():  
                        tools_info += f'    "{arg_name}": "参数值" // {arg_desc}\n'  
                except:  
                    # 如果无法读取tools.json，使用通用格式  
                    if tool_name == "exit":  
                        tools_info += '    "message": "可选的结束消息"\n'  
                    else:  
                        tools_info += '    "...": "查看tools.json获取此工具的参数"\n'  
                
                tools_info += "  }\n}\n```\n\n"
            
            tools_info += """
【API工作模式】
- 我作为API服务运行，不再有命令行交互界面
- 每个用户请求和响应作为独立的API调用处理
- 用户交互使用异步模式，需要用户在下一次请求中提供输入

【任务执行流程】
1. 收到新任务时，首先分析任务性质:
   - 如果是复杂任务：先用info工具提供整体计划
   - 如果是简单任务：直接使用相应工具执行

2. 使用info工具后:
   - 必须立即使用其他工具执行实际操作
   - 不要连续使用info工具

3. 执行步骤:
   - 使用适当的工具执行具体操作
   - 使用info工具提供阶段性进展
   - 使用interact工具在需要用户输入时与用户交互
   - 使用exit工具结束任务

4. 安全考虑:
   - 执行危险命令时系统会自动要求用户确认
   - 确保解释清楚命令的目的和可能的影响
   - 在执行修改系统状态的命令前先做好检查和备份

【注意事项】
- 如果你想要展示消息并获得用户的回复，请务必使用interact工具而非info工具
- 避免重复使用info工具，提供信息后立即执行
- 每次只返回一个工具调用，不要添加额外说明
- 大文件内容会自动截断，请提取关键信息处理
- 保持回答简洁，聚焦于任务目标
- 交互工具(interact)现在会暂停执行流程，等待下一次用户消息
- 任务完成时务必使用exit工具结束任务
"""
            
            return f"系统信息: {json.dumps(system_info, ensure_ascii=False)}\n{tools_info}"
        except Exception as e:
            print(f"获取系统信息失败: {e}", flush=True)
            return "无法获取完整系统信息。"
    
    def process_message(self, message: str) -> Dict:
        """处理用户消息并返回结果
        
        Args:
            message: 用户消息
            
        Returns:
            处理结果
        """
        # 添加用户消息到对话
        self.dialogue_manager.add_user_message(message)
        
        # 获取当前对话历史并发送请求
        messages = self.dialogue_manager.get_messages()
        response = self.model_communicator.send_request(messages)
        
        # 检查是否有错误
        if "error" in response:
            return {
                "type": "error",
                "message": response.get("error"),
                "details": response.get("details", "")
            }
        
        # 获取可用工具列表
        available_tools = list(self.tool_manager.get_tool_descriptions().keys())
        
        # 解析响应
        parsed_response = self.model_communicator.parse_response(response, available_tools)
        
        # 添加模型响应到对话历史
        if "choices" in response and len(response["choices"]) > 0:
            if "message" in response["choices"][0]:
                content = response["choices"][0]["message"].get("content", "")
                if content:
                    self.dialogue_manager.add_assistant_message(content)
        
        # 如果是错误类型响应，返回错误信息
        if isinstance(parsed_response, dict) and parsed_response.get("type") == "error":
            return {
                "type": "error",
                "message": parsed_response.get("message", "未知错误"),
                "content": parsed_response.get("content", "")
            }
        
        # 如果是EOF，转换为exit工具调用
        if parsed_response == "EOF":
            parsed_response = {
                "name": "exit",
                "args": {"message": "任务已完成"}
            }
        
        # 防止连续使用info工具
        if parsed_response.get("name") == "info" and self.dialogue_manager.was_last_tool_info():
            tool_result = {
                "success": False,
                "result": "检测到连续使用info工具。请改用其他工具执行具体操作。"
            }
            self.dialogue_manager.add_tool_result(parsed_response, tool_result)
            return {
                "type": "warning",
                "message": "连续使用info工具",
                "result": tool_result["result"],
                "next_action": "请使用其他工具执行具体操作，而非继续提供信息。"
            }
        
        # 处理工具调用
        tool_call = parsed_response
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        
        # 获取工具函数
        tool_function = self.tool_manager.get_tool_function(tool_name)
        
        if tool_function is None:
            result = {
                "success": False,
                "result": f"未知工具: {tool_name}"
            }
            # 添加结果到对话历史
            self.dialogue_manager.add_tool_result(tool_call, result)
            return {
                "type": "error",
                "message": f"未知工具: {tool_name}"
            }
        
        # 特殊处理interact工具
        if tool_name == "interact":
            # 创建交互请求
            interaction_id = str(uuid.uuid4())
            content = tool_args.get("content", "请输入您的回复")
            prompt = tool_args.get("prompt", "请输入您的回复: ")
            
            # 记录交互请求
            self.pending_interactions[interaction_id] = {
                "tool_call": tool_call,
                "content": content,
                "prompt": prompt
            }
            
            # 返回等待交互的响应
            return {
                "type": "interaction_required",
                "interaction_id": interaction_id,
                "content": content,
                "prompt": prompt
            }
        
        # 调用工具函数并传递参数
        result = tool_function(**tool_args)
        
        # 检查是否是exit工具且执行成功
        if tool_name == "exit" and result.get("success") and result.get("exit", False):
            # 添加结果到对话历史
            self.dialogue_manager.add_tool_result(tool_call, result)
            return {
                "type": "exit",
                "message": result.get("result", "任务已完成")
            }
        
        # 添加工具结果到对话历史
        self.dialogue_manager.add_tool_result(tool_call, result)
        
        # 根据工具类型构建响应
        return {
            "type": "tool_result",
            "tool": tool_name,
            "success": result.get("success", False),
            "result": result.get("result", "")
        }
    
    def complete_interaction(self, interaction_id: str, user_input: str) -> Dict:
        """完成交互操作，继续处理
        
        Args:
            interaction_id: 交互ID
            user_input: 用户输入
            
        Returns:
            处理结果
        """
        # 检查交互ID是否存在
        if interaction_id not in self.pending_interactions:
            return {
                "type": "error",
                "message": f"交互ID {interaction_id} 不存在或已过期"
            }
        
        # 获取挂起的交互信息
        interaction = self.pending_interactions.pop(interaction_id)
        tool_call = interaction["tool_call"]
        
        # 构造交互工具结果
        result = {
            "success": True,
            "result": f"用户回复: {user_input}",
            "user_input": user_input
        }
        
        # 添加工具结果到对话历史
        self.dialogue_manager.add_tool_result(tool_call, result)
        
        # 构造继续执行的消息
        return self.process_message("继续执行任务")