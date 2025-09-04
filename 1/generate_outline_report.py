import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
import sys
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import importlib.util

from collectors.tavily_collector import TavilyCollector
from collectors.brave_search_collector import BraveSearchCollector
from collectors.llm_processor import LLMProcessor
from fix_md_headings import fix_markdown_headings
import config
import logging

# 关闭HTTP请求日志，减少干扰
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class OutlineParser:
    """
    智能大纲解析器
    使用大模型理解和解析用户输入的层级结构大纲
    """
    
    def __init__(self, llm_processor=None):
        self.outline_structure = {}
        self.main_sections = []
        self.llm_processor = llm_processor
        
    def parse_outline(self, outline_text, extracted_topic=None):
        """
        智能解析大纲文本，优先使用LLM理解
        
        Args:
            outline_text (str): 大纲文本
            extracted_topic (str): 已提取的主题（如果有的话）
            
        Returns:
            dict: 解析后的大纲结构
        """
        print("🔍 开始智能解析大纲结构...")
        
        if self.llm_processor:
            print("📖 使用LLM直接理解大纲内容...")
            try:
                # 优先使用LLM完整理解大纲
                structure = self._parse_outline_with_llm_complete(outline_text, extracted_topic)
                if structure:
                    self.outline_structure = structure
                    self.main_sections = list(structure.keys())
                    
                    print(f"✅ LLM大纲解析完成，发现{len(self.main_sections)}个主要章节")
                    for section in self.main_sections:
                        sub_count = len(structure[section]['subsections'])
                        item_count = len(structure[section]['content'])
                        print(f"   - {section}: {sub_count}个子章节, {item_count}个直接内容项")
                    
                    return structure
            except Exception as e:
                print(f"⚠️ LLM解析失败: {str(e)}，尝试备用方法...")
        
        # 如果LLM不可用或失败，使用备用方法
        print("🔄 LLM不可用，使用备用解析方法...")
        structure = self._parse_outline_fallback(outline_text, extracted_topic)
        
        self.outline_structure = structure
        self.main_sections = list(structure.keys())
        
        print(f"✅ 备用解析完成，发现{len(self.main_sections)}个主要章节")
        for section in self.main_sections:
            sub_count = len(structure[section]['subsections'])
            item_count = len(structure[section]['content'])
            print(f"   - {section}: {sub_count}个子章节, {item_count}个直接内容项")
        
        return structure
    
    def _parse_outline_with_llm_complete(self, outline_text, extracted_topic=None):
        """使用LLM完整理解大纲内容"""
        topic_hint = ""
        if extracted_topic:
            topic_hint = f"\n注意：主题 '{extracted_topic}' 已经被识别，请在解析时不要将其重复作为章节处理。"
        
        prompt = f"""请仔细阅读以下大纲内容，理解其完整的层级结构和所有要点。{topic_hint}

大纲内容：
{outline_text}

请按照以下要求解析：

1. **完整理解**：请理解大纲的所有内容，不要遗漏任何要点
2. **层级识别**：识别主要章节和子要点的层级关系
3. **格式统一**：将所有内容转换为标准的JSON结构
4. **要点保留**：每个小要点都很重要，都需要后续搜索资料

请返回以下JSON格式：
{{
    "主要章节1": {{
        "title": "主要章节1",
        "subsections": {{
            "子要点1": {{
                "title": "子要点1",
                "items": []
            }},
            "子要点2": {{
                "title": "子要点2", 
                "items": []
            }}
        }},
        "content": []
    }},
    "主要章节2": {{
        "title": "主要章节2",
        "subsections": {{
            "子要点3": {{
                "title": "子要点3",
                "items": []
            }}
        }},
        "content": []
    }}
}}

**重要说明**：
- 请识别所有的主要章节（如"一、二、三"或类似标记的部分）
- 将每个主要章节下的小要点都识别为subsections
- 即使是简短的词语（如"非语言时代"、"符号与图像"）也是重要的子要点
- 确保不遗漏任何内容
- 只返回有效的JSON，不要包含其他文字

我需要为每个subsection搜索相关资料，所以请确保完整提取所有要点。
"""
        
        system_message = """你是一位专业的文档结构分析师，擅长理解各种格式的大纲和文档结构。
你需要完整理解用户提供的大纲内容，准确识别其层级关系，并转换为标准的JSON格式。
请确保不遗漏任何要点，每个要点都是后续研究的重要基础。
你的回答必须是严格的JSON格式，不包含任何其他文本。"""
        
        try:
            response = self.llm_processor.call_llm_api_json(prompt, system_message)
            
            # 验证响应格式
            if isinstance(response, dict) and self._validate_outline_structure(response):
                print(f"🎯 LLM成功理解大纲，识别了{len(response)}个主要章节")
                # 打印详细的解析结果
                for section, info in response.items():
                    subsection_count = len(info.get('subsections', {}))
                    print(f"   📝 {section}: {subsection_count}个子要点")
                    for sub_title in info.get('subsections', {}):
                        print(f"      - {sub_title}")
                
                return response
            else:
                print("❌ LLM返回的结构格式不正确")
                return None
                
        except Exception as e:
            print(f"❌ LLM完整解析出错: {str(e)}")
            return None
    
    def _parse_outline_with_llm(self, outline_text, extracted_topic=None):
        """使用大模型解析大纲"""
        topic_hint = ""
        if extracted_topic:
            topic_hint = f"\n注意：标题/主题 '{extracted_topic}' 已经被识别，请在解析时忽略它，不要将其作为章节处理。"
        
        prompt = f"""请解析以下大纲文本，提取其层级结构。无论用户使用什么符号或格式，请理解其含义并转换为标准结构。{topic_hint}

大纲文本：
{outline_text}

请将大纲解析为JSON格式，包含以下结构：
{{
    "主要章节标题1": {{
        "title": "主要章节标题1",
        "subsections": {{
            "子章节标题1": {{
                "title": "子章节标题1",
                "items": ["条目1", "条目2", "条目3"]
            }},
            "子章节标题2": {{
                "title": "子章节标题2", 
                "items": ["条目1", "条目2"]
            }}
        }},
        "content": ["直接隶属于主章节的内容项"]
    }},
    "主要章节标题2": {{
        "title": "主要章节标题2",
        "subsections": {{}},
        "content": ["内容项1", "内容项2"]
    }}
}}

解析规则：
1. 识别主要章节（通常是一级标题，如"一、"、"1."、"第一章"等）
2. 识别子章节（通常是二级标题，如"（一）"、"1.1"、"<一>"等）
3. 识别内容项（通常是项目符号、数字列表或缩进内容）
4. 忽略格式符号，提取纯内容
5. 保持层级关系清晰

注意：
- 只返回有效的JSON格式
- 不要包含任何解释性文字
- 确保JSON结构完整且可解析
- 如果某个章节没有子章节，subsections设为空对象{{}}
- 如果某个章节没有直接内容，content设为空数组[]
"""
        
        system_message = """你是一位专业的文档结构分析师，擅长理解各种格式的大纲和层级结构。
你需要准确识别文档的层级关系，无论用户使用什么样的符号或格式。
你的回答必须是严格的JSON格式，不包含任何其他文本。"""
        
        try:
            response = self.llm_processor.call_llm_api_json(prompt, system_message)
            
            # 验证响应格式
            if isinstance(response, dict) and self._validate_outline_structure(response):
                return response
            else:
                print("❌ LLM返回的结构格式不正确")
                return None
                
        except Exception as e:
            print(f"❌ LLM解析出错: {str(e)}")
            return None
    
    def _validate_outline_structure(self, structure):
        """验证解析后的大纲结构是否符合预期格式"""
        if not isinstance(structure, dict):
            return False
            
        for section_title, section_data in structure.items():
            if not isinstance(section_data, dict):
                return False
            
            required_fields = ['title', 'subsections', 'content']
            if not all(field in section_data for field in required_fields):
                return False
                
            if not isinstance(section_data['subsections'], dict):
                return False
                
            if not isinstance(section_data['content'], list):
                return False
                
            # 验证子章节结构
            for sub_title, sub_data in section_data['subsections'].items():
                if not isinstance(sub_data, dict):
                    return False
                if not all(field in sub_data for field in ['title', 'items']):
                    return False
                if not isinstance(sub_data['items'], list):
                    return False
        
        return True
    
    def _parse_outline_fallback(self, outline_text, extracted_topic=None):
        """备用解析方法 - 使用更灵活的规则"""
        lines = outline_text.strip().split('\n')
        structure = {}
        current_main = None
        current_sub = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 如果这行是已提取的主题，跳过它
            # 只跳过完全匹配的主题行，而不是包含主题词的章节标题
            if extracted_topic and (line == extracted_topic or 
                                   line.replace('#', '').strip() == extracted_topic):
                print(f"  🔍 跳过主题行: {line}")
                continue
            
            # 更灵活的主章节匹配
            # 匹配各种可能的主章节格式
            main_patterns = [
                r'^[一二三四五六七八九十]+[、．\.]?\s*(.+)',  # 一、二、三
                r'^[①②③④⑤⑥⑦⑧⑨⑩]+[、．\.]?\s*(.+)',     # ①②③
                r'^[1-9]\d*[、．\.]?\s*(.+)',                # 1、2、3
                r'^第[一二三四五六七八九十]+[章节部分][、．\.]?\s*(.+)',  # 第一章
                r'^[1-9]\d*\.\d*[、．\.]?\s*(.+)',           # 1.1、1.2
                r'^[A-Z][、．\.]?\s*(.+)',                   # A、B、C
            ]
            
            main_match = None
            for pattern in main_patterns:
                main_match = re.match(pattern, line)
                if main_match:
                    break
            
            if main_match:
                current_main = main_match.group(1).strip()
                structure[current_main] = {
                    'title': current_main,
                    'subsections': {},
                    'content': []
                }
                current_sub = None
                continue
            
            # 更灵活的子章节匹配
            sub_patterns = [
                r'^[（\(]\s*[一二三四五六七八九十]+\s*[）\)]\s*(.+)',  # （一）
                r'^[（\(]\s*[1-9]\d*\s*[）\)]\s*(.+)',              # （1）
                r'^[<＜]\s*[一二三四五六七八九十]+\s*[>＞]\s*(.+)',    # <一>
                r'^[【\[]\s*[一二三四五六七八九十]+\s*[】\]]\s*(.+)',  # 【一】
                r'^[1-9]\d*\.[1-9]\d*[、．\.]?\s*(.+)',             # 1.1、1.2
                r'^[a-zA-Z]\)\s*(.+)',                             # a) b) c)
            ]
            
            sub_match = None
            for pattern in sub_patterns:
                sub_match = re.match(pattern, line)
                if sub_match:
                    break
                    
            if sub_match and current_main:
                current_sub = sub_match.group(1).strip()
                structure[current_main]['subsections'][current_sub] = {
                    'title': current_sub,
                    'items': []
                }
                continue
            
            # 更灵活的项目符号匹配
            item_patterns = [
                r'^[\*\-\+•·]\s*(.+)',                 # * - + • ·
                r'^[1-9]\d*[\.。)]\s*(.+)',            # 1. 2. 3.
                r'^[a-zA-Z][\.。)]\s*(.+)',            # a. b. c.
                r'^[①②③④⑤⑥⑦⑧⑨⑩]+\s*(.+)',           # ①②③
                r'^→\s*(.+)',                          # →
                r'^▪\s*(.+)',                          # ▪
                r'^○\s*(.+)',                          # ○
            ]
            
            item_match = None
            for pattern in item_patterns:
                item_match = re.match(pattern, line)
                if item_match:
                    break
                    
            if item_match and current_main:
                item_text = item_match.group(1).strip()
                if current_sub and current_sub in structure[current_main]['subsections']:
                    structure[current_main]['subsections'][current_sub]['items'].append(item_text)
                else:
                    structure[current_main]['content'].append(item_text)
                continue
            
            # 处理缩进内容（更灵活）
            if (line.startswith('　') or line.startswith('    ') or 
                line.startswith('\t') or line.startswith('  ')):
                cleaned_line = line.lstrip('　 \t')
                if current_main and cleaned_line:
                    if current_sub and current_sub in structure[current_main]['subsections']:
                        structure[current_main]['subsections'][current_sub]['items'].append(cleaned_line)
                    else:
                        structure[current_main]['content'].append(cleaned_line)
                continue
            
            # 如果都不匹配，但有当前主章节，则作为内容项添加
            if current_main and line:
                # 增强对简单列表格式的支持
                # 如果行看起来像是一个要点（短且描述性），创建为子章节
                if (len(line) <= 20 and 
                    not any(char in line for char in ['。', '！', '？', '，', '；']) and
                    not line.startswith(('第', '本', '该', '这', '那', '在', '是', '有', '从', '对', '由', '被', '与', '为', '就', '都', '也', '还', '只', '更', '最', '很', '非常'))):
                    # 创建为子章节
                    structure[current_main]['subsections'][line] = {
                        'title': line,
                        'items': []
                    }
                    print(f"  📝 识别为子章节: {line}")
                else:
                    # 否则作为内容项
                    if current_sub and current_sub in structure[current_main]['subsections']:
                        structure[current_main]['subsections'][current_sub]['items'].append(line)
                    else:
                        structure[current_main]['content'].append(line)
        
        return structure

