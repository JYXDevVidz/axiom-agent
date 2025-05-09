import os
import json
import sys
import platform
import psutil
import requests
import importlib.util
import re
import time
import shlex
from typing import Dict, List, Union, Optional, Any, Tuple

class ConfigManager:
    """配置管理器：处理config.json文件"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件，如果不存在则创建"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"读取配置文件失败: {e}")
                return self.create_config()
        else:
            return self.create_config()
    
    def create_config(self) -> Dict:
        """交互式创建配置文件"""
        print("配置文件不存在，请输入以下信息：")
        
        base_url = input("API基础URL (例如: https://api.openai.com/v1): ").strip()
        api_key = input("API密钥: ").strip()
        model_name = input("模型名称 (例如: gpt-4o): ").strip()
        
        config = {
            "base_url": base_url,
            "api_key": api_key,
            "model_name": model_name,
            "max_retries": 3,           # 最大重试次数
            "retry_delay": 5,           # 重试间隔(秒)
            "timeout": 90,              # 请求超时时间(秒)
            "max_tokens": 16000,        # 最大令牌数
            "max_content_size": 10 * 1024  # 最大内容大小（字节）
        }
        
        # 保存配置
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print(f"配置已保存至 {self.config_path}")
        except Exception as e:
            print(f"保存配置失败: {e}")
        
        return config
    
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
                self.create_default_security_config()
        else:
            self.create_default_security_config()
    
    def create_default_security_config(self) -> None:
        """创建默认安全配置文件"""
        default_config = {
            "sensitive_commands": [
                {
                    "pattern": "rm",
                    "description": "删除文件或目录命令",
                    "os": ["linux", "darwin"]
                },
                {
                    "pattern": "rmdir",
                    "description": "删除目录命令",
                    "os": ["linux", "darwin", "windows"]
                },
                {
                    "pattern": "del",
                    "description": "删除文件命令",
                    "os": ["windows"]
                },
                {
                    "pattern": "format",
                    "description": "格式化磁盘命令",
                    "os": ["windows", "linux", "darwin"]
                },
                {
                    "pattern": "fdisk",
                    "description": "磁盘分区命令",
                    "os": ["linux", "darwin"]
                },
                {
                    "pattern": "mkfs",
                    "description": "创建文件系统命令",
                    "os": ["linux", "darwin"]
                },
                {
                    "pattern": ":(){",
                    "description": "fork炸弹",
                    "os": ["linux", "darwin"]
                },
                {
                    "pattern": "dd",
                    "description": "数据复制命令",
                    "os": ["linux", "darwin"]
                },
                {
                    "pattern": "chmod",
                    "description": "修改文件权限命令",
                    "os": ["linux", "darwin"]
                },
                {
                    "pattern": "chown",
                    "description": "修改文件所有者命令",
                    "os": ["linux", "darwin"]
                },
                {
                    "pattern": "sudo",
                    "description": "超级用户执行命令",
                    "os": ["linux", "darwin"]
                },
                {
                    "pattern": "diskpart",
                    "description": "磁盘分区工具",
                    "os": ["windows"]
                }
            ]
        }
        
        try:
            with open(self.security_config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            self.sensitive_commands = default_config["sensitive_commands"]
            print(f"已创建默认安全配置文件: {self.security_config_path}")
        except Exception as e:
            print(f"创建默认安全配置文件失败: {e}")
    
    def is_sensitive_command(self, command: str) -> Tuple[bool, str]:
        """检查命令是否为敏感命令
        
        Args:
            command: 要检查的命令
            
        Returns:
            (是否敏感, 敏感描述)
        """
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
                        # 特别危险的命令模式，如 rm -rf /
                        if (base_cmd == "rm" and "-rf" in cmd_parts and 
                            any(arg == "/" or arg == "*" for arg in cmd_parts)):
                            return True, "危险的递归删除命令"
                        
                        # 其他敏感模式
                        if (base_cmd == "dd" and 
                            any(arg.startswith("of=") for arg in cmd_parts)):
                            return True, "数据写入磁盘命令"
            
            return False, ""
            
        except Exception as e:
            print(f"检查敏感命令异常: {e}")
            # 出现异常时谨慎起见作为敏感命令处理
            return True, "命令检查异常，请谨慎执行"


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
        
        # 加载工具定义
        if os.path.exists(self.tools_path):
            try:
                with open(self.tools_path, 'r', encoding='utf-8') as f:
                    tool_definitions = json.load(f)
            except Exception as e:
                print(f"加载工具定义失败: {e}")
                tool_definitions = self.create_default_tools_json()
        else:
            tool_definitions = self.create_default_tools_json()
        
        # 逐个加载工具
        for tool_name, tool_info in tool_definitions.items():
            # 获取工具描述
            self.tool_descriptions[tool_name] = tool_info.get("description", "")
            
            # 获取工具实现路径
            implementation = tool_info.get("implementation", "")
            if not implementation:
                continue
            
            # 判断是内置工具还是自定义工具
            if implementation == "built-in":
                # 内置工具，从内置工具模块导入
                if tool_name == "read":
                    self.tools[tool_name] = self.read_file
                elif tool_name == "write":
                    self.tools[tool_name] = self.write_file
                elif tool_name == "execute":
                    self.tools[tool_name] = self.execute_command
                elif tool_name == "info":
                    self.tools[tool_name] = self.show_info
                elif tool_name == "interact":
                    self.tools[tool_name] = self.interact_with_user
                elif tool_name == "exit":
                    self.tools[tool_name] = self.exit_program
            else:
                # 自定义工具，从指定路径导入
                full_path = os.path.join(self.tools_dir, implementation)
                try:
                    self.load_custom_tool(tool_name, full_path)
                except Exception as e:
                    print(f"加载自定义工具 {tool_name} 失败: {e}")
    
    def create_default_tools_json(self) -> Dict:
        """创建默认工具定义文件"""
        default_tools = {
            "read": {
                "description": "读取文件内容",
                "implementation": "built-in",
                "args": {
                    "file_path": "要读取的文件路径"
                }
            },
            "write": {
                "description": "写入文件内容",
                "implementation": "built-in",
                "args": {
                    "file_path": "要写入的文件路径",
                    "content": "要写入的内容",
                    "mode": "写入模式：w(覆盖)或a(追加)"
                }
            },
            "execute": {
                "description": "执行系统命令",
                "implementation": "built-in",
                "args": {
                    "command": "要执行的命令"
                }
            },
            "info": {
                "description": "向用户显示重要信息",
                "implementation": "built-in",
                "args": {
                    "content": "要显示的信息内容"
                }
            },
            "interact": {
                "description": "与用户交互并获取输入",
                "implementation": "built-in", 
                "args": {
                    "content": "要向用户展示的内容",
                    "prompt": "可选的输入提示"
                }
            },
            "exit": {
                "description": "结束当前任务",
                "implementation": "built-in",
                "args": {
                    "message": "可选的结束消息"
                }
            }
        }
        
        # 保存默认工具定义
        try:
            with open(self.tools_path, 'w', encoding='utf-8') as f:
                json.dump(default_tools, f, indent=2)
            print(f"已创建默认工具定义文件: {self.tools_path}")
        except Exception as e:
            print(f"创建默认工具定义文件失败: {e}")
        
        return default_tools
    
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
    
    # 内置工具实现
    @staticmethod
    def read_file(file_path: str) -> Dict:
        """读取文件内容"""
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "result": f"文件不存在: {file_path}"
                }
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return {
                "success": True,
                "result": content
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"读取文件失败: {str(e)}"
            }
    
    @staticmethod
    def write_file(file_path: str, content: str, mode: str = "w") -> Dict:
        """写入文件内容"""
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "result": f"文件{'追加' if mode == 'a' else '写入'}成功: {file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"写入文件失败: {str(e)}"
            }
    
    def execute_command(self, command: str) -> Dict:
        """执行系统命令，带有敏感命令确认"""
        import subprocess
        
        try:
            # 检查是否为敏感命令
            is_sensitive, description = self.security_manager.is_sensitive_command(command)
            
            if is_sensitive:
                # 显示警告并请求确认
                print("\n[⚠️ 安全警告]")
                print("=" * 60)
                print(f"检测到敏感命令: {command}")
                print(f"描述: {description}")
                print("=" * 60)
                
                confirmation = input("\n此命令可能有风险，是否确认执行? (y/N): ").strip().lower()
                
                if confirmation != 'y':
                    return {
                        "success": False,
                        "result": "用户取消了敏感命令的执行"
                    }
                
                print("用户已确认执行敏感命令。\n")
            
            # 使用subprocess执行命令并捕获输出，修复编码问题
            process = subprocess.Popen(
                command, 
                shell=True,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=False  # 使用二进制模式避免编码问题
            )
            
            # 读取二进制输出并尝试多种编码
            stdout_binary, stderr_binary = process.communicate()
            
            # 尝试不同的编码来解码输出
            encodings = ['utf-8', 'latin1', 'gbk', 'cp1252']
            stdout = None
            stderr = None
            
            for encoding in encodings:
                try:
                    if stdout is None and stdout_binary:
                        stdout = stdout_binary.decode(encoding, errors='replace')
                    if stderr is None and stderr_binary:
                        stderr = stderr_binary.decode(encoding, errors='replace')
                    if stdout is not None and stderr is not None:
                        break
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都尝试失败，使用latin1（它可以解码任何字节序列）
            if stdout is None and stdout_binary:
                stdout = stdout_binary.decode('latin1', errors='replace')
            if stderr is None and stderr_binary:
                stderr = stderr_binary.decode('latin1', errors='replace')
            
            if not stdout:
                stdout = ""
            if not stderr:
                stderr = ""
                
            if process.returncode != 0:
                if stderr:
                    output = f"命令执行错误 (返回码: {process.returncode}):\n{stderr}\n{stdout}"
                else:
                    output = f"命令执行错误 (返回码: {process.returncode}):\n{stdout}"
                success = False
            else:
                output = stdout
                success = True
                
            return {
                "success": success,
                "result": output
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"执行命令失败: {str(e)}"
            }
    
    @staticmethod
    def show_info(content: str) -> Dict:
        """向用户显示重要信息"""
        try:
            print("\n[信息]")
            print("-" * 50)
            print(content)
            print("-" * 50)
            
            return {
                "success": True,
                "result": f"已显示信息: {content[:30]}..." if len(content) > 30 else content
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"显示信息失败: {str(e)}"
            }
    
    @staticmethod
    def interact_with_user(content: str, prompt: str = "请输入您的回复: ") -> Dict:
        """与用户交互并获取输入"""
        try:
            print("\n[交互]")
            print("=" * 50)
            print(content)
            print("=" * 50)
            
            user_input = input(f"\n{prompt}").strip()
            
            return {
                "success": True,
                "result": f"用户回复: {user_input}",
                "user_input": user_input
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"交互失败: {str(e)}"
            }
    
    @staticmethod
    def exit_program(message: str = "任务已完成") -> Dict:
        """结束当前任务"""
        try:
            print("\n[退出]")
            print("=" * 50)
            print(message)
            print("=" * 50)
            
            return {
                "success": True,
                "result": "程序执行结束",
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
            result_text = result["result"]
            if len(result_text) > 4000:
                result_text = result_text[:4000] + f"\n... [内容已截断，共 {len(result['result'])} 字符]"
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
        total_tokens = sum(len(msg["content"]) for msg in self.messages) // 4  # 粗略估计
        
        # 如果超过最大令牌数，删除最早的消息，但保留系统消息
        while total_tokens > self.max_tokens and len(self.messages) > 2:  # 保留至少system和最新user
            # 找到第一个非系统消息删除
            for i, msg in enumerate(self.messages):
                if msg["role"] != "system":
                    self.messages.pop(i)
                    # 重新计算令牌数
                    total_tokens = sum(len(msg["content"]) for msg in self.messages) // 4
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
        self.base_url = config.get("base_url")
        self.api_key = config.get("api_key")
        self.model_name = config.get("model_name")
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
                print(f"\n向模型发送请求{' (重试中: ' + str(retries) + '/' + str(self.max_retries) + ')' if retries > 0 else ''}...")
                
                # 使用requests发送请求
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    # 请求成功
                    return response.json()
                else:
                    # 某些错误可能需要重试
                    if 500 <= response.status_code < 600:  # 服务器错误
                        retries += 1
                        if retries <= self.max_retries:
                            print(f"API请求返回错误状态码: {response.status_code}，将在{self.retry_delay}秒后重试...")
                            time.sleep(self.retry_delay)
                            continue
                    
                    # 其他错误直接返回，不重试
                    print(f"API请求失败: {response.status_code}")
                    error_text = response.text
                    try:
                        error_json = response.json()
                        error_text = json.dumps(error_json, ensure_ascii=False)
                    except:
                        pass
                    print(error_text)
                    return {"error": f"API请求失败: {response.status_code}", "details": error_text}
                    
            except requests.exceptions.Timeout:
                # 超时错误，尝试重试
                retries += 1
                if retries <= self.max_retries:
                    print(f"API请求超时，将在{self.retry_delay}秒后重试 ({retries}/{self.max_retries})...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"API请求在{self.max_retries}次重试后仍然超时")
                    return {"error": "API请求多次超时，请检查网络连接或稍后再试"}
            
            except requests.exceptions.ConnectionError:
                # 连接错误，尝试重试
                retries += 1
                if retries <= self.max_retries:
                    print(f"API连接错误，将在{self.retry_delay}秒后重试 ({retries}/{self.max_retries})...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"API连接在{self.max_retries}次重试后仍然失败")
                    return {"error": "API连接多次失败，请检查网络连接或API服务是否可用"}
                
            except Exception as e:
                # 其他异常
                print(f"API请求异常: {e}")
                retries += 1
                if retries <= self.max_retries:
                    print(f"将在{self.retry_delay}秒后重试 ({retries}/{self.max_retries})...")
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
                print(f"模型响应错误: {response['error']}")
                return {"type": "error", "message": response.get("error")}
            
            # 获取实际内容
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 打印原始响应(调试用)
            # print(f"\n原始响应:\n{content}\n")
            
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
                    print(f"JSON解析失败: {e}")
            
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
                    
                    # 处理不同工具的参数提取逻辑
                    if tool_name == "read":
                        file_path_match = re.search(r'[\'"]([^\'"]+)[\'"]|文件\s*[:：]?\s*([^\s,]+)|路径\s*[:：]?\s*([^\s,]+)', rest_of_content)
                        if file_path_match:
                            # 选择第一个非None的组作为文件路径
                            file_path = next((g for g in file_path_match.groups() if g), "")
                            return {
                                "name": tool_name,
                                "args": {"file_path": file_path}
                            }
                    
                    elif tool_name == "write":
                        file_path_match = re.search(r'(?:文件|路径)\s*[:：]?\s*[\'"]?([^\'"]+)[\'"]?', rest_of_content)
                        content_match = re.search(r'(?:内容)\s*[:：]?\s*[\'"]([^\'"]+)[\'"]', rest_of_content)
                        mode_match = re.search(r'(?:模式)\s*[:：]?\s*[\'"]?([wa])[\'"]?', rest_of_content)
                        
                        if file_path_match:
                            args = {"file_path": file_path_match.group(1)}
                            if content_match:
                                args["content"] = content_match.group(1)
                            if mode_match:
                                args["mode"] = mode_match.group(1)
                            else:
                                args["mode"] = "w"  # 默认为覆盖模式
                            
                            return {
                                "name": tool_name,
                                "args": args
                            }
                    
                    elif tool_name == "execute":
                        command_match = re.search(r'(?:命令)\s*[:：]?\s*[\'"]?([^\'"]+)[\'"]?', rest_of_content)
                        if command_match:
                            return {
                                "name": tool_name,
                                "args": {"command": command_match.group(1)}
                            }
                        # 如果整个内容就是命令
                        elif rest_of_content:
                            return {
                                "name": tool_name,
                                "args": {"command": rest_of_content}
                            }
                    
                    elif tool_name in ["info", "exit"]:
                        # 这些工具主要参数是文本内容
                        content_match = re.search(r'(?:内容|消息)\s*[:：]?\s*[\'"]([^\'"]+)[\'"]', rest_of_content)
                        if content_match:
                            args = {"content" if tool_name == "info" else "message": content_match.group(1)}
                        else:
                            # 如果没有引号括起来，就用整个剩余内容
                            args = {"content" if tool_name == "info" else "message": rest_of_content}
                        
                        return {
                            "name": tool_name,
                            "args": args
                        }
                    
                    elif tool_name == "interact":
                        content_match = re.search(r'(?:内容)\s*[:：]?\s*[\'"]([^\'"]+)[\'"]', rest_of_content)
                        prompt_match = re.search(r'(?:提示)\s*[:：]?\s*[\'"]([^\'"]+)[\'"]', rest_of_content)
                        
                        args = {}
                        if content_match:
                            args["content"] = content_match.group(1)
                        else:
                            # 如果没有明确标识，整个内容作为content
                            args["content"] = rest_of_content
                        
                        if prompt_match:
                            args["prompt"] = prompt_match.group(1)
                        
                        return {
                            "name": tool_name,
                            "args": args
                        }
            
            # 3. 最后，尝试根据内容猜测最可能的工具
            
            # 3.1 内容包含"退出"、"结束"等关键词
            if re.search(r'退出|结束|完成|exit|quit', content, re.IGNORECASE):
                return {
                    "name": "exit",
                    "args": {"message": "任务已完成"}
                }
            
            # 3.2 内容看起来像是提供信息
            if len(content.strip().split()) > 3 and not re.search(r'文件|命令|读取|写入|执行', content, re.IGNORECASE):
                return {
                    "name": "info",
                    "args": {"content": content.strip()}
                }
            
            # 如果无法识别为任何工具调用，返回错误
            print(f"无法解析模型响应为工具调用:\n{content}")
            return {"type": "error", "message": "无法解析响应为工具调用", "content": content}
            
        except Exception as e:
            print(f"解析模型响应异常: {e}")
            print(f"异常详情: {str(e)}")
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
            tools_info = "欢迎使用Axiom Agent智能助手!\n\n【工具使用指南】\n你有以下工具可用，请按需选择最合适的工具:\n\n"
            
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
                    if tool_name == "read":  
                        tools_info += '    "file_path": "要读取的文件路径"\n'  
                    elif tool_name == "write":  
                        tools_info += '    "file_path": "要写入的文件路径",\n'  
                        tools_info += '    "content": "要写入的内容",\n'  
                        tools_info += '    "mode": "w或a"\n'  
                    elif tool_name == "execute":  
                        tools_info += '    "command": "要执行的命令"\n'  
                    elif tool_name == "info":  
                        tools_info += '    "content": "要显示的信息内容"\n'  
                    elif tool_name == "interact":  
                        tools_info += '    "content": "交互内容",\n'  
                        tools_info += '    "prompt": "可选的输入提示"\n'  
                    elif tool_name == "exit":  
                        tools_info += '    "message": "可选的结束消息"\n'  
                
                tools_info += "  }\n}\n```\n\n"
            
            tools_info += """
