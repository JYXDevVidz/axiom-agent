"""
文件读取工具: 读取文件内容
"""

import os

def execute(file_path: str) -> dict:
    """读取文件内容
    
    Args:
        file_path: 要读取的文件路径
        
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