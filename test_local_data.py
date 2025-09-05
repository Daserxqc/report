#!/usr/bin/env python3
"""
使用本地数据测试MCP工具，避免网络调用问题
"""

import asyncio
import aiohttp
import json

async def test_local_data():
    """测试使用本地数据的MCP工具调用"""
    
    # 使用本地数据，避免网络调用
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "generate_industry_dynamic_report",
            "arguments": {
                "industry": "新能源汽车",
                "time_range": "7天",
                "focus_areas": ["重大事件", "技术创新"],
                "max_results": 5,  # 减少结果数量
                "use_local_data": True  # 使用本地数据
            }
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/mcp/tools/call",
                json=request,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)  # 增加超时时间
            ) as response:
                print(f"📡 响应状态: {response.status}")
                
                if response.status == 200:
                    print("✅ 请求成功，开始接收流式响应...")
                    
                    message_count = 0
                    async for line in response.content:
                        if line:
                            message_count += 1
                            try:
                                # 解析SSE消息
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith('data: '):
                                    data_str = line_str[6:]  # 移除 'data: ' 前缀
                                    if data_str and data_str != '[DONE]':
                                        try:
                                            message = json.loads(data_str)
                                            print(f"📊 消息 {message_count}: [{message.get('type', 'unknown')}] {message.get('message', '')}")
                                        except json.JSONDecodeError:
                                            print(f"📊 消息 {message_count}: {data_str}")
                            except Exception as e:
                                print(f"⚠️ 解析消息失败: {e}")
                                continue
                    
                    print(f"✅ 测试完成，共接收 {message_count} 条消息")
                else:
                    print(f"❌ 请求失败: {response.status}")
                    error_content = await response.text()
                    print(f"错误内容: {error_content}")
                    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        print(f"详细错误信息:")
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 测试本地数据MCP工具")
    print("=" * 60)
    asyncio.run(test_local_data())
