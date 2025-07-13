"""
开题报告生成Agent
功能：
1. 根据用户输入的题目生成相关研究方向
2. 与用户交互确认研究方向
3. 生成开题报告大纲并与用户确认
4. 调用多个API进行内容检索和汇总
5. 生成规范的开题报告
"""

import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
import re

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.tavily_collector import TavilyCollector
from collectors.google_search_collector import GoogleSearchCollector
from collectors.brave_search_collector import BraveSearchCollector
from collectors.arxiv_collector import ArxivCollector
from collectors.llm_processor import LLMProcessor
from collectors.parallel_llm_processor import ParallelLLMProcessor

class ProposalReportAgent:
    """开题报告生成Agent"""
    
    def __init__(self):
        # 初始化各种搜索收集器
        self.collectors = {}
        self.llm_processor = None
        
        # 初始化LLM处理器
        try:
            self.llm_processor = LLMProcessor()
            print("✅ LLM处理器已初始化")
        except Exception as e:
            print(f"❌ LLM处理器初始化失败: {str(e)}")
            return
        
        # 初始化搜索收集器
        self._init_collectors()
        
        # 开题报告标准大纲
        self.standard_outline = {
            "1": "研究背景与意义",
            "2": "国内外研究现状",
            "3": "研究目标与内容",
            "4": "研究方法与技术路线",
            "5": "预期成果与创新点",
            "6": "研究进度安排",
            "7": "参考文献"
        }
    
    def _init_collectors(self):
        """初始化各种搜索收集器"""
        # 初始化Tavily
        try:
            self.tavily_collector = TavilyCollector()
            self.collectors['tavily'] = self.tavily_collector
            print("✅ Tavily搜索引擎已启用")
        except Exception as e:
            print(f"⚠️ Tavily搜索引擎不可用: {str(e)}")
        
        # 初始化Google搜索
        try:
            self.google_collector = GoogleSearchCollector()
            if self.google_collector.has_api_key:
                self.collectors['google'] = self.google_collector
                print("✅ Google搜索引擎已启用")
        except Exception as e:
            print(f"⚠️ Google搜索引擎不可用: {str(e)}")
        
        # 初始化Brave搜索
        try:
            self.brave_collector = BraveSearchCollector()
            if self.brave_collector.has_api_key:
                self.collectors['brave'] = self.brave_collector
                print("✅ Brave搜索引擎已启用")
        except Exception as e:
            print(f"⚠️ Brave搜索引擎不可用: {str(e)}")
        
        # 初始化ArXiv
        try:
            self.arxiv_collector = ArxivCollector()
            self.collectors['arxiv'] = self.arxiv_collector
            print("✅ ArXiv学术搜索已启用")
        except Exception as e:
            print(f"⚠️ ArXiv学术搜索不可用: {str(e)}")
        
        print(f"🔍 共启用 {len(self.collectors)} 个搜索引擎")
    
    def generate_research_directions(self, topic):
        """
        步骤1：根据用户题目生成相关研究方向
        """
        print(f"🧠 [研究方向生成] 正在为题目 '{topic}' 生成相关研究方向...")
        
        direction_prompt = f"""
        用户提供的研究题目: "{topic}"
        
        请作为一个资深的学术导师，基于该题目生成5个相关的、具体的研究方向。
        每个研究方向应该：
        1. 与原题目紧密相关但有所细化
        2. 具有学术研究价值和可行性
        3. 符合当前学术研究热点
        4. 可以作为学位论文的研究方向
        5. 表述清晰、专业
        
        请严格按照以下JSON格式返回：
        {{
            "original_topic": "原始题目",
            "research_directions": [
                {{
                    "direction": "研究方向1",
                    "description": "该方向的简要描述和研究价值",
                    "keywords": ["关键词1", "关键词2", "关键词3"]
                }},
                {{
                    "direction": "研究方向2",
                    "description": "该方向的简要描述和研究价值",
                    "keywords": ["关键词1", "关键词2", "关键词3"]
                }}
            ]
        }}
        
        确保生成5个不同的研究方向，每个方向都要有清晰的描述和相关关键词。
        """
        
        try:
            response = self.llm_processor.call_llm_api(
                direction_prompt,
                "你是一个资深的学术导师，擅长指导学生确定研究方向。",
                max_tokens=2000
            )
            
            # 解析JSON响应
            direction_data = self._parse_json_response(response)
            print(f"✅ 成功生成 {len(direction_data.get('research_directions', []))} 个研究方向")
            return direction_data
            
        except Exception as e:
            print(f"❌ 研究方向生成失败: {str(e)}")
            return self._get_fallback_directions(topic)
    
    def _parse_json_response(self, response):
        """解析LLM的JSON响应"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                raise ValueError("无法找到有效的JSON格式")
        except Exception as e:
            print(f"⚠️ JSON解析失败: {str(e)}")
            raise
    
    def _get_fallback_directions(self, topic):
        """备用研究方向生成"""
        return {
            "original_topic": topic,
            "research_directions": [
                {
                    "direction": f"{topic}的理论基础研究",
                    "description": "深入探讨该领域的理论基础和核心概念",
                    "keywords": ["理论基础", "核心概念", "基础研究"]
                },
                {
                    "direction": f"{topic}的技术实现研究",
                    "description": "研究该领域的技术实现方法和关键技术",
                    "keywords": ["技术实现", "关键技术", "方法研究"]
                },
                {
                    "direction": f"{topic}的应用场景研究",
                    "description": "探索该领域在实际应用中的场景和效果",
                    "keywords": ["应用场景", "实际应用", "效果评估"]
                }
            ]
        }
    
    def confirm_research_direction(self, directions_data):
        """
        步骤2：与用户交互确认研究方向
        """
        print(f"\n📋 基于您的题目 '{directions_data['original_topic']}' 生成的研究方向：")
        print("=" * 70)
        
        while True:
            # 显示研究方向
            directions = directions_data['research_directions']
            for i, direction in enumerate(directions, 1):
                print(f"\n{i}. {direction['direction']}")
                print(f"   描述：{direction['description']}")
                print(f"   关键词：{', '.join(direction['keywords'])}")
            
            print(f"\n选择选项：")
            print("1-5: 选择对应的研究方向")
            print("r: 重新生成研究方向")
            print("c: 自定义研究方向")
            
            choice = input("\n请输入您的选择: ").strip().lower()
            
            if choice in ['1', '2', '3', '4', '5']:
                idx = int(choice) - 1
                if idx < len(directions):
                    selected_direction = directions[idx]
                    print(f"\n✅ 您选择了: {selected_direction['direction']}")
                    confirm = input("确认此研究方向吗？(y/n): ").strip().lower()
                    if confirm == 'y':
                        return selected_direction
                    else:
                        continue
                else:
                    print("⚠️ 无效的选择，请重新输入")
            
            elif choice == 'r':
                # 重新生成研究方向
                print("\n🔄 重新生成研究方向...")
                new_directions = self.generate_research_directions(directions_data['original_topic'])
                directions_data = new_directions
                print(f"\n📋 重新生成的研究方向：")
                print("=" * 70)
                
            elif choice == 'c':
                # 自定义研究方向
                custom_direction = input("\n请输入您的自定义研究方向: ").strip()
                if custom_direction:
                    custom_description = input("请简要描述该研究方向的价值和意义: ").strip()
                    custom_keywords = input("请输入相关关键词（用逗号分隔）: ").strip().split(',')
                    
                    selected_direction = {
                        "direction": custom_direction,
                        "description": custom_description,
                        "keywords": [k.strip() for k in custom_keywords]
                    }
                    print(f"\n✅ 您的自定义研究方向: {selected_direction['direction']}")
                    return selected_direction
                else:
                    print("⚠️ 研究方向不能为空")
            
            else:
                print("⚠️ 无效的选择，请重新输入")
    
    def generate_proposal_outline(self, selected_direction):
        """
        步骤3：生成开题报告大纲
        """
        print(f"\n📝 [大纲生成] 正在为研究方向 '{selected_direction['direction']}' 生成开题报告大纲...")
        
        outline_prompt = f"""
        研究方向: "{selected_direction['direction']}"
        研究描述: "{selected_direction['description']}"
        关键词: {', '.join(selected_direction['keywords'])}
        
        请作为一个资深的学术导师，为该研究方向生成一个详细的开题报告大纲。
        
        标准开题报告应包含以下主要部分：
        1. 研究背景与意义
        2. 国内外研究现状
        3. 研究目标与内容
        4. 研究方法与技术路线
        5. 预期成果与创新点
        6. 研究进度安排
        7. 参考文献
        
        请为每个部分生成详细的子项目，确保：
        - 每个部分都有3-5个具体的子项目
        - 子项目要具体、可执行
        - 符合学术研究规范
        - 针对该研究方向的特点
        
        请严格按照以下JSON格式返回：
        {{
            "research_direction": "研究方向",
            "outline": {{
                "1": {{
                    "title": "研究背景与意义",
                    "sub_items": [
                        "具体子项目1",
                        "具体子项目2",
                        "具体子项目3"
                    ]
                }},
                "2": {{
                    "title": "国内外研究现状",
                    "sub_items": [
                        "具体子项目1",
                        "具体子项目2",
                        "具体子项目3"
                    ]
                }}
            }}
        }}
        
        确保生成完整的7个部分的大纲。
        """
        
        try:
            response = self.llm_processor.call_llm_api(
                outline_prompt,
                "你是一个资深的学术导师，擅长指导学生制定开题报告大纲。",
                max_tokens=3000
            )
            
            # 解析JSON响应
            outline_data = self._parse_json_response(response)
            print(f"✅ 成功生成开题报告大纲")
            return outline_data
            
        except Exception as e:
            print(f"❌ 大纲生成失败: {str(e)}")
            return self._get_fallback_outline(selected_direction)
    
    def _get_fallback_outline(self, selected_direction):
        """备用大纲生成"""
        return {
            "research_direction": selected_direction['direction'],
            "outline": {
                "1": {
                    "title": "研究背景与意义",
                    "sub_items": [
                        "研究问题的提出",
                        "研究意义分析",
                        "研究价值阐述"
                    ]
                },
                "2": {
                    "title": "国内外研究现状",
                    "sub_items": [
                        "国外研究现状分析",
                        "国内研究现状分析",
                        "研究不足与发展趋势"
                    ]
                },
                "3": {
                    "title": "研究目标与内容",
                    "sub_items": [
                        "研究目标确定",
                        "研究内容规划",
                        "研究范围界定"
                    ]
                },
                "4": {
                    "title": "研究方法与技术路线",
                    "sub_items": [
                        "研究方法选择",
                        "技术路线设计",
                        "实施方案制定"
                    ]
                },
                "5": {
                    "title": "预期成果与创新点",
                    "sub_items": [
                        "预期成果描述",
                        "创新点分析",
                        "学术贡献总结"
                    ]
                },
                "6": {
                    "title": "研究进度安排",
                    "sub_items": [
                        "研究阶段划分",
                        "时间进度安排",
                        "里程碑设定"
                    ]
                },
                "7": {
                    "title": "参考文献",
                    "sub_items": [
                        "文献收集整理",
                        "引用格式规范",
                        "参考文献列表"
                    ]
                }
            }
        }
    
    def confirm_outline(self, outline_data):
        """
        步骤4：与用户确认和修改大纲
        """
        print(f"\n📋 开题报告大纲 - {outline_data['research_direction']}")
        print("=" * 70)
        
        while True:
            # 显示大纲
            outline = outline_data['outline']
            for section_num, section_data in outline.items():
                print(f"\n{section_num}. {section_data['title']}")
                for i, sub_item in enumerate(section_data['sub_items'], 1):
                    print(f"   {section_num}.{i} {sub_item}")
            
            print(f"\n选择选项：")
            print("y: 确认大纲，开始生成报告")
            print("m: 修改某个部分")
            print("r: 重新生成整个大纲")
            
            choice = input("\n请输入您的选择: ").strip().lower()
            
            if choice == 'y':
                print("\n✅ 大纲确认完成，开始生成开题报告...")
                return outline_data
            
            elif choice == 'm':
                # 修改某个部分
                section_num = input("请输入要修改的部分编号 (1-7): ").strip()
                if section_num in outline:
                    print(f"\n当前部分：{outline[section_num]['title']}")
                    for i, sub_item in enumerate(outline[section_num]['sub_items'], 1):
                        print(f"   {section_num}.{i} {sub_item}")
                    
                    new_items = []
                    print("\n请输入新的子项目（每行一个，输入空行结束）：")
                    while True:
                        item = input().strip()
                        if not item:
                            break
                        new_items.append(item)
                    
                    if new_items:
                        outline[section_num]['sub_items'] = new_items
                        print(f"✅ 部分 {section_num} 修改完成")
                    else:
                        print("⚠️ 未输入任何内容，保持原状")
                else:
                    print("⚠️ 无效的部分编号")
            
            elif choice == 'r':
                # 重新生成大纲
                print("\n🔄 重新生成大纲...")
                # 这里需要传递selected_direction，需要在调用时保存
                print("⚠️ 重新生成功能需要在主流程中实现")
            
            else:
                print("⚠️ 无效的选择，请重新输入")
    
    def search_academic_content(self, direction, outline_data):
        """
        步骤5：搜索学术内容和论文
        """
        print(f"\n🔍 [内容搜索] 正在搜索相关学术内容...")
        
        # 构建搜索关键词
        search_keywords = direction['keywords']
        direction_name = direction['direction']
        
        all_content = {}
        all_papers = []
        
        # 1. 搜索学术论文
        print("📚 搜索学术论文...")
        papers = self._search_academic_papers(direction_name, search_keywords)
        all_papers.extend(papers)
        
        # 2. 为每个大纲部分搜索内容
        outline = outline_data['outline']
        for section_num, section_data in outline.items():
            if section_num == '7':  # 跳过参考文献部分
                continue
            
            print(f"🔍 搜索 '{section_data['title']}' 相关内容...")
            section_content = self._search_section_content(
                section_data['title'],
                direction_name,
                search_keywords
            )
            all_content[section_num] = section_content
        
        return all_content, all_papers
    
    def _search_academic_papers(self, direction_name, keywords):
        """搜索学术论文"""
        papers = []
        
        # 1. 从ArXiv搜索
        if 'arxiv' in self.collectors:
            try:
                arxiv_papers = self.arxiv_collector.get_papers_by_topic(
                    direction_name, keywords, days=365
                )
                papers.extend(arxiv_papers)
                print(f"   ArXiv: {len(arxiv_papers)} 篇论文")
            except Exception as e:
                print(f"   ArXiv搜索失败: {str(e)}")
        
        # 2. 从其他搜索引擎搜索学术内容
        for search_term in keywords[:5]:  # 限制搜索数量
            query = f"{direction_name} {search_term} academic paper research"
            
            # Tavily搜索
            if 'tavily' in self.collectors:
                try:
                    results = self.tavily_collector.search(query, max_results=5)
                    for result in results:
                        if self._is_academic_source(result.get('url', '')):
                            papers.append({
                                'title': result.get('title', ''),
                                'content': result.get('content', ''),
                                'url': result.get('url', ''),
                                'source': 'tavily',
                                'published': datetime.now().strftime('%Y-%m-%d')
                            })
                except Exception as e:
                    print(f"   Tavily搜索失败: {str(e)}")
            
            # Google搜索
            if 'google' in self.collectors:
                try:
                    results = self.google_collector.search(query, max_results=5)
                    for result in results:
                        if self._is_academic_source(result.get('url', '')):
                            papers.append({
                                'title': result.get('title', ''),
                                'content': result.get('snippet', ''),
                                'url': result.get('url', ''),
                                'source': 'google',
                                'published': datetime.now().strftime('%Y-%m-%d')
                            })
                except Exception as e:
                    print(f"   Google搜索失败: {str(e)}")
        
        # 去重
        unique_papers = []
        seen_urls = set()
        for paper in papers:
            url = paper.get('url', '')
            if url and url not in seen_urls:
                unique_papers.append(paper)
                seen_urls.add(url)
        
        print(f"📚 共找到 {len(unique_papers)} 篇相关论文")
        return unique_papers
    
    def _is_academic_source(self, url):
        """判断是否为学术来源"""
        academic_domains = [
            'arxiv.org', 'ieee.org', 'acm.org', 'springer.com',
            'elsevier.com', 'nature.com', 'science.org', 'wiley.com',
            'researchgate.net', 'scholar.google.com', 'dblp.org'
        ]
        return any(domain in url.lower() for domain in academic_domains)
    
    def _search_section_content(self, section_title, direction_name, keywords):
        """搜索特定部分的内容"""
        content = []
        
        # 构建针对性搜索查询
        queries = [
            f"{direction_name} {section_title}",
            f"{direction_name} research {section_title.lower()}",
            f"{keywords[0]} {section_title}" if keywords else f"{direction_name} {section_title}"
        ]
        
        for query in queries[:2]:  # 限制搜索数量
            # 使用各种搜索引擎
            for collector_name, collector in self.collectors.items():
                if collector_name == 'arxiv':
                    continue  # ArXiv已经在论文搜索中处理
                
                try:
                    if collector_name == 'tavily':
                        results = collector.search(query, max_results=3)
                    elif collector_name == 'google':
                        results = collector.search(query, max_results=3)
                    elif collector_name == 'brave':
                        results = collector.search(query, count=3)
                    else:
                        continue
                    
                    for result in results:
                        content.append({
                            'title': result.get('title', ''),
                            'content': result.get('content', result.get('snippet', '')),
                            'url': result.get('url', ''),
                            'source': collector_name
                        })
                except Exception as e:
                    print(f"      {collector_name}搜索失败: {str(e)}")
        
        return content
    
    def generate_report_content(self, direction, outline_data, search_content, papers):
        """
        步骤6：生成开题报告内容
        """
        print(f"\n📝 [报告生成] 正在生成开题报告内容...")
        
        # 初始化并行处理器
        parallel_processor = ParallelLLMProcessor(
            self.llm_processor,
            config={
                'section_generator': {'max_workers': 4},
                'content_analyzer': {'max_workers': 3}
            }
        )
        
        # 生成各个部分的内容
        report_sections = {}
        outline = outline_data['outline']
        
        for section_num, section_data in outline.items():
            if section_num == '7':  # 参考文献单独处理
                continue
            
            print(f"📝 生成 '{section_data['title']}' 部分...")
            
            # 获取该部分的搜索内容
            section_content = search_content.get(section_num, [])
            
            # 生成该部分的内容
            section_text = self._generate_section_content(
                section_data['title'],
                section_data['sub_items'],
                section_content,
                papers,
                direction
            )
            
            report_sections[section_num] = {
                'title': section_data['title'],
                'content': section_text
            }
        
        # 组合完整报告
        full_report = self._assemble_full_report(
            direction['direction'],
            report_sections,
            papers
        )
        
        return full_report
    
    def _generate_section_content(self, section_title, sub_items, content_data, papers, direction):
        """生成单个部分的内容"""
        # 准备内容材料
        content_materials = []
        for item in content_data:
            content_materials.append(f"标题: {item['title']}\n内容: {item['content']}")
        
        # 准备论文材料
        paper_materials = []
        for paper in papers[:10]:  # 限制论文数量
            paper_materials.append(f"论文: {paper['title']}\n摘要: {paper['content']}")
        
        section_prompt = f"""
        研究方向: {direction['direction']}
        部分标题: {section_title}
        子项目: {', '.join(sub_items)}
        
        参考内容:
        {chr(10).join(content_materials[:5])}
        
        相关论文:
        {chr(10).join(paper_materials[:5])}
        
        请基于以上材料，为开题报告的"{section_title}"部分撰写详细内容。
        
        要求：
        1. 内容要学术规范，符合开题报告要求
        2. 结构清晰，逻辑严密
        3. 适当引用相关文献（使用[1]、[2]等格式）
        4. 每个子项目都要有相应内容
        5. 字数控制在800-1500字
        6. 使用学术写作风格
        
        请直接返回该部分的内容，不要添加其他说明。
        """
        
        try:
            section_content = self.llm_processor.call_llm_api(
                section_prompt,
                "你是一个专业的学术写作助手，擅长撰写规范的开题报告。",
                max_tokens=3000
            )
            return section_content.strip()
        except Exception as e:
            print(f"生成'{section_title}'部分失败: {str(e)}")
            return f"## {section_title}\n\n本部分内容生成失败，请手动补充。"
    
    def _assemble_full_report(self, direction_name, report_sections, papers):
        """组装完整报告"""
        report = f"""# {direction_name} 开题报告

