#!/usr/bin/env python3
"""
MasterMcp使用演示
展示如何使用统一的MasterMcp来执行各种任务，包括原来的insight生成
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入MasterMcp
from collectors.master_mcp import MasterMcp, TaskType, TaskConfig


def demo_insight_generation():
    """演示洞察生成任务（原来的insight功能）"""
    print("\n🔍 洞察生成演示")
    print("=" * 60)
    
    # 初始化MasterMcp
    master_mcp = MasterMcp(enable_user_interaction=False)
    
    # 示例查询
    queries = [
        "分析生成式AI在2024年的发展趋势和商业机会",
        "ChatGPT对教育行业的影响洞察",
        "大语言模型技术发展的关键趋势",
        "人工智能芯片市场的投资机会分析"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n📋 示例 {i}: {query}")
        
        # 方式1: 自动意图识别
        result = master_mcp.execute_task(query)
        
        print(f"✅ 识别任务类型: {result.task_type.value}")
        print(f"📊 质量评分: {result.quality_score:.2f}")
        print(f"⏱️ 执行时间: {result.execution_time:.2f}秒")
        print(f"📁 输出文件: {result.output_path}")
        
        if i == 1:  # 只显示第一个示例的详细内容
            print(f"\n📄 报告预览:")
            print("-" * 40)
            print(result.output_content[:500] + "...")
        
        print("-" * 60)


def demo_explicit_task_configs():
    """演示显式指定任务配置"""
    print("\n🎯 显式任务配置演示")
    print("=" * 60)
    
    master_mcp = MasterMcp(enable_user_interaction=False)
    
    # 示例1: 明确指定为洞察生成
    config1 = TaskConfig(
        task_type=TaskType.INSIGHT_GENERATION,
        topic="区块链技术在金融领域的应用",
        requirements="重点分析投资机会和技术风险",
        quality_threshold=0.8
    )
    
    print("📋 任务1: 区块链金融应用洞察")
    result1 = master_mcp.execute_task("", config1)
    print(f"✅ 完成，输出: {result1.output_path}")
    
    # 示例2: 新闻分析任务
    config2 = TaskConfig(
        task_type=TaskType.NEWS_ANALYSIS,
        topic="苹果公司最新财报",
        requirements="分析财报对股价和市场的影响",
        quality_threshold=0.7
    )
    
    print("\n📋 任务2: 苹果财报新闻分析")
    result2 = master_mcp.execute_task("", config2)
    print(f"✅ 完成，输出: {result2.output_path}")
    
    # 示例3: 市场研究任务
    config3 = TaskConfig(
        task_type=TaskType.MARKET_RESEARCH,
        topic="电动汽车充电桩市场",
        requirements="分析市场规模、竞争格局和增长机会"
    )
    
    print("\n📋 任务3: 充电桩市场研究")
    result3 = master_mcp.execute_task("", config3)
    print(f"✅ 完成，输出: {result3.output_path}")


def demo_all_task_types():
    """演示所有任务类型"""
    print("\n🎪 所有任务类型演示")
    print("=" * 60)
    
    master_mcp = MasterMcp(enable_user_interaction=False)
    
    # 为每种任务类型准备示例
    task_examples = {
        TaskType.INSIGHT_GENERATION: "人工智能医疗应用的发展洞察",
        TaskType.RESEARCH_REPORT: "量子计算技术发展现状研究",
        TaskType.NEWS_ANALYSIS: "特斯拉最新自动驾驶技术发布",
        TaskType.MARKET_RESEARCH: "云计算服务市场竞争分析",
        TaskType.ACADEMIC_REPORT: "深度学习在图像识别中的应用",
        TaskType.BUSINESS_ANALYSIS: "Netflix流媒体业务战略分析",
        TaskType.TECHNICAL_DOCUMENTATION: "React 18新特性技术文档",
        TaskType.CONTENT_SUMMARIZATION: "2024年人工智能发展报告摘要",
        TaskType.DATA_ANALYSIS: "电商平台用户行为数据分析"
    }
    
    results = []
    
    for task_type, topic in task_examples.items():
        print(f"\n📋 执行: {task_type.value} - {topic}")
        
        try:
            config = TaskConfig(
                task_type=task_type,
                topic=topic,
                quality_threshold=0.6  # 降低阈值以加快演示
            )
            
            result = master_mcp.execute_task("", config)
            results.append(result)
            
            print(f"  ✅ 成功 - 质量: {result.quality_score:.2f}")
            print(f"  📁 输出: {os.path.basename(result.output_path)}")
            
        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
    
    # 总结
    print(f"\n📊 执行总结:")
    print(f"  ✅ 成功任务: {len([r for r in results if r.success])}")
    print(f"  ❌ 失败任务: {len([r for r in results if not r.success])}")
    print(f"  📈 平均质量: {sum(r.quality_score for r in results if r.success) / len(results):.2f}")


def demo_natural_language_queries():
    """演示自然语言查询的自动识别"""
    print("\n💬 自然语言查询演示")
    print("=" * 60)
    
    master_mcp = MasterMcp(enable_user_interaction=False)
    
    # 各种自然语言查询示例
    natural_queries = [
        "帮我分析一下OpenAI最近的发展趋势，我想了解他们的商业模式变化",
        "写一份关于新能源汽车行业的研究报告",
        "总结一下最近科技圈的重要新闻",
        "我需要了解5G技术在智慧城市中的应用情况",
        "分析一下元宇宙概念股的投资价值",
        "帮我写一个Python机器学习的技术文档",
        "对比分析一下腾讯和阿里的云计算业务",
        "整理最新的人工智能学术论文进展"
    ]
    
    for i, query in enumerate(natural_queries, 1):
        print(f"\n{i}. 用户查询: {query}")
        
        try:
            result = master_mcp.execute_task(query)
            
            print(f"   🎯 识别类型: {result.task_type.value}")
            print(f"   📋 提取主题: {result.topic}")
            print(f"   ✅ 执行状态: {'成功' if result.success else '失败'}")
            
            if result.success:
                print(f"   📊 质量评分: {result.quality_score:.2f}")
                print(f"   📁 输出文件: {os.path.basename(result.output_path)}")
        
        except Exception as e:
            print(f"   ❌ 执行出错: {str(e)}")


def demo_interactive_mode():
    """演示交互模式"""
    print("\n👤 交互模式演示")
    print("=" * 60)
    
    # 启用交互模式
    master_mcp = MasterMcp(enable_user_interaction=True)
    
    print("在交互模式下，MasterMcp会：")
    print("1. 在数据质量不足时询问是否继续")
    print("2. 在生成大纲后请求用户审查")
    print("3. 在关键决策点获取用户输入")
    
    print("\n模拟交互式执行...")
    
    # 这里可以添加模拟的交互式执行
    # 但在演示模式下，我们只展示功能说明
    print("💡 交互式功能包括:")
    print("  - 大纲审查和修改")
    print("  - 数据质量确认") 
    print("  - 任务参数调整")
    print("  - 输出格式选择")


def compare_with_original_agents():
    """对比原始agents的使用方式"""
    print("\n🔄 与原始agents的对比")
    print("=" * 60)
    
    print("🔴 原来的方式 (使用多个独立agents):")
    print("""
