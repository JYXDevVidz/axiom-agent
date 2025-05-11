from flask import Flask, request, jsonify
import uuid
import os
import json
import time
from agent import AIAgent
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 会话存储
sessions = {}

# 交互等待状态
interaction_requests = {}

# 每个会话的"继续"标志
continuation_flags = {}

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    处理用户消息的API端点 - 每次只执行一个工具，但支持前端"继续"请求
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400
            
        # 获取会话ID (如果没有则创建新会话)
        session_id = data.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            sessions[session_id] = AIAgent()
            continuation_flags[session_id] = False
            
        # 获取用户消息
        message = data.get('message')
        if not message:
            return jsonify({"error": "消息不能为空"}), 400
        
        # 检查是否是"继续"请求
        continue_execution = data.get('continue', False)
            
        # 检查会话是否存在
        if session_id not in sessions:
            sessions[session_id] = AIAgent()
            continuation_flags[session_id] = False
            
        agent = sessions[session_id]
        
        # 处理互动完成的情况
        interaction_id = data.get('interaction_id')
        if interaction_id and interaction_id in interaction_requests:
            # 用户正在响应交互请求
            user_input = message
            interaction_requests[interaction_id]['user_input'] = user_input
            interaction_requests[interaction_id]['completed'] = True
            
            # 完成交互流程并继续处理
            result = agent.complete_interaction(interaction_id, user_input)
            # 设置此会话有后续操作
            continuation_flags[session_id] = True
            
            # 添加会话ID和继续标志到响应
            result['session_id'] = session_id
            result['has_continuation'] = True
            return jsonify(result)
        
        # 如果是继续执行请求，使用特殊消息
        if continue_execution and continuation_flags.get(session_id, False):
            # 这是前端请求继续执行的情况
            message = "继续执行任务"
            # 重置继续标志
            continuation_flags[session_id] = False
        else:
            # 新消息，重置继续标志
            continuation_flags[session_id] = False
        
        # 正常消息处理 - 只执行一个工具
        result = agent.process_message(message)
        
        # 如果结果是互动请求，保存状态
        if result.get('type') == 'interaction_required':
            interaction_id = result.get('interaction_id')
            interaction_requests[interaction_id] = {
                'session_id': session_id,
                'completed': False,
                'created_at': time.time()
            }
            # 设置此会话无后续操作（因为需要用户输入）
            continuation_flags[session_id] = False
        else:
            # 非交互工具，设置继续标志
            continuation_flags[session_id] = True
        
        # 添加会话ID和继续标志到响应
        result['session_id'] = session_id
        result['has_continuation'] = continuation_flags[session_id]
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"处理请求时发生错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/outputs", methods=["GET"])
def outputs():
    return '', 204  # 空响应，状态码204

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    删除会话的API端点
    """
    if session_id in sessions:
        del sessions[session_id]
        if session_id in continuation_flags:
            del continuation_flags[session_id]
        return jsonify({"success": True, "message": f"会话 {session_id} 已删除"})
    else:
        return jsonify({"error": "会话不存在"}), 404

# 清理过期的交互请求和会话
@app.before_request
def cleanup_expired_data():
    current_time = time.time()
    # 清理超过30分钟的交互请求
    expired_interactions = [
        interaction_id for interaction_id, data in interaction_requests.items()
        if current_time - data['created_at'] > 1800
    ]
    for interaction_id in expired_interactions:
        del interaction_requests[interaction_id]

@app.route("/status", methods=["GET"])
def status():
    return {"status": "ok"}, 200

if __name__ == '__main__':
    # 确保data目录存在
    os.makedirs('data', exist_ok=True)
    # 默认开发模式运行
    app.run(debug=True, host='0.0.0.0', port=5000)