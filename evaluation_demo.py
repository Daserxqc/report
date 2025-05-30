#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
报告评估框架演示脚本
展示不同报告类型的自适应评估维度
"""

from report_utils import ReportEvaluator
import json

def demo_evaluation_framework():
    """演示评估框架的功能"""
    
    evaluator = ReportEvaluator()
    
    # 展示不同报告类型的评估维度
    report_types = ["insights", "news", "research"]
    
    print("=" * 60)
    print("报告评估框架 - 自适应评估维度演示")
    print("=" * 60)
    
    for report_type in report_types:
        print(f"\n### {evaluator.report_types[report_type]['name']} 评估维度")
        print(f"描述: {evaluator.report_types[report_type]['description']}")
        print(f"关键特征: {', '.join(evaluator.report_types[report_type]['key_features'])}")
        
        applicable_dims = evaluator.get_applicable_dimensions(report_type)
        
        print(f"\n适用的评估维度 (共{len(applicable_dims)}个):")
        total_weight = sum(dim['weight'] for dim in applicable_dims.values())
        
        for dim_name, dim_info in applicable_dims.items():
            print(f"  • {dim_info['description']} (权重: {dim_info['weight']:.1%})")
            print(f"    标准: {dim_info['criteria']}")
        
        print(f"总权重: {total_weight:.1%}")
        print("-" * 50)
    
    # 演示提示词生成
    print("\n### 提示词生成演示")
    sample_report = """
    # 人工智能行业洞察报告
    
    ## 摘要
    本报告分析了2024年人工智能行业的最新发展趋势...
    
    ## 市场现状
    当前AI市场规模达到...
    
    ## 关键趋势
    1. 大模型技术突破
    2. 行业应用深化
    3. 监管政策完善
    
    ## 投资建议
    建议重点关注...
    """
    
    for report_type in ["insights", "news", "research"]:
        print(f"\n--- {evaluator.report_types[report_type]['name']} 提示词示例 ---")
        prompt = evaluator.generate_evaluation_prompt(
            sample_report, 
            report_type, 
            "人工智能"
        )
        
        # 只显示提示词的前500字符，避免输出过长
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        print(f"完整提示词长度: {len(prompt)} 字符")
        print()

def demo_dimension_comparison():
    """演示不同报告类型的维度差异"""
    
    evaluator = ReportEvaluator()
    
    print("=" * 60)
    print("评估维度对比分析")
    print("=" * 60)
    
    # 获取所有维度
    all_dimensions = set()
    for dim_info in evaluator.evaluation_dimensions.values():
        all_dimensions.add(dim_info['description'])
    
    # 创建对比表
    print(f"{'维度':<12} {'洞察报告':<10} {'行业动态':<10} {'前沿研究':<10}")
    print("-" * 50)
    
    for dim_name, dim_info in evaluator.evaluation_dimensions.items():
        row = f"{dim_info['description']:<12}"
        
        for report_type in ["insights", "news", "research"]:
            if report_type in dim_info["applies_to"]:
                weight = dim_info["weight"][report_type]
                row += f"{weight:>8.1%}  "
            else:
                row += f"{'--':>8}  "
        
        print(row)
    
    print("\n注：'--' 表示该维度不适用于该报告类型")

def demo_weight_analysis():
    """演示权重分析"""
    
    evaluator = ReportEvaluator()
    
    print("=" * 60)
    print("权重分析 - 各报告类型的关注重点")
    print("=" * 60)
    
    for report_type in ["insights", "news", "research"]:
        print(f"\n### {evaluator.report_types[report_type]['name']}")
        applicable_dims = evaluator.get_applicable_dimensions(report_type)
        
        # 按权重排序
        sorted_dims = sorted(
            applicable_dims.items(), 
            key=lambda x: x[1]['weight'], 
            reverse=True
        )
        
        print("权重排序 (从高到低):")
        for i, (dim_name, dim_info) in enumerate(sorted_dims, 1):
            print(f"{i:2d}. {dim_info['description']:<12} {dim_info['weight']:>6.1%}")

if __name__ == "__main__":
    demo_evaluation_framework()
    print("\n" + "=" * 60)
    demo_dimension_comparison() 
    print("\n" + "=" * 60)
    demo_weight_analysis() 