import os
import requests
import json
import config

def test_direct_api_call():
    """
    直接使用requests测试DeepSeek API调用，避免依赖OpenAI库
    """
    # 测试文本
    text = "This is a test message to verify the translation API is working directly with HTTP requests."
    
    print("=== API参数信息 ===")
    api_key = config.OPENAI_API_KEY if hasattr(config, 'OPENAI_API_KEY') else None
    print(f"API密钥存在: {bool(api_key)}")
    
    base_url = config.OPENAI_BASE_URL if hasattr(config, 'OPENAI_BASE_URL') else "https://api.openai.com"
    print(f"API基础URL: {base_url}")
    
    # 确保URL格式正确
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    # 判断是否为DeepSeek API
    is_deepseek = "deepseek" in base_url.lower()
    print(f"使用DeepSeek API: {is_deepseek}")
    
    # 构建API端点
    if "/v1/chat/completions" in base_url:
        api_endpoint = base_url
    else:
        if base_url.endswith("/v1"):
            api_endpoint = f"{base_url}/chat/completions"
        else:
            api_endpoint = f"{base_url}/v1/chat/completions"
    
    print(f"API端点: {api_endpoint}")
    
    # 构建请求头和数据
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    messages = [
        {"role": "system", "content": "您是一位专业的翻译专家，请将以下英文文本翻译成中文。直接返回翻译结果，不要添加任何说明、注释或额外文本。"},
        {"role": "user", "content": text}
    ]
    
    data = {
        "model": "deepseek-chat" if is_deepseek else "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 500
    }
    
    print("\n=== 请求详情 ===")
    print(f"头部信息: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    # 发送请求
    try:
        print("\n=== 发送API请求 ===")
        response = requests.post(api_endpoint, headers=headers, json=data, timeout=30)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        # 检查响应状态
        if response.status_code == 200:
            response_data = response.json()
            print("\n=== 响应内容 ===")
            print(f"原始响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                print(f"\n翻译结果: {content}")
                print(f"\n请求成功完成!")
            else:
                print("\n响应中没有找到翻译结果")
        else:
            print("\n=== 错误响应 ===")
            print(f"响应内容: {response.text}")
    
    except Exception as e:
        import traceback
        print(f"\n=== 发生错误 ===")
        print(f"错误信息: {str(e)}")
        print("详细错误堆栈:")
        traceback.print_exc()

if __name__ == "__main__":
    print("开始直接测试API调用...")
    test_direct_api_call()
    print("测试完成") 