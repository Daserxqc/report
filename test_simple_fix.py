#!/usr/bin/env python3
"""
简单测试修复方案
"""

import asyncio
import aiohttp
import json

async def test_simple_request():
    """测试简单的请求"""
    print("🧪 测试简单修复方案")
    print("=" * 60)
    
    # 简化的请求 - 使用本地数据避免网络调用
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "generate_industry_dynamic_report",
            "arguments": {
                "industry": "新能源汽车",
                "time_range": "recent",
                "days": 30,
                "focus_areas": ["市场趋势"],
                "include_analysis": True,
                "data_sources": ["news"],
                # "use_local_data": True  # 注释掉，使用真实网络搜索
            }
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/mcp/tools/call",
                json=request,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"📡 响应状态: {response.status}")
                
                if response.status == 200:
                    print("✅ 请求成功，开始接收流式响应...")
                    
                    message_count = 0
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                message_count += 1
                                
                                if 'method' in data and data['method'] == 'notifications/message':
                                    msg_data = data.get('params', {}).get('data', {}).get('msg', {})
                                    status = msg_data.get('status', 'unknown')
                                    message = msg_data.get('message', '')
                                    
                                    print(f"📊 消息 {message_count}: [{status}] {message}")
                                    
                                    # 如果看到重大事件分析完成，就停止
                                    if status == 'completed' and '重大事件' in message:
                                        print("🎉 重大事件分析完成！")
                                        break
                                        
                            except json.JSONDecodeError:
                                continue
                                
                    print(f"📊 总共收到 {message_count} 条消息")
                    
                else:
                    print(f"❌ 请求失败: {response.status}")
                    text = await response.text()
                    print(f"错误内容: {text}")
                    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        print(f"详细错误信息:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_request())

