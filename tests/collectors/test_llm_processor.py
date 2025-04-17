#!/usr/bin/env python3
import os
import sys
import argparse
from collectors.tavily_collector import TavilyCollector
from collections import defaultdict
import time

def main():
    """
    测试LLMProcessor与TavilyCollector的集成
    演示使用LLM处理搜索结果与直接硬编码处理的区别
    """
    parser = argparse.ArgumentParser(description='测试使用LLM处理Tavily搜索结果')
    parser.add_argument('--topic', '-t', type=str, default='人工智能', help='要搜索的主题')
    parser.add_argument('--compare', '-c', action='store_true', help='比较LLM处理与直接处理的结果')
    parser.add_argument('--save', '-s', action='store_true', help='保存结果到文件')
    args = parser.parse_args()
    
    topic = args.topic
    print(f"开始为主题 '{topic}' 生成报告...")
    
    # 初始化TavilyCollector
    collector = TavilyCollector()
    
    # 检查是否有必要的API密钥
    if not collector.has_api_key:
        print("错误: 未找到Tavily API密钥。请在config.py中设置TAVILY_API_KEY。")
        return
    
    llm_processor = collector._get_llm_processor()
    if not llm_processor and args.compare:
        print("警告: 未找到OpenAI API密钥，无法使用LLM处理器进行比较。")
        print("请在config.py中设置OPENAI_API_KEY以启用LLM处理功能。")
        args.compare = False
    
    # 创建查询列表
    queries = [
        {"query": f"{topic} 行业概况 市场特点 主要参与者", "section": "行业概况"},
        {"query": f"{topic} 政策支持 监管政策 国家战略", "section": "政策支持"},
        {"query": f"{topic} 市场规模 增长率 市场份额 数据", "section": "市场规模"},
        {"query": f"{topic} 技术趋势 创新 研发方向", "section": "技术趋势"},
        {"query": f"{topic} 未来展望 发展预测 建议", "section": "未来展望"}
    ]
    
    # 收集搜索结果
    print(f"执行{len(queries)}个查询收集信息...")
    raw_results = []
    for query_info in queries:
        query = query_info["query"]
        section = query_info["section"]
        
        print(f"搜索: {query}")
        results = collector.search(query, max_results=3)
        
        for result in results:
            result["section"] = section
        
        raw_results.extend(results)
    
    print(f"总共获取到{len(raw_results)}条搜索结果")
    
    if args.compare:
        # 使用两种不同方法处理结果并比较
        print("\n使用两种方法处理搜索结果进行比较...")
        
        # 1. 使用LLM处理器
        print("\n=== 使用LLM处理器生成报告 ===")
        start_time = time.time()
        llm_report = llm_processor.organize_search_results(raw_results, topic)
        llm_time = time.time() - start_time
        
        # 2. 使用直接处理方法(硬编码规则)
        print("\n=== 使用硬编码方法生成报告 ===")
        start_time = time.time()
        direct_report = collector._direct_integrate_results(raw_results.copy(), topic)
        direct_time = time.time() - start_time
        
        # 比较结果
        print("\n=== 结果比较 ===")
        print(f"LLM处理时间: {llm_time:.2f}秒")
        print(f"直接处理时间: {direct_time:.2f}秒")
        
        # 比较章节数量
        llm_sections = len(llm_report.get("sections", []))
        direct_sections = len(direct_report.get("sections", []))
        print(f"LLM处理章节数: {llm_sections}")
        print(f"直接处理章节数: {direct_sections}")
        
        # 比较内容长度
        llm_content_length = len(llm_report.get("content", ""))
        direct_content_length = len(direct_report.get("content", ""))
        print(f"LLM处理内容长度: {llm_content_length}字符")
        print(f"直接处理内容长度: {direct_content_length}字符")
        
        # 保存结果
        if args.save:
            print("\n保存比较结果到文件...")
            with open(f"{topic}_llm_report.md", "w", encoding="utf-8") as f:
                f.write(llm_report["content"])
            with open(f"{topic}_direct_report.md", "w", encoding="utf-8") as f:
                f.write(direct_report["content"])
            print(f"报告保存在: {topic}_llm_report.md 和 {topic}_direct_report.md")
            
    else:
        # 只使用LLM处理器或直接处理方法
        if llm_processor:
            print("\n使用LLM处理器生成报告...")
            report = llm_processor.organize_search_results(raw_results, topic)
        else:
            print("\n使用直接处理方法生成报告...")
            report = collector._direct_integrate_results(raw_results, topic)
        
        print(f"生成报告完成，包含{len(report.get('sections', []))}个章节，共{len(report.get('content', ''))}字符")
        
        # 保存结果
        if args.save:
            filename = f"{topic}_report.md"
            print(f"\n保存报告到文件: {filename}")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report["content"])
            print(f"报告已保存在: {filename}")
        
        # 显示报告前300个字符预览
        preview = report.get("content", "")[:300] + "..." if len(report.get("content", "")) > 300 else report.get("content", "")
        print("\n报告内容预览:")
        print(preview)

if __name__ == "__main__":
    main() 