# 需要分别调用不同的agent
from generate_insights_report import generate_insights
from generate_research_report import generate_research  
from generate_news_report import generate_news

# 洞察生成
insights = generate_insights("AI发展趋势")

# 研究报告  
research = generate_research("量子计算")

# 新闻分析
news = generate_news("特斯拉财报")
""")
    
    print("🟢 现在的方式 (使用统一MasterMcp):")
    print("""
# 统一入口，自动识别任务类型
from collectors.master_mcp import MasterMcp

master_mcp = MasterMcp()

# 自动识别为洞察生成
result1 = master_mcp.execute_task("分析AI发展趋势的商业机会")

# 自动识别为研究报告
result2 = master_mcp.execute_task("写一份量子计算技术研究报告")  

# 自动识别为新闻分析
result3 = master_mcp.execute_task("分析特斯拉最新财报新闻")
""")
    
    print("✅ 优势对比:")
    advantages = [
        "统一入口，无需选择具体agent",
        "自动意图识别和任务分派", 
        "标准化的数据流和处理流程",
        "内置质量控制和错误处理",
        "支持用户交互和反馈循环",
        "可扩展的任务类型和配置",
        "统一的输出格式和结果管理"
    ]
    
    for i, advantage in enumerate(advantages, 1):
        print(f"  {i}. {advantage}")


def main():
    """主函数"""
    print("🚀 MasterMcp统一管理系统演示")
    print("=" * 80)
    
    try:
        # 检查命令行参数
        if "--insight" in sys.argv:
            demo_insight_generation()
        elif "--explicit" in sys.argv:
            demo_explicit_task_configs()
        elif "--all" in sys.argv:
            demo_all_task_types()
        elif "--natural" in sys.argv:
            demo_natural_language_queries()
        elif "--interactive" in sys.argv:
            demo_interactive_mode()
        elif "--compare" in sys.argv:
            compare_with_original_agents()
        else:
            # 默认执行核心演示
            print("🎯 执行核心功能演示...")
            demo_insight_generation()
            
            print("\n" + "="*80)
            demo_natural_language_queries()
            
            print("\n" + "="*80)
            compare_with_original_agents()
            
            print("\n💡 更多演示选项:")
            print("  --insight    洞察生成专项演示")
            print("  --explicit   显式任务配置演示")
            print("  --all        所有任务类型演示")
            print("  --natural    自然语言查询演示")
            print("  --interactive 交互模式演示")
            print("  --compare    与原始agents对比")
    
    except KeyboardInterrupt:
        print("\n❌ 用户中断了演示")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 