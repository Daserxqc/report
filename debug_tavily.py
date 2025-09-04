#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import config

def test_tavily_api():
    """测试Tavily API连接和搜索功能"""
    print("=== Tavily API 调试测试 ===")
    
    # 检查API密钥
    api_key = config.TAVILY_API_KEY
    print(f"API密钥: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")
    
    if not api_key:
        print("❌ 未找到Tavily API密钥")
        return
    
    # 测试API连接
    base_url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "query": "人工智能",
        "search_depth": "basic",
        "include_answer": False,
        "include_images": False,
        "include_raw_content": False,
        "max_results": 3
    }
    
    try:
        print(f"正在测试API连接...")
        print(f"URL: {base_url}")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(base_url, headers=headers, json=payload, timeout=30)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ API调用成功!")
            print(f"结果数量: {len(result.get('results', []))}")
            
            for i, item in enumerate(result.get('results', [])[:2]):
                print(f"\n--- 结果 {i+1} ---")
                print(f"标题: {item.get('title', 'N/A')}")
                print(f"URL: {item.get('url', 'N/A')}")
                print(f"内容长度: {len(item.get('content', ''))}")
        else:
            print(f"❌ API调用失败")
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        print(f"错误类型: {type(e).__name__}")

if __name__ == "__main__":
    test_tavily_api()