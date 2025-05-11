"""
信息显示工具: 向用户显示重要信息，API版本只返回信息，不打印
"""

def execute(content: str) -> dict:
    """向用户显示重要信息
    
    Args:
        content: 要显示的信息内容
        
    Returns:
        包含成功状态和结果的字典
    """
    try:
        # API版本只返回信息，不打印到控制台
        return {
            "success": True,
            "result": content
        }
    except Exception as e:
        return {
            "success": False,
            "result": f"显示信息失败: {str(e)}"
        }