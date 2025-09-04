#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试流式响应中的任务类型检测
"""

import requests
import json
import time

def test_streaming_debug():
    """测试流式响应并打印详细调试信息"""
    
    # 测试数据
    test_data = {
        "task": "生成AI Agent领域最近一周的行业重大事件报告",
        "task_type": "news_report",
        "kwargs": {}
    }
    
    print("🧪 调试流式响应中的任务类型检测")
    print("=" * 60)
    print(f"📋 任务: {test_data['task']}")
    print(f"📋 任务类型: {test_data['task_type']}")
    print("=" * 60)
    
    try:
        # 发送请求
        response = requests.post(
            "http://localhost:8001/mcp/streaming/orchestrator",
            json=test_data,
            stream=True,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            return
        
        print("✅ 连接成功，开始接收流式数据...\n")
        
        # 处理流式响应
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                    
                    # 打印所有消息的详细信息
                    if 'method' in data:
                        method = data['method']
                        params = data.get('params', {})
                        
                        print(f"📨 方法: {method}")
                        
                        if method == "notifications/message":
                            msg_data = params.get('data', {}).get('msg', {})
                            status = msg_data.get('status', '')
                            message = msg_data.get('message', '')
                            details = msg_data.get('details', {})
                            
                            print(f"   状态: {status}")
                            print(f"   消息: {message}")
                            
                            if details:
                                print(f"   详细信息:")
                                for key, value in details.items():
                                    print(f"     {key}: {value}")
                        
                        elif method == "session/started":
                            session_id = params.get('session_id', '')
                            print(f"   会话ID: {session_id}")
                        
                        elif method == "tools/result":
                            result_data = params.get('data', {})
                            print(f"   结果数据: {json.dumps(result_data, ensure_ascii=False, indent=2)}")
                        
                        print()
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析错误: {e}")
                    print(f"   原始数据: {line}")
                    
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

if __name__ == "__main__":
    # 检查服务器是否运行
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI服务器运行正常\n")
        else:
            print(f"⚠️ FastAPI服务器响应异常: {response.status_code}\n")
    except:
        print("❌ 无法连接到FastAPI服务器，请确保服务器正在运行\n")
        exit(1)
    
    test_streaming_debug()