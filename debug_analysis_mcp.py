#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试分析MCP的详细测试脚本
用于诊断为什么分析MCP总是返回0分的问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.analysis_mcp import AnalysisMcp
from collectors.llm_processor import LLMProcessor
from collectors.search_mcp import Document
import json
import traceback

def test_llm_processor():
    """测试LLM处理器是否正常工作"""
    print("\n" + "="*80)
    print("🔧 测试LLM处理器")
    print("="*80)
    
    try:
        llm = LLMProcessor()
        print(f"✅ LLM处理器初始化成功")
        print(f"   模型: {llm.model}")
        print(f"   API URL: {llm.base_url}")
        print(f"   有API密钥: {bool(llm.api_key)}")
        
        # 测试简单的API调用
        try:
            simple_prompt = "请回答：1+1等于几？"
            response = llm.call_llm_api(simple_prompt)
            print(f"✅ 简单API调用成功")
            print(f"   响应: {response[:100]}...")
            
            # 测试JSON API调用
            json_prompt = "请以JSON格式返回：{\"result\": 2, \"explanation\": \"1+1=2\"}"
            json_response = llm.call_llm_api_json(json_prompt)
            print(f"✅ JSON API调用成功")
            print(f"   JSON响应: {json_response}")
            
            return True
            
        except Exception as e:
            print(f"❌ API调用失败: {str(e)}")
            print(f"   错误详情: {traceback.format_exc()}")
            return False
            
    except Exception as e:
        print(f"❌ LLM处理器初始化失败: {str(e)}")
        return False

def test_analysis_mcp_initialization():
    """测试分析MCP初始化"""
    print("\n" + "="*80)
    print("🔧 测试分析MCP初始化")
    print("="*80)
    
    try:
        analysis_mcp = AnalysisMcp()
        print(f"✅ 分析MCP初始化成功")
        print(f"   有LLM处理器: {analysis_mcp.has_llm}")
        print(f"   分析模板数量: {len(analysis_mcp.analysis_templates)}")
        
        # 列出可用的分析模板
        print("   可用模板:")
        for template_name in analysis_mcp.analysis_templates.keys():
            print(f"     - {template_name}")
            
        return analysis_mcp
        
    except Exception as e:
        print(f"❌ 分析MCP初始化失败: {str(e)}")
        print(f"   错误详情: {traceback.format_exc()}")
        return None

def test_quality_analysis_with_mock_data(analysis_mcp):
    """使用模拟数据测试质量分析"""
    print("\n" + "="*80)
    print("🔧 测试质量分析功能")
    print("="*80)
    
    # 创建模拟搜索结果
    mock_data = [
        {
            "title": "人工智能发展现状与趋势",
            "content": "人工智能技术在近年来取得了显著进展，特别是在深度学习、自然语言处理和计算机视觉等领域。随着算力的提升和数据量的增加，AI模型的性能不断改善。",
            "url": "https://example.com/ai-trends",
            "source": "技术报告"
        },
        {
            "title": "机器学习在医疗领域的应用",
            "content": "机器学习技术在医疗诊断、药物发现和个性化治疗方面展现出巨大潜力。通过分析大量医疗数据，AI系统能够辅助医生做出更准确的诊断。",
            "url": "https://example.com/ml-healthcare",
            "source": "学术论文"
        },
        {
            "title": "AI伦理与安全挑战",
            "content": "随着AI技术的广泛应用，相关的伦理和安全问题也日益突出。如何确保AI系统的公平性、透明性和可解释性成为重要议题。",
            "url": "https://example.com/ai-ethics",
            "source": "政策文件"
        }
    ]
    
    topic = "人工智能发展趋势"
    
    print(f"📊 测试数据:")
    print(f"   主题: {topic}")
    print(f"   数据条数: {len(mock_data)}")
    
    try:
        # 测试质量分析
        print("\n🔍 执行质量分析...")
        result = analysis_mcp.analyze_quality(
            data=mock_data,
            topic=topic,
            evaluation_mode="initial"
        )
        
        print(f"✅ 质量分析完成")
        print(f"   分析类型: {result.analysis_type}")
        print(f"   质量评分: {result.score}/10")
        print(f"   评估理由: {result.reasoning}")
        print(f"   详细信息: {json.dumps(result.details, ensure_ascii=False, indent=2)}")
        
        if result.metadata:
            print(f"   元数据: {json.dumps(result.metadata, ensure_ascii=False, indent=2)}")
        
        return result
        
    except Exception as e:
        print(f"❌ 质量分析失败: {str(e)}")
        print(f"   错误详情: {traceback.format_exc()}")
        return None

