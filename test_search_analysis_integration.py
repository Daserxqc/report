#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索MCP与分析MCP集成测试
测试搜索结果与分析评估之间的数据格式兼容性问题
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "collectors"))
sys.path.insert(0, str(project_root / "search_mcp" / "src"))

def test_search_mcp_output_format():
    """测试搜索MCP的输出格式"""
    print("\n" + "="*60)
    print("🔍 测试搜索MCP输出格式")
    print("="*60)
    
    try:
        # 导入main.py中的搜索函数
        from main import comprehensive_search, parallel_search
        
        # 测试comprehensive_search
        print("\n1. 测试comprehensive_search输出格式:")
        search_result = comprehensive_search("人工智能", days=7, max_results=3)
        print(f"   返回类型: {type(search_result)}")
        print(f"   返回内容长度: {len(search_result) if search_result else 0}")
        print(f"   前200字符: {search_result[:200] if search_result else 'None'}...")
        
        # 测试parallel_search
        print("\n2. 测试parallel_search输出格式:")
        parallel_result = parallel_search(["AI技术", "机器学习"], max_results=3, topic="人工智能")
        print(f"   返回类型: {type(parallel_result)}")
        print(f"   返回内容长度: {len(parallel_result) if parallel_result else 0}")
        print(f"   前200字符: {parallel_result[:200] if parallel_result else 'None'}...")
        
        return search_result, parallel_result
        
    except Exception as e:
        print(f"❌ 搜索MCP测试失败: {e}")
        return None, None

def test_analysis_mcp_input_requirements():
    """测试分析MCP的输入要求"""
    print("\n" + "="*60)
    print("🔍 测试分析MCP输入要求")
    print("="*60)
    
    try:
        from main import analysis_mcp
        
        # 测试1: 使用正确的List[Dict]格式
        print("\n1. 测试正确的List[Dict]格式:")
        correct_data = [
            {
                "title": "人工智能发展趋势",
                "content": "人工智能技术正在快速发展，特别是在机器学习和深度学习领域取得了重大突破。",
                "url": "https://example.com/ai-trends",
                "source": "tech_news"
            },
            {
                "title": "AI在医疗领域的应用",
                "content": "人工智能在医疗诊断、药物发现和个性化治疗方面展现出巨大潜力。",
                "url": "https://example.com/ai-medical",
                "source": "medical_journal"
            }
        ]
        
        result1 = analysis_mcp("quality", correct_data, "人工智能")
        print(f"   返回类型: {type(result1)}")
        
        # 尝试解析JSON结果
        try:
            parsed_result = json.loads(result1)
            print(f"   解析成功，得分: {parsed_result.get('score', 'N/A')}")
            print(f"   分析类型: {parsed_result.get('analysis_type', 'N/A')}")
        except:
            print(f"   JSON解析失败，原始结果: {result1[:200]}...")
        
        # 测试2: 使用错误的字符串格式
        print("\n2. 测试错误的字符串格式:")
        wrong_data = "这是一个字符串格式的搜索结果，包含人工智能相关信息..."
        
        result2 = analysis_mcp("quality", wrong_data, "人工智能")
        print(f"   返回类型: {type(result2)}")
        
        try:
            parsed_result2 = json.loads(result2)
            print(f"   解析成功，得分: {parsed_result2.get('score', 'N/A')}")
        except:
            print(f"   JSON解析失败，原始结果: {result2[:200]}...")
            
        return result1, result2
        
    except Exception as e:
        print(f"❌ 分析MCP测试失败: {e}")
        return None, None

