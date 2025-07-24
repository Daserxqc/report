import os
import json
import datetime
from openai import OpenAI
import config
import pandas as pd
from tqdm import tqdm

class ReportGenerator:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key if api_key else config.OPENAI_API_KEY
        self.base_url = base_url if base_url else config.OPENAI_BASE_URL
        
        # Initialize OpenAI client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            
        self.client = OpenAI(**client_kwargs)
        
        # 使用 dashscope 配置，统一使用 deepseek-v3 模型
        self.default_models = {
            "chat": ["deepseek-v3"],  # 使用 dashscope 的 deepseek-v3 模型
            "embedding": ["embedding"]
        }
        print("使用 dashscope API，已配置 deepseek-v3 模型")
        
        # Create output directory if it doesn't exist
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
    def call_openai_with_fallback(self, messages, max_tokens=None, temperature=None, purpose="chat"):
        """
        Call OpenAI API, try to use fallback model if error occurs
        
        Args:
            messages (list): List of messages
            max_tokens (int): Maximum number of tokens to generate
            temperature (float): Generation temperature
            purpose (str): Purpose (chat or embedding)
            
        Returns:
            str: Generated content
        """
        models = self.default_models.get(purpose, self.default_models["chat"])
        last_error = None
        
        for model in models:
            try:
                if purpose == "chat":
                    kwargs = {
                        "model": model,
                        "messages": messages
                    }
                    if max_tokens:
                        kwargs["max_tokens"] = max_tokens
                    if temperature is not None:
                        kwargs["temperature"] = temperature
                    
                    response = self.client.chat.completions.create(**kwargs)
                    return response.choices[0].message.content.strip()
                    
            except Exception as e:
                last_error = str(e)
                print(f"使用模型 {model} 时出错: {str(e)}")
                if len(models) > 1:  # 只有当有多个模型可尝试时才显示"尝试下一个模型"
                    print("尝试下一个模型...")
                continue
        
        # 所有模型都失败时的处理
        print("dashscope API调用失败。可能的原因：")
        print("1. API密钥不正确或已过期")
        print("2. 使用了不支持的参数")
        print("3. 服务器暂时不可用")
        
        # 如果所有模型都失败，返回一个基本回应
        fallback_msg = f"无法生成内容。请检查API配置或尝试稍后再试。最后错误: {last_error}"
        print(fallback_msg)
        return fallback_msg
        
    def categorize_content(self, articles, categories):
        """
        使用GPT将文章分类到预定义的类别中
        
        Args:
            articles (list): 文章字典列表
            categories (list): 类别名称列表
            
        Returns:
            dict: 将类别映射到文章列表的字典
        """
        categorized = {category: [] for category in categories}
        
        for article in tqdm(articles, desc="正在分类文章"):
            # 创建分类提示
            prompt = f"""
            请将以下文章分配到这个列表中最相关的类别：{', '.join(categories)}。
            
            文章标题：{article['title']}
            文章摘要：{article['summary']}
            
            只返回类别名称，不要返回其他内容。
            """
            
            try:
                category = self.call_openai_with_fallback(
                    messages=[
                        {"role": "system", "content": "您是一位能够准确分类内容的助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=50,
                    temperature=0.3
                )
                
                # 如果响应不是有效类别，则放入第一个类别
                if category not in categories:
                    category = categories[0]
                    
                categorized[category].append(article)
                
            except Exception as e:
                print(f"文章 {article['title']} 分类出错: {str(e)}")
                # 错误时默认为第一个类别
                categorized[categories[0]].append(article)
                
        return categorized
        
    def generate_article_summary(self, article):
        """
        生成文章的简洁摘要
        
        Args:
            article (dict): 文章字典
            
        Returns:
            str: 文章的简洁摘要
        """
        # 如果文章已经带有结构化标记，直接返回内容前60个字符作为摘要
        if article.get('structured_section', False):
            content = article.get('content', '')
            summary = content[:200] + '...' if len(content) > 200 else content
            return summary
        
        # 创建摘要提示
        prompt = f"""
        请为这篇文章提供一个2-3句话的简明摘要。关注关键发现、创新或新闻。
        
        标题：{article['title']}
        作者：{', '.join(article['authors'])}
        摘要：{article['summary']}
        
        摘要应该信息丰富，突出最重要的方面。请使用中文撰写。
        """
        
        try:
            summary = self.call_openai_with_fallback(
                messages=[
                    {"role": "system", "content": "您是一位能够提供简明、信息丰富的中文摘要的助手。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.5
            )
            
            # 检查是否需要翻译
            summary = self.translate_to_chinese(summary)
            return summary
            
        except Exception as e:
            print(f"文章 {article['title']} 摘要生成出错: {str(e)}")
            # 检查原摘要是否需要翻译
            if article['summary']:
                translated_summary = self.translate_to_chinese(article['summary'])
                return translated_summary
            return article['summary']
            
    def generate_report_section(self, category, articles, max_articles=None):
        """
        为一个类别生成报告部分
        
        Args:
            category (str): 类别名称
            articles (list): 类别中的文章列表
            max_articles (int): 要包含的最大文章数
            
        Returns:
            str: Markdown格式的报告部分
        """
        if max_articles is None:
            max_articles = config.MAX_ARTICLES_PER_CATEGORY
            
        # 确保所有文章都是字典类型
        valid_articles = []
        for article in articles:
            if not isinstance(article, dict):
                print(f"警告: 在{category}分类中发现非字典类型的文章: {article}")
                continue
            valid_articles.append(article)
            
        # 检查是否有结构化章节
        structured_articles = [a for a in valid_articles if a.get('structured_section', False)]
        reference_articles = [a for a in valid_articles if a.get('is_reference', False)]
        regular_articles = [a for a in valid_articles if not a.get('structured_section', False) and not a.get('is_reference', False)]
        
        # 如果有结构化章节，优先使用这些来生成报告
        if structured_articles:
            print(f"为{category}类别生成结构化报告章节")
            
            # 对结构化章节按order或title排序
            structured_articles.sort(key=lambda x: x.get('order', 0))
            
            # 构建结构化章节
            section_content = f"\n## {category}\n\n"
            
            for article in structured_articles:
                section_content += f"### {article['title']}\n\n"
                section_content += f"{article['content']}\n\n"
            
            # 添加参考资料（如果有）
            if reference_articles:
                for ref_article in reference_articles:
                    section_content += f"{ref_article['content']}\n\n"
            
            return section_content
            
        # 否则使用常规方法处理普通文章
        # 按日期排序（最新的在前）
        regular_articles = sorted(regular_articles, key=lambda x: x.get('published', ''), reverse=True)
        
        # 限制文章数量
        regular_articles = regular_articles[:max_articles]
        
        # 为每篇文章生成摘要
        article_sections = []
        
        for i, article in enumerate(regular_articles):
            if i >= max_articles:
                break
                
            summary = self.generate_article_summary(article)
            authors = ', '.join(article['authors']) if article['authors'] else '未知'
            
            article_section = f"""
### {i+1}. {article['title']}

**来源**: {article['source']} | **日期**: {article['published']} | **作者**: {authors}

{summary}

**链接**: [{article['url']}]({article['url']})
"""
            article_sections.append(article_section)
            
        # 合并文章部分
        combined_sections = '\n'.join(article_sections)
        
        # 创建部分标题
        section = f"""
## {category}

{combined_sections}
"""
        return section
        
    def translate_to_chinese(self, text):
        """
        将英文文本翻译成中文
        
        Args:
            text (str): 要翻译的文本
            
        Returns:
            str: 翻译后的中文文本
        """
        # 使用OpenAI API进行翻译
        try:
            if not text or len(text.strip()) < 5:  # 文本太短或为空则不翻译
                return text
                
            # 简单检测是否为英文文本(如果超过70%的字符是ASCII，则认为是英文)
            ascii_chars = sum(1 for c in text if ord(c) < 128)
            if ascii_chars / len(text) < 0.7:
                # 大部分是非ASCII字符，可能已经是中文
                return text
                
            print("检测到英文内容，尝试翻译...")
            
            # 获取当前配置的模型列表
            models_to_try = self.default_models["chat"]
            print(f"将使用配置的模型进行翻译: {models_to_try}")
            
            # 配置翻译提示
            system_content = "你是一位专业翻译，请将非中文内容翻译成流畅、准确的中文。保留专业术语和技术细节。"
            user_content = f"将以下非中文内容翻译成中文:\n\n{text}"
            
            # 尝试翻译
            try:
                for model_name in models_to_try:
                    try:
                        # 调用API翻译
                        response = self.client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": system_content},
                                {"role": "user", "content": user_content}
                            ],
                            temperature=0.3,
                            max_tokens=1500
                        )
                        
                        translated_text = response.choices[0].message.content.strip()
                        print(f"使用模型{model_name}翻译完成")
                        return translated_text
                    except Exception as model_error:
                        print(f"模型{model_name}翻译失败: {str(model_error)}")
                        continue
                
                # 如果所有模型都失败，使用自带翻译方法
                print("所有配置的模型翻译失败，使用备用翻译方法")
                return self._basic_translate(text)
                
            except Exception as api_error:
                print(f"API翻译初始化失败: {str(api_error)}")
                return self._basic_translate(text)
                
        except Exception as general_error:
            print(f"翻译过程中出现意外错误: {str(general_error)}")
            # 出现任何错误，直接返回原文
            return text
            
    def _basic_translate(self, text):
        """
        当API翻译失败时，使用基本的关键词替换进行简单翻译
        
        Args:
            text (str): 要翻译的文本
            
        Returns:
            str: 处理后的文本
        """
        print("使用备用翻译方法 - 添加中文标记")
        
        # 非API翻译方法：目前不对文本进行处理，但不添加明显的技术性注释
        return f"{text}\n\n[本节包含外文内容。]"

    def generate_introduction(self, topic, articles):
        """
        为报告生成介绍
        
        Args:
            topic (str): 报告主题
            articles (list): 报告中的所有文章
            
        Returns:
            str: Markdown格式的介绍
        """
        # 创建介绍提示
        prompt = f"""
        请为一篇关于{topic}最新行业趋势的报告写一个介绍。
        该报告分为三个主要部分：
        1. 行业最新动态 - 公司和组织的最新发展
        2. 研究方向 - 最新学术研究和突破
        3. 行业洞察 - {topic}领域的分析、趋势，包括产业概况、政策、市场、技术趋势等全面信息
        
        介绍应当:
        1. 提供当前领域状况的背景
        2. 强调最近发展中观察到的关键趋势或主题
        3. 写3-4段长
        
        介绍必须使用中文撰写，面向中国读者。
        """
        
        try:
            introduction = self.call_openai_with_fallback(
                messages=[
                    {"role": "system", "content": "您是一位行业分析师，提供深入的行业分析和趋势洞察。请使用中文编写。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=700,
                temperature=0.7
            )
            
            # 检查内容是否为英文，如果是则翻译
            introduction = self.translate_to_chinese(introduction)
            
            # 组织为Markdown
            introduction = f"""
# {topic}行业趋势报告（{datetime.datetime.now().strftime('%Y年%m月%d日')}）

{introduction}
"""
            return introduction
            
        except Exception as e:
            print(f"生成介绍出错: {str(e)}")
            # 提供简单的后备介绍
            return f"""
# {topic}行业趋势报告（{datetime.datetime.now().strftime('%Y年%m月%d日')}）

本报告提供了关于{topic}行业的最新趋势、研究方向和行业洞察的全面概览。
"""
            
    def generate_conclusion(self, topic, articles):
        """
        为报告生成结论
        
        Args:
            topic (str): 报告主题
            articles (list): 报告中的所有文章
            
        Returns:
            str: Markdown格式的结论
        """
        # 提取所有文章的标题和摘要
        article_info = []
        for article in articles:
            if article.get('title') and article.get('summary'):
                article_info.append(f"标题: {article['title']}\n摘要: {article['summary']}")
                
        # 如果文章太多，只取前20个
        if len(article_info) > 20:
            article_info = article_info[:20]
            
        # 连接文章信息
        article_text = "\n\n".join(article_info)
        
        # 创建结论提示
        prompt = f"""
        基于以下文章摘要，为{topic}行业趋势报告写一个结论部分。
        
        {article_text}
        
        结论应当:
        1. 总结重要发现和趋势
        2. 讨论对行业的短期和长期影响
        3. 提供未来展望和潜在机会
        4. 写2-3段，言简意赅
        5. 使用中文撰写，面向中国读者
        """
        
        try:
            conclusion = self.call_openai_with_fallback(
                messages=[
                    {"role": "system", "content": "您是一位行业分析师，能够提供深入的行业分析和预测。必须使用中文。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # 检查是否需要翻译
            conclusion = self.translate_to_chinese(conclusion)
            
            # 组织为Markdown
            conclusion = f"""
## 结论

{conclusion}
"""
            return conclusion
            
        except Exception as e:
            print(f"生成结论出错: {str(e)}")
            # 提供简单的后备结论
            return f"""
## 结论

{topic}行业正在快速发展和变化。基于我们的研究，未来几年将出现多项重要趋势和机遇。企业需要密切关注技术创新、市场需求变化和竞争格局，以在这个不断变化的生态系统中保持竞争力。
"""
            
    def generate_section_reports(self, topic, section_articles):
        """
        基于预定义的报告结构生成报告部分
        
        Args:
            topic (str): 报告主题
            section_articles (dict): 将部分名称映射到文章列表的字典
            
        Returns:
            list: 生成的部分报告列表
        """
        section_reports = []
        
        for section in config.REPORT_SECTIONS:
            if section in section_articles and section_articles[section]:
                section_report = self.generate_report_section(section, section_articles[section])
                section_reports.append(section_report)
                
        return section_reports
            
    def evaluate_report_quality(self, report, topic):
        """
        评估报告的质量，并提供改进建议
        
        Args:
            report (str): 生成的报告内容
            topic (str): 报告主题
            
        Returns:
            dict: 包含质量评估和改进建议的字典
        """
        print("正在评估报告质量...")
        
        # 创建评估提示
        prompt = f"""
        请作为专业的行业分析师，评估以下{topic}行业报告的质量。
        
        评估标准:
        1. 专业性: 报告是否使用了专业术语和行业标准表述
        2. 结构性: 报告结构是否清晰合理，各部分是否有逻辑连贯性
        3. 完整性: 报告是否包含了行业的关键方面
        4. 客观性: 内容是否客观中立，避免了主观臆断
        5. 信息价值: 报告是否提供了有价值的见解和信息
        
        请详细评分(1-10分)并给出具体改进建议。
        
        报告内容:
        ```
        {report[:15000]}  # 限制长度避免超出token限制
        ...
        ```
        """
        
        try:
            evaluation = self.call_openai_with_fallback(
                messages=[
                    {"role": "system", "content": "您是一位专业的报告质量评估专家，精通行业分析报告的评估和改进。您的评估应客观、详细、有建设性。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # 将评估结果写入日志文件
            log_dir = os.path.join(config.OUTPUT_DIR, "evaluation_logs")
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, f"{topic.replace(' ', '_').lower()}_evaluation_{datetime.datetime.now().strftime('%Y%m%d')}.txt")
            
            # 检查评估内容中的中文字符
            chinese_chars = sum(1 for c in evaluation if '\u4e00' <= c <= '\u9fff')
            print(f"评估报告包含 {chinese_chars} 个中文字符")
            
            # 使用UTF-8-SIG编码保存
            with open(log_file, 'w', encoding='utf-8-sig') as f:
                f.write(f"# {topic}行业报告质量评估\n\n")
                f.write(evaluation)
            
            print(f"报告质量评估已保存至: {log_file}")
            
            # 提取评分和建议
            return {
                "evaluation": evaluation,
                "log_file": log_file
            }
            
        except Exception as e:
            print(f"报告质量评估出错: {str(e)}")
            return {
                "evaluation": f"无法完成报告质量评估: {str(e)}",
                "log_file": None
            }
            
    def generate_full_report(self, topic, section_articles):
        """
        使用三部分结构生成完整报告
        
        Args:
            topic (str): 报告主题
            section_articles (dict): 将部分名称映射到文章列表的字典
            
        Returns:
            str: Markdown格式的报告
        """
        # 扁平化所有文章以便生成介绍和结论
        all_articles = []
        for articles in section_articles.values():
            all_articles.extend(articles)
            
        # 确保我们有文章
        if not all_articles:
            return f"# {topic}行业趋势报告（{datetime.datetime.now().strftime('%Y年%m月%d日')}）\n\n未找到关于此主题的最新文章。"
            
        # 生成介绍
        introduction = self.generate_introduction(topic, all_articles)
        
        # 生成部分报告
        section_reports = self.generate_section_reports(topic, section_articles)
        
        # 生成结论
        conclusion = self.generate_conclusion(topic, all_articles)
        
        # 合并所有部分，不添加参考文献
        report = f"""
{introduction}

{'\n'.join(section_reports)}

{conclusion}
"""
        
        # 评估报告质量
        print("生成报告完成，正在评估报告质量...")
        evaluation_result = self.evaluate_report_quality(report, topic)
        
        # 保存报告
        filename = f"{topic.replace(' ', '_').lower()}_report_{datetime.datetime.now().strftime('%Y%m%d')}.md"
        filepath = os.path.join(config.OUTPUT_DIR, filename)
        
        # 检查报告中的中文字符数量
        chinese_chars = sum(1 for c in report if '\u4e00' <= c <= '\u9fff')
        print(f"报告包含 {chinese_chars} 个中文字符")
        
        # 使用UTF-8-SIG编码（带BOM标记）保存文件，确保中文正确显示
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(report)
            
        # 验证文件内容
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                read_chinese = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                if read_chinese == chinese_chars:
                    print(f"报告已正确保存至 {filepath}，中文字符验证成功")
                else:
                    print(f"警告: 文件保存可能存在问题，写入了{chinese_chars}个中文字符，但读取到{read_chinese}个")
        except Exception as e:
            print(f"文件验证失败: {str(e)}")
        
        if evaluation_result.get("log_file"):
            print(f"报告质量评估已保存至: {evaluation_result.get('log_file')}")
        
        return report 