【任务执行流程】
1. 收到新任务时，首先分析任务性质:
   - 如果是复杂任务：先用info工具提供整体计划
   - 如果是简单任务：直接使用相应工具执行

2. 使用info工具后:
   - 必须立即使用其他工具(read/write/execute)执行实际操作
   - 不要连续使用info工具

3. 执行步骤:
   - 使用read/write/execute等工具执行具体操作
   - 使用info工具提供阶段性进展
   - 使用interact工具在需要用户输入时与用户交互
   - 使用exit工具结束任务

4. 安全考虑:
   - 执行危险命令(如rm、del、format等)时系统会要求用户确认
   - 确保解释清楚命令的目的和可能的影响
   - 在执行修改系统状态的命令前先做好检查和备份

【注意事项】
- 避免重复使用info工具，提供信息后立即执行
- 每次只返回一个工具调用，不要添加额外说明
- 大文件内容会自动截断，请提取关键信息处理
- 保持回答简洁，聚焦于任务目标
- 任务完成时务必使用exit工具结束任务
"""
            
            return f"系统信息: {json.dumps(system_info, ensure_ascii=False)}\n{tools_info}"
        except Exception as e:
            print(f"获取系统信息失败: {e}")
            return "无法获取完整系统信息。"
    
    def run(self):
        """运行AI Agent"""
        print("Axiom Agent智能助手已启动，请输入您的要求:")
        
        # 获取系统提示并添加到对话
        system_prompt = self.get_system_prompt()
        self.dialogue_manager.add_system_message(system_prompt)
        
        # 获取用户第一个指令
        user_request = input("> ").strip()
        self.dialogue_manager.add_user_message(user_request)
        
        while True:
            # 检查是否要退出
            if user_request.lower() == "bye":
                print("\n感谢使用Axiom Agent智能助手，再见!")
                break
                
            # 获取当前对话历史并发送请求
            messages = self.dialogue_manager.get_messages()
            response = self.model_communicator.send_request(messages)
            
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
            
            # 如果是EOF，显示信息并继续（为了向后兼容）
            if parsed_response == "EOF":
                print("\n注意: 收到EOF标记，但应使用exit工具结束任务。")
                user_request = "请使用exit工具结束任务。"
                self.dialogue_manager.add_user_message(user_request)
                continue
            
            # 如果是错误，显示错误并继续
            if isinstance(parsed_response, dict) and parsed_response.get("type") == "error":
                print(f"\n错误: {parsed_response.get('message')}")
                
                # 如果有原始内容，显示
                if "content" in parsed_response:
                    print(f"\n模型原始响应:\n{parsed_response.get('content')}")
                
                user_request = input("\n请提供新的指令或输入'bye'退出: ").strip()
                # 如果用户输入bye，视为退出
                if user_request.lower() == "bye":
                    print("\n感谢使用Axiom Agent智能助手，再见!")
                    break
                
                self.dialogue_manager.add_user_message(user_request)
                continue
            
            # 防止连续使用info工具
            if parsed_response.get("name") == "info" and self.dialogue_manager.was_last_tool_info():
                print("\n警告: 检测到连续使用info工具。请改用其他工具执行具体操作。")
                user_request = "请使用read、write或execute等工具执行具体操作，而非继续提供信息。"
                self.dialogue_manager.add_user_message(user_request)
                continue
            
            # 处理工具调用
            tool_call = parsed_response
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            
            # 获取工具函数
            tool_function = self.tool_manager.get_tool_function(tool_name)
            
            if tool_function is None:
                print(f"\n未知工具: {tool_name}")
                result = {
                    "success": False,
                    "result": f"未知工具: {tool_name}"
                }
            else:
                print(f"\n执行工具: {tool_name}")
                # 调用工具函数并传递参数
                result = tool_function(**tool_args)
            
            # 检查是否是exit工具且执行成功
            if tool_name == "exit" and result.get("success") and result.get("exit", False):
                print("\n感谢使用Axiom Agent智能助手，再见!")
                break
            
            # 检查是否是interact工具，获取用户输入
            if tool_name == "interact" and "user_input" in result:
                user_input = result["user_input"]
                # 如果用户输入bye，视为退出
                if user_input.lower() == "bye":
                    print("\n感谢使用Axiom Agent智能助手，再见!")
                    break
            
            # 打印工具执行结果
            if tool_name not in ["info", "interact", "exit"]:  # 这些工具已经打印了结果
                if result.get("result") is not None:
                    result_preview = result['result']
                    if len(result_preview) > 100:
                        result_preview = result_preview[:100] + "..."
                    print(f"结果 (成功: {result['success']}): {result_preview}")
                else:
                    print(f"结果 (成功: {result['success']}): 无内容")
            
            # 添加工具结果到对话历史
            self.dialogue_manager.add_tool_result(tool_call, result)
            
            # 准备下一轮请求
            user_request = "继续执行任务"
            self.dialogue_manager.add_user_message(user_request)


if __name__ == "__main__":
    agent = AIAgent()
    agent.run()
