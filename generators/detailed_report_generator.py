import os
import datetime
import json
from openai import OpenAI
import config

class DetailedReportGenerator:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key if api_key else config.OPENAI_API_KEY
        self.base_url = base_url if base_url else config.OPENAI_BASE_URL
        
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            
        self.client = OpenAI(**client_kwargs)
        self.model = "deepseek-v3" 
        print(f"DetailedReportGenerator initialized with model: {self.model}")

    def generate_detailed_report(self, topic, articles, outline, min_length=30000):
        print(f"开始生成关于 '{topic}' 的详细报告，目标长度: {min_length}字")
        
        introduction = self._generate_introduction(topic, articles)
        body = self._generate_body(topic, articles, outline)
        conclusion = self._generate_conclusion(topic, articles)
        
        report = f"# {topic}行业趋势深度分析报告\n\n"
        report += f"报告生成日期: {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
        report += f"## 1. 引言\n\n{introduction}\n\n"
        report += f"## 2. 核心分析\n\n{body}\n\n"
        report += f"## 3. 结论与展望\n\n{conclusion}\n\n"
        
        print(f"报告生成完毕，总长度: {len(report)}字")
        return report

    def _generate_outline(self, topic, articles):
        print("正在生成报告大纲...")
        article_summaries = "\n".join([f"- {article['title']}: {article.get('summary', '无摘要')}" for article in articles])
        
        prompt = f'''
        作为一名顶级的行业分析师，你的任务是为一份关于“{topic}”的深度研究报告创建一个详尽的、结构化的大纲。

        **可用的研究资料（文章标题和摘要）:**
        ---
        {article_summaries}
        ---

        **大纲要求:**
        1.  **深度与广度:** 大纲必须覆盖该主题的多个方面，体现出深度和广度。
        2.  **结构化:** 必须包含一个引言、一个结论，以及至少5个核心分析章节。
        3.  **详细的关键要点:** 每个核心分析章节必须包含至少4个具体的、有深度的关键要点 (key_points)。这些要点应该是需要深入探讨的具体问题，而不是宽泛的标题。
        4.  **逻辑性:** 章节和要点之间必须有清晰的逻辑关系，层层递进。
        5.  **输出格式:** 必须严格按照以下JSON格式输出，不要包含任何额外的解释或文本。

        **JSON输出格式示例:**
        {{
          "title": "报告标题",
          "sections": [
            {{
              "title": "第一章节标题",
              "key_points": [
                "第一个关键要点",
                "第二个关键要点",
                "第三个关键要点",
                "第四个关键要点"
              ]
            }},
            {{
              "title": "第二章节标题",
              "key_points": [
                "第一个关键要点",
                "第二个关键要点",
                "第三个关键要点",
                "第四个关键要点"
              ]
            }}
          ]
        }}

        请立即为关于“{topic}”的报告生成JSON格式的详细大纲。
        '''
        
        response_str = self._call_llm(prompt, max_tokens=3000, temperature=0.5)
        try:
            # The response might contain markdown code block delimiters
            if response_str.startswith("```json"):
                response_str = response_str[7:]
                if response_str.endswith("```"):
                    response_str = response_str[:-3]
            
            outline = json.loads(response_str)
            # Basic validation
            if 'title' in outline and 'sections' in outline:
                print("大纲生成成功。")
                return outline
            else:
                raise ValueError("Outline format is incorrect.")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"解析大纲JSON时出错: {e}")
            print(f"收到的原始字符串: {response_str}")
            # Fallback or error handling
            return None

    def _generate_introduction(self, topic, articles):
        print("正在生成引言...")
        article_summaries = "\n".join([f"- {article['title']}: {article.get('summary', '无摘要')}" for article in articles[:10]])
        
        prompt = f"""
        作为一名资深行业分析师，请为一份关于“{topic}”的深度分析报告撰写引言。
        这份报告基于以下核心文章：
        {article_summaries}

        引言需要达到以下要求：
        1.  **背景设定**: 简要介绍“{topic}”领域的当前宏观背景和重要性。
        2.  **趋势概述**: 基于所提供的文章标题和摘要，提炼出当前最显著的几个趋势或关键动态。
        3.  **报告结构说明**: 清晰地说明本报告将如何展开，将从哪些方面进行深入分析。
        4.  **语言风格**: 专业、客观、富有洞察力。
        5.  **篇幅要求**: 800 - 1200字。
        """
        
        return self._call_llm(prompt)

    def _generate_body(self, topic, articles, outline):
        print("正在生成报告主体...")
        body_parts = []
        full_content_context = "\n\n---\n\n".join([f"标题: {article['title']}\n内容: {article.get('full_content', article.get('summary', '无可用内容'))}" for article in articles])

        if 'sections' in outline:
            for section in outline['sections']:
                section_title = section.get('title', '无标题章节')
                print(f"  - 正在生成章节: {section_title}")
                body_parts.append(f"### {section_title}")

                key_points = section.get('key_points', [])
                if not key_points:
                    continue

                for point in key_points:
                    print(f"    - 正在阐述要点: {point}")
                    point_prompt = f"""
                    作为一名顶级的行业分析师，你的任务是为一份关于“{topic}”的深度报告，就“{section_title}”章节中的一个关键要点“{point}”撰写一份极其详尽、深度结构化的分析报告。

                    **报告的整体上下文和可用信息库:**
                    ---
                    {full_content_context[:50000]}
                    ---

                    **当前聚焦的核心要点:** {point}

                    **极其严格的结构化撰写指令（必须逐项深入分析）:**
                    你必须严格按照以下三个部分来组织你的分析，每个部分都要深入、详尽，并充分利用“信息库”中的信息。

                    **第一部分：背景、现状与重要性**
                    - **深度背景阐述:** 深入阐述该要点的技术、市场和行业背景。它解决了什么核心问题？
                    - **当前发展现状:** 分析其发展的最新动态、市场规模、主要参与者和竞争格局。
                    - **战略重要性:** 论述该要点为何在当前及未来对整个行业具有不可或缺的战略重要性。
                    - **引用支撑:** 必须频繁并具体地引用信息库中的数据、案例或观点来支撑你的分析。

                    **第二部分：核心技术、实现方法与应用案例**
                    - **技术/方法拆解:** 详细拆解与该要点相关的1-2个核心技术或关键实现方法。它们是如何工作的？技术难点在哪里？
                    - **具体应用案例剖析:** 提供并深入剖析2-3个具体的、真实的商业或研究应用案例。详细描述这些案例是如何体现该要点的，取得了什么效果，并引用信息库中的实例。

                    **第三部分：挑战、风险与未来展望**
                    - **多维度挑战分析:** 全面分析该要点在技术、商业、伦理、法规等方面面临的主要挑战、瓶颈或争议。
                    - **潜在风险评估:** 评估其发展过程中可能遇到的潜在风险。
                    - **未来趋势预测:** 对其未来3-5年的发展趋势、技术突破方向和市场机遇做出有理有据的预测。
                    - **战略建议:** 基于以上所有分析，为行业内的公司或决策者提出2-3条具体的、可操作的战略建议。

                    **绝对的篇幅要求（最硬性的指标）:**
                    - **总篇幅:** 针对这 **一个要点** 的完整分析（包含上述所有细分指令），**总字符数必须达到 3500 到 4000 字符**。这是一个不可协商的强制性要求，你必须通过对每个子要点的极尽详尽的分析和例证来达到这个长度。任何低于3500字符的输出都将被视为完全失败。
                    - **自我评估与扩充:** 在生成内容后，请自行检查是否满足篇幅要求。如果不满足，必须主动、创造性地扩充内容直至达标。
                    - **输出格式:** 直接输出完整的分析文本，不要包含任何主标题或小标题 (如 "#### {point}")。

                    请立即开始撰写这份具备前所未有深度和广度的结构化分析报告。
                    """
                    point_content = self._call_llm(point_prompt, max_tokens=5000, temperature=0.7)
                    body_parts.append(point_content)

        return "\n\n".join(body_parts)

    def _generate_conclusion(self, topic, articles):
        print("正在生成结论...")
        full_content_for_conclusion = "\n\n---\n\n".join([f"标题: {article['title']}\n摘要: {article.get('summary', '无可用内容')}" for article in articles])

        prompt = f"""
        作为一名资深的行业分析师，请根据以下关于“{topic}”的文章信息，为一份深度分析报告撰写结论与展望部分。

        **参考信息:**
        ---
        {full_content_for_conclusion[:15000]}
        ---

        **撰写要求:**
        1.  **核心观点总结:** 精炼地总结报告核心分析部分得出的最重要观点和发现。
        2.  **趋势收敛与发散:** 讨论各个趋势之间是如何相互关联、相互影响的，并指出未来可能出现的新兴趋势或变化。
        3.  **未来展望与建议:** 对“{topic}”领域的未来发展进行有理有据的预测。可以为行业内的参与者（如企业、投资者、研究人员）提出具体的战略建议。
        4.  **语言风格:** 高度概括、富有前瞻性、结论明确。
        5.  **篇幅要求:** 1000 - 1500字。
        """
        
        return self._call_llm(prompt)

    def _call_llm(self, prompt, max_tokens=2000, temperature=0.7):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一名顶级的行业分析师和内容创作者，擅长撰写深度、详尽、专业的分析报告。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"调用LLM时出错: {e}")
            return f"无法生成内容，错误: {e}"