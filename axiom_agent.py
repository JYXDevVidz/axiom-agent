
import os
import json
import subprocess
import sys
import platform
import psutil
import requests
from typing import Dict, List, Union, Optional, Tuple
import re
import time

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
            "timeout": 90               # 请求超时时间(秒)
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


class ToolHandler:
    """工具处理器：执行读取、写入和命令执行操作"""
    
    @staticmethod
    def reader(file_path: str) -> Dict:
        """读取文件内容
        
        Args:
            file_path: 需要读取的文件路径
            
        Returns:
            包含成功状态和结果的字典
        """
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
    def writer(file_path: str, content: str, mode: str = "w") -> Dict:
        """写入文件内容
        
        Args:
            file_path: 目标文件路径
            content: 要写入的内容
            mode: 写入模式，'w'覆盖，'a'追加
            
        Returns:
            包含成功状态和结果的字典
        """
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
    
    @staticmethod
    def execute_command(command: str) -> Dict:
        """执行系统命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            包含成功状态和结果的字典
        """
        try:
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
    def answer(content: str) -> Dict:
        """提供答案（不终止程序）
        
        Args:
            content: 答案内容
            
        Returns:
            包含成功状态和结果的字典
        """
        try:
            print("\n[最终答案]")
            print("=" * 50)
            print(content)
            print("=" * 50)
            
            return {
                "success": True,
                "result": f"已显示答案: {content[:30]}..." if len(content) > 30 else content
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"显示答案失败: {str(e)}"
            }
    
    @staticmethod
    def comment(content: str) -> Dict:
        """记录注释内容，用于项目规划和执行进度跟踪
        
        Args:
            content: 注释内容
            
        Returns:
            包含成功状态和结果的字典
        """
        try:
            print("\n[注释]")
            print("-" * 50)
            print(content)
            print("-" * 50)
            
            return {
                "success": True,
                "result": f"已记录注释: {content[:30]}..." if len(content) > 30 else content
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"记录注释失败: {str(e)}"
            }


