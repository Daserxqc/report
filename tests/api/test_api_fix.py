import os
import re
import requests
import json
import config
from tqdm import tqdm

class ImprovedTranslator:
    def __init__(self):
        """初始化改进后的翻译器"""
        self.api_key = config.OPENAI_API_KEY if hasattr(config, 'OPENAI_API_KEY') else None
        self.base_url = config.OPENAI_BASE_URL if hasattr(config, 'OPENAI_BASE_URL') else "https://api.openai.com"
        
        # 确保URL格式正确
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
        
        # 判断API类型
        self.is_deepseek = "deepseek" in self.base_url.lower()
        
        # 打印配置信息
        print(f"API密钥: {'已配置' if self.api_key else '未配置'}")
        print(f"基础URL: {self.base_url}")
        print(f"API类型: {'DeepSeek' if self.is_deepseek else 'OpenAI'}")
        
        # 设置API端点
        if "/v1/chat/completions" in self.base_url:
            self.api_endpoint = self.base_url
        else:
            if self.base_url.endswith("/v1"):
                self.api_endpoint = f"{self.base_url}/chat/completions"
            else:
                self.api_endpoint = f"{self.base_url}/v1/chat/completions"
        
        print(f"API端点: {self.api_endpoint}")

    def translate_to_chinese(self, text):
        """
        改进的英文到中文翻译函数
        
        Args:
            text (str): 要翻译的英文文本
            
        Returns:
            str: 翻译后的中文文本
        """
        if not text or len(text.strip()) == 0:
            print("警告: 收到空文本，跳过翻译")
            return ""
        
        # 检查是否主要是英文
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        if ascii_chars / len(text) < 0.7:
            print("文本主要是非英文，不需要翻译")
            return text
        
        # 准备API请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = [
            {"role": "system", "content": "您是一位专业的翻译专家，请将以下英文文本翻译成中文。直接返回翻译结果，不要添加任何说明、注释或额外文本。"},
            {"role": "user", "content": text}
        ]
        
        data = {
            "model": "deepseek-chat" if self.is_deepseek else "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": min(len(text) * 2, 1500)  # 动态调整token长度
        }
        
        try:
            print(f"开始翻译，文本长度: {len(text)}字符")
            response = requests.post(
                self.api_endpoint, 
                headers=headers, 
                json=data, 
                timeout=60
            )
            
            # 检查状态码
            if response.status_code != 200:
                print(f"API请求失败，状态码: {response.status_code}")
                print(f"错误内容: {response.text}")
                return text
            
            # 解析响应
            response_data = response.json()
            
            if "choices" not in response_data or len(response_data["choices"]) == 0:
                print(f"API响应格式错误，没有choices字段: {json.dumps(response_data)}")
                return text
            
            # 提取翻译结果
            translated_text = response_data["choices"][0]["message"]["content"].strip()
            
            # 清理翻译结果
            if translated_text.startswith("翻译:") or translated_text.startswith("翻译："):
                translated_text = translated_text[3:].strip()
                
            # 清理可能的翻译元信息
            if translated_text.startswith("翻译说明"):
                parts = translated_text.split("\n\n", 1)
                if len(parts) > 1:
                    translated_text = parts[1]
            
            # 移除常见的元信息标记
            common_patterns = [
                "以下是符合要求的翻译：", 
                "以下是符合要求的翻译:", 
                "以下是符合要求的翻译",
                "以下是翻译结果："
            ]
            for pattern in common_patterns:
                if pattern in translated_text:
                    translated_text = translated_text.replace(pattern, "")
            
            # 移除其他可能的元信息标记
            translated_text = re.sub(r'[\[（\(]翻译.*?[\]）\)]', '', translated_text)
            translated_text = re.sub(r'[\[（\(]译注.*?[\]）\)]', '', translated_text)
            
            print(f"翻译成功，结果长度: {len(translated_text)}字符")
            return translated_text.strip()
            
        except Exception as e:
            import traceback
            print(f"翻译过程中发生错误: {str(e)}")
            print(f"详细错误信息: {traceback.format_exc()}")
            return text

def test_translate():
    """测试翻译功能"""
    sample_texts = [
        "This is a simple test message to verify the translation functionality.",
        "Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to intelligence of humans and other animals.",
        "The metaverse is a hypothetical iteration of the Internet as a single, universal and immersive virtual world that is facilitated by the use of virtual reality (VR) and augmented reality (AR) headsets.",
        "This text contains some Chinese characters 你好 in the middle to test the detection algorithm.",
        "元宇宙是一个主要由中文组成的文本，it shouldn't need translation."
    ]
    
    translator = ImprovedTranslator()
    
    print("\n=== 开始翻译测试 ===\n")
    for i, text in enumerate(sample_texts):
        print(f"样本 {i+1}:")
        print(f"原文: {text}")
        translated = translator.translate_to_chinese(text)
        print(f"译文: {translated}")
        print("-" * 50)

if __name__ == "__main__":
    print("=== 改进版翻译器测试 ===")
    test_translate() 