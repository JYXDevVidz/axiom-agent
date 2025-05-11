"""
计算工具：一个示例的自定义工具，用于计算Python表达式的值
支持标准的Python数学表达式和函数
"""
import math
import ast
import operator as op

def safe_eval(expr):
    """
    安全地评估数学表达式
    使用ast模块解析表达式，只允许安全操作
    """
    # 定义允许的操作符
    operators = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
        ast.USub: op.neg, ast.UAdd: op.pos,
        ast.FloorDiv: op.floordiv, ast.Mod: op.mod
    }
    
    # 定义允许的函数和常量
    safe_names = {
        'abs': abs, 'round': round,
        'min': min, 'max': max,
        'sum': sum, 'len': len,
        # 数学函数
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
        'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10,
        'exp': math.exp, 'ceil': math.ceil, 'floor': math.floor,
        # 常量
        'pi': math.pi, 'e': math.e
    }
    
    def _eval(node):
        # 数字常量
        if isinstance(node, ast.Num):
            return node.n
        # 一元操作符 (比如 -1)
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](_eval(node.operand))
        # 二元操作符 (比如 1 + 2)
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        # 函数调用 (比如 sin(0.5))
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name not in safe_names:
                raise ValueError(f"函数 '{func_name}' 不在安全函数列表中")
            args = [_eval(arg) for arg in node.args]
            return safe_names[func_name](*args)
        # 访问允许的变量/常量 (比如 pi)
        elif isinstance(node, ast.Name):
            if node.id not in safe_names:
                raise ValueError(f"变量 '{node.id}' 不在安全变量列表中")
            return safe_names[node.id]
        # 元组支持 (比如 min(1, 2, 3))
        elif isinstance(node, ast.Tuple) or isinstance(node, ast.List):
            return tuple(_eval(el) for el in node.elts)
        else:
            raise TypeError(f"不支持的表达式类型: {type(node)}")
    
    try:
        parsed_expr = ast.parse(expr, mode='eval').body
        return _eval(parsed_expr)
    except Exception as e:
        raise ValueError(f"表达式计算失败: {str(e)}")

def execute(expression):
    """
    计算Python表达式的值
    
    Args:
        expression: 要计算的表达式
            
    Returns:
        包含成功状态和结果的字典
    """
    try:
        # 尝试安全地计算表达式
        result = safe_eval(expression)
        
        return {
            "success": True,
            "result": f"计算结果: {result}"
        }
    except Exception as e:
        return {
            "success": False,
            "result": f"计算失败: {str(e)}"
        }