class DialogueManager:
    """对话管理器: 管理与模型的对话历史"""
    
    def __init__(self, max_tokens: int = 16000):
        self.max_tokens = max_tokens
        self.messages = []  # 对话历史
        self.last_tool_was_comment = False  # 跟踪上一个工具是否为注释
    
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
        tool_type = tool_call.get("type")
        tool_args = tool_call.get("args", {})
        
        # 记录当前工具是否为注释
        self.last_tool_was_comment = (tool_type == "comment")
        
        # 构建工具结果消息
        if tool_type == "reader":
            message = f"工具调用结果 (读取文件 {tool_args.get('file_path', '')})\n"
        elif tool_type == "writer":
            message = f"工具调用结果 (写入文件 {tool_args.get('file_path', '')})\n"
        elif tool_type == "command":
            message = f"工具调用结果 (执行命令 {tool_args.get('command', '')})\n"
        elif tool_type == "comment":
            message = f"工具调用结果 (记录注释)\n"
        elif tool_type == "answer":
            message = f"工具调用结果 (提供答案)\n"
        else:
            message = f"工具调用结果 (未知工具)\n"
        
        message += f"成功: {result['success']}\n"
        
        if result.get("result") is not None:
            # 截断过长结果
            result_text = result["result"]
            if len(result_text) > 4000:
                result_text = result_text[:4000] + f"\n... [内容已截断，共 {len(result['result'])} 字符]"
            message += f"结果:\n{result_text}"
        else:
            message += "结果: 无内容"
        
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
    
    def was_last_tool_comment(self) -> bool:
        """检查上一个使用的工具是否为注释工具"""
        return self.last_tool_was_comment


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
    
    def parse_response(self, response: Dict) -> Union[str, Dict]:
        """解析模型响应
        
        Args:
            response: 模型响应
            
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
            
            # 尝试解析为工具调用
            # 1. 查找JSON代码块
            json_pattern = re.search(r'```(?:json|python)?\s*([\s\S]*?)```', content)
            if json_pattern:
                try:
                    # 提取JSON块内容
                    json_text = json_pattern.group(1)
                    
                    # 清理文本
                    json_text = re.sub(r'^(?:writer|reader|command|answer|comment)工具(?:调用)?', '', json_text, flags=re.MULTILINE).strip()
                    
                    # 尝试找到实际的JSON部分
                    json_obj_match = re.search(r'({[\s\S]*})', json_text)
                    if json_obj_match:
                        json_text = json_obj_match.group(1)
                    
                    # 处理多行JSON文本
                    lines = [line.strip() for line in json_text.split('\n')]
                    lines = [line for line in lines if line]
                    json_text = ' '.join(lines)
                    
                    # 尝试解析JSON
                    tool_json = json.loads(json_text)
                    
                    # 判断工具类型
                    if "type" in tool_json and "args" in tool_json:
                        # 标准格式
                        return tool_json
                    elif "file_path" in tool_json:
                        if "content" in tool_json:
                            # writer工具
                            return {
                                "type": "writer",
                                "args": {
                                    "file_path": tool_json.get("file_path", ""),
                                    "content": tool_json.get("content", ""),
                                    "mode": tool_json.get("mode", "w")
                                }
                            }
                        else:
                            # reader工具
                            return {
                                "type": "reader",
                                "args": {"file_path": tool_json.get("file_path", "")}
                            }
                    elif "command" in tool_json:
                        # command工具
                        return {
                            "type": "command",
                            "args": {"command": tool_json.get("command", "")}
                        }
                    elif "content" in tool_json and not "file_path" in tool_json:
                        # 区分answer和comment工具
                        if re.search(r'comment|注释|规划|计划|进度', json_text, re.IGNORECASE):
                            return {
                                "type": "comment",
                                "args": {"content": tool_json.get("content", "")}
                            }
                        else:
                            return {
                                "type": "answer",
                                "args": {"content": tool_json.get("content", "")}
                            }
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
            
            # 2. 查找关键词来判断工具类型
            if re.search(r'comment|注释|规划|计划|进度', content, re.IGNORECASE) and not re.search(r'answer|答案|结论|总结', content, re.IGNORECASE):
                # 如果内容包含注释相关关键词，判断为comment工具
                # 尝试提取内容
                comment_pattern = re.search(r'"content"\s*:\s*"([^"]*)"', content)
                if comment_pattern:
                    return {
                        "type": "comment",
                        "args": {"content": comment_pattern.group(1)}
                    }
                else:
                    # 可能整个内容就是注释
                    clean_content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
                    clean_content = re.sub(r'(?:comment|注释|规划|计划|进度)(?:\s*:|：)?', '', clean_content, flags=re.IGNORECASE).strip()
                    if clean_content:
                        return {
                            "type": "comment",
                            "args": {"content": clean_content}
                        }
            
            # 3. 其他工具调用模式
            # 3.1 尝试匹配command工具
            command_match = re.search(r'"command"\s*:\s*"([^"]+)"', content)
            if command_match:
                return {
                    "type": "command",
                    "args": {"command": command_match.group(1)}
                }
                
            # 3.2 尝试匹配writer工具
            file_path_match = re.search(r'"file_path"\s*:\s*"([^"]+)"', content)
            content_match = re.search(r'"content"\s*:\s*"([^"]*)"', content)
            
            if file_path_match and content_match:
                mode_match = re.search(r'"mode"\s*:\s*"([^"]+)"', content)
                return {
                    "type": "writer",
                    "args": {
                        "file_path": file_path_match.group(1),
                        "content": content_match.group(1),
                        "mode": mode_match.group(1) if mode_match else "w"
                    }
                }
            
            # 3.3 尝试匹配reader工具
            if file_path_match and not content_match:
                return {
                    "type": "reader",
                    "args": {"file_path": file_path_match.group(1)}
                }
            
            # 4. 检查是否是answer工具
            if "answer" in content.lower() or "最终答案" in content or "结论" in content:
                # 尝试提取答案内容
                answer_pattern = re.search(r'"content"\s*:\s*"([^"]*)"', content)
                if answer_pattern:
                    return {
                        "type": "answer",
                        "args": {"content": answer_pattern.group(1)}
                    }
                else:
                    # 可能整个内容就是答案
                    clean_content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
                    clean_content = re.sub(r'(?:answer|最终答案|结论)(?:\s*:|：)?', '', clean_content, flags=re.IGNORECASE).strip()
                    if clean_content:
                        return {
                            "type": "answer",
                            "args": {"content": clean_content}
                        }
            
            # 5. 如果内容看起来像一个直接的回答，使用answer工具
            if content.strip() and len(content.strip().split()) > 3:
                # 移除可能的代码块
                clean_content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
                if clean_content.strip():
                    return {
                        "type": "answer",
                        "args": {"content": clean_content.strip()}
                    }
            
            # 如果无法解析为工具调用或EOF，返回错误
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
        self.tool_handler = ToolHandler()
        self.dialogue_manager = DialogueManager()
        self.model_communicator = ModelCommunicator(self.config)
        
        # 添加大文件处理的配置
        self.max_content_size = 10 * 1024  # 10KB，超过则截断
    
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
            
            tools_info = """
