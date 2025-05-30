#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
维度缺失问题调试工具
"""

import sys
import json
import re
sys.path.append('.')
from report_utils import ReportEvaluator

def analyze_llm_response(response_text, report_type="research"):
    """分析LLM响应中的维度情况"""
    print("=" * 60)
    print("LLM响应维度分析")
    print("=" * 60)
    
    evaluator = ReportEvaluator()
    applicable_dims = evaluator.get_applicable_dimensions(report_type)
    
    print(f"期望的维度 ({len(applicable_dims)} 个):")
    for dim_name, dim_info in applicable_dims.items():
        print(f"  - {dim_name} ({dim_info['description']})")
    
    print(f"\n原始响应长度: {len(response_text)} 字符")
    print("响应内容预览:")
    print("-" * 40)
    print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
    print("-" * 40)
    
    # 尝试提取JSON
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    
    if json_start != -1 and json_end > json_start:
        json_text = response_text[json_start:json_end]
        print(f"\n提取的JSON长度: {len(json_text)} 字符")
        
        try:
            parsed_json = json.loads(json_text)
            if "scores" in parsed_json:
                found_dims = list(parsed_json["scores"].keys())
                print(f"\nJSON中找到的维度 ({len(found_dims)} 个):")
                for dim in found_dims:
                    score = parsed_json["scores"][dim].get("score", "N/A")
                    print(f"  - {dim}: {score}分")
                
                # 检查缺失的维度
                missing = [dim for dim in applicable_dims.keys() if dim not in found_dims]
                if missing:
                    print(f"\n缺失的维度 ({len(missing)} 个):")
                    for dim in missing:
                        print(f"  - {dim} ({applicable_dims[dim]['description']})")
                        
                        # 尝试在原始文本中查找相关内容
                        variants = [
                            dim, 
                            dim.replace("_", "_and_"), 
                            dim.replace("_", " "),
                            applicable_dims[dim]["description"]
                        ]
                        
                        for variant in variants:
                            if variant.lower() in response_text.lower():
                                print(f"    在响应中找到变体: '{variant}'")
                                # 尝试提取分数
                                patterns = [
                                    rf'"{re.escape(variant)}"[^}}]*?"score"[：:\s]*(\d+)',
                                    rf"{re.escape(variant)}[：:]\s*(\d+)",
                                    rf"{re.escape(variant)}.*?(\d+)/10"
                                ]
                                for pattern in patterns:
                                    matches = re.findall(pattern, response_text, re.IGNORECASE)
                                    if matches:
                                        print(f"    可能的分数: {matches[0]}")
                                        break
                                break
                else:
                    print("\n✓ 所有维度都已找到!")
                    
            else:
                print("\n❌ JSON中没有找到 'scores' 字段")
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON解析失败: {e}")
            print("JSON文本:")
            print(json_text[:200] + "..." if len(json_text) > 200 else json_text)
    else:
        print("\n❌ 没有找到有效的JSON格式")

def test_with_sample_response():
    """使用示例响应进行测试"""
    # 模拟一个缺失Data_Evidence的响应
    sample_response = '''
{
    "scores": {
        "Structure": {
            "score": 9,
            "reason": "报告结构清晰...",
            "strengths": ["清晰"],
            "weaknesses": ["无"]
        },
        "Coherence": {
            "score": 8,
            "reason": "内容连贯...",
            "strengths": ["连贯"],
            "weaknesses": ["无"]
        },
        "Data_and_Evidence": {
            "score": 9,
            "reason": "数据丰富...",
            "strengths": ["数据多"],
            "weaknesses": ["无"]
        }
    },
    "evaluation": "这是一份优秀的报告",
    "suggestions": ["建议1", "建议2"]
}
'''
    
    print("使用示例响应测试:")
    analyze_llm_response(sample_response)

if __name__ == "__main__":
    test_with_sample_response()
    
    # 可以用于分析实际的LLM响应
    # 如果有实际响应文本，可以取消下面的注释
    # actual_response = """实际的LLM响应文本"""
    # analyze_llm_response(actual_response) 