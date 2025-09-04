#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的服务器连接测试
"""

import requests
import time
import sys

def test_server_connection():
    """测试服务器连接状态"""
    print("🔍 测试服务器连接状态...")
    
    # 测试健康检查端点
    try:
        response = requests.get('http://localhost:8001/health', timeout=5)
        print(f"✅ 健康检查响应: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False
    
    # 测试流式端点是否存在
    try:
        # 发送一个简单的POST请求到流式端点
        test_data = {
            "query": "测试查询",
            "session_id": "test_session"
        }
        response = requests.post(
            'http://localhost:8001/mcp/streaming/orchestrator',
            json=test_data,
            timeout=10,
            stream=True
        )
        print(f"✅ 流式端点响应: {response.status_code}")
        
        # 读取前几行响应
        lines_read = 0
        for line in response.iter_lines(decode_unicode=True):
            if line:
                print(f"📡 流式响应: {line}")
                lines_read += 1
                if lines_read >= 3:  # 只读取前3行
                    break
        
        return True
        
    except Exception as e:
        print(f"❌ 流式端点测试失败: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🧪 服务器连接测试")
    print("="*60)
    
    success = test_server_connection()
    
    if success:
        print("\n✅ 服务器连接测试通过")
        sys.exit(0)
    else:
        print("\n❌ 服务器连接测试失败")
        sys.exit(1)