def test_fallback_analysis(analysis_mcp):
    """测试回退分析功能"""
    print("\n" + "="*80)
    print("🔧 测试回退分析功能")
    print("="*80)
    
    # 临时禁用LLM来测试回退机制
    original_has_llm = analysis_mcp.has_llm
    analysis_mcp.has_llm = False
    
    mock_data = [{"title": "测试", "content": "测试内容"}] * 5
    topic = "测试主题"
    
    try:
        print("🔄 强制使用回退机制...")
        result = analysis_mcp.analyze_quality(
            data=mock_data,
            topic=topic,
            evaluation_mode="initial"
        )
        
        print(f"✅ 回退分析完成")
        print(f"   质量评分: {result.score}/10")
        print(f"   评估理由: {result.reasoning}")
        print(f"   详细信息: {json.dumps(result.details, ensure_ascii=False, indent=2)}")
        
        # 恢复原始设置
        analysis_mcp.has_llm = original_has_llm
        
        return result
        
    except Exception as e:
        print(f"❌ 回退分析失败: {str(e)}")
        analysis_mcp.has_llm = original_has_llm
        return None

def test_template_rendering(analysis_mcp):
    """测试模板渲染"""
    print("\n" + "="*80)
    print("🔧 测试分析模板渲染")
    print("="*80)
    
    try:
        # 获取初始搜索质量模板
        template = analysis_mcp.analysis_templates.get("initial_search_quality")
        if not template:
            print("❌ 找不到initial_search_quality模板")
            return False
            
        print(f"✅ 找到模板，长度: {len(template)}字符")
        
        # 测试模板参数
        template_params = {
            "topic": "人工智能发展趋势",
            "content_data": "测试内容数据",
            "data_count": 3
        }
        
        # 渲染模板
        rendered_prompt = template.format(**template_params)
        print(f"✅ 模板渲染成功")
        print(f"   渲染后长度: {len(rendered_prompt)}字符")
        print(f"   前200字符: {rendered_prompt[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板渲染失败: {str(e)}")
        print(f"   错误详情: {traceback.format_exc()}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始调试分析MCP")
    print("="*80)
    
    # 测试结果统计
    test_results = {
        "llm_processor": False,
        "analysis_mcp_init": False,
        "quality_analysis": False,
        "fallback_analysis": False,
        "template_rendering": False
    }
    
    # 1. 测试LLM处理器
    test_results["llm_processor"] = test_llm_processor()
    
    # 2. 测试分析MCP初始化
    analysis_mcp = test_analysis_mcp_initialization()
    if analysis_mcp:
        test_results["analysis_mcp_init"] = True
        
        # 3. 测试模板渲染
        test_results["template_rendering"] = test_template_rendering(analysis_mcp)
        
        # 4. 测试质量分析
        quality_result = test_quality_analysis_with_mock_data(analysis_mcp)
        if quality_result:
            test_results["quality_analysis"] = True
        
        # 5. 测试回退分析
        fallback_result = test_fallback_analysis(analysis_mcp)
        if fallback_result:
            test_results["fallback_analysis"] = True
    
    # 输出测试总结
    print("\n" + "="*80)
    print("📊 调试测试结果总结")
    print("="*80)
    
    for test_name, passed in test_results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:<25} {status}")
    
    passed_count = sum(test_results.values())
    total_count = len(test_results)
    
    print(f"\n总体结果: {passed_count}/{total_count} 项测试通过")
    
    if passed_count == total_count:
        print("🎉 所有测试通过！分析MCP功能正常")
    else:
        print("⚠️ 存在问题，需要进一步调试")
        
        # 提供诊断建议
        print("\n💡 诊断建议:")
        if not test_results["llm_processor"]:
            print("   - 检查LLM API配置（API密钥、URL、模型名称）")
            print("   - 确认网络连接和API服务可用性")
        if not test_results["analysis_mcp_init"]:
            print("   - 检查分析MCP的依赖项是否正确安装")
        if not test_results["template_rendering"]:
            print("   - 检查分析模板的格式和参数")
        if not test_results["quality_analysis"]:
            print("   - 检查质量分析的数据格式和处理逻辑")
        if not test_results["fallback_analysis"]:
            print("   - 检查回退机制的实现")

if __name__ == "__main__":
    main()