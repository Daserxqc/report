"""
意图理解与内容检索Agent API接口
提供简单的函数接口供外部调用
"""

import os
import json
import sys
from dotenv import load_dotenv

# 确保可以导入自定义模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

from intent_search_agent import IntentSearchAgent

# 全局Agent实例（单例模式）
_agent_instance = None

def get_agent():
    """获取Agent实例（单例模式）"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = IntentSearchAgent()
    return _agent_instance

def search_with_intent(query, return_json=True):
    """
    主要API接口：根据用户查询进行意图理解与内容检索
    
    Args:
        query (str): 用户查询
        return_json (bool): 是否返回JSON格式，否则返回字典
    
    Returns:
        dict或str: 包含意图理解和内容检索结果的数据
    """
    try:
        agent = get_agent()
        result = agent.search_and_summarize(query)
        
        if return_json:
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return result
            
    except Exception as e:
        error_result = {
            "user_query": query,
            "error": str(e),
            "core_intent": "处理查询时发生错误",
            "expanded_topics": [],
            "summary": "抱歉，处理您的查询时发生错误，请稍后重试。",
            "result_count": 0,
            "timestamp": None
        }
        
        if return_json:
            return json.dumps(error_result, ensure_ascii=False, indent=2)
        else:
            return error_result

def quick_search(query):
    """快速搜索接口，只返回精简摘要"""
    try:
        result = search_with_intent(query, return_json=False)
        return result.get('summary', '未找到相关信息')
    except Exception as e:
        return f"搜索失败: {str(e)}"

def detailed_search(query):
    """详细搜索接口，返回完整的结构化数据"""
    return search_with_intent(query, return_json=False)

def batch_search(queries):
    """批量搜索接口"""
    results = []
    
    for query in queries:
        try:
            result = search_with_intent(query, return_json=False)
            results.append(result)
        except Exception as e:
            results.append({
                "user_query": query,
                "error": str(e),
                "summary": "处理失败"
            })
    
    return results

# 示例使用函数
def demo_usage():
    """演示如何使用API接口"""
    print("🚀 意图理解与内容检索Agent API演示")
    print("=" * 50)
    
    # 测试查询
    test_queries = ["AI", "人工智能", "机器学习"]
    
    print("\n📝 1. 快速搜索演示:")
    for query in test_queries:
        summary = quick_search(query)
        print(f"   {query}: {summary}")
    
    print("\n📊 2. 详细搜索演示:")
    detailed_result = detailed_search("AI")
    print(f"   查询: AI")
    print(f"   意图: {detailed_result.get('core_intent', 'N/A')}")
    print(f"   主题: {', '.join(detailed_result.get('expanded_topics', []))}")
    print(f"   摘要: {detailed_result.get('summary', 'N/A')}")
    
    print("\n🔄 3. JSON格式输出演示:")
    json_result = search_with_intent("区块链", return_json=True)
    print(f"   JSON结果: {json_result}")
    
    print("\n📦 4. 批量搜索演示:")
    batch_queries = ["量子计算", "元宇宙"]
    batch_results = batch_search(batch_queries)
    for result in batch_results:
        print(f"   {result.get('user_query', 'N/A')}: {result.get('summary', 'N/A')}")

if __name__ == "__main__":
    demo_usage() 