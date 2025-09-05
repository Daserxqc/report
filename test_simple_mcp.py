#!/usr/bin/env python3
"""
简单的MCP服务器测试
"""

import asyncio
import aiohttp
import json

async def test_mcp_server():
    """测试MCP服务器"""
    base_url = "http://localhost:8000"
    
    # 测试不同的端点
    endpoints = [
        "/",
        "/mcp",
        "/tools",
        "/tools/call",
        "/api/tools/call"
    ]
    
    # 测试不同的请求格式
    test_requests = [
        # 标准MCP格式
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search",
                "arguments": {
                    "query": "test",
                    "max_results": 3
                }
            }
        },
        # 简化格式
        {
            "method": "search",
            "params": {
                "query": "test",
                "max_results": 3
            }
        },
        # 直接调用格式
        {
            "tool": "search",
            "query": "test",
            "max_results": 3
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            print(f"🔍 测试端点: {endpoint}")
            
            for i, test_request in enumerate(test_requests):
                try:
                    print(f"  格式 {i+1}: {list(test_request.keys())}")
                    
                    async with session.post(
                        f"{base_url}{endpoint}",
                        json=test_request,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        print(f"    状态码: {response.status}")
                        
                        if response.status == 200:
                            text = await response.text()
                            print(f"    ✅ 成功! 响应: {text[:200]}...")
                            break
                        elif response.status == 404:
                            print(f"    ❌ 端点不存在")
                        elif response.status == 406:
                            print(f"    ⚠️ 端点存在但请求格式不对")
                        else:
                            print(f"    ❓ 其他错误: {response.status}")
                            
                except Exception as e:
                    print(f"    ❌ 连接错误: {str(e)}")
            
            print()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
