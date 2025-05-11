"""
命令执行工具: 执行系统命令，具有敏感命令确认功能
"""

import subprocess
import platform
import os
import shlex
import json
import uuid

def is_sensitive_command(command: str) -> tuple:
    """检查命令是否为敏感命令
    
    Args:
        command: 要检查的命令
        
    Returns:
        (是否敏感, 敏感描述)
    """
    # 加载敏感命令配置
    if os.path.exists("security.json"):
        try:
            with open("security.json", 'r', encoding='utf-8') as f:
                security_config = json.load(f)
                sensitive_commands = security_config.get("sensitive_commands", [])
        except Exception:
            sensitive_commands = []
    else:
        sensitive_commands = []
    
    if not sensitive_commands:
        return False, ""
        
    current_os = platform.system().lower()
    # 解析命令获取第一个部分（命令名）
    try:
        cmd_parts = shlex.split(command)
        if not cmd_parts:
            return False, ""
        
        base_cmd = cmd_parts[0].lower()
        
        # 检查是否为定义的敏感命令
        for sensitive_cmd in sensitive_commands:
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

def execute(command: str) -> dict:
    """执行系统命令
    
    Args:
        command: 要执行的命令
        
    Returns:
        包含成功状态和结果的字典
    """
    try:
        # 检查是否为敏感命令
        is_sensitive, description = is_sensitive_command(command)
        
        if is_sensitive:
            # 在API版本中，无法直接请求用户确认，返回需要确认的结果
            # 该命令将不会被执行，直到用户确认
            return {
                "success": False,
                "result": f"检测到敏感命令: {command}\n描述: {description}\n请谨慎执行此命令，它可能会导致不可恢复的变更。",
                "sensitive_command": True,
                "needs_confirmation": True,
                "description": description
            }
        
        # 使用subprocess执行命令并捕获输出
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