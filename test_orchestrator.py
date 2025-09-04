#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试orchestrator的智能任务分派功能
"""

import requests
import json
import time

def test_single_mcp_call():
    """测试单个MCP工具调用（如analysis）"""
    print("\n=== 测试单个MCP工具调用 ===")
    
    # 测试analysis任务
    test_data = {
        "task": "分析一下人工智能在医疗领域的应用现状",
        "task_type": "auto",
        "kwargs": {}
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/mcp/streaming/orchestrator",
            json=test_data,
            stream=True,
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("\n流式响应内容:")
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if 'params' in data and 'data' in data['params']:
                            msg_data = data['params']['data']
                            if 'msg' in msg_data:
                                msg = msg_data['msg']
                                print(f"状态: {msg.get('status', 'unknown')}")
                                print(f"消息: {msg.get('message', '')}")
                                if 'details' in msg:
                                    print(f"详情: {msg['details']}")
                                print("---")
                    except json.JSONDecodeError:
                        print(f"无法解析JSON: {line}")
        else:
            print(f"请求失败: {response.text}")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")

def test_full_report_generation():
    """测试完整报告生成"""
    print("\n=== 测试完整报告生成 ===")
    
    test_data = {
        "task": "生成一份关于人工智能在医疗领域应用的详细报告，包括现状分析、技术趋势、挑战和未来展望",
        "task_type": "auto",
        "kwargs": {}
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/mcp/streaming/orchestrator",
            json=test_data,
            stream=True,
            timeout=60
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("\n流式响应内容:")
            step_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if 'params' in data and 'data' in data['params']:
                            msg_data = data['params']['data']
                            if 'msg' in msg_data:
                                msg = msg_data['msg']
                                status = msg.get('status', 'unknown')
                                message = msg.get('message', '')
                                
                                if 'step' in msg.get('details', {}):
                                    step_count += 1
                                    print(f"步骤 {step_count}: {status} - {message}")
                                else:
                                    print(f"状态: {status} - {message}")
                                    
                                if status == 'completed':
                                    print("\n报告生成完成!")
                                    break
                                    
                    except json.JSONDecodeError:
                        continue
        else:
            print(f"请求失败: {response.text}")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")

def test_search_task():
    """测试搜索任务"""
    print("\n=== 测试搜索任务 ===")
    
    test_data = {
        "task": "搜索人工智能最新发展动态",
        "task_type": "auto",
        "kwargs": {}
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/mcp/streaming/orchestrator",
            json=test_data,
            stream=True,
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("\n流式响应内容:")
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if 'params' in data and 'data' in data['params']:
                            msg_data = data['params']['data']
                            if 'msg' in msg_data:
                                msg = msg_data['msg']
                                print(f"状态: {msg.get('status', 'unknown')}")
                                print(f"消息: {msg.get('message', '')}")
                                if msg.get('status') == 'completed':
                                    break
                    except json.JSONDecodeError:
                        continue
        else:
            print(f"请求失败: {response.text}")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    print("开始测试orchestrator智能任务分派功能...")
    
    # 等待服务器完全启动
    print("等待服务器启动...")
    time.sleep(2)
    
    # 测试单个MCP工具调用
    test_single_mcp_call()
    
    # 等待一段时间
    time.sleep(3)
    
    # 测试搜索任务
    test_search_task()
    
    # 等待一段时间
    time.sleep(3)
    
    # 测试完整报告生成（注释掉以节省时间）
    # test_full_report_generation()
    
    print("\n测试完成!")