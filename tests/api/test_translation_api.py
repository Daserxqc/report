import os
import config
from openai import OpenAI
import sys

def test_translation():
    """
    简单测试翻译API调用
    """
    # 测试文本
    text = "This is a test message to verify the translation API is working properly."
    
    print("=== API参数信息 ===")
    print(f"OPENAI_API_KEY存在: {bool(config.OPENAI_API_KEY)}")
    print(f"OPENAI_API_KEY长度: {len(config.OPENAI_API_KEY) if hasattr(config, 'OPENAI_API_KEY') else 0}")
    
    if hasattr(config, 'OPENAI_BASE_URL') and config.OPENAI_BASE_URL:
        print(f"OPENAI_BASE_URL: {config.OPENAI_BASE_URL}")
        is_deepseek = "deepseek" in config.OPENAI_BASE_URL.lower()
        print(f"使用DeepSeek API: {is_deepseek}")
    else:
        print("未配置OPENAI_BASE_URL，使用默认OpenAI端点")
        is_deepseek = False
    
    # 初始化客户端
    try:
        print("\n=== 初始化API客户端 ===")
        client_kwargs = {"api_key": config.OPENAI_API_KEY}
        if hasattr(config, 'OPENAI_BASE_URL') and config.OPENAI_BASE_URL:
            client_kwargs["base_url"] = config.OPENAI_BASE_URL
            print(f"使用自定义base_url: {config.OPENAI_BASE_URL}")
        
        client = OpenAI(**client_kwargs)
        print("客户端初始化成功")
        
        # 选择模型
        if is_deepseek:
            models_to_try = ["deepseek-chat"]
        else:
            models_to_try = ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]
        
        print(f"\n=== 开始翻译测试 ===")
        print(f"待翻译文本: {text}")
        print(f"尝试模型列表: {models_to_try}")
        
        for model_name in models_to_try:
            try:
                print(f"\n尝试使用模型: {model_name}")
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "您是一位专业的翻译专家，请将以下英文文本翻译成中文。直接返回翻译结果，不要添加任何说明、注释或额外文本。"},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.1
                )
                
                translated_text = response.choices[0].message.content.strip()
                print(f"翻译成功！结果: {translated_text}")
                print(f"成功使用模型: {model_name}")
                return
                
            except Exception as e:
                print(f"使用模型 {model_name} 失败: {str(e)}")
                continue
                
        print("\n所有模型尝试失败")
        
    except Exception as e:
        import traceback
        print(f"\n=== 发生错误 ===")
        print(f"错误信息: {str(e)}")
        print("详细错误堆栈:")
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试翻译API...")
    test_translation()
    print("测试完成") 