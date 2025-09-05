#!/usr/bin/env python3
"""
简化的MCP工具调用测试
只测试一个工具调用，避免长时间运行和错误
"""

import json
import asyncio
import aiohttp
import time

async def test_simple_tool_call():
    """测试简单的工具调用"""
    base_url = "http://localhost:8001"
    
    # 简单的搜索请求
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search",
            "arguments": {
                "query": "人工智能",
                "max_results": 3
            }
        }
    }
    
    print("🧪 简单MCP工具调用测试")
    print("=" * 50)
    print(f"🚀 发送请求: {request_data['params']['name']}")
    print(f"📋 请求ID: {request_data['id']}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=60)  # 1分钟超时
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{base_url}/mcp/tools/call",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    print(f"❌ HTTP错误: {response.status}")
                    return
                
                print(f"✅ 请求成功，状态码: {response.status}")
                
                # 处理SSE流式响应
                message_count = 0
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # 去掉 'data: ' 前缀
                            message_count += 1
                            
                            if 'method' in data and data['method'] == 'notifications/message':
                                # 进度更新消息
                                msg_data = data['params']['data']['msg']
                                print(f"📊 进度更新: [{msg_data.get('status', 'unknown')}] {msg_data.get('message', '')}")
                                
                            elif 'result' in data:
                                # 最终结果
                                result = data['result']
                                content = result.get('content', '')
                                print(f"✅ 最终结果: {content[:200]}..." if len(content) > 200 else f"✅ 最终结果: {content}")
                                
                            elif 'error' in data:
                                # 错误信息
                                error = data['error']
                                print(f"❌ 错误: {error.get('message', 'Unknown error')}")
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON解析错误: {e}")
                            continue
                
                print(f"✅ 测试完成，共收到 {message_count} 条消息")
                
    except asyncio.TimeoutError:
        print("⏰ 请求超时")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_simple_tool_call())