你是Axiom Agent智能助手!

【工具使用指南】
你有以下工具可用，请按需选择最合适的工具:

1. reader工具: 读取文件内容
   何时使用: 需要获取文件内容时
   调用格式: 
   ```json
   {
     "type": "reader",
     "args": {
       "file_path": "要读取的文件路径"
     }
   }
   ```
   
2. writer工具: 写入文件内容
   何时使用: 需要创建或修改文件时
   调用格式:
   ```json
   {
     "type": "writer",
     "args": {
       "file_path": "要写入的文件路径",
       "content": "要写入的内容",
       "mode": "w或a"
     }
   }
   ```
   
3. command工具: 执行系统命令
   何时使用: 需要执行命令行操作时
   调用格式:
   ```json
   {
     "type": "command",
     "args": {
       "command": "要执行的命令"
     }
   }
   ```

4. comment工具: 记录项目规划和执行进度
   何时使用: 新任务开始时记录计划，或完成重要步骤后记录进度
   特别注意: 使用一次后，应立即转向执行工具，不要连续使用
   调用格式:
   ```json
   {
     "type": "comment",
     "args": {
       "content": "规划或进度说明"
     }
   }
   ```

5. answer工具: 提供答案并等待用户进一步指令
   何时使用: 任务阶段性完成需要反馈用户时
   调用格式:
   ```json
   {
     "type": "answer",
     "args": {
       "content": "答案内容"
     }
   }
   ```

【任务执行流程】
1. 收到新任务时，首先分析任务性质:
   - 如果是复杂任务：先用comment工具记录整体计划
   - 如果是简单任务：直接使用相应工具执行

2. 使用comment工具后:
   - 必须立即使用其他工具(reader/writer/command)执行实际操作
   - 不要连续使用comment工具

3. 执行步骤:
   - 使用reader/writer/command等工具执行具体操作
   - 操作完成后用answer工具提供反馈
   - 根据用户后续指令继续执行或结束任务

4. 会话结束:
   - 用户输入"bye"时，程序会终止

