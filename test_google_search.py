#!/usr/bin/env python3
"""
Google Search API 测试脚本
用于验证 Google Custom Search API 的配置和连接状态
"""

import os
import sys
import requests
from dotenv import load_dotenv
import json
from urllib.parse import urlencode

# 加载环境变量
load_dotenv()

def test_google_search_api():
    """测试 Google Search API 的基本功能"""
    
    print("=" * 60)
    print("Google Search API 测试")
    print("=" * 60)
    
    # 检查环境变量
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_CX")
    
    print(f"API Key: {'✅ 已配置' if api_key else '❌ 未配置'}")
    print(f"CX (搜索引擎ID): {'✅ 已配置' if cx else '❌ 未配置'}")
    
    if not api_key:
        print("\n❌ 错误: GOOGLE_SEARCH_API_KEY 未配置")
        print("请在 .env 文件中添加: GOOGLE_SEARCH_API_KEY=your_api_key")
        return False
    
    if not cx:
        print("\n❌ 错误: GOOGLE_SEARCH_CX 未配置")
        print("请在 .env 文件中添加: GOOGLE_SEARCH_CX=your_search_engine_id")
        return False
    
    # 显示配置信息（部分隐藏）
    print(f"\nAPI Key (部分): {api_key[:10]}...{api_key[-4:]}")
    print(f"CX: {cx}")
    
    # 测试基本连接
    print(f"\n🔍 测试基本搜索功能...")
    
    base_url = "https://www.googleapis.com/customsearch/v1"
    test_query = "人工智能"
    
    params = {
        'key': api_key,
        'cx': cx,
        'q': test_query,
        'num': 3,  # 只获取3个结果用于测试
        'safe': 'active'
    }
    
    try:
        print(f"正在搜索: '{test_query}'")
        print(f"请求URL: {base_url}")
        print(f"参数: {json.dumps({k: v for k, v in params.items() if k != 'key'}, ensure_ascii=False, indent=2)}")
        
        response = requests.get(base_url, params=params, timeout=30)
        
        print(f"\n📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构
            if 'items' in data:
                items = data['items']
                print(f"✅ 搜索成功! 获得 {len(items)} 条结果")
                
                # 显示前2个结果
                for i, item in enumerate(items[:2], 1):
                    print(f"\n结果 {i}:")
                    print(f"  标题: {item.get('title', 'N/A')}")
                    print(f"  链接: {item.get('link', 'N/A')}")
                    print(f"  摘要: {item.get('snippet', 'N/A')[:100]}...")
                
                # 显示配额信息
                if 'searchInformation' in data:
                    search_info = data['searchInformation']
                    print(f"\n📈 搜索信息:")
                    print(f"  搜索时间: {search_info.get('searchTime', 'N/A')} 秒")
                    print(f"  总结果数: {search_info.get('totalResults', 'N/A')}")
                
                return True
                
            else:
                print("❌ 响应中没有 'items' 字段")
                print(f"响应内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
                return False
                
        elif response.status_code == 400:
            print("❌ 400 错误: 请求参数有误")
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_info = error_data['error']
                    print(f"错误信息: {error_info.get('message', 'N/A')}")
                    print(f"错误代码: {error_info.get('code', 'N/A')}")
                    
                    # 常见错误提示
                    if 'Invalid Value' in error_info.get('message', ''):
                        print("\n💡 可能的解决方案:")
                        print("1. 检查 CX (搜索引擎ID) 是否正确")
                        print("2. 确认搜索引擎已启用")
                        print("3. 检查搜索引擎配置是否正确")
            except:
                print(f"错误响应: {response.text}")
            return False
            
        elif response.status_code == 403:
            print("❌ 403 错误: API密钥无效或配额不足")
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_info = error_data['error']
                    print(f"错误信息: {error_info.get('message', 'N/A')}")
                    
                    if 'quota' in error_info.get('message', '').lower():
                        print("\n💡 配额问题解决方案:")
                        print("1. 检查 Google Cloud Console 中的配额使用情况")
                        print("2. 确认 API 已启用")
                        print("3. 检查计费账户状态")
                    else:
                        print("\n💡 API密钥问题解决方案:")
                        print("1. 检查 API 密钥是否正确")
                        print("2. 确认 API 密钥有 Custom Search API 权限")
                        print("3. 检查 API 密钥是否有 IP 限制")
            except:
                print(f"错误响应: {response.text}")
            return False
            
        else:
            print(f"❌ HTTP {response.status_code} 错误")
            print(f"响应: {response.text}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL 错误: {str(e)}")
        print("\n💡 SSL 问题解决方案:")
        print("1. 检查网络连接")
        print("2. 尝试更新 requests 库: pip install --upgrade requests")
        print("3. 检查防火墙设置")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {str(e)}")
        print("\n💡 连接问题解决方案:")
        print("1. 检查网络连接")
        print("2. 检查代理设置")
        print("3. 尝试稍后重试")
        return False
        
    except requests.exceptions.Timeout as e:
        print(f"❌ 超时错误: {str(e)}")
        print("请检查网络连接或稍后重试")
        return False
        
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        return False

def test_advanced_features():
    """测试高级搜索功能"""
    
    print(f"\n🔬 测试高级搜索功能...")
    
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_CX")
    
    if not (api_key and cx):
        print("跳过高级功能测试 (API未配置)")
        return
    
    base_url = "https://www.googleapis.com/customsearch/v1"
    
    # 测试时间过滤
    print("\n📅 测试时间过滤 (最近7天)...")
    params = {
        'key': api_key,
        'cx': cx,
        'q': '人工智能 新闻',
        'num': 2,
        'dateRestrict': 'd7',  # 最近7天
        'safe': 'active'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                print(f"✅ 时间过滤成功! 获得 {len(data['items'])} 条最近7天的结果")
            else:
                print("⚠️ 时间过滤: 无结果")
        else:
            print(f"❌ 时间过滤测试失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 时间过滤测试出错: {str(e)}")
    
    # 测试语言过滤
    print("\n🌐 测试语言过滤...")
    params = {
        'key': api_key,
        'cx': cx,
        'q': 'artificial intelligence',
        'num': 2,
        'lr': 'lang_en',  # 英文结果
        'safe': 'active'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                print(f"✅ 语言过滤成功! 获得 {len(data['items'])} 条英文结果")
            else:
                print("⚠️ 语言过滤: 无结果")
        else:
            print(f"❌ 语言过滤测试失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 语言过滤测试出错: {str(e)}")

def show_setup_guide():
    """显示设置指南"""
    
    print(f"\n📖 Google Search API 设置指南:")
    print("=" * 40)
    
    print("1. 获取 API 密钥:")
    print("   - 访问: https://console.developers.google.com/")
    print("   - 创建项目或选择现有项目")
    print("   - 启用 'Custom Search API'")
    print("   - 创建 API 密钥")
    
    print("\n2. 创建自定义搜索引擎:")
    print("   - 访问: https://cse.google.com/cse/")
    print("   - 点击 'Add' 创建新搜索引擎")
    print("   - 选择 '搜索整个网络'")
    print("   - 获取搜索引擎 ID (CX)")
    
    print("\n3. 配置环境变量:")
    print("   在 .env 文件中添加:")
    print("   GOOGLE_SEARCH_API_KEY=your_api_key_here")
    print("   GOOGLE_SEARCH_CX=your_search_engine_id_here")
    
    print("\n4. 配额限制:")
    print("   - 免费版: 每天100次搜索")
    print("   - 付费版: 每天最多10,000次搜索")

def main():
    """主函数"""
    
    print("🔍 Google Search API 测试工具")
    
    # 基本功能测试
    success = test_google_search_api()
    
    if success:
        # 高级功能测试
        test_advanced_features()
        
        print(f"\n🎉 测试完成!")
        print("Google Search API 配置正确，可以正常使用。")
    else:
        print(f"\n❌ 测试失败!")
        show_setup_guide()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 