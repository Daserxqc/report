#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索结果解析工具
用于将字符串格式的搜索结果转换为结构化数据
"""

import re
from typing import List, Dict
import json

def _parse_search_result_string(search_result_string: str) -> List[Dict]:
    """
    解析搜索结果字符串，转换为结构化数据
    
    Args:
        search_result_string: 搜索结果的字符串格式
        
    Returns:
        List[Dict]: 结构化的搜索结果列表
    """
    if not search_result_string or not isinstance(search_result_string, str):
        return []
    
    parsed_results = []
    
    try:
        # 尝试按行分割并解析
        lines = search_result_string.strip().split('\n')
        current_item = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                # 空行表示一个条目结束
                if current_item:
                    parsed_results.append(current_item)
                    current_item = {}
                continue
            
            # 解析不同的字段
            if line.startswith('标题:') or line.startswith('Title:'):
                current_item['title'] = line.split(':', 1)[1].strip()
            elif line.startswith('来源:') or line.startswith('Source:') or line.startswith('URL:'):
                current_item['source'] = line.split(':', 1)[1].strip()
                current_item['url'] = current_item['source']
            elif line.startswith('内容:') or line.startswith('Content:') or line.startswith('摘要:'):
                current_item['content'] = line.split(':', 1)[1].strip()
                current_item['summary'] = current_item['content']
            elif line.startswith('时间:') or line.startswith('Date:'):
                current_item['date'] = line.split(':', 1)[1].strip()
            elif line.startswith('[') and ']' in line:
                # 处理编号格式 [1] 标题: xxx
                if '标题:' in line or 'Title:' in line:
                    current_item['title'] = line.split(':', 1)[1].strip()
                elif '来源:' in line or 'Source:' in line:
                    current_item['source'] = line.split(':', 1)[1].strip()
                    current_item['url'] = current_item['source']
                elif '内容:' in line or 'Content:' in line:
                    current_item['content'] = line.split(':', 1)[1].strip()
                    current_item['summary'] = current_item['content']
            elif '：' in line:  # 中文冒号
                key, value = line.split('：', 1)
                key = key.strip()
                value = value.strip()
                if '标题' in key or 'title' in key.lower():
                    current_item['title'] = value
                elif '来源' in key or 'source' in key.lower() or 'url' in key.lower():
                    current_item['source'] = value
                    current_item['url'] = value
                elif '内容' in key or 'content' in key.lower() or '摘要' in key:
                    current_item['content'] = value
                    current_item['summary'] = value
        
        # 添加最后一个条目
        if current_item:
            parsed_results.append(current_item)
        
        # 如果没有解析到结构化数据，尝试其他方法
        if not parsed_results:
            # 尝试按段落分割
            paragraphs = search_result_string.split('\n\n')
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    parsed_results.append({
                        'title': f'搜索结果 {i+1}',
                        'content': paragraph.strip(),
                        'summary': paragraph.strip()[:200] + '...' if len(paragraph) > 200 else paragraph.strip(),
                        'source': '搜索引擎',
                        'url': ''
                    })
        
        # 确保每个结果都有必要的字段
        for result in parsed_results:
            if 'title' not in result:
                result['title'] = '无标题'
            if 'content' not in result:
                result['content'] = result.get('summary', '')
            if 'summary' not in result:
                result['summary'] = result.get('content', '')[:200] + '...' if len(result.get('content', '')) > 200 else result.get('content', '')
            if 'source' not in result:
                result['source'] = '未知来源'
            if 'url' not in result:
                result['url'] = result.get('source', '')
        
        return parsed_results
        
    except Exception as e:
        print(f"⚠️ 解析搜索结果字符串失败: {e}")
        # 回退方案：将整个字符串作为一个结果
        return [{
            'title': '搜索结果',
            'content': search_result_string,
            'summary': search_result_string[:300] + '...' if len(search_result_string) > 300 else search_result_string,
            'source': '搜索引擎',
            'url': ''
        }]

if __name__ == "__main__":
    # 测试解析功能
    test_string = """
标题: 人工智能发展现状
来源: https://example.com/ai-status
内容: 人工智能技术在近年来取得了显著进展...

标题: 机器学习应用
来源: https://example.com/ml-apps
内容: 机器学习在各个领域都有广泛应用...
    """
    
    results = _parse_search_result_string(test_string)
    print(f"解析得到 {len(results)} 条结果:")
    for i, result in enumerate(results, 1):
        print(f"[{i}] {result['title']} - {result['source']}")