【注意事项】
- 避免重复使用comment工具，记录规划后立即执行
- 每次只返回一个工具调用，不要添加额外说明
- 大文件内容会自动截断，请提取关键信息处理
- 保持回答简洁，聚焦于任务目标
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
            
            # 解析响应
            parsed_response = self.model_communicator.parse_response(response)
            
            # 添加模型响应到对话历史
            if "choices" in response and len(response["choices"]) > 0:
                if "message" in response["choices"][0]:
                    content = response["choices"][0]["message"].get("content", "")
                    if content:
                        self.dialogue_manager.add_assistant_message(content)
            
            # 如果是EOF，显示信息并继续（为了向后兼容）
            if parsed_response == "EOF":
                print("\n注意: 收到EOF标记，但应使用answer工具提供总结。")
                user_request = "请使用answer工具提供总结。"
                self.dialogue_manager.add_user_message(user_request)
                continue
            
            # 如果是错误，显示错误并继续
            if isinstance(parsed_response, dict) and parsed_response.get("type") == "error":
                print(f"\n错误: {parsed_response.get('message')}")
                
                # 如果有原始内容，显示
                if "content" in parsed_response:
                    print(f"\n模型原始响应:\n{parsed_response.get('content')}")
                
                user_request = input("\n请提供新的指令或输入'bye'退出: ").strip()
                self.dialogue_manager.add_user_message(user_request)
                continue
            
            # 防止连续使用comment工具
            if parsed_response.get("type") == "comment" and self.dialogue_manager.was_last_tool_comment():
                print("\n警告: 检测到连续使用comment工具。请改用其他工具执行具体操作。")
                user_request = "请使用reader、writer或command等工具执行具体操作，而非继续规划。"
                self.dialogue_manager.add_user_message(user_request)
                continue
            
            # 处理工具调用
            tool_call = parsed_response
            tool_type = tool_call.get("type")
            
            if tool_type == "reader":
                file_path = tool_call.get("args", {}).get("file_path", "")
                print(f"\n执行读取操作: {file_path}")
                result = self.tool_handler.reader(file_path)
                
                # 处理超长内容
                if result["success"] and result["result"] is not None and len(result["result"]) > self.max_content_size:
                    print(f"文件内容过大 ({len(result['result'])} 字节)，将截断至 {self.max_content_size} 字节")
                    result["result_full"] = result["result"]  # 保存完整内容
                    result["result"] = result["result"][:self.max_content_size] + f"\n... [内容已截断，共 {len(result['result'])} 字节]"
            
            elif tool_type == "writer":
                args = tool_call.get("args", {})
                file_path = args.get("file_path", "")
                content = args.get("content", "")
                mode = args.get("mode", "w")
                print(f"\n执行写入操作: {file_path} (模式: {mode})")
                result = self.tool_handler.writer(file_path, content, mode)
            
            elif tool_type == "command":
                command = tool_call.get("args", {}).get("command", "")
                print(f"\n执行命令: {command}")
                result = self.tool_handler.execute_command(command)
                
                # 处理超长输出
                if result["success"] and result["result"] is not None and len(result["result"]) > self.max_content_size:
                    print(f"命令输出过大 ({len(result['result'])} 字节)，将截断至 {self.max_content_size} 字节")
                    result["result_full"] = result["result"]  # 保存完整内容
                    result["result"] = result["result"][:self.max_content_size] + f"\n... [内容已截断，共 {len(result['result'])} 字节]"
            
            elif tool_type == "comment":
                content = tool_call.get("args", {}).get("content", "")
                print(f"\n记录注释")
                result = self.tool_handler.comment(content)
            
            elif tool_type == "answer":
                content = tool_call.get("args", {}).get("content", "")
                print(f"\n提供答案")
                result = self.tool_handler.answer(content)
                # answer工具不再终止程序，而是等待用户下一步指令
                user_request = input("\n请输入下一步指令或'bye'退出: ").strip()
                # 添加工具结果和用户输入到对话历史
                self.dialogue_manager.add_tool_result(tool_call, result)
                self.dialogue_manager.add_user_message(user_request)
                continue
            
            else:
                print(f"\n未知工具类型: {tool_type}")
                result = {
                    "success": False,
                    "result": f"未知工具类型: {tool_type}"
                }
            
            # 打印工具执行结果
            if tool_type not in ["answer", "comment"]:  # 这些工具已经打印了结果
                if result["result"] is not None:
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
