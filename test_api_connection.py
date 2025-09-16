#!/usr/bin/env python3
"""
API连接测试脚本
用于诊断大模型API连接问题
"""

import os
import time
import json
import requests
import ssl
from datetime import datetime
from dotenv import load_dotenv
import config

def test_ssl_connection():
    """测试SSL连接"""
    print("🔍 测试SSL连接...")
    try:
        import ssl
        print(f"✅ SSL版本: {ssl.OPENSSL_VERSION}")
        
        # 测试SSL证书
        context = ssl.create_default_context()
        print("✅ SSL上下文创建成功")
        
        return True
    except Exception as e:
        print(f"❌ SSL连接测试失败: {str(e)}")
        return False

def test_network_connectivity():
    """测试网络连通性"""
    print("\n🌐 测试网络连通性...")
    
    test_urls = [
        "https://www.baidu.com",
        "https://www.google.com", 
        "https://dashscope.aliyuncs.com",
        "https://api.openai.com"
    ]
    
    results = {}
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            results[url] = {
                "status": "success",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
            print(f"✅ {url}: {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
        except Exception as e:
            results[url] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ {url}: {str(e)}")
    
    return results

def test_dashscope_api():
    """测试DashScope API连接"""
    print("\n🚀 测试DashScope API...")
    
    api_key = config.OPENAI_API_KEY
    base_url = config.OPENAI_BASE_URL
    
    if not api_key:
        print("❌ 未找到API密钥")
        return False
    
    print(f"🔑 API密钥: {api_key[:10]}...")
    print(f"🌐 Base URL: {base_url}")
    
    # 测试简单的API调用
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 构建测试数据
    test_data = {
        "model": "deepseek-v3",
        "messages": [
            {"role": "user", "content": "Hello, please respond with 'API test successful'"}
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    endpoint = f"{base_url}/chat/completions"
    
    try:
        print(f"📡 发送请求到: {endpoint}")
        start_time = time.time()
        
        response = requests.post(
            endpoint, 
            headers=headers, 
            json=test_data, 
            timeout=30,
            verify=True
        )
        
        response_time = time.time() - start_time
        print(f"⏱️ 响应时间: {response_time:.2f}秒")
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(f"✅ API调用成功!")
                print(f"📝 响应内容: {content}")
                
                # 检查用量信息
                if "usage" in result:
                    usage = result["usage"]
                    print(f"📈 Token使用: {usage}")
                
                return True
            else:
                print(f"❌ API响应格式异常: {result}")
                return False
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"📄 错误响应: {response.text}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL错误: {str(e)}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {str(e)}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ 超时错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False

def test_openai_library():
    """测试OpenAI库调用"""
    print("\n📚 测试OpenAI库调用...")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL
        )
        
        print("✅ OpenAI客户端创建成功")
        
        # 测试简单调用
        start_time = time.time()
        response = client.chat.completions.create(
            model="deepseek-v3",
            messages=[
                {"role": "user", "content": "Hello, please respond with 'OpenAI library test successful'"}
            ],
            temperature=0.1,
            max_tokens=50
        )
        
        response_time = time.time() - start_time
        print(f"⏱️ 响应时间: {response_time:.2f}秒")
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print(f"✅ OpenAI库调用成功!")
            print(f"📝 响应内容: {content}")
            
            # 检查用量信息
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                print(f"📈 Token使用: {usage}")
            
            return True
        else:
            print("❌ OpenAI库响应格式异常")
            return False
            
    except ImportError:
        print("❌ OpenAI库未安装")
        return False
    except Exception as e:
        print(f"❌ OpenAI库调用失败: {str(e)}")
        return False

def test_llm_processor():
    """测试LLM处理器"""
    print("\n🔧 测试LLM处理器...")
    
    try:
        from collectors.llm_processor import LLMProcessor
        
        processor = LLMProcessor()
        print("✅ LLM处理器初始化成功")
        
        # 测试简单调用
        start_time = time.time()
        result = processor.call_llm_api(
            prompt="Hello, please respond with 'LLM processor test successful'",
            system_message="You are a helpful assistant.",
            temperature=0.1,
            max_tokens=50
        )
        
        response_time = time.time() - start_time
        print(f"⏱️ 响应时间: {response_time:.2f}秒")
        print(f"✅ LLM处理器调用成功!")
        print(f"📝 响应内容: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM处理器测试失败: {str(e)}")
        import traceback
        print(f"📄 详细错误: {traceback.format_exc()}")
        return False

def test_json_api():
    """测试JSON API调用"""
    print("\n📋 测试JSON API调用...")
    
    try:
        from collectors.llm_processor import LLMProcessor
        
        processor = LLMProcessor()
        
        # 测试JSON格式调用
        start_time = time.time()
        result = processor.call_llm_api_json(
            prompt="请返回一个简单的JSON对象，包含字段'test'和值'success'",
            system_message="你是一个API程序，只返回有效的JSON格式数据。",
            temperature=0.1,
            max_tokens=100
        )
        
        response_time = time.time() - start_time
        print(f"⏱️ 响应时间: {response_time:.2f}秒")
        print(f"✅ JSON API调用成功!")
        print(f"📝 响应内容: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON API测试失败: {str(e)}")
        import traceback
        print(f"📄 详细错误: {traceback.format_exc()}")
        return False

def generate_test_report(results):
    """生成测试报告"""
    print("\n" + "="*60)
    print("📊 API连接测试报告")
    print("="*60)
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"🕐 测试时间: {current_time}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"📈 测试结果: {passed_tests}/{total_tests} 通过")
    
    print("\n📋 详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    # 保存报告到文件
    report_data = {
        "test_time": current_time,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "results": results
    }
    
    report_file = f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 测试报告已保存到: {report_file}")
    
    return report_file

def main():
    """主测试函数"""
    print("🚀 API连接诊断测试开始")
    print("="*60)
    
    # 加载环境变量
    load_dotenv()
    
    # 运行所有测试
    test_results = {}
    
    # 1. SSL连接测试
    test_results["SSL连接"] = test_ssl_connection()
    
    # 2. 网络连通性测试
    network_results = test_network_connectivity()
    test_results["网络连通性"] = all(
        result["status"] == "success" 
        for result in network_results.values()
    )
    
    # 3. DashScope API测试
    test_results["DashScope API"] = test_dashscope_api()
    
    # 4. OpenAI库测试
    test_results["OpenAI库"] = test_openai_library()
    
    # 5. LLM处理器测试
    test_results["LLM处理器"] = test_llm_processor()
    
    # 6. JSON API测试
    test_results["JSON API"] = test_json_api()
    
    # 生成测试报告
    report_file = generate_test_report(test_results)
    
    print("\n🎯 测试完成!")
    
    # 给出建议
    if not test_results["LLM处理器"]:
        print("\n💡 建议:")
        if not test_results["网络连通性"]:
            print("  - 检查网络连接和防火墙设置")
        if not test_results["SSL连接"]:
            print("  - 检查SSL证书和系统时间")
        if not test_results["DashScope API"]:
            print("  - 检查API密钥和base_url配置")
        print("  - 尝试使用备用网络环境")
        print("  - 联系API服务提供商")

if __name__ == "__main__":
    main()

