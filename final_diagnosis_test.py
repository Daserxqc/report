#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终诊断测试：搜索MCP和分析MCP集成问题
"""

import sys
import os
from pathlib import Path
import json

# 添加路径
collectors_path = Path(__file__).parent / "collectors"
if str(collectors_path) not in sys.path:
    sys.path.insert(0, str(collectors_path))

search_mcp_path = Path(__file__).parent / "search_mcp" / "src"
if str(search_mcp_path) not in sys.path:
    sys.path.insert(0, str(search_mcp_path))

def test_complete_workflow():
    """测试完整的搜索-分析工作流"""
    print("\n=== 完整工作流测试 ===")
    
    try:
        # 1. 导入main.py中的函数
        sys.path.insert(0, str(Path(__file__).parent))
        from main import comprehensive_search, analysis_mcp
        
        print("✅ 成功导入main.py中的函数")
        
        # 2. 执行搜索
        print("\n🔍 执行搜索...")
        search_result = comprehensive_search("人工智能最新发展", days=7, max_results=5)
        print(f"搜索结果类型: {type(search_result)}")
        print(f"搜索结果长度: {len(search_result) if search_result else 0}")
        print(f"搜索结果前200字符: {search_result[:200] if search_result else 'None'}...")
        
        # 3. 解析搜索结果为结构化数据
        print("\n🔄 解析搜索结果...")
        if search_result and "数据收集完成" in search_result:
            # 尝试从搜索结果中提取结构化数据
            lines = search_result.split('\n')
            structured_data = []
            
            current_item = {}
            for line in lines:
                line = line.strip()
                if line.startswith('标题:'):
                    if current_item:
                        structured_data.append(current_item)
                    current_item = {'title': line.replace('标题:', '').strip()}
                elif line.startswith('来源:'):
                    current_item['source'] = line.replace('来源:', '').strip()
                elif line.startswith('内容:'):
                    current_item['content'] = line.replace('内容:', '').strip()
                elif line.startswith('URL:'):
                    current_item['url'] = line.replace('URL:', '').strip()
            
            if current_item:
                structured_data.append(current_item)
            
            print(f"解析得到 {len(structured_data)} 条结构化数据")
            
            # 4. 执行分析
            print("\n📊 执行质量分析...")
            analysis_result = analysis_mcp(
                analysis_type="quality",
                data=structured_data,
                topic="人工智能最新发展",
                evaluation_mode="initial"
            )
            
            print(f"分析结果类型: {type(analysis_result)}")
            print(f"分析结果: {analysis_result}")
            
            # 5. 解析分析结果
            try:
                analysis_data = json.loads(analysis_result)
                score = analysis_data.get('score', 0)
                print(f"\n🎯 最终评分: {score}/10")
                print(f"分析类型: {analysis_data.get('analysis_type', 'unknown')}")
                print(f"推理: {analysis_data.get('reasoning', 'no reasoning')[:200]}...")
                
                if score == 0:
                    print("\n❌ 问题确认：评分为0")
                    print("详细信息:")
                    print(json.dumps(analysis_data, ensure_ascii=False, indent=2))
                else:
                    print(f"\n✅ 评分正常: {score}/10")
                    
            except json.JSONDecodeError as e:
                print(f"❌ 分析结果JSON解析失败: {e}")
                print(f"原始结果: {analysis_result}")
        else:
            print("❌ 搜索结果格式异常或为空")
            
    except Exception as e:
        print(f"❌ 完整工作流测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_direct_analysis_mcp():
    """直接测试analysis_mcp函数"""
    print("\n=== 直接分析MCP测试 ===")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from main import analysis_mcp
        
        # 创建测试数据
        test_data = [
            {
                "title": "人工智能在医疗领域的突破性进展",
                "content": "最新研究显示，AI技术在疾病诊断和药物发现方面取得了重大突破，准确率提升了30%。",
                "source": "科技日报",
                "url": "https://example.com/ai-medical"
            },
            {
                "title": "ChatGPT-5即将发布，性能大幅提升",
                "content": "OpenAI宣布将在明年发布ChatGPT-5，新版本在推理能力和多模态处理方面有显著改进。",
                "source": "TechCrunch",
                "url": "https://example.com/chatgpt5"
            },
            {
                "title": "中国AI芯片技术获得重大突破",
                "content": "国产AI芯片在性能和能效比方面达到国际先进水平，有望打破技术垄断。",
                "source": "新华网",
                "url": "https://example.com/ai-chip"
            }
        ]
        
        print(f"测试数据: {len(test_data)} 条")
        
        # 执行分析
        result = analysis_mcp(
            analysis_type="quality",
            data=test_data,
            topic="人工智能最新发展",
            evaluation_mode="initial"
        )
        
        print(f"分析结果: {result}")
        
        # 解析结果
        try:
            analysis_data = json.loads(result)
            score = analysis_data.get('score', 0)
            print(f"\n🎯 评分: {score}/10")
            
            if score == 0:
                print("❌ 问题确认：直接调用analysis_mcp也返回0分")
            else:
                print(f"✅ 直接调用analysis_mcp正常: {score}/10")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            
    except Exception as e:
        print(f"❌ 直接分析MCP测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_analysis_mcp_instance():
    """测试AnalysisMcp实例"""
    print("\n=== AnalysisMcp实例测试 ===")
    
    try:
        from collectors.analysis_mcp import AnalysisMcp
        
        analysis_mcp_instance = AnalysisMcp()
        print("✅ AnalysisMcp实例创建成功")
        
        # 测试数据
        test_data = [
            {
                "title": "人工智能技术发展报告",
                "content": "2024年人工智能技术在各个领域都取得了显著进展，特别是在自然语言处理和计算机视觉方面。",
                "source": "AI研究院",
                "url": "https://example.com/ai-report"
            }
        ]
        
        # 直接调用analyze_quality
        result = analysis_mcp_instance.analyze_quality(
            data=test_data,
            topic="人工智能最新发展",
            analysis_aspects=["relevance", "depth", "accuracy", "completeness", "timeliness"],
            evaluation_mode="initial"
        )
        
        print(f"AnalysisResult类型: {type(result)}")
        print(f"评分: {result.score}")
        print(f"分析类型: {result.analysis_type}")
        print(f"推理: {result.reasoning[:200]}...")
        
        if result.score == 0:
            print("❌ 问题确认：AnalysisMcp实例也返回0分")
            print(f"详细信息: {result.details}")
        else:
            print(f"✅ AnalysisMcp实例正常: {result.score}/10")
            
    except Exception as e:
        print(f"❌ AnalysisMcp实例测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔍 最终诊断测试：搜索MCP和分析MCP集成问题")
    print("=" * 60)
    
    # 测试1：直接测试AnalysisMcp实例
    test_analysis_mcp_instance()
    
    # 测试2：直接测试analysis_mcp函数
    test_direct_analysis_mcp()
    
    # 测试3：完整工作流测试
    test_complete_workflow()
    
    print("\n" + "=" * 60)
    print("🏁 诊断测试完成")

if __name__ == "__main__":
    main()