def convert_search_result_to_dict_format(search_result_str: str) -> List[Dict]:
    """将搜索MCP的字符串结果转换为分析MCP期望的List[Dict]格式"""
    print("\n" + "="*60)
    print("🔄 转换搜索结果格式")
    print("="*60)
    
    if not search_result_str or not isinstance(search_result_str, str):
        print("❌ 输入数据无效")
        return []
    
    # 简单的文本解析逻辑
    # 这里需要根据实际的搜索结果格式进行调整
    converted_data = []
    
    try:
        # 尝试从文本中提取结构化信息
        lines = search_result_str.split('\n')
        current_item = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检测标题行（通常以数字开头或包含**）
            if line.startswith(('1.', '2.', '3.', '4.', '5.')) or '**' in line:
                if current_item and current_item.get('title'):
                    converted_data.append(current_item)
                    current_item = {}
                
                # 提取标题
                title = line.replace('**', '').strip()
                if title.startswith(tuple('12345')):
                    title = title[2:].strip()  # 移除序号
                current_item['title'] = title
                
            # 检测URL行
            elif 'http' in line or '来源:' in line:
                if '来源:' in line:
                    url = line.replace('来源:', '').strip()
                else:
                    url = line.strip()
                current_item['url'] = url
                
            # 检测搜索引擎行
            elif '搜索引擎:' in line:
                source = line.replace('搜索引擎:', '').strip()
                current_item['source'] = source
                
            # 其他行作为内容
            elif line and not line.startswith(('#', '=', '-')):
                if 'content' not in current_item:
                    current_item['content'] = line
                else:
                    current_item['content'] += ' ' + line
        
        # 添加最后一个项目
        if current_item and current_item.get('title'):
            converted_data.append(current_item)
        
        # 如果解析失败，创建一个通用项目
        if not converted_data:
            converted_data = [{
                'title': '搜索结果',
                'content': search_result_str[:500],  # 取前500字符
                'url': 'unknown',
                'source': 'search_mcp'
            }]
            
        print(f"✅ 转换完成，共提取 {len(converted_data)} 个项目")
        for i, item in enumerate(converted_data, 1):
            print(f"   [{i}] 标题: {item.get('title', 'N/A')[:50]}...")
            print(f"       内容长度: {len(item.get('content', ''))}")
            
        return converted_data
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        # 返回一个基本的格式
        return [{
            'title': '搜索结果',
            'content': search_result_str[:500] if search_result_str else '',
            'url': 'unknown',
            'source': 'search_mcp'
        }]

def test_integrated_workflow():
    """测试完整的搜索->转换->分析工作流"""
    print("\n" + "="*60)
    print("🚀 测试完整工作流")
    print("="*60)
    
    try:
        from main import comprehensive_search, analysis_mcp
        
        # 步骤1: 执行搜索
        print("\n步骤1: 执行搜索")
        search_result = comprehensive_search("人工智能", days=7, max_results=3)
        print(f"搜索完成，结果长度: {len(search_result) if search_result else 0}")
        
        if not search_result:
            print("❌ 搜索无结果，测试终止")
            return False
        
        # 步骤2: 转换格式
        print("\n步骤2: 转换数据格式")
        converted_data = convert_search_result_to_dict_format(search_result)
        print(f"转换完成，数据项数: {len(converted_data)}")
        
        # 步骤3: 执行分析
        print("\n步骤3: 执行质量分析")
        analysis_result = analysis_mcp("quality", converted_data, "人工智能")
        print(f"分析完成，结果类型: {type(analysis_result)}")
        
        # 步骤4: 解析分析结果
        print("\n步骤4: 解析分析结果")
        try:
            parsed_analysis = json.loads(analysis_result)
            score = parsed_analysis.get('score', 0)
            reasoning = parsed_analysis.get('reasoning', 'N/A')
            
            print(f"✅ 质量评分: {score}/10")
            print(f"✅ 评估理由: {reasoning[:200]}...")
            
            if score > 0:
                print("\n🎉 集成测试成功！搜索结果成功转换并获得了质量评分")
                return True
            else:
                print("\n⚠️ 集成测试部分成功，但质量评分为0")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ 分析结果JSON解析失败: {e}")
            print(f"原始结果: {analysis_result[:300]}...")
            return False
            
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 搜索MCP与分析MCP集成测试")
    print("=" * 80)
    
    # 测试结果统计
    test_results = {
        'search_output_format': False,
        'analysis_input_requirements': False,
        'format_conversion': False,
        'integrated_workflow': False
    }
    
    # 1. 测试搜索MCP输出格式
    search_result, parallel_result = test_search_mcp_output_format()
    test_results['search_output_format'] = search_result is not None
    
    # 2. 测试分析MCP输入要求
    analysis_result1, analysis_result2 = test_analysis_mcp_input_requirements()
    test_results['analysis_input_requirements'] = analysis_result1 is not None
    
    # 3. 测试格式转换
    if search_result:
        converted_data = convert_search_result_to_dict_format(search_result)
        test_results['format_conversion'] = len(converted_data) > 0
    
    # 4. 测试完整工作流
    test_results['integrated_workflow'] = test_integrated_workflow()
    
    # 输出测试总结
    print("\n" + "="*80)
    print("📊 测试结果总结")
    print("="*80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:30} {status}")
    
    print(f"\n总体结果: {passed_tests}/{total_tests} 项测试通过")
    
    if test_results['integrated_workflow']:
        print("\n🎉 问题已解决！搜索MCP和分析MCP现在可以正常协作了")
    else:
        print("\n⚠️ 仍存在集成问题，需要进一步调试")
        
        # 提供解决方案建议
        print("\n💡 解决方案建议:")
        print("1. 修改搜索MCP返回结构化的List[Dict]数据而不是字符串")
        print("2. 在调用分析MCP之前添加数据格式转换步骤")
        print("3. 统一搜索和分析MCP之间的数据接口规范")

if __name__ == "__main__":
    main()