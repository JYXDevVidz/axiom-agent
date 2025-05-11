"""
用户交互工具: 与用户交互并获取输入，API版只返回交互请求，不直接获取输入
"""

def execute(content: str, prompt: str = "请输入您的回复: ") -> dict:
    """与用户交互并获取输入
    
    Args:
        content: 要向用户展示的内容
        prompt: 输入提示
        
    Returns:
        包含成功状态、结果和交互请求的字典
    """
    try:
        # API版本只返回交互请求，不直接获取输入
        # 实际输入的获取由API服务的后续请求处理
        return {
            "success": True,
            "result": "需要用户交互",
            "content": content,
            "prompt": prompt,
            "awaiting_user_input": True
        }
    except Exception as e:
        return {
            "success": False,
            "result": f"创建交互请求失败: {str(e)}"
        }