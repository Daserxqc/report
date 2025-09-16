import asyncio
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from collectors.llm_processor import LLMProcessor
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'search_mcp', 'src'))
from collectors.search_mcp_old import Document
from collectors.outline_writer_mcp import OutlineNode


@dataclass
class ContentWritingConfig:
    """内容写作配置类"""
    writing_style: str = "professional"  # 写作风格
    target_audience: str = "行业专家"      # 目标受众
    tone: str = "objective"              # 语调
    depth_level: str = "detailed"        # 深度级别
    include_examples: bool = True         # 是否包含示例
    include_citations: bool = True        # 是否包含引用
    max_section_length: int = 8000       # 最大章节长度
    min_section_length: int = 8000       # 最小章节长度


class DetailedContentWriterMcp:
    """
    详细内容撰写MCP (Model Context Protocol)
    
    用途：报告内容撰写的主力，负责填充各个章节。
    
    职责：
    - 根据章节标题和参考资料撰写详细内容
    - 可被并行调用，同时为多个章节生成内容
    - 在生成内容时，可根据指令添加引用标记
    
    输入：section_title: str, content_data: list[Document], overall_report_context: str
    输出：str (章节内容文本)
    
    实现要点：Prompt需非常紧凑，包含角色扮演（"你是一位...分析师"）、章节标题、参考资料和全局上下文。
    """
    
    def __init__(self, llm_processor=None):
        """初始化DetailedContentWriterMcp"""
        try:
            self.llm_processor = llm_processor or LLMProcessor()
            self.has_llm = True
            print("✅ DetailedContentWriterMcp初始化完成")
        except Exception as e:
            print(f"⚠️ LLM处理器初始化失败: {str(e)}")
            self.has_llm = False
        
        # 预定义的写作模板
        self.writing_templates = self._load_writing_templates()
        
        # 角色定义
        self.role_definitions = self._load_role_definitions()
    
    def _load_writing_templates(self) -> Dict[str, str]:
        """加载写作模板"""
        return {
            "single_item": """
请基于以下关于"{topic}{section_name}"的详细资料，创建一个内容丰富、结构清晰的专业分析章节：

资料标题: {title}
资料内容: {content}

要求：
1. 创建一个内容极其丰富的专业行业分析章节，深度挖掘资料中的核心观点和数据
2. 分析必须非常深入且全面，使用多级标题组织内容（##、###、####）
3. 必须详尽覆盖资料中的重要观点，进行系统性扩展与深度阐述
4. 章节应分为至少7-10个子标题，每个子标题下内容详尽充实
5. 总体内容长度应达到4000-6000字，确保分析深度远超普通报告
6. 在适当位置添加来源引用：[^1]: {source} - {url}
7. 每个小节标题应具体明确，并能准确概括其内容
8. 不要简单复述资料，必须形成有深度的分析框架和独到见解
9. 内容应呈现层次递进的结构，从基础概念到深度分析，从现状到趋势预测
10. 避免并列式的举例，而要构建有逻辑层次的阐述性内容
""",

            "two_items": """
请基于以下两条资料，为'{topic}行业洞察报告'的'{section_name}'章节创建一个连贯、深入的专业分析章节：

资料1标题: {item1_title}
资料1内容: {item1_content}

资料2标题: {item2_title}
资料2内容: {item2_content}

要求：
1. 创建一个内容极其丰富的专业行业分析章节，整合两个资料的核心观点和数据
2. 分析必须非常深入且全面，使用多级标题组织内容（##、###、####）
3. 必须详尽覆盖两个资料中的重要观点，进行系统性整合与深度拓展
4. 章节应分为至少7-10个子标题，每个子标题下内容详尽充实
5. 总体内容长度应达到4000-6000字，确保分析深度远超普通报告
6. 在适当位置添加来源引用：
  [^1]: {item1_source} - {item1_url}
  [^2]: {item2_source} - {item2_url}
7. 每个小节标题应具体明确，并能准确概括其内容
8. 不要简单堆砌资料，必须形成有深度的分析框架和独到见解
9. 内容应呈现层次递进的结构，从基础概念到深度分析，从现状到趋势预测
10. 避免并列式的举例，而要构建有逻辑层次的阐述性内容
""",

            "multiple_items": """
请基于以下关于"{topic}{section_name}"的多个资料来源，创建一个极其详尽、专业且结构清晰的行业分析章节：

{all_resources}

要求：
1. 创建一个内容极其丰富的专业行业分析章节，整合所有资料的核心观点和数据
2. 分析必须非常深入且全面，使用多级标题组织内容（##、###、####）
3. 必须详尽覆盖所有资料中的重要观点，进行系统性整合与深度拓展
4. 章节应分为至少7-10个子标题，每个子标题下内容详尽充实
5. 总体内容长度应达到4000-6000字，确保分析深度远超普通报告
6. 在适当位置添加来源引用：
{source_reference_text}
7. 每个小节标题应具体明确，并能准确概括其内容
8. 不要简单堆砌资料，必须形成有深度的分析框架和独到见解
9. 内容应呈现层次递进的结构，从基础概念到深度分析，从现状到趋势预测
10. 避免并列式的举例，而要构建有逻辑层次的阐述性内容
""",

            "standard": """
你是一位专业的{role}，正在撰写关于"{overall_topic}"的{section_title}章节。

章节要求：
- 目标受众：{target_audience}
- 写作风格：{writing_style}
- 内容深度：{depth_level}
- 字数要求：{word_count_requirement}

参考资料：
{reference_content}

全局报告上下文：
{overall_report_context}

撰写要求：
1. **专业深度**：基于参考资料提供深入、专业的分析
2. **逻辑结构**：内容应有清晰的逻辑层次和段落结构
3. **实用价值**：突出实际应用价值和现实意义
4. **引用规范**：在引用参考资料时使用[1]、[2]等标记
5. **语言表达**：使用{tone}的语调，适合{target_audience}阅读
6. **引用要求**：在适当位置添加引用标记以支撑观点和数据

章节结构建议：
- 开篇：简要介绍本章节的核心议题
- 主体：围绕关键要点展开详细分析
- 实例：{example_instruction}
- 总结：概括本章节的主要观点

引用指导：
- 在引用具体数据、观点或案例时，请在相关内容后添加引用标记
- 重要论述和关键信息应提供引用支撑
- 引用标记应自然融入文本，保持阅读流畅性

请撰写完整的章节内容，确保信息准确、逻辑清晰、表达流畅，并包含适当的引用标记。
""",

            "academic": """
你是一位资深的{role}，正在撰写学术报告中的"{section_title}"章节。

研究主题：{overall_topic}
章节定位：{section_context}

参考文献和资料：
{reference_content}

学术写作要求：
1. **理论基础**：建立坚实的理论框架
2. **文献综述**：充分回顾和引用相关研究
3. **方法论述**：清晰说明研究方法和逻辑
4. **客观分析**：保持学术的客观性和严谨性
5. **创新观点**：提出有价值的见解和观点
6. **引用规范**：在适当位置使用[1]、[2]等格式标注引用来源

写作规范：
- 使用学术语言和专业术语
- 遵循学术引用规范 [1]、[2] 等
- 字数控制在 {word_count_requirement} 
- 逻辑严密，论证充分

引用要求：
- 在引用具体数据、观点或研究结果时，请在句末添加引用标记，如："根据最新研究显示...[1]"
- 重要论断和关键数据必须提供引用支撑
- 引用标记应自然融入文本，不影响阅读流畅性

请按照学术写作标准撰写本章节内容，确保包含适当的引用标记。
""",

            "business": """
你是一位经验丰富的{role}，正在为商业报告撰写"{section_title}"章节。

商业主题：{overall_topic}
商业背景：{business_context}

市场数据和资料：
{reference_content}

商业写作要求：
1. **商业洞察**：提供深刻的商业洞察和分析
2. **数据驱动**：使用具体数据支撑观点
3. **实用导向**：关注实际应用和商业价值
4. **决策支持**：为决策者提供有价值的信息
5. **风险意识**：识别和分析潜在风险
6. **引用规范**：在适当位置使用[1]、[2]等格式标注数据来源

内容结构：
- 现状分析：基于数据的客观分析
- 趋势洞察：识别关键趋势和机会
- 战略建议：提出可行的战略建议
- 风险提示：指出需要注意的风险点

引用要求：
- 在引用市场数据、行业报告或案例研究时，请添加引用标记，如："市场规模达到XX亿元[1]"
- 重要的商业数据和趋势分析必须提供数据来源
- 引用应增强内容的可信度和权威性

字数要求：{word_count_requirement}
目标受众：{target_audience}

请撰写具有商业价值且包含适当引用的章节内容。
""",

            "technical": """
你是一位专业的{role}，正在撰写技术报告中的"{section_title}"章节。

技术主题：{overall_topic}
技术背景：{technical_context}

技术资料和参考：
{reference_content}

技术写作要求：
1. **技术准确性**：确保技术信息的准确性
2. **原理阐述**：清楚解释技术原理和机制
3. **实现细节**：描述关键的实现方法和技术路径
4. **性能分析**：分析技术性能和优劣势
5. **应用场景**：说明实际应用场景和案例
6. **引用规范**：在适当位置使用[1]、[2]等格式标注技术资料来源

内容组织：
- 技术概述：介绍核心技术概念
- 原理分析：深入分析技术原理
- 实现方案：描述技术实现方法
- 应用实例：提供具体应用案例
- 发展趋势：分析技术发展方向

引用要求：
- 在引用技术规范、性能数据或实现案例时，请添加引用标记，如："该算法的时间复杂度为O(n)[1]"
- 重要的技术参数和性能指标必须提供参考来源
- 引用应支撑技术论述的准确性和可靠性

写作风格：技术性强但易于理解
字数要求：{word_count_requirement}

请撰写专业且实用的技术章节内容，确保包含适当的引用标记。
"""
        }
    
    def _load_role_definitions(self) -> Dict[str, str]:
        """加载角色定义"""
        return {
            "academic": "学术研究专家和教授",
            "business": "商业分析师和战略顾问", 
            "technical": "技术专家和架构师",
            "industry": "行业分析师和咨询顾问",
            "market": "市场研究专家和投资分析师",
            "policy": "政策分析专家和研究员",
            "general": "专业内容分析师"
        }
    
    def _parse_json_from_text(self, text: str) -> Optional[Dict]:
        """从文本中提取JSON对象"""
        try:
            # 找到第一个 '{' 和最后一个 '}'
            start_index = text.find('{')
            end_index = text.rfind('}')
            
            if start_index != -1 and end_index != -1 and start_index < end_index:
                json_str = text[start_index:end_index+1]
                return json.loads(json_str)
            return None
        except json.JSONDecodeError:
            return None

    async def _generate_outline(self, topic: str, articles: List[Document]) -> Dict:
        """
        使用LLM动态生成报告大纲。
        """
        print("正在生成报告大纲...")
        
        article_summaries = "\n".join([f"- {doc.title}: {doc.content[:200]}..." for doc in articles])
        
        prompt = f"""
        你是一位顶级的行业研究员，你需要为一个关于“{topic}”的深度分析报告创建一个结构化的大纲。
        报告需要全面、深入，并且逻辑清晰。请参考以下相关文章摘要：

        {article_summaries}

        你的任务是生成一个JSON格式的大纲，必须遵循以下结构：
        1.  **引言 (introduction)**: 明确报告的研究目的和核心问题。
        2.  **核心分析章节 (body)**: 至少包含5个独立的分析章节。每个章节必须有：
            - 一个清晰的章节标题 (title)。
            - 至少4个具体的关键要点 (key_points)，这些要点应具有深度和可分析性。
        3.  **结论 (conclusion)**: 总结报告的核心发现和未来展望。

        **输出格式要求**：
        - 必须是严格的JSON格式，否则无法解析。
        - 根对象应包含 'introduction', 'body', 'conclusion' 三个键。
        - 'body' 的值应该是一个包含多个章节对象的列表。
        - 每个章节对象应包含 'title' 和 'key_points' 两个键。
        - 'key_points' 的值应该是一个字符串列表。

        **JSON结构示例**:
        {{
          "introduction": "...",
          "body": [
            {{
              "title": "章节一标题",
              "key_points": ["要点1", "要点2", "要点3", "要点4"]
            }},
            {{
              "title": "章节二标题",
              "key_points": ["要点A", "要点B", "要点C", "要点D"]
            }}
          ],
          "conclusion": "..."
        }}

        请立即生成符合上述要求的JSON大纲。
        """
        
        response_text = await asyncio.get_event_loop().run_in_executor(None, lambda: self.llm_processor.call_llm_api(prompt, max_tokens=4000))
        outline_json = self._parse_json_from_text(response_text)
        
        if outline_json and 'body' in outline_json and 'introduction' in outline_json and 'conclusion' in outline_json:
            print("✅ 报告大纲生成成功。")
            return outline_json
        else:
            print("❌ 报告大纲生成失败或格式不正确。")
            raise ValueError("无法生成有效的大纲。")

    async def _generate_introduction(self, topic: str, outline: Dict) -> str:
        """
        生成报告引言。
        """
        print("正在生成引言...")
        prompt = f"""
        你是一位资深的行业分析师，请为一份关于“{topic}”的深度分析报告撰写引言。
        报告大纲的引言部分要求如下：
        - {outline['introduction']}

        请根据这个要求，生成一段大约300-500字的引言，清晰地阐述报告的研究背景、核心问题和重要性。

        **内容风格要求 (非常重要)**:
        - **禁止元评论**: 绝对不要在最终的文本中包含任何关于你正在生成内容的评论或开场白。
        - **直接呈现内容**: 直接开始撰写引言正文，不要说“本引言将...”或类似的话。
        - **自然流畅**: 语言风格应自然、流畅、专业，避免使用模板化的句子。
        """
        introduction = await asyncio.get_event_loop().run_in_executor(None, lambda: self.llm_processor.call_llm_api(prompt, max_tokens=1000, temperature=0.7))
        print("✅ 引言生成完毕。")
        return f"# {topic}：深度分析报告\n\n## 1. 引言\n\n{introduction}\n\n"

    async def _generate_body(self, topic: str, outline: Dict) -> str:
        """
        生成报告主体。
        """
        print("正在生成报告主体...")
        
        # 检查outline格式
        if not isinstance(outline, dict) or 'body' not in outline:
            print(f"错误：outline格式不正确，类型: {type(outline)}")
            return f"## 报告主体\n\n由于大纲格式错误，无法生成详细内容。\n\n错误信息：outline类型为{type(outline)}，期望为dict类型。"
        
        body_content = []
        for i, chapter in enumerate(outline['body']):
            chapter_title = chapter['title']
            print(f"  - 正在生成章节: {chapter_title}")
            chapter_content = [f"## {i+2}. {chapter_title}\n"]
            for point in chapter['key_points']:
                print(f"    - 正在阐述要点: {point}")
                
                prompt = f"""
                你是一位顶级的行业分析师，你需要为一个关于“{topic}”的深度报告撰写其中一个要点。

                章节标题: "{chapter_title}"
                当前要点: "{point}"

                **写作指令**:
                1.  **结构化阐述**: 你的分析必须包含以下三个明确的部分，并使用Markdown的H4标题（####）进行标记：
                    -   `#### 背景与现状`: 解释该要点提出的背景、当前的发展状况以及其重要性。
                    -   `#### 关键技术与应用案例`: 深入剖析与该要点相关的核心技术、解决方案，并提供1-2个具体的真实世界应用案例进行佐证。
                    -   `#### 挑战与未来展望`: 探讨当前面临的挑战、潜在的风险，并对未来的发展趋势和前景进行预测。
                2.  **深度与篇幅要求**:
                    -   **硬性要求**: 整个要点的总字符数必须在 **3500到4000字符** 之间。这是一个严格的指标，必须达到。
                    -   **内容详尽**: 每个结构化部分（背景、技术、挑战）都必须内容充实，论述充分，避免泛泛而谈。
                3.  **专业性与数据支撑**:
                    -   使用专业术语和分析框架。
                    -   如果可能，引用假设性数据或行业趋势来增强说服力。
                4.  **内容风格要求 (至关重要)**:
                    -   **绝对禁止元评论**: 严禁在文本中包含任何关于内容本身的评论、评估或注释。这包括但不限于：“自我评估”、“字符数统计”、“专业度验证”、“结构完整性”、“以下是对...的分析”、“本文严格遵循了...指令”或任何类似的AI自我反思性语句。尤其禁止在末尾添加关于字符数是否达标的注释，例如 `（注：实际字符数约XXXX，符合要求）` 这种格式是完全不允许的。
                    -   **直接呈现，无需开场白**: 你是一个行业专家，直接撰写正文即可。不要有任何介绍性的段落来解释你将要写什么。
                    -   **专业、自然的语言**: 语言风格必须像一个资深的人类专家，自然、流畅、专业，避免使用模板化或机械的句子。

                请严格按照以上指令，生成关于要点“{point}”的详细、深入、结构化的分析内容。
                """
                
                point_content = await asyncio.get_event_loop().run_in_executor(None, lambda: self.llm_processor.call_llm_api(prompt, max_tokens=5000, temperature=0.7))
                chapter_content.append(f"### {point}\n\n{point_content}\n")
            
            body_content.append("\n".join(chapter_content))
        
        print("✅ 报告主体生成完毕。")
        return "\n".join(body_content)

    async def _generate_conclusion(self, topic: str, outline: Dict, full_report_text: str) -> str:
        """
        生成报告结论。
        """
        print("正在生成结论...")
        prompt = f"""
        你是一位资深的行业分析师，请根据以下关于“{topic}”的完整报告内容和结论要求，撰写一个全面而深刻的结论。

        报告结论要求：
        - {outline['conclusion']}

        完整报告内容（节选）：
        ---
        {full_report_text[:10000]}
        ---

        请撰写一段大约400-600字的结论，总结报告的核心发现，强调其意义，并对未来趋势提出最终的展望。

        **内容风格要求 (非常重要)**:
        - **禁止元评论**: 绝对不要在结论的开头或结尾添加任何反思性或总结性的评论。
        - **直接呈现内容**: 直接开始撰写结论正文。
        - **自然流畅**: 语言风格应深刻、精炼、有洞察力，避免空洞的套话。
        """
        conclusion = await asyncio.get_event_loop().run_in_executor(None, lambda: self.llm_processor.call_llm_api(prompt, max_tokens=1000, temperature=0.7))
        print("✅ 结论生成完毕。")
        conclusion_chapter_number = len(outline.get('body', [])) + 2
        return f"## {conclusion_chapter_number}. 结论\n\n{conclusion}\n"

    async def generate_full_report(self, topic: str, articles: List[Document]) -> str:
        """
        生成完整的深度分析报告。
        """
        print(f"开始生成关于'{topic}'的完整报告...")
        
        # 生成引用数据
        citation_data = self._generate_citations_from_documents(articles)
        
        # 1. 生成大纲
        try:
            outline = await self._generate_outline(topic, articles)
            if not outline or not isinstance(outline, dict):
                return f"# {topic}\n\n报告生成失败：无法创建有效大纲。"
        except Exception as e:
            print(f"大纲生成错误: {e}")
            return f"# {topic}\n\n报告生成失败：大纲生成异常 - {str(e)}"
        
        # 2. 生成引言
        introduction = await self._generate_introduction(topic, outline)
        
        # 3. 生成主体
        body = await self._generate_body(topic, outline)
        
        # 组装初步报告用于生成结论
        temp_report = introduction + body
        
        # 4. 生成结论
        conclusion = await self._generate_conclusion(topic, outline, temp_report)
        
        # 在内容中注入引用（如果启用）
        if articles:  # 只有当有文档时才添加引用
            introduction = self._inject_citations_into_content(introduction, articles[:2])  # 引言使用前2个文档
            body = self._inject_citations_into_content(body, articles)  # 正文使用所有文档
            conclusion = self._inject_citations_into_content(conclusion, articles[-2:])  # 结论使用后2个文档
        
        # 生成参考文献章节
        references_section = self._generate_references_section(citation_data)
        
        # 5. 组装最终报告
        final_report = introduction + body + conclusion + references_section
        
        print(f"✅ 完整报告生成完成（包含引用支持），总长度: {len(final_report)}字")
        return final_report
    
    def generate_full_report_sync(self, topic: str, articles: List[Document]) -> str:
        """
        生成完整报告的同步方法
        
        Args:
            topic: 报告主题
            articles: 相关文档列表
            
        Returns:
            str: 完整的报告内容
        """
        try:
            # 检查是否在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果在事件循环中，使用线程池执行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.generate_full_report(topic, articles))
                    return future.result(timeout=300)  # 5分钟超时
            except RuntimeError:
                # 没有运行的事件循环，直接运行
                return asyncio.run(self.generate_full_report(topic, articles))
                
        except Exception as e:
            print(f"同步生成完整报告时出错: {str(e)}")
            # 返回基础报告结构
            return f"# {topic}\n\n报告生成过程中遇到技术问题，请稍后重试。\n\n错误信息: {str(e)}"
    
    def write_section_content(self,
                             section_title: str,
                             content_data: List[Union[Document, Dict]],
                             overall_report_context: str,
                             config: ContentWritingConfig = None) -> str:
        """
        撰写章节详细内容
        
        Args:
            section_title: 章节标题
            content_data: 参考内容数据
            overall_report_context: 整体报告上下文
            config: 写作配置
            
        Returns:
            str: 章节内容
        """
        if not self.has_llm:
            return self._fallback_content_generation(section_title, content_data)
        
        if config is None:
            config = ContentWritingConfig()
        
        try:
            print(f"✍️ 开始撰写章节: {section_title}")
            
            # 根据资料数量选择不同的生成策略
            if len(content_data) == 0:
                content = self._generate_no_data_content(section_title, overall_report_context, config)
            elif len(content_data) == 1:
                content = self._generate_single_item_content(content_data[0], overall_report_context, section_title, config)
            elif len(content_data) == 2:
                content = self._generate_two_items_content(content_data, overall_report_context, section_title, config)
            else:
                content = self._generate_multiple_items_content(content_data, overall_report_context, section_title, config)
            
            # 添加引用支持（如果启用且有文档数据）
            if config.include_citations and content_data:
                # 过滤出Document对象
                documents = [item for item in content_data if isinstance(item, Document)]
                if documents:
                    content = self._inject_citations_into_content(content, documents)
            
            # 后处理内容
            processed_content = self._post_process_content(content, config)
            
            print(f"✅ 章节'{section_title}'撰写完成，长度: {len(processed_content)}字符")
            return processed_content
            
        except Exception as e:
            print(f"❌ 章节'{section_title}'撰写失败: {str(e)}")
            return self._fallback_content_generation(section_title, content_data)
    
    def _generate_single_item_content(self, item, overall_context, section_name, config=None):
        """单个资料的内容生成"""
        # 提取资料信息
        if isinstance(item, dict):
            title = item.get("title", "")
            content = item.get("content", "").strip()
            source = item.get("source", "行业分析")
            url = item.get("url", "#")
        else:
            title = getattr(item, 'title', '')
            content = getattr(item, 'content', '').strip()
            source = getattr(item, 'source', '行业分析')
            url = getattr(item, 'url', '#')
        
        # 提取主题
        topic = self._extract_overall_topic(overall_context)
        
        # 使用单项资料模板
        template = self.writing_templates["single_item"]
        
        prompt = template.format(
            topic=topic,
            section_name=section_name,
            title=title,
            content=content,
            source=source,
            url=url
        )
        
        system_message = f"你是一位专业的{topic}行业分析师和内容组织专家，擅长创建结构清晰的专业报告。"
        
        result = self.llm_processor.call_llm_api(prompt, system_message, temperature=0.2, max_tokens=16000)
        
        # 检查结果是否为协程对象
        if asyncio.iscoroutine(result):
            print(f"⚠️ 警告: LLM API返回协程对象，尝试等待结果")
            try:
                import asyncio
                result = asyncio.run(result)
            except Exception as e:
                print(f"⚠️ 错误: 无法等待协程结果: {e}")
                return f"内容生成失败: 协程处理错误 - {str(e)}"
        
        # 确保结果是字符串
        if not isinstance(result, str):
            result = str(result) if result else "内容生成失败"
            
        return result
    
    def _generate_two_items_content(self, section_items, overall_context, section_name, config=None):
        """两个资料的内容生成"""
        item1, item2 = section_items[0], section_items[1]
        
        # 提取资料信息
        if isinstance(item1, dict):
            item1_title = item1.get("title", "")
            item1_content = item1.get("content", "")
        else:
            item1_title = getattr(item1, 'title', '')
            item1_content = getattr(item1, 'content', '')
            
        if isinstance(item2, dict):
            item2_title = item2.get("title", "")
            item2_content = item2.get("content", "")
        else:
            item2_title = getattr(item2, 'title', '')
            item2_content = getattr(item2, 'content', '')
        
        # 提取主题
        topic = self._extract_overall_topic(overall_context)
        
        # 使用双项资料模板
        template = self.writing_templates["two_items"]
        
        # 准备引用信息
        item1_source = getattr(item1, 'source', '行业分析') if hasattr(item1, 'source') else item1.get('source', '行业分析')
        item1_url = getattr(item1, 'url', '#') if hasattr(item1, 'url') else item1.get('url', '#')
        item2_source = getattr(item2, 'source', '行业分析') if hasattr(item2, 'source') else item2.get('source', '行业分析')
        item2_url = getattr(item2, 'url', '#') if hasattr(item2, 'url') else item2.get('url', '#')
        
        prompt = template.format(
            topic=topic,
            section_name=section_name,
            item1_title=item1_title,
            item1_content=item1_content,
            item2_title=item2_title,
            item2_content=item2_content,
            item1_source=item1_source,
            item1_url=item1_url,
            item2_source=item2_source,
            item2_url=item2_url
        )
        
        system_message = f"你是一位专业的{topic}行业分析师和内容组织专家。"
        
        result = self.llm_processor.call_llm_api(prompt, system_message, temperature=0.2, max_tokens=16000)
        
        # 检查结果是否为协程对象
        if asyncio.iscoroutine(result):
            print(f"⚠️ 警告: LLM API返回协程对象，尝试等待结果")
            try:
                result = asyncio.run(result)
            except Exception as e:
                print(f"⚠️ 错误: 无法等待协程结果: {e}")
                return f"内容生成失败: 协程处理错误 - {str(e)}"
        
        # 确保结果是字符串
        if not isinstance(result, str):
            result = str(result) if result else "内容生成失败"
            
        return result
    
    def _generate_multiple_items_content(self, section_items, overall_context, section_name, config=None):
        """多个资料的内容生成"""
        resource_texts = []
        source_references = []
        
        for i, item in enumerate(section_items):
            if isinstance(item, dict):
                title = item.get("title", "")
                content = item.get("content", "").strip()
                source = item.get("source", "行业分析")
                url = item.get("url", "#")
            else:
                title = getattr(item, 'title', '')
                content = getattr(item, 'content', '').strip()
                source = getattr(item, 'source', '行业分析')
                url = getattr(item, 'url', '#')
            
            resource_texts.append(f"资料{i+1}标题: {title}\n资料{i+1}内容: {content}")
            source_references.append(f"[^{i+1}]: {source} - {url}")
        
        all_resources = "\n\n".join(resource_texts)
        source_reference_text = "\n".join(source_references)
        
        # 提取主题
        topic = self._extract_overall_topic(overall_context)
        
        # 使用多项资料模板
        template = self.writing_templates["multiple_items"]
        
        prompt = template.format(
            topic=topic,
            section_name=section_name,
            all_resources=all_resources,
            source_reference_text=source_reference_text
        )
        
        system_message = f"你是一位专业的{topic}行业分析师和内容组织专家。"
        
        result = self.llm_processor.call_llm_api(prompt, system_message, temperature=0.2, max_tokens=16000)
        
        # 检查结果是否为协程对象
        if asyncio.iscoroutine(result):
            print(f"⚠️ 警告: LLM API返回协程对象，尝试等待结果")
            try:
                result = asyncio.run(result)
            except Exception as e:
                print(f"⚠️ 错误: 无法等待协程结果: {e}")
                return f"内容生成失败: 协程处理错误 - {str(e)}"
        
        # 确保结果是字符串
        if not isinstance(result, str):
            result = str(result) if result else "内容生成失败"
            
        return result
    
    def _generate_no_data_content(self, section_title, overall_context, config=None):
        """无数据时的内容生成"""
        topic = self._extract_overall_topic(overall_context)
        
        prompt = f"""
请为"{topic}"报告中的"{section_title}"章节生成专业内容。

由于缺乏具体的参考资料，请基于行业通用知识和最佳实践生成内容。

要求：
1. 内容应专业、准确且有价值
2. 使用markdown格式组织内容
3. 包含至少3-5个子标题
4. 每个小节应有充分的内容展开
5. 总字数不少于1500字
6. 注明这是基于行业通用知识的分析
"""
        
        system_message = f"你是一位专业的{topic}行业分析师。"
        
        result = self.llm_processor.call_llm_api(prompt, system_message, temperature=0.3, max_tokens=6000)
        
        # 检查结果是否为协程对象
        if asyncio.iscoroutine(result):
            print(f"⚠️ 警告: LLM API返回协程对象，尝试等待结果")
            try:
                result = asyncio.run(result)
            except Exception as e:
                print(f"⚠️ 错误: 无法等待协程结果: {e}")
                return f"内容生成失败: 协程处理错误 - {str(e)}"
        
        # 确保结果是字符串
        if not isinstance(result, str):
            result = str(result) if result else "内容生成失败"
            
        return result
    
    def write_section_content_original_style(self,
                             section_title: str,
                             content_data: List[Union[Document, Dict]],
                             overall_report_context: str,
                             config: ContentWritingConfig = None) -> str:
        """
        使用原始风格撰写章节内容（保留原有逻辑作为备用）
        
        Args:
            section_title: 章节标题
            content_data: 参考资料列表
            overall_report_context: 全局报告上下文
            config: 写作配置
            
        Returns:
            str: 生成的章节内容
        """
        if not self.has_llm:
            return self._fallback_content_generation(section_title, content_data)
        
        try:
            # 使用默认配置
            if config is None:
                config = ContentWritingConfig()
            
            # 准备参考资料内容
            reference_content = self._prepare_reference_content(content_data)
            
            # 确定写作角色
            role = self._determine_writing_role(section_title, overall_report_context)
            
            # 选择写作模板
            template = self._select_writing_template(config.writing_style, role)
            
            # 准备模板参数
            template_params = self._prepare_template_params(
                section_title, overall_report_context, reference_content, config, role
            )
            
            # 格式化prompt
            prompt = template.format(**template_params)
            
            # 设置系统消息
            system_message = f"你是一位专业的{role}，擅长创建结构清晰的专业报告。"
            
            # 调用LLM生成内容
            content = self.llm_processor.call_llm_api(
                prompt=prompt,
                system_message=system_message,
                temperature=0.2,
                max_tokens=8000
            )
            
            # 检查结果是否为协程对象
            if asyncio.iscoroutine(content):
                print(f"⚠️ 警告: LLM API返回协程对象，尝试等待结果")
                try:
                    content = asyncio.run(content)
                except Exception as e:
                    print(f"⚠️ 错误: 无法等待协程结果: {e}")
                    return f"内容生成失败: 协程处理错误 - {str(e)}"
            
            # 确保结果是字符串
            if not isinstance(content, str):
                content = str(content) if content else "内容生成失败"
            
            # 后处理内容
            processed_content = self._post_process_content(content, config)
            
            return processed_content
            
        except Exception as e:
            print(f"⚠️ 内容生成失败: {str(e)}")
            return self._fallback_content_generation(section_title, content_data)
    
    def _prepare_reference_content(self, content_data: List[Union[Document, Dict]]) -> str:
        """准备参考内容"""
        if not content_data:
            return "无参考资料"
        
        reference_parts = []
        
        for i, item in enumerate(content_data[:8]):  # 限制前8个参考资料
            if isinstance(item, Document):
                ref_text = f"[{i+1}] {item.title}\n来源: {item.source} ({item.source_type})\n内容: {item.content[:300]}..."
                if item.authors:
                    ref_text += f"\n作者: {', '.join(item.authors)}"
                if item.publish_date:
                    ref_text += f"\n发布时间: {item.publish_date}"
                    
            elif isinstance(item, dict):
                title = item.get("title", f"参考资料{i+1}")
                content = item.get("content", item.get("summary", ""))[:300]
                source = item.get("source", "未知来源")
                ref_text = f"[{i+1}] {title}\n来源: {source}\n内容: {content}..."
                
            reference_parts.append(ref_text)
        
        return "\n\n".join(reference_parts)
    
    def _determine_writing_role(self, section_title: str, context: str) -> str:
        """根据章节标题和上下文确定写作角色"""
        title_lower = section_title.lower()
        context_lower = context.lower()
        
        # 学术相关关键词
        if any(keyword in title_lower for keyword in ["研究", "理论", "方法", "文献", "学术"]):
            return "academic"
        
        # 商业相关关键词  
        if any(keyword in title_lower for keyword in ["市场", "商业", "投资", "收益", "策略", "竞争"]):
            return "business"
        
        # 技术相关关键词
        if any(keyword in title_lower for keyword in ["技术", "算法", "架构", "实现", "系统", "开发"]):
            return "technical"
        
        # 政策相关关键词
        if any(keyword in title_lower for keyword in ["政策", "法规", "监管", "标准", "规范"]):
            return "policy"
        
        # 行业相关关键词
        if any(keyword in title_lower for keyword in ["行业", "产业", "发展", "趋势", "现状"]):
            return "industry"
        
        # 根据上下文判断
        if "学术" in context_lower or "研究" in context_lower:
            return "academic"
        elif "商业" in context_lower or "市场" in context_lower:
            return "business"
        elif "技术" in context_lower:
            return "technical"
        
        return "general"
    
    def _select_writing_template(self, writing_style: str, role: str) -> str:
        """选择写作模板"""
        # 根据角色选择模板
        if role == "academic":
            return self.writing_templates["academic"]
        elif role == "business":
            return self.writing_templates["business"]
        elif role == "technical":
            return self.writing_templates["technical"]
        else:
            return self.writing_templates["standard"]
    
    def _prepare_template_params(self, section_title: str, overall_report_context: str, 
                                reference_content: str, config: ContentWritingConfig, role: str) -> Dict[str, str]:
        """准备模板参数"""
        # 提取整体主题
        overall_topic = self._extract_overall_topic(overall_report_context)
        
        # 角色描述
        role_description = self.role_definitions.get(role, self.role_definitions["general"])
        
        # 字数要求描述
        word_count_requirement = f"{config.min_section_length}-{config.max_section_length}字"
        
        # 示例指导
        example_instruction = "结合具体案例和实例进行说明" if config.include_examples else "重点进行理论分析"
        
        # 语调描述
        tone_descriptions = {
            "objective": "客观、中性",
            "analytical": "分析性、深入",
            "professional": "专业、正式",
            "engaging": "生动、引人入胜",
            "authoritative": "权威、可信"
        }
        
        return {
            "role": role_description,
            "overall_topic": overall_topic,
            "section_title": section_title,
            "target_audience": config.target_audience,
            "writing_style": config.writing_style,
            "depth_level": config.depth_level,
            "word_count_requirement": word_count_requirement,
            "reference_content": reference_content,
            "overall_report_context": overall_report_context,
            "tone": tone_descriptions.get(config.tone, "客观、专业"),
            "example_instruction": example_instruction,
            "section_context": f"作为整体报告的重要组成部分",
            "business_context": overall_report_context if role == "business" else "",
            "technical_context": overall_report_context if role == "technical" else ""
        }
    
    def _extract_overall_topic(self, context: str) -> str:
        """从上下文中提取整体主题"""
        # 简单的主题提取逻辑
        lines = context.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('•', '-', '*', '1.', '2.')):
                # 取第一个非列表项的行作为主题
                return line[:50] + ("..." if len(line) > 50 else "")
        
        return "相关主题"
    
    def _post_process_content(self, content: str, config: ContentWritingConfig) -> str:
        """后处理生成的内容"""
        if not content:
            return "内容生成失败"
        
        # 清理格式
        content = content.strip()
        
        # 移除可能的标题重复
        lines = content.split('\n')
        if lines and lines[0].strip().startswith('#'):
            content = '\n'.join(lines[1:]).strip()
        
        # 检查长度
        if len(content) < config.min_section_length:
            print(f"⚠️ 内容长度({len(content)})低于最小要求({config.min_section_length})")
        elif len(content) > config.max_section_length:
            print(f"⚠️ 内容长度({len(content)})超过最大限制({config.max_section_length})")
        
        # 确保引用格式正确
        if config.include_citations:
            content = self._normalize_citations(content)
        
        return content
    
    def _normalize_citations(self, content: str) -> str:
        """规范化引用格式"""
        import re
        
        # 统一引用格式为 [数字]
        content = re.sub(r'\[(\d+)\]', r'[\1]', content)
        content = re.sub(r'（(\d+)）', r'[\1]', content)
        content = re.sub(r'\((\d+)\)', r'[\1]', content)
        
        return content
    
    def _generate_citations_from_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """从文档列表生成引用信息"""
        citations = {}
        citation_list = []
        
        for i, doc in enumerate(documents, 1):
            citation_key = f"[{i}]"
            citation_info = {
                "id": i,
                "title": doc.title,
                "url": doc.url,
                "source": doc.source,
                "source_type": doc.source_type,
                "publish_date": getattr(doc, 'publish_date', None),
                "authors": getattr(doc, 'authors', []),
                "venue": getattr(doc, 'venue', None)
            }
            
            citations[citation_key] = citation_info
            citation_list.append(citation_info)
        
        return {
            "citations_map": citations,
            "citation_list": citation_list,
            "total_count": len(documents)
        }
    
    def _format_citation_reference(self, citation_info: Dict) -> str:
        """格式化单个引用条目"""
        title = citation_info.get('title', '未知标题')
        url = citation_info.get('url', '')
        source = citation_info.get('source', '未知来源')
        publish_date = citation_info.get('publish_date', '')
        authors = citation_info.get('authors', [])
        venue = citation_info.get('venue', '')
        
        # 构建引用格式
        citation_parts = []
        
        # 添加作者信息
        if authors and len(authors) > 0:
            if len(authors) == 1:
                citation_parts.append(f"{authors[0]}")
            elif len(authors) <= 3:
                citation_parts.append(f"{', '.join(authors)}")
            else:
                citation_parts.append(f"{authors[0]} 等")
        
        # 添加标题
        citation_parts.append(f"《{title}》")
        
        # 添加发表信息
        if venue:
            citation_parts.append(f"{venue}")
        elif source:
            citation_parts.append(f"{source}")
        
        # 添加日期
        if publish_date:
            citation_parts.append(f"{publish_date}")
        
        # 添加URL
        if url:
            citation_parts.append(f"链接: {url}")
        
        return ". ".join(citation_parts)
    
    def _generate_references_section(self, citation_data: Dict) -> str:
        """生成参考文献章节"""
        if not citation_data or citation_data.get('total_count', 0) == 0:
            return ""
        
        references_content = ["\n## 参考文献\n"]
        
        for citation_info in citation_data.get('citation_list', []):
            citation_id = citation_info.get('id', 1)
            formatted_citation = self._format_citation_reference(citation_info)
            references_content.append(f"[{citation_id}] {formatted_citation}")
        
        return "\n".join(references_content)
    
    def _inject_citations_into_content(self, content: str, documents: List[Document]) -> str:
        """在内容中注入引用标记"""
        try:
            if not documents:
                return content
            
            # 检查content是否为协程对象
            import asyncio
            if asyncio.iscoroutine(content):
                print(f"⚠️ 警告: _inject_citations_into_content收到协程对象，跳过引用注入")
                return "内容生成异常：收到协程对象"
            
            # 确保content是字符串
            if not isinstance(content, str):
                print(f"⚠️ 警告: content类型错误: {type(content)}，转换为字符串")
                content = str(content)
            
            print(f"🔍 开始处理引用注入，content长度: {len(content)}, documents数量: {len(documents)}")
        
            import re
            
            # 创建关键词到引用的映射
            keyword_to_citation = {}
            for i, doc in enumerate(documents, 1):
                citation = f"[{i}]"
                
                # 从标题中提取关键词
                title_words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', doc.title)
                for word in title_words:
                    if len(word) >= 2:  # 至少2个字符
                        keyword_to_citation[word.lower()] = citation
                
                # 从内容中提取关键词
                content_words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', doc.content[:100])
                for word in content_words[:5]:  # 只取前5个词
                    if len(word) >= 3:  # 内容关键词要求更长
                        keyword_to_citation[word.lower()] = citation
            
            # 按句子分割内容
            sentences = re.split(r'([。！？\.])', content)
            modified_sentences = []
            citation_used = set()
            
            for i in range(0, len(sentences), 2):
                if i >= len(sentences):
                    break
                    
                sentence = sentences[i]
                punctuation = sentences[i+1] if i+1 < len(sentences) else ''
                
                # 检查句子是否已有引用
                if re.search(r'\[\d+\]', sentence):
                    modified_sentences.extend([sentence, punctuation])
                    continue
                
                # 查找匹配的关键词
                try:
                    # 安全地调用sentence.lower()，检查是否返回协程
                    sentence_lower = sentence.lower()
                    
                    # 检查sentence_lower是否为协程对象
                    if asyncio.iscoroutine(sentence_lower):
                        print(f"⚠️ 错误: sentence.lower()返回协程对象，跳过此句子")
                        modified_sentences.extend([sentence, punctuation])
                        continue
                        
                    # 确保sentence_lower是字符串
                    if not isinstance(sentence_lower, str):
                        print(f"⚠️ 错误: sentence_lower不是字符串: {type(sentence_lower)}")
                        modified_sentences.extend([sentence, punctuation])
                        continue
                        
                except Exception as lower_error:
                    print(f"⚠️ 错误: sentence.lower()调用失败: {lower_error}")
                    modified_sentences.extend([sentence, punctuation])
                    continue
                
                citation_to_add = None
                
                for keyword, citation in keyword_to_citation.items():
                    try:
                        if not isinstance(keyword, str):
                            print(f"⚠️ 错误: keyword不是字符串: {type(keyword)}")
                            continue
                            
                        if (keyword in sentence_lower and 
                            len(sentence.strip()) > 15 and  # 句子足够长
                            citation not in citation_used):
                            citation_to_add = citation
                            citation_used.add(citation)
                            break
                    except Exception as e:
                        print(f"⚠️ 关键字检查错误: {e}, keyword={keyword}")
                        continue
                
                # 添加引用
                if citation_to_add:
                    modified_sentences.extend([sentence + citation_to_add, punctuation])
                else:
                    modified_sentences.extend([sentence, punctuation])
            
            # 如果没有添加任何引用，强制在前几个句子中添加
            if not citation_used and documents:
                result = ''.join(modified_sentences)
                sentences_for_citation = re.split(r'([。！？\.])', result)
                
                for i in range(0, min(6, len(sentences_for_citation)), 2):
                    sentence = sentences_for_citation[i]
                    if len(sentence.strip()) > 20 and not re.search(r'\[\d+\]', sentence):
                        citation_num = (i // 2) % len(documents) + 1
                        sentences_for_citation[i] = sentence + f"[{citation_num}]"
                        break
                
                return ''.join(sentences_for_citation)
            
            return ''.join(modified_sentences)
        
        except Exception as e:
            print(f"❌ _inject_citations_into_content发生错误: {e}")
            print(f"   content类型: {type(content)}")
            print(f"   content内容预览: {str(content)[:100] if content else 'None'}")
            import traceback
            traceback.print_exc()
            return str(content) if content else "引用注入失败"
    
    def write_multiple_sections(self,
                               sections: List[Dict[str, any]],
                               overall_context: str,
                               config: ContentWritingConfig = None) -> Dict[str, str]:
        """
        批量撰写多个章节
        
        Args:
            sections: 章节信息列表，每个包含 title, content_data 等
            overall_context: 整体上下文
            config: 写作配置
            
        Returns:
            Dict[str, str]: 章节标题到内容的映射
        """
        if config is None:
            config = ContentWritingConfig()
        
        results = {}
        
        for i, section_info in enumerate(sections):
            try:
                section_title = section_info.get("title", f"章节{i+1}")
                content_data = section_info.get("content_data", [])
                
                # 为该章节创建特定配置
                section_config = config
                if "config" in section_info:
                    # 允许为每个章节自定义配置
                    section_config = ContentWritingConfig(**section_info["config"])
                
                content = self.write_section_content(
                    section_title=section_title,
                    content_data=content_data, 
                    overall_report_context=overall_context,
                    config=section_config
                )
                
                results[section_title] = content
                print(f"  ✅ [{i+1}/{len(sections)}] '{section_title}' 完成")
                
            except Exception as e:
                print(f"  ❌ [{i+1}/{len(sections)}] '{section_title}' 失败: {str(e)}")
                results[section_title] = f"章节内容生成失败: {str(e)}"
        
        return results
    
    def enhance_section_content(self,
                               existing_content: str,
                               section_title: str,
                               enhancement_type: str = "depth",
                               additional_data: List[Union[Document, Dict]] = None) -> str:
        """
        增强现有章节内容
        
        Args:
            existing_content: 现有内容
            section_title: 章节标题
            enhancement_type: 增强类型 (depth, examples, analysis, citations)
            additional_data: 额外数据
            
        Returns:
            str: 增强后的内容
        """
        if not self.has_llm:
            print("⚠️ 内容增强功能需要LLM支持")
            return existing_content
        
        try:
            enhancement_instructions = {
                "depth": "增加内容的深度和专业性，补充更多技术细节和理论分析",
                "examples": "添加更多具体案例和实例，增强内容的实用性",
                "analysis": "增强分析性内容，加入更多批判性思考和深入见解",
                "citations": "完善引用和参考资料，增加内容的权威性"
            }
            
            instruction = enhancement_instructions.get(enhancement_type, enhancement_instructions["depth"])
            
            # 准备额外参考内容
            additional_ref = ""
            if additional_data:
                additional_ref = f"\n补充参考资料：\n{self._prepare_reference_content(additional_data)}"
            
            prompt = f"""
请对以下章节内容进行增强优化：

章节标题：{section_title}
增强要求：{instruction}

现有内容：
{existing_content}
{additional_ref}

优化要求：
1. 保持原有内容的核心结构和观点
2. {instruction}
3. 确保增强后的内容逻辑连贯
4. 增强后长度应比原内容增加30-50%
5. 保持专业性和准确性

请输出增强后的完整章节内容。
"""
            
            enhanced_content = self.llm_processor.call_llm_api(
                prompt,
                f"你是一位专业的内容编辑专家，擅长优化和增强技术文档内容。",
                temperature=0.3,
                max_tokens=4000
            )
            
            print(f"✅ 章节内容增强完成，原长度: {len(existing_content)}, 新长度: {len(enhanced_content)}")
            return enhanced_content.strip()
            
        except Exception as e:
            print(f"❌ 内容增强失败: {str(e)}")
            return existing_content
    
    def _fallback_content_generation(self, section_title: str, content_data: List) -> str:
        """备用内容生成方法"""
        try:
            # 基于标题和数据生成简单内容
            content_parts = [f"## {section_title}\n"]
            
            if content_data:
                content_parts.append("基于现有资料分析，本章节主要内容包括：\n")
                
                for i, item in enumerate(content_data[:3]):
                    if isinstance(item, Document):
                        summary = item.content[:200] + "..." if len(item.content) > 200 else item.content
                        content_parts.append(f"### {item.title}\n{summary}\n")
                    elif isinstance(item, dict):
                        title = item.get("title", f"要点{i+1}")
                        content = item.get("content", "")[:200]
                        content_parts.append(f"### {title}\n{content}\n")
            else:
                content_parts.append(f"本章节将详细介绍{section_title}的相关内容，包括基本概念、发展现状、应用场景等方面。\n")
            
            content_parts.append("更多详细内容有待进一步研究和分析。")
            
            return '\n'.join(content_parts)
            
        except Exception as e:
            return f"## {section_title}\n\n内容生成失败: {str(e)}\n\n本章节需要进一步完善。"