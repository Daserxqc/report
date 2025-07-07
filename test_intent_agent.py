"""
意图理解与内容检索Agent测试脚本
演示如何使用IntentSearchAgent
"""

import os
import json
import sys
from dotenv import load_dotenv

# 确保可以导入自定义模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intent_search_agent import IntentSearchAgent

def test_single_query(agent, query):
    """测试单个查询"""
    print(f"\n{'='*60}")
    print(f"🔍 测试查询: {query}")
    print('='*60)
    
    try:
        # 执行意图理解与内容检索
        result = agent.search_and_summarize(query)
        
        # 格式化输出结果
        print(f"\n📄 JSON结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 验证摘要长度
        summary_length = len(result.get('summary', ''))
        print(f"\n📊 摘要长度验证: {summary_length}字 (目标: 50-60字)")
        if 45 <= summary_length <= 80:
            print("✅ 摘要长度合格")
        else:
            print("⚠️ 摘要长度需要调整")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return None

def interactive_test():
    """交互式测试"""
    print("🤖 欢迎使用意图理解与内容检索Agent (交互式测试模式)")
    print("输入 'quit' 或 'exit' 退出")
    
    # 初始化Agent
    agent = IntentSearchAgent()
    
    while True:
        try:
            user_input = input("\n🔍 请输入您的查询: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
                
            if not user_input:
                print("⚠️ 请输入有效的查询")
                continue
                
            # 执行搜索和摘要
            result = test_single_query(agent, user_input)
            
            if result:
                print(f"\n⭐ 快速预览:")
                print(f"   意图: {result.get('core_intent', 'N/A')}")
                print(f"   主题: {', '.join(result.get('expanded_topics', []))}")
                print(f"   摘要: {result.get('summary', 'N/A')}")
                
        except KeyboardInterrupt:
            print("\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {str(e)}")

def batch_test():
    """批量测试预设查询"""
    print("🧪 批量测试模式")
    
    # 预设测试查询
    test_queries = [
        "AI",
        "人工智能",
        "机器学习",  
        "区块链",
        "新能源汽车",
        "量子计算",
        "元宇宙",
        "ChatGPT",
        "自动驾驶",
        "5G技术"
    ]
    
    # 初始化Agent
    agent = IntentSearchAgent()
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] 处理查询: {query}")
        result = test_single_query(agent, query)
        
        if result:
            results.append(result)
            
        # 避免API调用过快
        if i < len(test_queries):
            print("⏸️ 暂停3秒...")
            import time
            time.sleep(3)
    
    # 生成测试报告
    print(f"\n📊 测试总结:")
    print(f"   总查询数: {len(test_queries)}")
    print(f"   成功处理: {len(results)}")
    print(f"   成功率: {len(results)/len(test_queries)*100:.1f}%")
    
    # 摘要长度分析
    summary_lengths = [len(r.get('summary', '')) for r in results]
    if summary_lengths:
        avg_length = sum(summary_lengths) / len(summary_lengths)
        print(f"   平均摘要长度: {avg_length:.1f}字")
        print(f"   摘要长度范围: {min(summary_lengths)}-{max(summary_lengths)}字")

def main():
    """主函数"""
    load_dotenv()
    
    print("🚀 意图理解与内容检索Agent 测试系统")
    print("=" * 60)
    
    # 选择测试模式
    print("请选择测试模式:")
    print("1. 交互式测试 (推荐)")
    print("2. 批量测试")
    print("3. 快速演示")
    
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == '1':
            interactive_test()
        elif choice == '2':
            batch_test()
        elif choice == '3':
            # 快速演示
            print("\n🎯 快速演示: 使用 'AI' 作为示例查询")
            agent = IntentSearchAgent()
            test_single_query(agent, "AI")
        else:
            print("❌ 无效选择，退出")
            
    except KeyboardInterrupt:
        print("\n👋 用户中断，再见！")
    except Exception as e:
        print(f"❌ 程序异常: {str(e)}")

if __name__ == "__main__":
    main() 