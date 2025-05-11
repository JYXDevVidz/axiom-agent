"""
文件写入工具: 写入文件内容
"""

import os

def execute(file_path: str, content: str, mode: str = "w") -> dict:
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