## 摘要

本研究旨在深入探讨{direction_name}领域的相关问题，通过系统的理论分析和实证研究，为该领域的发展提供新的见解和解决方案。

"""
        
        # 添加各个部分
        for section_num in sorted(report_sections.keys()):
            section_data = report_sections[section_num]
            report += f"## {section_num}. {section_data['title']}\n\n"
            report += section_data['content']
            report += "\n\n"
        
        # 添加参考文献
        report += "## 7. 参考文献\n\n"
        for i, paper in enumerate(papers[:30], 1):
            title = paper.get('title', '无标题')
            url = paper.get('url', '')
            authors = paper.get('authors', ['未知作者'])
            published = paper.get('published', '未知时间')
            
            if isinstance(authors, list):
                authors_str = ', '.join(authors)
            else:
                authors_str = str(authors)
            
            report += f"[{i}] {authors_str}. {title}. {published}. Available: {url}\n\n"
        
        return report
    
    def save_report(self, report_content, direction_name):
        """保存报告到文件"""
        # 确保输出目录存在
        os.makedirs('reports', exist_ok=True)
        
        # 生成文件名
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"proposal_report_{direction_name.replace(' ', '_')}_{date_str}.md"
        filepath = os.path.join('reports', filename)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ 开题报告已保存至: {filepath}")
        return filepath
    
    def run(self, topic):
        """运行完整的开题报告生成流程"""
        print(f"\n🚀 开题报告生成Agent启动")
        print(f"📝 用户题目: '{topic}'")
        print("=" * 70)
        
        try:
            # 步骤1: 生成研究方向
            directions_data = self.generate_research_directions(topic)
            
            # 步骤2: 确认研究方向
            selected_direction = self.confirm_research_direction(directions_data)
            
            # 步骤3: 生成大纲
            outline_data = self.generate_proposal_outline(selected_direction)
            
            # 步骤4: 确认大纲
            confirmed_outline = self.confirm_outline(outline_data)
            
            # 步骤5: 搜索内容
            search_content, papers = self.search_academic_content(selected_direction, confirmed_outline)
            
            # 步骤6: 生成报告
            report_content = self.generate_report_content(
                selected_direction, confirmed_outline, search_content, papers
            )
            
            # 步骤7: 保存报告
            filepath = self.save_report(report_content, selected_direction['direction'])
            
            print(f"\n✅ 开题报告生成完成！")
            print(f"📄 报告文件: {filepath}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ 开题报告生成失败: {str(e)}")
            return None

def main():
    """主函数"""
    load_dotenv()
    
    print("🎓 开题报告生成Agent")
    print("=" * 50)
    
    # 创建Agent实例
    agent = ProposalReportAgent()
    
    # 获取用户输入
    topic = input("请输入您的研究题目: ").strip()
    
    if not topic:
        print("❌ 题目不能为空")
        return
    
    # 运行开题报告生成流程
    result = agent.run(topic)
    
    if result:
        print(f"\n🎉 开题报告生成成功！")
        print(f"📁 文件位置: {result}")
    else:
        print(f"\n❌ 开题报告生成失败")

if __name__ == "__main__":
    main() 