class OutlineDataCollector:
    """
    基于大纲的数据收集器
    负责为每个章节收集相关数据
    """
    
    def __init__(self, llm_processor=None):
        self.results_lock = threading.Lock()
        self.llm_processor = llm_processor
        
        # 初始化搜索收集器
        self.collectors = {}
        
        # Tavily收集器（必需）
        try:
            self.tavily_collector = TavilyCollector()
            self.collectors['tavily'] = self.tavily_collector
            print("✅ Tavily搜索收集器已初始化")
        except Exception as e:
            print(f"❌ Tavily搜索收集器初始化失败: {str(e)}")
            raise
        
        # Brave收集器（可选）
        try:
            self.brave_collector = BraveSearchCollector()
            if hasattr(self.brave_collector, 'has_api_key') and self.brave_collector.has_api_key:
                self.collectors['brave'] = self.brave_collector
                print("✅ Brave搜索收集器已启用")
            else:
                print("⚠️ Brave搜索收集器未配置API密钥，已跳过")
        except Exception as e:
            print(f"⚠️ Brave搜索收集器初始化失败: {str(e)}")
        
        # 初始化数据筛选处理器
        from collectors.data_filter_processor import DataFilterProcessor
        self.data_filter = DataFilterProcessor(llm_processor=llm_processor)
        print("✅ 数据筛选处理器已初始化")
    
    def parallel_collect_main_sections(self, outline_structure, topic, target_audience="通用", max_workers=4):
        """
        并行收集主要章节的数据
        
        Args:
            outline_structure (dict): 大纲结构
            topic (str): 主题
            target_audience (str): 目标受众
            max_workers (int): 最大并行工作数
            
        Returns:
            dict: 按章节组织的数据结果
        """
        print(f"🚀 [并行收集] 开始并行收集{len(outline_structure)}个主要章节的数据...")
        start_time = time.time()
        
        sections_data = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 🚀 并行提交主要章节任务
            future_to_section = {
                executor.submit(
                    self._collect_section_data, topic, section_title, section_info, target_audience
                ): section_title for section_title, section_info in outline_structure.items()
            }
            
            # 🔄 收集章节结果
            completed_count = 0
            for future in as_completed(future_to_section):
                section_title = future_to_section[future]
                try:
                    section_data = future.result()
                    completed_count += 1
                    
                    with self.results_lock:
                        sections_data[section_title] = section_data
                    
                    print(f"  ✅ [{completed_count}/{len(outline_structure)}] 章节'{section_title}'收集完成，获得{len(section_data)}条数据")
                    
                except Exception as e:
                    print(f"  ❌ 章节'{section_title}'收集失败: {str(e)}")
                    sections_data[section_title] = []
        
        total_time = time.time() - start_time
        total_items = sum(len(data) for data in sections_data.values())
        print(f"📊 [并行收集完成] 总计收集{total_items}条数据，耗时{total_time:.1f}秒")
        
        return sections_data
    
    def _collect_section_data(self, topic, section_title, section_info, target_audience):
        """收集单个章节的数据"""
        print(f"  🔍 开始收集章节'{section_title}'的数据...")
        
        # 生成搜索查询
        queries = self._generate_section_queries(topic, section_title, section_info, target_audience)
        
        raw_results = []
        seen_urls = set()
        
        # 串行执行查询（避免过度并行）
        for query in queries:
            try:
                query_results = self._execute_single_query(query)
                
                # 去重并添加到结果
                for result in query_results:
                    url = result.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        result["section"] = section_title
                        result["source_query"] = query
                        raw_results.append(result)
                        
            except Exception as e:
                print(f"    ❌ 查询失败: {str(e)}")
                continue
        
        print(f"  📊 收集到 {len(raw_results)} 条原始数据，开始质量筛选...")
        
        # 转换为DataSource对象
        data_sources = self._convert_to_data_sources(raw_results)
        
        # 使用DataFilterProcessor筛选数据
        try:
            filtered_data = self.data_filter.filter_and_score_data(
                data_sources=data_sources,
                topic=topic,
                section_title=section_title,
                min_score=0.6  # 可调整的最低分数阈值
            )
            
            print(f"  ✅ 筛选完成，{len(filtered_data)} 条数据通过筛选")
            return filtered_data
            
        except Exception as e:
            print(f"  ⚠️ 数据筛选失败: {str(e)}，返回原始数据")
            # 如果筛选失败，返回简单处理的原始数据
            if len(raw_results) > 10:
                raw_results.sort(key=lambda x: len(x.get("content", "")), reverse=True)
                raw_results = raw_results[:10]
            return raw_results
    
    def _generate_section_queries(self, topic, section_title, section_info, target_audience):
        """为特定章节生成搜索查询"""
        if self.llm_processor:
            return self._generate_queries_with_llm(topic, section_title, section_info, target_audience)
        else:
            return self._generate_queries_fallback(topic, section_title, section_info, target_audience)
    
    def _generate_queries_with_llm(self, topic, section_title, section_info, target_audience):
        """使用LLM生成智能搜索查询"""
        try:
            # 构建子章节信息
            subsections_text = ""
            if section_info.get('subsections'):
                subsections_text = "子章节：\n"
                for sub_title, sub_data in section_info['subsections'].items():
                    subsections_text += f"- {sub_title}\n"
                    if sub_data.get('items'):
                        for item in sub_data['items'][:3]:  # 限制显示数量
                            subsections_text += f"  * {item}\n"
            
            # 构建直接内容信息
            content_text = ""
            if section_info.get('content'):
                content_text = "主要内容：\n"
                for item in section_info['content'][:5]:  # 限制显示数量
                    content_text += f"- {item}\n"
            
            # 计算查询数量
            subsection_count = len(section_info.get('subsections', {}))
            content_count = len(section_info.get('content', []))
            
            # 动态调整查询数量
            if subsection_count > 3 or content_count > 3:
                query_count = "12-15"
                max_queries = 15
            elif subsection_count > 1 or content_count > 1:
                query_count = "10-12"
                max_queries = 12
            else:
                query_count = "8-10"
                max_queries = 10
            
            prompt = f"""请为以下章节生成{query_count}个最有效的搜索查询，用于收集相关资料：

主题：{topic}
章节标题：{section_title}
目标受众：{target_audience}

{subsections_text}
{content_text}

**重要要求**：
- 必须为每个子章节/要点生成至少2个专门的查询
- 确保所有列出的子章节和内容项都有对应的搜索查询
- 不要遗漏任何要点

请生成针对性强、多样化的搜索查询，包括：
1. 基础概念和定义类查询
2. 技术原理和机制类查询
3. 应用案例和实践类查询
4. 发展趋势和前沿类查询
5. 针对特定受众的查询
6. **每个子章节/要点的专门查询**

目标受众特点：
- 高校学生：注重教学、学习、基础原理
- 企业从业者：注重实践、应用、商业价值
- AI爱好者：注重前沿技术、最新发展
- 通用：平衡各方面需求

请以JSON格式返回查询列表：
{{
    "queries": [
        "查询1",
        "查询2",
        "查询3",
        "查询4",
        "查询5",
        "查询6",
        "查询7",
        "查询8",
        "查询9",
        "查询10",
        "查询11",
        "查询12"
    ]
}}

注意：
- 查询应简洁明确，适合搜索引擎
- 避免重复，确保多样性
- 考虑中英文搜索的需要
- 查询长度控制在10-30个字符
- 确保每个要点都有对应的查询
"""
            
            system_message = f"""你是一位专业的{topic}领域专家和搜索策略专家。
你需要根据给定的章节信息和目标受众，生成最有效的搜索查询。
你的回答必须是严格的JSON格式，不包含任何其他文本。"""
            
            response = self.llm_processor.call_llm_api_json(prompt, system_message)
            
            if isinstance(response, dict) and 'queries' in response:
                queries = response['queries']
                if isinstance(queries, list) and len(queries) > 0:
                    print(f"    📊 LLM为章节'{section_title}'生成{len(queries)}个查询")
                    return queries[:max_queries]  # 使用动态数量
            
        except Exception as e:
            print(f"❌ LLM生成搜索查询失败: {str(e)}")
        
        # 失败时使用备用方法
        return self._generate_queries_fallback(topic, section_title, section_info, target_audience)
    
    def _generate_queries_fallback(self, topic, section_title, section_info, target_audience):
        """备用查询生成方法 - 优化版，确保每个小点都有查询"""
        queries = []
        
        # 基于章节标题的查询（优先级最高）
        queries.append(f"{topic} {section_title}")
        queries.append(f"{topic} {section_title} 详解")
        
        # 基于子章节的查询（每个子章节都要有查询）
        for sub_title in section_info.get('subsections', {}):
            queries.append(f"{topic} {sub_title}")
            queries.append(f"{section_title} {sub_title}")
            queries.append(f"{topic} {sub_title} 发展")  # 增加变化
        
        # 基于内容项的查询（确保每个要点都有）
        for item in section_info.get('content', []):
            if len(item) > 3:  # 降低过滤阈值
                queries.append(f"{topic} {item}")
                queries.append(f"{section_title} {item}")
        
        # 根据目标受众调整查询
        audience_queries = []
        if target_audience == "高校学生":
            audience_queries.extend([
                f"{topic} {section_title} 教学 学习",
                f"{topic} {section_title} 基础 原理"
            ])
        elif target_audience == "企业从业者":
            audience_queries.extend([
                f"{topic} {section_title} 实践 应用",
                f"{topic} {section_title} 商业 案例"
            ])
        elif target_audience == "AI爱好者":
            audience_queries.extend([
                f"{topic} {section_title} 前沿 技术",
                f"{topic} {section_title} 最新 发展"
            ])
        
        # 合并所有查询
        all_queries = queries + audience_queries
        
        # 去重但保持顺序
        unique_queries = []
        seen = set()
        for q in all_queries:
            if q not in seen:
                unique_queries.append(q)
                seen.add(q)
        
        # 根据章节复杂度调整查询数量
        subsection_count = len(section_info.get('subsections', {}))
        content_count = len(section_info.get('content', []))
        
        # 动态调整查询数量
        if subsection_count > 3 or content_count > 3:
            max_queries = 15  # 复杂章节允许更多查询
        elif subsection_count > 1 or content_count > 1:
            max_queries = 12  # 中等复杂度
        else:
            max_queries = 8   # 简单章节
        
        print(f"    📊 为章节'{section_title}'生成{len(unique_queries[:max_queries])}个查询（子章节:{subsection_count}, 内容项:{content_count}）")
        
        return unique_queries[:max_queries]
    
    def _execute_single_query(self, query):
        """执行单个查询"""
        search_results = []
        used_urls = set()
        
        for name, collector in self.collectors.items():
            try:
                if name == 'tavily':
                    results = collector.search(query, max_results=3)
                elif name == 'brave':
                    results = collector.search(query, count=3)
                else:
                    continue
                    
                if results:
                    for result in results:
                        url = result.get('url', '')
                        if url and url not in used_urls:
                            result['search_source'] = name
                            search_results.append(result)
                            used_urls.add(url)
                            
            except Exception:
                continue
        
        return search_results
    
    def _convert_to_data_sources(self, raw_results):
        """将原始搜索结果转换为DataSource对象"""
        from collectors.data_filter_processor import DataSource
        
        data_sources = []
        
        for result in raw_results:
            try:
                # 确定来源类型
                source_type = self._determine_source_type(result)
                
                # 提取发布日期
                publish_date = self._extract_publish_date(result)
                
                # 创建DataSource对象，保留搜索来源信息
                data_source = DataSource(
                    content=result.get('content', ''),
                    url=result.get('url', ''),
                    title=result.get('title', ''),
                    source_type=source_type,
                    publish_date=publish_date,
                    author=result.get('author', None)
                )
                
                # 保存搜索来源信息到域名字段，用于后续分组
                if 'search_source' in result:
                    data_source.domain = f"{result['search_source']}.search_engine"
                
                data_sources.append(data_source)
                
            except Exception as e:
                print(f"    ⚠️ 转换数据源失败: {str(e)}")
                continue
        
        return data_sources
    
    def _determine_source_type(self, result):
        """确定数据源类型"""
        url = result.get('url', '').lower()
        
        # 学术来源
        if any(domain in url for domain in ['arxiv.org', 'ieee.org', 'acm.org', 'springer.com', 'nature.com']):
            return 'academic'
        
        # 新闻来源
        if any(domain in url for domain in ['news', 'reuters', 'bloomberg', 'xinhua', 'people.com']):
            return 'news'
        
        # 市场研究
        if any(domain in url for domain in ['market', 'research', 'report', 'analysis']):
            return 'market'
        
        # 默认为网页
        return 'web'
    
    def _extract_publish_date(self, result):
        """提取发布日期"""
        # 尝试从多个可能的字段提取日期
        date_fields = ['published_date', 'publish_date', 'date', 'published']
        
        for field in date_fields:
            if field in result and result[field]:
                date_str = result[field]
                try:
                    # 尝试不同的日期格式
                    import re
                    from datetime import datetime
                    
                    # 匹配YYYY-MM-DD格式
                    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', str(date_str))
                    if date_match:
                        return f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                    
                    # 匹配YYYY/MM/DD格式
                    date_match = re.search(r'(\d{4})/(\d{2})/(\d{2})', str(date_str))
                    if date_match:
                        return f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                    
                except:
                    continue
        
        return None

