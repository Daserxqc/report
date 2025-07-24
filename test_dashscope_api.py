#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from openai import OpenAI

def test_dashscope_api():
    """测试 dashscope API 调用"""
    
    # 初始化客户端
    client = OpenAI(
        api_key="sk-5b73166a137b4a93add9e4ffe6d68aa6",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    try:
        # 测试简单对话
        response = client.chat.completions.create(
            model="deepseek-v3",
            messages=[
                {"role": "user", "content": "你好，请简单介绍一下你自己"}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        print("✅ API调用成功！")
        print(f"模型: deepseek-v3")
        print(f"回复: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
    return False

if __name__ == "__main__":
    test_dashscope_api() 