#!/usr/bin/env python3
"""
Brave Search API 测试脚本
用于验证 Brave Web Search API 的配置和连接状态
"""

import os
import sys
import requests
from dotenv import load_dotenv
import json
import time

# 加载环境变量
load_dotenv()

def test_brave_search_api():
    """测试 Brave Search API 的基本功能"""
    
    print("=" * 60)
    print("Brave Search API 测试")
    print("=" * 60)
    
    # 检查环境变量
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    
    print(f"API Key: {'✅ 已配置' if api_key else '❌ 未配置'}")
    
    if not api_key:
        print("\n❌ 错误: BRAVE_SEARCH_API_KEY 未配置")
        print("请在 .env 文件中添加: BRAVE_SEARCH_API_KEY=your_api_key")
        return False
    
    # 显示配置信息（部分隐藏）
    print(f"\nAPI Key (部分): {api_key[:10]}...{api_key[-4:]}")
    
    # 测试基本连接
    print(f"\n🔍 测试基本搜索功能...")
    
    base_url = "https://api.search.brave.com/res/v1/web/search"
    test_query = "人工智能"
    
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': api_key,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    params = {
        'q': test_query,
        'count': 3,  # 只获取3个结果用于测试
        'safesearch': 'moderate'
    }
    
    try:
        print(f"正在搜索: '{test_query}'")
        print(f"请求URL: {base_url}")
        print(f"参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
        
        response = requests.get(base_url, headers=headers, params=params, timeout=30)
        
        print(f"\n📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构
            if 'web' in data and 'results' in data['web']:
                results = data['web']['results']
                print(f"✅ 搜索成功! 获得 {len(results)} 条结果")
                
                # 显示前2个结果
                for i, item in enumerate(results[:2], 1):
                    print(f"\n结果 {i}:")
                    print(f"  标题: {item.get('title', 'N/A')}")
                    print(f"  链接: {item.get('url', 'N/A')}")
                    print(f"  描述: {item.get('description', 'N/A')[:100]}...")
                    print(f"  发布时间: {item.get('age', 'N/A')}")
                
                # 显示查询信息
                if 'query' in data:
                    query_info = data['query']
                    print(f"\n📈 查询信息:")
                    print(f"  原始查询: {query_info.get('original', 'N/A')}")
                    print(f"  是否拼写纠正: {query_info.get('spellcheck_off', False)}")
                
                return True
                
            else:
                print("❌ 响应中没有 'web.results' 字段")
                print(f"响应结构: {list(data.keys())}")
                if 'web' in data:
                    print(f"web字段内容: {list(data['web'].keys())}")
                return False
                
        elif response.status_code == 400:
            print("❌ 400 错误: 请求参数有误")
            try:
                error_data = response.json()
                print(f"错误响应: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                print(f"错误响应: {response.text}")
            return False
            
        elif response.status_code == 401:
            print("❌ 401 错误: API密钥无效")
            print("\n💡 解决方案:")
            print("1. 检查 API 密钥是否正确")
            print("2. 确认 API 密钥是否已激活")
            print("3. 访问 https://brave.com/search/api/ 检查账户状态")
            return False
            
        elif response.status_code == 403:
            print("❌ 403 错误: 访问被拒绝")
            print("\n💡 可能的原因:")
            print("1. API 密钥权限不足")
            print("2. 超出配额限制")
            print("3. IP 地址被限制")
            return False
            
        elif response.status_code == 429:
            print("❌ 429 错误: 请求过于频繁")
            print("请稍后重试，或检查请求频率限制")
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
    
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    
    if not api_key:
        print("跳过高级功能测试 (API未配置)")
        return
    
    base_url = "https://api.search.brave.com/res/v1/web/search"
    
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': api_key,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # 测试时间过滤
    print("\n📅 测试时间过滤 (最近一周)...")
    params = {
        'q': '人工智能 新闻',
        'count': 2,
        'freshness': 'pw',  # 最近一周
        'safesearch': 'moderate'
    }
    
    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'web' in data and 'results' in data['web']:
                results = data['web']['results']
                print(f"✅ 时间过滤成功! 获得 {len(results)} 条最近一周的结果")
            else:
                print("⚠️ 时间过滤: 无结果")
        else:
            print(f"❌ 时间过滤测试失败: HTTP {response.status_code}")
        
        time.sleep(0.5)  # 避免请求过快
    except Exception as e:
        print(f"❌ 时间过滤测试出错: {str(e)}")
    
    # 测试安全搜索级别
    print("\n🛡️ 测试安全搜索...")
    params = {
        'q': 'technology news',
        'count': 2,
        'safesearch': 'strict',  # 严格安全搜索
    }
    
    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'web' in data and 'results' in data['web']:
                results = data['web']['results']
                print(f"✅ 安全搜索成功! 获得 {len(results)} 条安全过滤结果")
            else:
                print("⚠️ 安全搜索: 无结果")
        else:
            print(f"❌ 安全搜索测试失败: HTTP {response.status_code}")
        
        time.sleep(0.5)  # 避免请求过快
    except Exception as e:
        print(f"❌ 安全搜索测试出错: {str(e)}")

def test_rate_limits():
    """测试请求频率限制"""
    
    print(f"\n⏱️ 测试请求频率限制...")
    
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    
    if not api_key:
        print("跳过频率限制测试 (API未配置)")
        return
    
    base_url = "https://api.search.brave.com/res/v1/web/search"
    
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': api_key,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # 快速发送3个请求测试频率限制
    for i in range(3):
        params = {
            'q': f'test query {i+1}',
            'count': 1,
            'safesearch': 'moderate'
        }
        
        try:
            print(f"发送第 {i+1} 个请求...")
            response = requests.get(base_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ 请求 {i+1} 成功")
            elif response.status_code == 429:
                print(f"  ⚠️ 请求 {i+1} 被限流 (429)")
                break
            else:
                print(f"  ❌ 请求 {i+1} 失败: {response.status_code}")
            
            # 短暂延迟
            time.sleep(0.2)
            
        except Exception as e:
            print(f"  ❌ 请求 {i+1} 出错: {str(e)}")
    
    print("频率限制测试完成")

def show_setup_guide():
    """显示设置指南"""
    
    print(f"\n📖 Brave Search API 设置指南:")
    print("=" * 40)
    
    print("1. 获取 API 密钥:")
    print("   - 访问: https://brave.com/search/api/")
    print("   - 注册账户")
    print("   - 选择订阅计划:")
    print("     * 免费层: 每月2,000次搜索")
    print("     * 基础层: 每月更多搜索次数")
    print("     * 专业层: 高级功能和更高配额")
    
    print("\n2. 配置环境变量:")
    print("   在 .env 文件中添加:")
    print("   BRAVE_SEARCH_API_KEY=your_api_key_here")
    
    print("\n3. API 特性:")
    print("   - 独立搜索引擎，不依赖Google")
    print("   - 注重隐私保护")
    print("   - 支持时间过滤、安全搜索等功能")
    print("   - 快速响应和高质量结果")
    
    print("\n4. 使用限制:")
    print("   - 请求频率: 建议间隔100ms以上")
    print("   - 每次最多20个结果")
    print("   - 支持多种搜索参数")

def main():
    """主函数"""
    
    print("🔍 Brave Search API 测试工具")
    
    # 基本功能测试
    success = test_brave_search_api()
    
    if success:
        # 高级功能测试
        test_advanced_features()
        
        # 频率限制测试
        test_rate_limits()
        
        print(f"\n🎉 测试完成!")
        print("Brave Search API 配置正确，可以正常使用。")
    else:
        print(f"\n❌ 测试失败!")
        show_setup_guide()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 