class OutlineContentGenerator:
    """
    基于大纲的内容生成器
    负责生成章节内容
    """
    
    def __init__(self, llm_processor):
        self.llm_processor = llm_processor
        self.results_lock = threading.Lock()
    
    def parallel_generate_main_sections(self, outline_structure, sections_data, topic, target_audience="通用", max_workers=3):
        """
        并行生成主要章节的内容
        
        Args:
            outline_structure (dict): 大纲结构
            sections_data (dict): 收集的数据
            topic (str): 主题
            target_audience (str): 目标受众
            max_workers (int): 最大并行工作数
            
        Returns:
            dict: 生成的章节内容
        """
        print(f"⚡ [并行生成] 开始并行生成{len(outline_structure)}个主要章节的内容...")
        start_time = time.time()
        
        generated_sections = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 🚀 并行提交章节内容生成任务
            future_to_section = {}
            
            for section_title, section_info in outline_structure.items():
                section_data = sections_data.get(section_title, [])
                future_to_section[executor.submit(
                    self._generate_section_content, 
                    section_title, section_info, section_data, topic, target_audience
                )] = section_title
            
            # 🔄 收集生成结果
            completed_count = 0
            for future in as_completed(future_to_section):
                section_title = future_to_section[future]
                try:
                    section_content = future.result()
                    completed_count += 1
                    
                    with self.results_lock:
                        generated_sections[section_title] = section_content
                    
                    content_length = len(section_content) if section_content else 0
                    print(f"  ✅ [{completed_count}/{len(future_to_section)}] 章节'{section_title}'内容生成完成，长度{content_length}字符")
                    
                except Exception as e:
                    print(f"  ❌ 章节'{section_title}'内容生成失败: {str(e)}")
                    generated_sections[section_title] = ""
        
        total_time = time.time() - start_time
        total_length = sum(len(content) for content in generated_sections.values())
        print(f"📊 [并行生成完成] 总计生成{total_length}字符内容，耗时{total_time:.1f}秒")
        
        return generated_sections
    
    def _generate_section_content(self, section_title, section_info, section_data, topic, target_audience):
        """生成单个章节的内容（串行处理子章节）"""
        if not self.llm_processor:
            return self._generate_simple_section_content(section_title, section_info, section_data)
        
        try:
            # 根据目标受众调整语言风格
            audience_style = self._get_audience_style(target_audience)
            
            # 串行生成子章节内容
            subsection_contents = []
            
            # 评估主章节复杂度并分配字数
            main_complexity = self._assess_section_complexity(section_title, section_info, topic)
            main_word_req = self._get_word_count_requirements(main_complexity)
            
            # 计算子章节字数分配
            subsection_count = len(section_info.get('subsections', {}))
            if subsection_count > 0:
                # 为概述预留字数
                overview_words = {"high": 500, "medium": 350, "low": 250}[main_complexity]
                # 剩余字数分配给子章节
                available_words = main_word_req['min_words'] - overview_words
                words_per_subsection = max(300, available_words // subsection_count)
                
                print(f"  📊 主章节复杂度: {main_complexity.upper()}, 总预算: {main_word_req['min_words']}字")
                print(f"  📋 {subsection_count}个子章节，每个分配约{words_per_subsection}字")
            
            # 处理子章节
            for sub_title, sub_info in section_info.get('subsections', {}).items():
                allocated_words = words_per_subsection if subsection_count > 0 else None
                sub_content = self._generate_subsection_content(
                    sub_title, sub_info, section_data, topic, audience_style, allocated_words
                )
                subsection_contents.append({
                    'title': sub_title,
                    'content': sub_content
                })
                
            # 生成主章节内容
            main_content = self._generate_main_section_content(
                section_title, section_info, subsection_contents, section_data, topic, audience_style
            )
            
            return main_content
            
        except Exception as e:
            print(f"⚠️ LLM生成章节'{section_title}'内容失败: {str(e)}，使用简单方法")
            return self._generate_simple_section_content(section_title, section_info, section_data)
    
    def _get_audience_style(self, target_audience):
        """获取目标受众的语言风格"""
        styles = {
            "高校学生": {
                "tone": "教学式、循序渐进",
                "complexity": "中等，注重概念解释",
                "examples": "学术案例和实验",
                "language": "清晰准确，适量专业术语"
            },
            "企业从业者": {
                "tone": "实用性强、解决方案导向",
                "complexity": "高，注重实际应用",
                "examples": "商业案例和最佳实践",
                "language": "商业化表达，注重ROI和效益"
            },
            "AI爱好者": {
                "tone": "前沿探索、技术深入",
                "complexity": "高，注重技术细节",
                "examples": "最新研究和技术突破",
                "language": "技术性强，可使用专业术语"
            },
            "通用": {
                "tone": "平衡性、易于理解",
                "complexity": "中等，兼顾深度和广度",
                "examples": "多样化案例",
                "language": "通俗易懂，适度专业"
            }
        }
        
        return styles.get(target_audience, styles["通用"])
    
    def _assess_section_complexity(self, section_title, section_info, topic):
        """评估章节复杂度"""
        complexity_score = 0
        
        # 1. 子章节数量 (权重: 25%) - 降低权重，让内容要点数量更重要
        subsection_count = len(section_info.get('subsections', {}))
        if subsection_count >= 5:
            complexity_score += 25
        elif subsection_count >= 3:
            complexity_score += 18
        else:
            complexity_score += 10
        
        # 2. 内容要点数量 (权重: 25%) - 增加权重，细化阈值
        total_items = 0
        for sub_info in section_info.get('subsections', {}).values():
            total_items += len(sub_info.get('items', []))
        
        if total_items >= 20:  # 20个以上要点 = 高复杂度
            complexity_score += 25
        elif total_items >= 15:  # 15-19个要点 = 中高复杂度
            complexity_score += 20
        elif total_items >= 10:  # 10-14个要点 = 中等复杂度
            complexity_score += 15
        else:  # <10个要点 = 低复杂度
            complexity_score += 10
        
        # 3. 技术关键词密度 (权重: 25%)
        tech_keywords = [
            '算法', '架构', '模型', '技术', '方法', '系统', '框架', '机制', '原理', '策略',
            '优化', '实现', '设计', '开发', '部署', '评估', '分析', '处理', '计算', '数据'
        ]
        
        text_content = f"{section_title} {' '.join(section_info.get('content', []))}"
        for sub_info in section_info.get('subsections', {}).values():
            text_content += f" {' '.join(sub_info.get('items', []))}"
        
        tech_count = sum(1 for keyword in tech_keywords if keyword in text_content)
        
        if tech_count >= 8:
            complexity_score += 25
        elif tech_count >= 5:
            complexity_score += 20
        elif tech_count >= 3:
            complexity_score += 15
        else:
            complexity_score += 10
        
        # 4. 标题长度和复杂性 (权重: 25%)
        title_length = len(section_title)
        if title_length >= 15:
            complexity_score += 25
        elif title_length >= 10:
            complexity_score += 20
        else:
            complexity_score += 15
        
        # 根据复杂度分数分类
        if complexity_score >= 80:
            return "high"  # 高复杂度
        elif complexity_score >= 60:
            return "medium"  # 中等复杂度
        else:
            return "low"  # 低复杂度
    
    def _get_word_count_requirements(self, complexity):
        """根据复杂度获取字数要求"""
        requirements = {
            "high": {
                "min_words": 3500,
                "max_words": 5000,
                "max_tokens": 8000,
                "description": "高复杂度内容，需要深入详细的分析"
            },
            "medium": {
                "min_words": 2500,
                "max_words": 3500,
                "max_tokens": 6000,
                "description": "中等复杂度内容，平衡深度与广度"
            },
            "low": {
                "min_words": 2000,
                "max_words": 3000,
                "max_tokens": 5000,
                "description": "基础复杂度内容，注重清晰性"
            }
        }
        
        return requirements.get(complexity, requirements["medium"])
    
    def _generate_subsection_content(self, sub_title, sub_info, section_data, topic, audience_style, allocated_words=None):
        """生成子章节内容"""
        items = sub_info.get('items', [])
        
        # 如果有分配的字数，使用分配值；否则使用单独评估
        if allocated_words:
            word_req = {
                'min_words': max(300, int(allocated_words * 0.8)),  # 最少300字
                'max_words': min(2000, int(allocated_words * 1.2)), # 最多2000字
                'max_tokens': min(4000, int(allocated_words * 2)),
                'description': f"分配字数约{allocated_words}字"
            }
            complexity = "allocated"  # 标记为分配模式
        else:
            # 后备方案：单独评估子章节复杂度
            section_info = {'subsections': {sub_title: sub_info}, 'content': items}
            complexity = self._assess_section_complexity(sub_title, section_info, topic)
            word_req = self._get_word_count_requirements(complexity)
        
        # 显示字数分配信息
        if allocated_words:
            print(f"  📝 子章节'{sub_title}' - 分配字数: {allocated_words}字 (范围: {word_req['min_words']}-{word_req['max_words']}字)")
        else:
            print(f"  📝 子章节'{sub_title}' - 复杂度: {complexity.upper()}, 目标字数: {word_req['min_words']}-{word_req['max_words']}字")
        
        # 准备参考数据和引用信息
        reference_content = self._prepare_reference_content(section_data, sub_title)
        citations = self._prepare_citations(section_data)
        
        # 构建子章节内容生成提示
        prompt = f"""请为"{topic}"主题下的子章节"{sub_title}"生成详细内容。

子章节要点：
{chr(10).join(f"- {item}" for item in items)}

目标受众：{audience_style['tone']}
复杂度：{audience_style['complexity']}
语言风格：{audience_style['language']}

内容长度要求：{word_req['description']}

{reference_content}

请生成一个结构清晰、内容详实的子章节，包括：
1. 核心概念解释
2. 关键要点分析
3. 实际应用或案例
4. 图表建议（如果适用）
5. 与其他概念的关联

要求：
- 字数控制在{word_req['min_words']}-{word_req['max_words']}字
- 使用标准Markdown格式
- 根据目标受众调整语言难度
- 在适当位置标注"[建议插入图表：图表描述]"
- 在适当位置标注"[建议插入案例：案例描述]"
- 重要：不要在内容开头添加标题，内容将自动添加到相应的章节标题下
- 如果需要使用小节标题，请使用四级标题（####）格式
- 严格禁止使用中文符号作为标题标记：
  * 不要使用：一、二、三、四、五...
  * 不要使用：（一）、（二）、（三）...
  * 不要使用：<一>、<二>、<三>...
  * 不要使用：【一】、【二】、【三】...
  * 不要使用：①②③④⑤...
  * 不要使用：1.、2.、3.作为标题
- 所有标题必须使用Markdown格式：#### 标题名称
- **重要**：在引用参考资料时，请使用相应的引用标记，如[1]、[2]等

根据字数要求生成相应长度的内容，确保信息丰富且逻辑清晰。
"""
        
        system_message = f"你是一位专业的{topic}领域专家和内容创作者，擅长为不同受众创作高质量的技术内容。请直接输出内容，不要添加章节标题。严格遵守Markdown格式规范，所有标题必须使用#号标记。根据指定的字数要求生成相应长度的内容。确保在适当位置包含引用标记。"
        
        content = self.llm_processor.call_llm_api(prompt, system_message, temperature=0.3, max_tokens=word_req['max_tokens'])
        
        # 在内容末尾添加引用信息（如果有）
        if citations:
            content += f"\n\n{citations}"
        
        return content
    
    def _prepare_reference_content(self, section_data, current_section):
        """准备参考内容用于LLM生成"""
        if not section_data:
            return ""
        
        # 处理不同的数据格式
        if isinstance(section_data, list) and len(section_data) > 0:
            # 检查是否是FilteredData对象
            if hasattr(section_data[0], 'selected_excerpts'):
                # 新的FilteredData格式
                reference_parts = []
                for i, filtered_data in enumerate(section_data[:5]):  # 最多5个参考源
                    if filtered_data.selected_excerpts:
                        source_info = f"来源{i+1}: {filtered_data.source.title}"
                        excerpts = '\n'.join(f"- {excerpt}" for excerpt in filtered_data.selected_excerpts[:3])
                        reference_parts.append(f"{source_info}\n{excerpts}")
                
                if reference_parts:
                    return f"""
参考资料摘录：
{chr(10).join(reference_parts)}

请在生成内容时合理引用这些资料，使用[1]、[2]等标记。
"""
            else:
                # 原始格式
                reference_parts = []
                for i, data in enumerate(section_data[:5]):
                    if data.get('content'):
                        content_snippet = data['content'][:200] + '...' if len(data['content']) > 200 else data['content']
                        reference_parts.append(f"来源{i+1}: {data.get('title', '未知标题')}\n- {content_snippet}")
                
                if reference_parts:
                    return f"""
参考资料摘录：
{chr(10).join(reference_parts)}

请在生成内容时合理引用这些资料，使用[1]、[2]等标记。
"""
        
        return ""
    
    def _prepare_citations(self, section_data):
        """准备引用信息"""
        if not section_data:
            return ""
        
        citations = []
        
        # 处理不同的数据格式
        if isinstance(section_data, list) and len(section_data) > 0:
            # 检查是否是FilteredData对象
            if hasattr(section_data[0], 'source'):
                # 新的FilteredData格式
                for i, filtered_data in enumerate(section_data[:5]):  # 最多5个参考源
                    citation = f"[{i+1}] {filtered_data.source.title}"
                    if filtered_data.source.url:
                        citation += f" - {filtered_data.source.url}"
                    if filtered_data.source.publish_date:
                        citation += f" ({filtered_data.source.publish_date})"
                    
                    # 添加质量评分信息
                    score = filtered_data.quality_score.total_score
                    citation += f" [评分: {score:.2f}]"
                    
                    citations.append(citation)
            else:
                # 原始格式
                for i, data in enumerate(section_data[:5]):
                    citation = f"[{i+1}] {data.get('title', '未知标题')}"
                    if data.get('url'):
                        citation += f" - {data['url']}"
                    citations.append(citation)
        
        if citations:
            return "**参考资料：**\n" + '\n'.join(citations)
        
        return ""
    
    def _generate_main_section_content(self, section_title, section_info, subsection_contents, section_data, topic, audience_style):
        """生成主章节内容"""
        # 构建主章节内容 - 使用二级标题（##）而不是一级标题
        main_content = f"## {section_title}\n\n"
        
        # 评估章节复杂度
        complexity = self._assess_section_complexity(section_title, section_info, topic)
        word_req = self._get_word_count_requirements(complexity)
        
        # 根据复杂度调整概述长度
        overview_length = {
            "high": "400-600字",
            "medium": "300-400字", 
            "low": "200-300字"
        }
        
        # 添加章节概述
        overview_prompt = f"""请为"{topic}"主题下的主章节"{section_title}"生成一个详细的概述段落。

章节包含的子章节：
{chr(10).join(f"- {sub['title']}" for sub in subsection_contents)}

目标受众：{audience_style['tone']}
语言风格：{audience_style['language']}
章节复杂度：{complexity.upper()} ({word_req['description']})

请生成一个{overview_length[complexity]}的概述，介绍本章节的主要内容和重要性。
根据复杂度要求：
{complexity == "high" and "- 深入介绍技术背景和前沿发展\n- 详细说明各子章节的关联性\n- 强调技术原理和应用价值" or ""}
{complexity == "medium" and "- 平衡介绍基础概念和应用场景\n- 说明各子章节的逻辑关系\n- 突出实际价值和发展趋势" or ""}
{complexity == "low" and "- 简明介绍核心概念\n- 概述主要内容结构\n- 强调基础性和实用性" or ""}

注意：生成普通段落文本，不要添加任何标题标记。
"""
        
        overview_max_tokens = {
            "high": 1200,
            "medium": 800,
            "low": 600
        }
        
        try:
            overview = self.llm_processor.call_llm_api(overview_prompt, 
                f"你是一位专业的{topic}领域专家，擅长生成清晰的段落文本。", 
                temperature=0.3, max_tokens=overview_max_tokens[complexity])
            main_content += f"{overview}\n\n"
        except:
            main_content += f"本章节将详细介绍{section_title}的相关内容。\n\n"
        
        # 添加子章节内容 - 使用三级标题（###）
        for sub_content in subsection_contents:
            # 清理子章节标题，确保格式正确
            clean_title = self._clean_section_title(sub_content['title'])
            main_content += f"### {clean_title}\n\n"
            
            # 处理子章节内容，确保内部标题层级正确
            clean_content = self._normalize_content_headings(sub_content['content'])
            main_content += f"{clean_content}\n\n"
        
        # 添加直接内容项
        if section_info.get('content'):
            main_content += "### 补充要点\n\n"
            for item in section_info['content']:
                main_content += f"- {item}\n"
            main_content += "\n"
        
        # 添加章节级别的参考资料
        if section_data:
            main_content += "### 参考资料\n\n"
            
            # 处理不同的数据格式
            if isinstance(section_data, list) and len(section_data) > 0:
                # 检查是否是FilteredData对象
                if hasattr(section_data[0], 'source'):
                    # 新的FilteredData格式
                    for i, filtered_data in enumerate(section_data[:5]):  # 最多5个来源
                        source = filtered_data.source
                        title = source.title if source.title else f'参考资料{i+1}'
                        url = source.url if source.url else '#'
                        
                        # 构建引用信息
                        citation_info = f"- [{title}]({url})"
                        
                        # 添加来源类型
                        if source.source_type:
                            citation_info += f" ({source.source_type})"
                        
                        # 添加发布日期
                        if source.publish_date:
                            citation_info += f" - {source.publish_date}"
                        
                        # 添加质量评分
                        score = filtered_data.quality_score.total_score
                        citation_info += f" [评分: {score:.2f}]"
                        
                        # 添加评分理由
                        if filtered_data.reasoning:
                            citation_info += f"\n  - 评分理由: {filtered_data.reasoning}"
                        
                        main_content += citation_info + "\n"
                else:
                    # 原始格式
                    for i, data in enumerate(section_data[:5]):
                        title = data.get('title', f'参考资料{i+1}')
                        url = data.get('url', '#')
                        source = data.get('search_source', '未知来源')
                        main_content += f"- [{title}]({url}) - {source}\n"
        
        return main_content
    
    def _clean_section_title(self, title):
        """清理章节标题，移除中文符号并规范化"""
        import re
        
        # 移除各种中文符号
        title = re.sub(r'^[（(]\s*[一二三四五六七八九十]+\s*[）)]\s*', '', title)  # 移除（一）、（二）等
        title = re.sub(r'^[<＜]\s*[一二三四五六七八九十]+\s*[>＞]\s*', '', title)  # 移除<一>、<二>等
        title = re.sub(r'^[【\[]\s*[一二三四五六七八九十]+\s*[】\]]\s*', '', title)  # 移除【一】、【二】等
        title = re.sub(r'^[一二三四五六七八九十]+[、．\.]?\s*', '', title)  # 移除一、二、等
        title = re.sub(r'^[①②③④⑤⑥⑦⑧⑨⑩]+\s*', '', title)  # 移除①②③等
        title = re.sub(r'^[1-9]\d*[\.。)]\s*', '', title)  # 移除1.、2.等
        title = re.sub(r'^[A-Za-z][\.。)]\s*', '', title)  # 移除A.、B.等
        
        return title.strip()
    
    def _normalize_content_headings(self, content):
        """规范化内容中的标题层级"""
        import re
        
        # 将一级标题降级为四级标题
        content = re.sub(r'^#\s+', '#### ', content, flags=re.MULTILINE)
        
        # 将二级标题降级为四级标题
        content = re.sub(r'^##\s+', '#### ', content, flags=re.MULTILINE)
        
        # 将三级标题降级为四级标题
        content = re.sub(r'^###\s+', '#### ', content, flags=re.MULTILINE)
        
        # 处理加粗标题转换为四级标题
        content = re.sub(r'^\*\*([^*]+)\*\*\s*$', r'#### \1', content, flags=re.MULTILINE)
        
        return content
    
    def _generate_simple_section_content(self, section_title, section_info, section_data):
        """简单的章节内容生成"""
        content = f"## {section_title}\n\n"
        
        # 添加子章节
        for sub_title, sub_info in section_info.get('subsections', {}).items():
            # 清理子章节标题
            clean_title = self._clean_section_title(sub_title)
            content += f"### {clean_title}\n\n"
            for item in sub_info.get('items', []):
                content += f"- {item}\n"
            content += "\n"
        
        # 添加直接内容
        if section_info.get('content'):
            content += "### 主要要点\n\n"
            for item in section_info['content']:
                content += f"- {item}\n"
            content += "\n"
        
        return content

def generate_outline_report(topic, outline_text, target_audience="通用", output_file=None, parallel_config="balanced", extracted_topic=None):
    """
    根据大纲生成报告
    
    Args:
        topic (str): 主题
        outline_text (str): 大纲文本
        target_audience (str): 目标受众
        output_file (str): 输出文件路径
        parallel_config (str): 并行配置
        extracted_topic (str): 已提取的主题（用于避免重复处理）
        
    Returns:
        tuple: (报告文件路径, 报告数据)
    """
    print(f"🚀 开始生成基于大纲的报告: {topic}")
    print(f"👥 目标受众: {target_audience}")
    print(f"⚙️ 并行配置: {parallel_config}")
    
    # 确保输出目录存在
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # 步骤1：初始化LLM处理器
    llm_processor = None
    try:
        llm_processor = LLMProcessor()
        print("✅ 已初始化LLM处理器用于智能大纲解析和内容生成")
    except Exception as e:
        print(f"⚠️ 初始化LLM处理器失败: {str(e)}，将使用备用解析方法")
    
    # 步骤2：智能解析大纲（传递已提取的主题以避免重复处理）
    parser = OutlineParser(llm_processor)
    # 使用已提取的主题，避免把主题当作章节处理
    outline_structure = parser.parse_outline(outline_text, extracted_topic)
    
    if not outline_structure:
        raise ValueError("大纲解析失败，请检查大纲格式")
    
    # 步骤3：并行收集数据
    try:
        collector = OutlineDataCollector(llm_processor)
        
        # 配置并行参数
        parallel_configs = {
            "conservative": {"data_workers": 2, "content_workers": 2},
            "balanced": {"data_workers": 3, "content_workers": 3},
            "aggressive": {"data_workers": 4, "content_workers": 4}
        }
        
        config_params = parallel_configs.get(parallel_config, parallel_configs["balanced"])
        
        sections_data = collector.parallel_collect_main_sections(
            outline_structure, topic, target_audience, 
            max_workers=config_params['data_workers']
        )
        
    except Exception as e:
        print(f"⚠️ 数据收集失败: {str(e)}，将使用基础生成方法")
        sections_data = {}
    
    # 步骤4：评估各章节复杂度
    print("\n📊 章节复杂度评估:")
    complexity_stats = {"high": 0, "medium": 0, "low": 0}
    
    if llm_processor:
        temp_generator = OutlineContentGenerator(llm_processor)
        for section_title, section_info in outline_structure.items():
            complexity = temp_generator._assess_section_complexity(section_title, section_info, topic)
            word_req = temp_generator._get_word_count_requirements(complexity)
            complexity_stats[complexity] += 1
            print(f"  📝 {section_title}: {complexity.upper()} ({word_req['min_words']}-{word_req['max_words']}字)")
    
    print(f"\n📈 复杂度统计: 高复杂度 {complexity_stats['high']}个, 中等复杂度 {complexity_stats['medium']}个, 低复杂度 {complexity_stats['low']}个")
    
    # 步骤5：并行生成内容
    try:
        if llm_processor:
            generator = OutlineContentGenerator(llm_processor)
            generated_sections = generator.parallel_generate_main_sections(
                outline_structure, sections_data, topic, target_audience,
                max_workers=config_params['content_workers']
            )
        else:
            generator = OutlineContentGenerator(None)
            generated_sections = generator.parallel_generate_main_sections(
                outline_structure, sections_data, topic, target_audience, max_workers=1
            )
        
    except Exception as e:
        print(f"⚠️ 内容生成失败: {str(e)}，使用简单生成方法")
        generator = OutlineContentGenerator(None)
        generated_sections = generator.parallel_generate_main_sections(
            outline_structure, sections_data, topic, target_audience, max_workers=1
        )
    
    # 步骤6：组织报告
    report_content = _organize_outline_report(
        topic, outline_structure, generated_sections, target_audience
    )
    
    # 步骤7：保存报告
    if not output_file:
        date_str = datetime.now().strftime('%Y%m%d')
        clean_topic = topic.replace(' ', '_').replace('/', '_').replace('\\', '_').lower()
        output_file = os.path.join(config.OUTPUT_DIR, f"{clean_topic}_outline_report_{date_str}.md")
    elif not os.path.isabs(output_file):
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write(report_content)
    
    print(f"\n🎉 === 大纲报告生成完成 ===")
    print(f"📄 报告已保存至: {output_file}")
    print(f"📊 报告统计:")
    print(f"   - 主要章节: {len(outline_structure)}")
    print(f"   - 目标受众: {target_audience}")
    print(f"   - 文件大小: {len(report_content)} 字符")
    
    # 修复标题格式
    print("🔧 正在优化报告标题格式...")
    try:
        if _fix_outline_report_format(output_file):
            print("✅ Markdown格式修复成功")
        else:
            print("⚠️ Markdown格式修复失败，但报告已生成")
    except Exception as e:
        print(f"⚠️ 格式修复出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    return output_file, {
        'title': f"{topic}报告",
        'content': report_content,
        'outline_structure': outline_structure,
        'target_audience': target_audience,
        'date': datetime.now().strftime('%Y-%m-%d')
    }

def _organize_outline_report(topic, outline_structure, generated_sections, target_audience):
    """组织大纲报告"""
    # 生成报告标题
    report_content = f"# {topic}报告\n\n"
    
    # 添加报告信息
    report_content += f"**目标受众**: {target_audience}\n\n"
    report_content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # 添加目录
    report_content += "## 目录\n\n"
    for i, section_title in enumerate(outline_structure.keys(), 1):
        # 清理标题用于目录链接
        clean_title = _clean_title_for_link(section_title)
        report_content += f"{i}. [{section_title}](#{clean_title})\n"
    report_content += "\n"
    
    # 添加章节内容
    for section_title in outline_structure.keys():
        section_content = generated_sections.get(section_title, "")
        if section_content:
            # 确保章节内容不重复添加标题
            if section_content.strip().startswith(f"## {section_title}"):
                report_content += f"{section_content}\n\n"
            else:
                report_content += f"## {section_title}\n\n{section_content}\n\n"
        else:
            # 备用内容
            report_content += f"## {section_title}\n\n"
            report_content += f"本章节将详细介绍{section_title}的相关内容。\n\n"
    
    # 添加使用说明
    report_content += "---\n\n"
    report_content += "## 使用说明\n\n"
    report_content += "- 本报告基于AI技术生成，内容仅供参考\n"
    report_content += "- 建议结合最新资料进行验证和更新\n"
    report_content += "- 图表和案例标注位置建议根据实际需要插入相应内容\n"
    
    return report_content

def _clean_title_for_link(title):
    """清理标题用于Markdown链接"""
    import re
    
    # 移除各种中文符号和特殊字符
    clean_title = re.sub(r'[（）()【】\[\]<>＜＞、。，,\s]+', '-', title)
    clean_title = re.sub(r'[一二三四五六七八九十①②③④⑤⑥⑦⑧⑨⑩]+', '', clean_title)
    clean_title = re.sub(r'-+', '-', clean_title)  # 合并多个连字符
    clean_title = clean_title.strip('-').lower()  # 移除首尾连字符并转小写
    
    return clean_title

def _fix_outline_report_format(file_path):
    """修复大纲报告的Markdown格式 - 使用新的有效后处理逻辑"""
    import re
    
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # 创建备份
        backup_path = file_path + '.bak'
        with open(backup_path, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        
        print(f"已创建备份文件: {backup_path}")
        
        # 修复代码块标记和Mermaid语法问题
        print("正在修复代码块标记和Mermaid语法问题...")
        fixed_content = _fix_code_block_issues(content)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"报告格式修复完成: {file_path}")
        return True
        
    except Exception as e:
        print(f"修复报告格式时出错: {str(e)}")
        return False

def _fix_code_block_issues(content):
    """修复代码块标记问题和Mermaid语法问题"""
    import re
    
    # 1. 首先修复Mermaid语法问题
    content = _fix_mermaid_syntax(content)
    
    # 2. 移除错误的 ```markdown 标记
    content = re.sub(r'^```markdown\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^`````markdown\s*$', '', content, flags=re.MULTILINE)
    
    # 3. 移除孤立的 ``` 标记（不是真正的代码块）
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 如果是孤立的 ``` 行
        if stripped in ['```', '`````']:
            # 检查前后是否有真正的代码内容
            has_code_before = False
            has_code_after = False
            
            # 检查前面10行
            for j in range(max(0, i-10), i):
                prev_line = lines[j].strip()
                if prev_line.startswith('```') and prev_line not in ['```', '`````']:
                    has_code_before = True
                    break
            
            # 检查后面10行
            for j in range(i+1, min(len(lines), i+11)):
                next_line = lines[j].strip()
                if next_line.startswith('```') and next_line not in ['```', '`````']:
                    has_code_after = True
                    break
            
            # 如果不是真正的代码块，就移除
            if not (has_code_before or has_code_after):
                continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def _fix_mermaid_syntax(content):
    """修复Mermaid图表的语法问题"""
    lines = content.split('\n')
    fixed_lines = []
    in_mermaid_block = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 检查是否是mermaid块的开始
        if stripped == '```mermaid':
            in_mermaid_block = True
            fixed_lines.append(line)
            continue
        
        # 如果在mermaid块中，检查是否是结束标记
        if in_mermaid_block:
            # 如果遇到结束标记
            if stripped == '```':
                in_mermaid_block = False
                fixed_lines.append(line)
                continue
            
            # 如果遇到以 # 开头的行（可能是markdown标题），说明mermaid块没有正确结束
            if stripped.startswith('#'):
                # 插入缺失的结束标记
                fixed_lines.append('```')
                fixed_lines.append('')  # 添加空行
                fixed_lines.append(line)
                in_mermaid_block = False
                continue
        
        fixed_lines.append(line)
    
    # 如果文件结束时仍在mermaid块中，添加结束标记
    if in_mermaid_block:
        fixed_lines.append('```')
    
    return '\n'.join(fixed_lines)



def load_outline_from_file(file_path):
    """从文件加载大纲"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 读取大纲文件失败: {str(e)}")
        return None

def extract_topic_from_outline(outline_text, outline_file_path=None):
    """从大纲内容中提取题目"""
    import re
    
    if not outline_text:
        return None
    
    # 尝试从大纲内容的开头几行提取题目
    lines = outline_text.strip().split('\n')
    
    for i, line in enumerate(lines[:10]):  # 只检查前10行
        line = line.strip()
        if not line:
            continue
        
        # 匹配可能的题目格式
        title_patterns = [
            r'^#\s*(.+)$',  # Markdown一级标题
            r'^##\s*(.+)$',  # Markdown二级标题
            r'^[《<](.+)[》>]$',  # 书名号
            r'^【(.+)】$',  # 方括号
            r'^「(.+)」$',  # 日式引号
            r'^"(.+)"$',  # 双引号
            r'^[\u2018\u2019](.+)[\u2018\u2019]$',  # 中文引号
            r'^题目[:：]\s*(.+)$',  # 题目: 格式
            r'^主题[:：]\s*(.+)$',  # 主题: 格式
            r'^标题[:：]\s*(.+)$',  # 标题: 格式
            r'^报告[:：]\s*(.+)$',  # 报告: 格式
        ]
        
        for pattern in title_patterns:
            match = re.match(pattern, line)
            if match:
                title = match.group(1).strip()
                if len(title) > 3 and not _is_structural_text(title):
                    return title
        
        # 如果是第一行且不是明显的结构性文本，可能是题目
        if i == 0 and len(line) > 3 and not _is_structural_text(line):
            # 移除可能的序号或符号
            cleaned_line = re.sub(r'^[一二三四五六七八九十\d]+[、．\.\s]*', '', line)
            if cleaned_line and len(cleaned_line) > 3:
                return cleaned_line
    
    # 如果没有找到题目，尝试从文件名提取
    if outline_file_path:
        file_name = os.path.basename(outline_file_path)
        # 移除文件扩展名
        name_without_ext = os.path.splitext(file_name)[0]
        
        # 清理常见的文件名模式
        cleaned_name = re.sub(r'[_\-\s]', ' ', name_without_ext)
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
        
        if len(cleaned_name) > 3:
            return cleaned_name
    
    return None

def _is_structural_text(text):
    """判断文本是否是结构性文本（如目录、大纲等）"""
    structural_keywords = [
        '目录', '大纲', '提纲', '结构', '框架', '索引', '内容',
        '第一', '第二', '第三', '第四', '第五',
        '一、', '二、', '三、', '四、', '五、',
        '（一）', '（二）', '（三）', '（四）', '（五）',
        '1.', '2.', '3.', '4.', '5.',
        'outline', 'contents', 'index', 'structure'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in structural_keywords)

if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='🚀 基于大纲生成定制化报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python generate_outline_report.py --topic "生成式大模型" --outline-file outline.txt --audience "高校学生"
  python generate_outline_report.py --topic "AI应用" --outline "一、概述..." --audience "企业从业者"
  python generate_outline_report.py --outline-file outline.txt  # 自动解析题目和使用默认受众
  python generate_outline_report.py --outline-file outline.txt --test-complexity  # 测试章节复杂度
  
目标受众选项:
  - 高校学生: 教学式、循序渐进的表达方式
  - 企业从业者: 实用性强、解决方案导向
  - AI爱好者: 前沿探索、技术深入
  - 通用: 平衡性、易于理解
        """
    )
    
    parser.add_argument('--topic', type=str, help='报告的主题（如果不指定，将从大纲内容或文件名自动解析）')
    parser.add_argument('--outline', type=str, help='大纲文本（直接输入）')
    parser.add_argument('--outline-file', type=str, help='大纲文件路径')
    parser.add_argument('--audience', type=str, choices=['高校学生', '企业从业者', 'AI爱好者', '通用'], 
                       default='通用', help='目标受众 (默认: 通用)')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--parallel', type=str, choices=['conservative', 'balanced', 'aggressive'], 
                       default='balanced', help='并行配置 (默认: balanced)')
    parser.add_argument('--test-complexity', action='store_true', help='测试章节复杂度评估（使用现有评估逻辑）')
    
    args = parser.parse_args()
    
    # 如果是测试复杂度模式
    if args.test_complexity:
        # 获取大纲内容
        outline_text = None
        outline_file_path = None
        if args.outline:
            outline_text = args.outline
        elif args.outline_file:
            outline_file_path = args.outline_file
            outline_text = load_outline_from_file(args.outline_file)
        else:
            print("❌ 请提供大纲内容（--outline）或大纲文件路径（--outline-file）")
            sys.exit(1)
        
        if not outline_text:
            print("❌ 无法获取大纲内容")
            sys.exit(1)
        
        # 如果用户没有指定topic，尝试从大纲内容或文件名自动解析
        topic = args.topic
        if not topic:
            print("🔍 未指定主题，正在从大纲内容自动解析...")
            topic = extract_topic_from_outline(outline_text, outline_file_path)
            if topic:
                print(f"✅ 自动解析到题目: {topic}")
            else:
                print("❌ 无法自动解析题目，请手动指定 --topic 参数")
                sys.exit(1)
        
        # 解析大纲
        print("🔍 解析大纲结构...")
        parser_obj = OutlineParser()
        outline_structure = parser_obj.parse_outline(outline_text, topic if not args.topic else None)
        
        if not outline_structure:
            print("❌ 大纲解析失败")
            sys.exit(1)
        
        # 使用现有的复杂度评估方法
        print("\n📊 使用现有评估逻辑测试章节复杂度:")
        print("=" * 60)
        
        # 创建生成器实例来使用评估方法
        generator = OutlineContentGenerator(None)
        
        complexity_stats = {"high": 0, "medium": 0, "low": 0}
        
        for section_title, section_info in outline_structure.items():
            print(f"\n📝 章节: {section_title}")
            print("-" * 40)
            
            # 使用现有的评估方法
            complexity = generator._assess_section_complexity(section_title, section_info, topic)
            word_req = generator._get_word_count_requirements(complexity)
            
            complexity_stats[complexity] += 1
            
            # 显示详细信息
            subsection_count = len(section_info.get('subsections', {}))
            total_items = sum(len(sub_info.get('items', [])) for sub_info in section_info.get('subsections', {}).values())
            
            print(f"   子章节数量: {subsection_count}")
            print(f"   内容要点数量: {total_items}")
            print(f"   标题长度: {len(section_title)} 字符")
            
            # 计算技术关键词
            tech_keywords = [
                '算法', '架构', '模型', '技术', '方法', '系统', '框架', '机制', '原理', '策略',
                '优化', '实现', '设计', '开发', '部署', '评估', '分析', '处理', '计算', '数据'
            ]
            
            text_content = f"{section_title} {' '.join(section_info.get('content', []))}"
            for sub_info in section_info.get('subsections', {}).values():
                text_content += f" {' '.join(sub_info.get('items', []))}"
            
            tech_count = sum(1 for keyword in tech_keywords if keyword in text_content)
            print(f"   技术关键词数量: {tech_count}")
            
            print(f"   → 复杂度等级: {complexity.upper()}")
            print(f"   → 目标字数: {word_req['min_words']}-{word_req['max_words']} 字")
            print(f"   → 描述: {word_req['description']}")
            
            # 显示子章节详情
            if section_info.get('subsections'):
                print("   子章节详情:")
                for sub_title, sub_info in section_info['subsections'].items():
                    items_count = len(sub_info.get('items', []))
                    print(f"     - {sub_title}: {items_count} 个要点")
        
        print("\n" + "=" * 60)
        print("📈 复杂度统计总结:")
        print(f"   高复杂度章节: {complexity_stats['high']} 个")
        print(f"   中等复杂度章节: {complexity_stats['medium']} 个")
        print(f"   低复杂度章节: {complexity_stats['low']} 个")
        
        total_sections = sum(complexity_stats.values())
        if total_sections > 0:
            print(f"   平均复杂度分布: 高 {complexity_stats['high']/total_sections*100:.1f}%, 中 {complexity_stats['medium']/total_sections*100:.1f}%, 低 {complexity_stats['low']/total_sections*100:.1f}%")
        
        sys.exit(0)
    
    # 获取大纲内容
    outline_text = None
    outline_file_path = None
    if args.outline:
        outline_text = args.outline
    elif args.outline_file:
        outline_file_path = args.outline_file
        outline_text = load_outline_from_file(args.outline_file)
    else:
        print("❌ 请提供大纲内容（--outline）或大纲文件路径（--outline-file）")
        sys.exit(1)
    
    if not outline_text:
        print("❌ 无法获取大纲内容")
        sys.exit(1)
    
    # 如果用户没有指定topic，尝试从大纲内容或文件名自动解析
    topic = args.topic
    if not topic:
        print("🔍 未指定主题，正在从大纲内容自动解析...")
        topic = extract_topic_from_outline(outline_text, outline_file_path)
        if topic:
            print(f"✅ 自动解析到题目: {topic}")
        else:
            print("❌ 无法自动解析题目，请手动指定 --topic 参数")
            sys.exit(1)
    
    # 显示启动信息
    print("🚀 " + "=" * 50)
    print("🚀 基于大纲的定制化报告生成器")
    print("🚀 " + "=" * 50)
    print(f"📝 主题: {topic}" + (" (自动解析)" if not args.topic else ""))
    print(f"👥 目标受众: {args.audience}")
    print(f"⚙️ 并行配置: {args.parallel}")
    if args.output:
        print(f"📄 输出文件: {args.output}")
    print("🚀 " + "=" * 50)
    
    # 生成报告
    try:
        output_file, report_data = generate_outline_report(
            topic, 
            outline_text, 
            args.audience, 
            args.output, 
            args.parallel,
            extracted_topic=topic if not args.topic else None  # 只有当topic是自动解析时才传递
        )
        
        print(f"\n✅ 报告生成成功!")
        print(f"📄 文件路径: {output_file}")
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断了报告生成过程")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 报告生成失败: {str(e)}")
        sys.exit(1) 