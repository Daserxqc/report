#!/usr/bin/env python3
"""
调试流式推送问题
"""

import asyncio
import aiohttp
import json

async def test_streaming_debug():
    """测试流式推送并显示详细错误信息"""
    
    # 测试请求
    request_data = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "generate_industry_dynamic_report",
            "arguments": {
                "request": {
                    "industry": "新能源汽车",
                    "time_range": "recent",
                    "focus_areas": ["市场趋势", "技术创新", "政策影响", "竞争格局"],
                    "include_analysis": True,
                    "data_sources": ["news", "research", "market_data"]
                }
            }
        }
    }
    
    print("🧪 开始调试流式推送...")
    print(f"📋 请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
            async with session.post(
                "http://localhost:8001/mcp/tools/call",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"📡 响应状态: {response.status}")
                print(f"📡 响应头: {dict(response.headers)}")
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ HTTP错误: {error_text}")
                    return
                
                message_count = 0
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        message_count += 1
                        data_str = line_str[6:]  # 移除 'data: ' 前缀
                        try:
                            data = json.loads(data_str)
                            print(f"📨 消息 {message_count}: {data.get('method', 'unknown')}")
                            if 'error' in data:
                                print(f"❌ 错误: {data['error']}")
                            elif 'result' in data:
                                print(f"✅ 结果: {data['result'].get('content', '')[:100]}...")
                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON解析错误: {e}")
                            print(f"⚠️ 原始数据: {data_str[:200]}...")
                
                print(f"📊 总共收到 {message_count} 条消息")
                
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming_debug())

