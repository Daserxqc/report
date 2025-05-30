#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
报告评估工具 - 用于评估已生成的行业报告质量
使用方法: python evaluate_report.py --report 报告文件路径 --type 报告类型 --topic 报告主题
"""

import os
import argparse
from pathlib import Path
from report_utils import ReportEvaluator

def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='行业报告质量评估工具')
    parser.add_argument('--report', '-r', type=str, required=True, help='报告文件路径')
    parser.add_argument('--type', '-t', type=str, default='news', choices=['news', 'insights', 'research'], 
                        help='报告类型 (news:新闻报告, insights:洞察报告, research:研究报告)')
    parser.add_argument('--topic', '-p', type=str, 
                        help='报告主题，如不提供则尝试从文件名猜测')
    
    # 解析参数
    args = parser.parse_args()
    report_path = args.report
    report_type = args.type
    report_topic = args.topic
    
    # 检查报告文件是否存在
    if not os.path.exists(report_path):
        print(f"错误: 报告文件 '{report_path}' 不存在")
        return
    
    # 如果没有提供主题，尝试从文件名猜测
    if not report_topic:
        filename = Path(report_path).stem
        
        # 首先尝试从文件名中识别报告类型
        report_types = {
            "research": ["research", "研究"],
            "news": ["news", "动态", "新闻"],
            "insights": ["insights", "洞察", "趋势"]
        }
        
        # 识别文件名中包含的报告类型
        detected_type = None
        for type_key, indicators in report_types.items():
            for indicator in indicators:
                if indicator in filename.lower():
                    detected_type = type_key
                    break
            if detected_type:
                break
        
        # 如果文件名中包含报告类型，更新报告类型
        if detected_type and report_type == 'news':  # 只在用户未明确指定类型时更新
            report_type = detected_type
            print(f"从文件名检测到报告类型: {report_type}")
        
        # 提取主题
        if "行业" in filename:
            report_topic = filename.split("行业")[0]
        else:
            parts = filename.split("_")
            
            # 移除包含报告类型和日期的部分
            filtered_parts = []
            for part in parts:
                # 检查是否为报告类型关键词
                is_report_type = False
                for type_indicators in report_types.values():
                    if any(indicator in part.lower() for indicator in type_indicators):
                        is_report_type = True
                        break
                
                # 检查是否为日期(包含数字)
                has_digits = any(char.isdigit() for char in part)
                
                # 保留非报告类型且非日期的部分
                if not is_report_type and not has_digits and part.lower() != "report":
                    filtered_parts.append(part)
            
            # 如果过滤后没有部分，使用第一个非日期部分
            if not filtered_parts:
                for part in parts:
                    if not any(char.isdigit() for char in part):
                        filtered_parts.append(part)
                        break
            
            report_topic = "_".join(filtered_parts)
        
        print(f"从文件名猜测报告主题: {report_topic}")
    
    # 读取报告内容
    try:
        with open(report_path, "r", encoding="utf-8-sig") as f:
            report_content = f.read()
    except UnicodeDecodeError:
        try:
            # 尝试使用不同的编码
            with open(report_path, "r", encoding="gbk") as f:
                report_content = f.read()
        except:
            print(f"错误: 无法读取报告文件，请检查文件编码")
            return
    
    print(f"正在评估报告: {report_path}")
    print(f"报告类型: {report_type}")
    print(f"报告主题: {report_topic}")
    print(f"报告长度: {len(report_content)} 字符")
    print("正在进行评估，这可能需要一些时间...")
    
    # 创建评估器并评估报告
    evaluator = ReportEvaluator()
    evaluation = evaluator.evaluate_report(
        report_content=report_content,
        report_type=report_type,
        topic=report_topic
    )
    
    # 检查评估是否成功
    if not evaluation:
        print("错误: 评估失败，未返回有效结果")
        return
    
    if "error" in evaluation:
        print(f"评估过程中发生错误: {evaluation['error']}")
        if "raw_response" in evaluation:
            print(f"原始响应: {evaluation['raw_response'][:500]}...")
        return
    
    # 打印评估结果
    print("\n" + "="*50)
    print(f"报告 '{Path(report_path).name}' 评估结果")
    print("="*50)
    
    print(f"总体评分: {evaluation['overall_score']}/10")
    
    # 显示评估可靠性信息
    if 'score_reliability' in evaluation:
        print(f"评估可靠性: {evaluation['score_reliability']}")
    
    if 'evaluation_attempts' in evaluation:
        print(f"评估尝试次数: {evaluation['evaluation_attempts']}")
    
    if 'missing_dimensions' in evaluation:
        print(f"缺失维度: {evaluation['missing_dimensions']}")
    
    print("\n各维度评分:")
    for dimension, data in evaluation['scores'].items():
        supplemented_mark = " (补充评估)" if data.get('supplemented') else ""
        extracted_mark = " (文本提取)" if data.get('extracted') else ""
        suspicious_mark = " ⚠️ 存疑" if data.get('suspicious') else ""
        print(f"- {dimension}: {data['score']}/10 - {data['reason']}{supplemented_mark}{extracted_mark}{suspicious_mark}")
        
        # 如果有警告信息，显示详细信息
        if data.get('warning'):
            print(f"  ⚠️ 警告: {data['warning']}")
        if data.get('evidence') and data.get('supplemented'):
            print(f"    证据: {data['evidence'][:100]}...")
    
    print(f"\n总体评价: \n{evaluation['evaluation']}")
    
    print(f"\n改进建议: \n{evaluation['suggestions']}")
    
    # 检查是否有可疑评分
    suspicious_dims = [dim for dim, data in evaluation['scores'].items() if data.get('suspicious')]
    if suspicious_dims:
        print(f"\n⚠️ 注意: 以下维度的补充评分可能不够准确，建议重新评估:")
        for dim in suspicious_dims:
            print(f"   - {dim}: {evaluation['scores'][dim]['score']}分")
    
    # 将评估结果保存到文件
    output_path = Path(report_path).with_suffix('.evaluation.txt')
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(f"报告 '{Path(report_path).name}' 评估结果\n")
        f.write("="*50 + "\n")
        f.write(f"总体评分: {evaluation['overall_score']}/10\n")
        
        # 写入评估元信息
        if 'score_reliability' in evaluation:
            f.write(f"评估可靠性: {evaluation['score_reliability']}\n")
        if 'evaluation_attempts' in evaluation:
            f.write(f"评估尝试次数: {evaluation['evaluation_attempts']}\n")
        if 'missing_dimensions' in evaluation:
            f.write(f"缺失维度: {evaluation['missing_dimensions']}\n")
        
        f.write("\n各维度评分:\n")
        for dimension, data in evaluation['scores'].items():
            supplemented_mark = " (补充评估)" if data.get('supplemented') else ""
            extracted_mark = " (文本提取)" if data.get('extracted') else ""
            suspicious_mark = " ⚠️ 存疑" if data.get('suspicious') else ""
            f.write(f"- {dimension}: {data['score']}/10 - {data['reason']}{supplemented_mark}{extracted_mark}{suspicious_mark}\n")
            
            if data.get('warning'):
                f.write(f"  ⚠️ 警告: {data['warning']}\n")
            if data.get('evidence') and data.get('supplemented'):
                f.write(f"    证据: {data['evidence']}\n")
        
        # 写入可疑评分警告
        suspicious_dims = [dim for dim, data in evaluation['scores'].items() if data.get('suspicious')]
        if suspicious_dims:
            f.write(f"\n⚠️ 可疑评分警告:\n")
            f.write(f"以下维度的补充评分可能不够准确，建议重新评估:\n")
            for dim in suspicious_dims:
                f.write(f"   - {dim}: {evaluation['scores'][dim]['score']}分\n")
        
        f.write(f"\n总体评价: \n{evaluation['evaluation']}\n")
        f.write(f"\n改进建议: \n{evaluation['suggestions']}\n")
    
    print(f"\n评估结果已保存至: {output_path}")

if __name__ == "__main__":
    main() 