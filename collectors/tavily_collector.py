import requests
import json
from datetime import datetime, timedelta
from tqdm import tqdm
import config
import re
import os
from tenacity import retry, stop_after_attempt, wait_exponential
from collectors.llm_processor import LLMProcessor
import time

class TavilyCollector:
    def __init__(self, api_key=None):
        self.api_key = api_key if api_key else config.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com/search"
        self.has_api_key = bool(self.api_key)
        
        # Initialize the LLM processor
        self.llm_processor = None
        
        if not self.has_api_key:
            print("Tavily API key not provided, using fallback methods for content generation")
            
    def _get_llm_processor(self):
        """
        Lazily initialize LLM processor to avoid unnecessary API connections
        """
        if self.llm_processor is None:
            # Check if we have OpenAI API key in config
            openai_key = getattr(config, "OPENAI_API_KEY", None)
            if openai_key:
                self.llm_processor = LLMProcessor()
                print("LLM Processor initialized for advanced content generation")
            else:
                print("OpenAI API key not found, LLM processing unavailable")
        return self.llm_processor

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search(self, query, search_depth="advanced", max_results=None):
        """
        使用Tavily API执行网络搜索
        
        Args:
            query (str): 搜索查询
            search_depth (str): 搜索深度
            max_results (int, optional): 最大结果数量
            
        Returns:
            list: 搜索结果列表
        """
        if not self.has_api_key:
            print("警告：无法执行搜索，未提供Tavily API密钥")
            return []
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"  # 使用Bearer令牌格式
        }
        
        # 确保max_results在合理范围内
        if max_results is None:
            max_results = config.TAVILY_MAX_RESULTS
        else:
            max_results = min(max_results, 20)  # 限制最大结果数，避免过多请求
        
        # 优化payload配置以提高可靠性
        payload = {
            "query": query,
            "search_depth": search_depth,
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,  # 默认设为False减轻响应大小，除非特别需要
            "max_results": max_results
        }
        
        try:
            print(f"正在搜索: {query}")
            start_time = time.time()
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            
            # 处理常见错误状态码
            if response.status_code == 429:  # 速率限制
                wait_time = int(response.headers.get('Retry-After', 30))
                print(f"API速率限制，等待{wait_time}秒后重试...")
                time.sleep(wait_time)
                # 重试请求
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            
            # 其他错误状态码处理    
            response.raise_for_status()
            
            # 计算响应时间
            response_time = time.time() - start_time
            result = response.json()
            
            # 获取结果数量
            results = result.get("results", [])
            total_count = len(results)
            
            if total_count == 0:
                print(f"警告：查询'{query}'未返回任何结果")
                
            # 最多返回max_results个结果，同时确保整合多个数据源的内容
            if max_results and max_results < total_count:
                print(f"限制结果数量从{total_count}个到{max_results}个")
                results = results[:max_results]
                
            print(f"成功获取'{query}'的搜索结果，共{len(results)}条 (用时{response_time:.2f}秒)")
            
            # 确保所有结果都有相同的字段结构
            for result in results:
                # 确保每个结果都有基本字段
                if 'content' not in result or not result['content']:
                    result['content'] = result.get('snippet', '')
                
                if 'title' not in result or not result['title']:
                    result['title'] = "未知标题"
                    
                if 'url' not in result:
                    result['url'] = "#"
                    
                # 确保有source字段
                if 'source' not in result or not result['source']:
                    url = result.get('url', '')
                    if url and url != "#":
                        try:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(url)
                            result['source'] = parsed_url.netloc
                        except:
                            result['source'] = "未知来源"
                    else:
                        result['source'] = "未知来源"
            
            # 让搜索API在多次调用之间短暂休息，以避免速率限制
            time.sleep(1)
            
            return results
            
        except requests.exceptions.Timeout:
            print(f"搜索超时: '{query}'")
            return []
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else "未知"
            print(f"HTTP错误 ({status_code}): {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"API响应: {e.response.text}")
            return []
        except Exception as e:
            print(f"搜索时出错: {str(e)}")
            # 记录更多调试信息
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"API响应: {e.response.text}")
            return []

    def get_company_news(self, company, topic, days=7, max_results=15):
        """
        获取特定公司相关的最新新闻
        
        Args:
            company (str): 公司名称
            topic (str): 主题领域
            days (int): 天数范围，默认7天
            max_results (int): 返回的最大结果数，默认10条
            
        Returns:
            list: 包含新闻信息的列表
        """
        try:
            # 构造查询，强化时间约束
            current_year = datetime.now().year
            search_query = f"{company} {topic} 最新动态 新闻 {current_year}年 最新"
            print(f"搜索: {search_query}")
            
            # 执行搜索 - 获取比需要的更多结果，以便后续筛选
            search_results = self.search(search_query, max_results=max_results * 2)
            
            if not search_results:
                print(f"未找到 {company} 相关新闻")
                return []
                
            # 处理结果
            raw_news_items = []
            for result in search_results:
                news_item = {
                    "title": result.get("title", "无标题"),
                    "content": result.get("content", "无内容"),
                    "url": result.get("url", "#"),
                    "source": result.get("source", "未知来源"),
                    "company": company,
                    "news_type": "company_news",
                    "published_date": result.get("published_date", "未知日期")
                }
                raw_news_items.append(news_item)
            
            # 对公司新闻进行相关性评估
            llm_processor = self._get_llm_processor()
            
            # 评估标准适合公司新闻
            company_criteria = {
                "主题相关性": 0.5,  # 提高相关性权重，确保新闻真正与公司相关
                "时效性": 0.3,
                "信息质量": 0.15,
                "来源可靠性": 0.05
            }
            
            # 首先进行时间过滤
            time_filtered_news = self._filter_by_date(raw_news_items, days)
            
            # 执行相关性评估
            scored_news = self.evaluate_content_relevance(
                time_filtered_news,
                f"{company} {topic}",
                criteria=company_criteria,
                llm_processor=llm_processor
            )
            
            # 保留评分最高的结果
            news_items = scored_news[:max_results]
            
            print(f"为 {company} 找到 {len(news_items)}/{len(raw_news_items)} 条高相关性新闻")
            return news_items
            
        except Exception as e:
            print(f"获取{company}相关新闻时出错: {str(e)}")
            return []

    def get_company_news_bulk(self, companies, days_back=7):
        """
        批量获取多个公司新闻
        
        Args:
            companies (list): 公司名称列表
            days_back (int): 获取多少天内的新闻
            
        Returns:
            list: 新闻列表
        """
        all_news = []
        
        for company in companies:
            query = f"{company} news latest {days_back} days"
            results = self.search(query, max_results=5)
            
            for result in results:
                result["company"] = company
                all_news.append(result)
                
        return all_news

    def generate_research_insights_fallback(self, topic, subtopics=None):
        """
        当Tavily API不可用时生成研究洞察的备用方法
        
        Args:
            topic (str): 主题
            subtopics (list, optional): 子主题列表
            
        Returns:
            list: 生成的洞察文章列表
        """
        print("使用备用方法生成研究洞察...")
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        if not subtopics:
            subtopics = ["概述", "最新发展", "市场前景", "主要挑战", "未来趋势"]
            
        insights = []
        
        for i, subtopic in enumerate(subtopics):
            article = {
                "title": f"{topic} - {subtopic}",
                "content": f"关于{topic}的{subtopic}的深入分析。由于无法访问实时数据，这是一个占位内容。请检查API密钥配置或网络连接，以获取实际内容。",
                "url": "#",
                "source": "系统生成",
                "published": current_date,
                "authors": ["System"]
            }
            insights.append(article)
            
        return insights

    def get_research_insights(self, topic, subtopics=None):
        """
        获取主题的研究洞察
        
        Args:
            topic (str): 研究主题
            subtopics (list, optional): 子主题列表
            
        Returns:
            dict: 包含洞察和来源的字典
        """
        if not subtopics:
            subtopics = ["概述", "最新发展", "市场前景", "主要挑战", "未来趋势"]
            
        if not self.has_api_key:
            print("Tavily API密钥未提供，使用备用方法生成内容")
            insights_articles = self.generate_research_insights_fallback(topic, subtopics)
            return {
                "content": "\n\n".join([f"## {article['title']}\n\n{article['content']}" for article in insights_articles]),
                "sources": [{"title": article["title"], "url": article["url"]} for article in insights_articles]
            }
            
        # 使用Tavily API获取研究洞察
        all_results = []
        
        for subtopic in subtopics:
            query = f"{topic} {subtopic} latest research insights analysis"
            results = self.search(query, max_results=2)
            all_results.extend(results)
            
        # 如果没有结果，使用备用方法
        if not all_results:
            print("无法获取研究洞察，使用备用方法")
            insights_articles = self.generate_research_insights_fallback(topic, subtopics)
        else:
            # 处理结果
            insights_articles = []
            
            for result in all_results:
                article = {
                    "title": result.get("title", f"{topic} 研究"),
                    "content": result.get("content", "内容未提供"),
                    "url": result.get("url", "#"),
                    "source": result.get("source", "网络搜索"),
                    "published": result.get("published_date", datetime.now().strftime('%Y-%m-%d')),
                    "authors": result.get("authors", ["未知"]),
                    "topic": topic
                }
                insights_articles.append(article)
                
        # 创建报告内容
        report_content = f"# {topic} 研究洞察\n\n"
        
        for article in insights_articles:
            report_content += f"## {article['title']}\n\n"
            report_content += f"**来源**: {article['source']} | **日期**: {article['published']} | **作者**: {', '.join(article['authors'])}\n\n"
            report_content += f"{article['content']}\n\n"
            report_content += f"**链接**: [{article['url']}]({article['url']})\n\n"
            
        return {
            "content": report_content,
            "sources": [{"title": article["title"], "url": article["url"]} for article in insights_articles]
        }

    def generate_industry_insights_fallback(self, topic, subtopics=None):
        """
        生成行业洞察的备用方法，当API不可用时使用
        
        Args:
            topic (str): 主题/行业
            subtopics (list, optional): 子主题列表
            
        Returns:
            list: 生成的洞察文章列表
        """
        print("使用备用方法生成行业洞察...")
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        if not subtopics:
            subtopics = ["行业概况", "政策支持", "市场规模", "技术趋势", "未来展望"]
            
        insights = []
        
        for i, subtopic in enumerate(subtopics):
            article = {
                "title": f"{topic} - {subtopic}",
                "content": f"关于{topic}的{subtopic}的深入分析。由于无法访问实时数据，这是一个占位内容。请检查API密钥配置或网络连接，以获取实际内容。",
                "url": "#",
                "source": "系统生成",
                "published": current_date,
                "authors": ["System"]
            }
            insights.append(article)
            
        return insights

    def translate_to_chinese(self, text):
        """
        将英文文本翻译为中文
        
        Args:
            text (str): 需要翻译的文本
            
        Returns:
            str: 翻译后的中文文本
        """
        # 尝试使用LLM处理器翻译
        llm_processor = self._get_llm_processor()
        if llm_processor:
            try:
                return llm_processor.translate_text(text, "中文")
            except Exception as e:
                print(f"LLM翻译失败，使用备用翻译方法: {str(e)}")
        
        # 备用翻译方法
        if not text or len(text.strip()) == 0:
            print("警告: 收到空文本，跳过翻译")
            return ""
        
        # 检查是否主要是英文
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        if ascii_chars / len(text) < 0.7:
            print("文本主要是非英文，无需翻译")
            return text
        
        try:
            # 获取API配置
            api_key = config.OPENAI_API_KEY if hasattr(config, 'OPENAI_API_KEY') else None
            base_url = config.OPENAI_BASE_URL if hasattr(config, 'OPENAI_BASE_URL') else "https://api.openai.com"
            
            if not api_key:
                print("未找到OpenAI API密钥，无法翻译内容")
                return text
                
            # 检查URL格式
            if base_url.endswith('/'):
                base_url = base_url[:-1]
                
            if "/v1" not in base_url:
                base_url += "/v1"
                
            # 构建请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            prompt = f"请将以下英文文本翻译成中文，直接给出翻译结果，不要有任何额外说明：\n\n{text}"
            
            # 准备请求数据
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "你是一个专业的翻译助手，请将英文文本翻译成中文，保持专业准确。直接给出翻译结果，不要包含任何解释或额外文字。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            }
            
            # 发送请求
            response = requests.post(f"{base_url}/chat/completions", headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # 提取翻译后的文本
            translated_text = result["choices"][0]["message"]["content"]
            
            # 清理可能的元信息
            # 有时LLM会在开头加上"翻译："等字样，需要移除
            patterns = [
                "翻译:", "翻译：", "以下是翻译:", "以下是翻译：",
                "翻译结果:", "翻译结果：", "译文:", "译文："
            ]
            for pattern in patterns:
                if translated_text.startswith(pattern):
                    translated_text = translated_text[len(pattern):].strip()
                    
            # 清理其他可能的问题
            # 有时翻译会包含类似"[Original English text]"的部分
            translated_text = re.sub(r'\[.*?English.*?\]', '', translated_text)
            translated_text = re.sub(r'\(.*?English.*?\)', '', translated_text)
            
            return translated_text
            
        except Exception as e:
            print(f"翻译时出错: {str(e)}")
            return text

    def _is_mainly_english(self, text):
        """
        判断文本是否主要为英文
        
        Args:
            text (str): 需要判断的文本
            
        Returns:
            bool: 如果文本主要为英文返回True，否则返回False
        """
        if not text:
            return False
            
        # 计算ASCII字符的比例
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        return ascii_chars / len(text) > 0.7

    def get_industry_insights(self, topic, subtopics=None):
        """
        获取行业洞察
        
        Args:
            topic (str): 行业主题
            subtopics (list, optional): 子主题列表
            
        Returns:
            dict: 包含洞察和来源的字典
        """
        if not subtopics:
            # 默认使用标准的行业报告章节结构
            subtopics = ["行业概况", "政策支持", "市场规模", "技术趋势", "未来展望"]
        
        # 检查Tavily API可用性
        if not self.has_api_key:
            print("Tavily API密钥未提供，使用备用方法生成内容")
            insights_articles = self.generate_industry_insights_fallback(topic, subtopics)
            return self._format_fallback_results(insights_articles)
            
        # 使用多个查询以增加信息的广度和深度
        queries = []
        
        # 按章节创建更具体的查询
        for section in subtopics:
            if section == "行业概况":
                queries.append({"query": f"{topic} 行业概况 主要参与者 市场特点", "section": section})
            elif section == "政策支持":
                queries.append({"query": f"{topic} 政策支持 扶持政策 监管框架", "section": section})
            elif section == "市场规模":
                queries.append({"query": f"{topic} 市场规模 增长率 份额 数据", "section": section})
            elif section == "技术趋势":
                queries.append({"query": f"{topic} 技术趋势 创新 研发方向", "section": section})
            elif section == "未来展望":
                queries.append({"query": f"{topic} 未来展望 发展预测 机遇 挑战", "section": section})
            else:
                # 处理自定义章节
                queries.append({"query": f"{topic} {section} 最新信息 分析", "section": section})
        
        # 执行多个查询并收集结果
        all_results = []
        query_errors = 0
        
        for query_info in queries:
            query = query_info["query"]
            section = query_info["section"]
            
            try:
                # 每次查询限制结果数量，避免信息过载
                results = self.search(query, max_results=5)  # 增加初始结果数以便后续筛选
                
                # 调试: 输出每个查询的结果
                print(f"查询 '{query}' 返回了 {len(results)} 条结果")
                
                if not results:
                    print(f"警告: 查询 '{query}' 没有返回任何结果")
                    continue
                
                # 验证结果格式
                for i, result in enumerate(results):
                    if not isinstance(result, dict):
                        print(f"警告: 查询 '{query}' 的第 {i+1} 条结果不是字典类型: {type(result)}")
                        continue
                        
                    # 确保result有必要的字段
                    if "content" not in result or not result["content"]:
                        print(f"警告: 查询 '{query}' 的第 {i+1} 条结果缺少content字段")
                        # 设置一个默认的content值
                        result["content"] = f"关于{query}的内容未获取到详细信息。"
                    
                    # 设置章节字段
                    result["section"] = section
                
                # 添加到总结果集
                all_results.extend(results)
                
            except Exception as e:
                print(f"查询'{query}'时出错: {str(e)}")
                query_errors += 1
        
        # 调试: 输出所有查询的结果总数        
        print(f"总共获取到 {len(all_results)} 条搜索结果")
                
        # 如果所有查询都失败，或结果太少，使用fallback生成
        if query_errors == len(queries) or len(all_results) == 0:
            print("所有查询失败或没有返回结果，使用备用生成方法")
            insights_articles = self.generate_industry_insights_fallback(topic, subtopics)
            return self._format_fallback_results(insights_articles)
            
        # 获取LLM处理器进行相关性评分
        llm_processor = self._get_llm_processor()
        
        # 对所有获取的结果进行相关性评估
        print("对搜索结果进行相关性评估和排序...")
        section_results = {}
        
        # 按章节分组结果，并为每个章节的结果评分
        for section in subtopics:
            section_items = [item for item in all_results if item.get("section") == section]
            if section_items:
                # 评估该章节内容的相关性
                scored_items = self.evaluate_content_relevance(section_items, f"{topic} {section}", llm_processor=llm_processor)
                # 每个章节保留最相关的3条结果
                section_results[section] = scored_items[:3]
                print(f"章节 '{section}' 评估完成，保留 {len(section_results[section])}/{len(scored_items)} 条最相关结果")
        
        # 重建筛选后的结果列表
        filtered_results = []
        for section_items in section_results.values():
            filtered_results.extend(section_items)
            
        print(f"相关性评估完成，从{len(all_results)}条结果中筛选出{len(filtered_results)}条高相关性内容")
        
        # 使用筛选后的高质量结果组织内容并生成报告
        return self.organize_industry_insights(filtered_results, topic, subtopics)

    def _format_fallback_results(self, insights_articles):
        """
        格式化备用生成的结果为统一的报告格式
        
        Args:
            insights_articles (list): 洞察文章列表
            
        Returns:
            dict: 包含格式化内容和来源的字典
        """
        # 获取当前日期
        current_date = datetime.now().strftime('%Y-%m-%d')
            
        # 检查文章列表是否为空
        if not insights_articles:
            return {
                "content": "# 行业洞察报告\n\n未能生成报告内容，请稍后再试。",
                "sources": [],
                "sections": [],
                "date": current_date
            }
            
        # 处理并修正每篇文章
        for article in insights_articles:
            if "content" not in article or not article["content"]:
                article["content"] = "暂无详细内容。"
                
        # 转换为统一的报告格式
        report_content = f"# {insights_articles[0].get('topic', '行业')}洞察报告\n\n"
        
        # 构建结构化的sections数组和收集参考资料
        structured_sections = []
        all_references = []
        
        for article in insights_articles:
            # 准备文章内容
            meta_info = f"**来源**: {article['source']} | **日期**: {article['published']} | **作者**: {', '.join(article['authors'])}\n\n"
            article_content = meta_info + f"{article['content']}\n\n"
            
            # 收集参考资料而不是直接添加链接
            all_references.append(f"- [{article['title']}]({article['url']})")
            
            # 使用H2级别标题
            report_content += f"## {article['title']}\n\n"
            report_content += article_content
            
            # 添加到结构化章节
            structured_sections.append({
                "title": article['title'],
                "content": article_content
            })
        
        # 在报告末尾添加参考资料部分
        report_content += "\n参考资料:\n"
        for ref in all_references:
            report_content += f"{ref}\n"
        
        # 检查报告中中文字符的数量
        chinese_chars = sum(1 for c in report_content if '\u4e00' <= c <= '\u9fff')
        print(f"报告生成完成，包含 {chinese_chars} 个中文字符")
        
        return {
            "content": report_content,
            "sources": [{"title": article["title"], "url": article["url"]} for article in insights_articles],
            "sections": structured_sections,
            "date": current_date
        }

    def _normalize_heading_structure(self, content):
        """
        规范化Markdown标题结构，确保正确的标题层级，并将参考资料移动到文档末尾
        
        Args:
            content (str): 原始Markdown内容
            
        Returns:
            str: 处理后的Markdown内容
        """
        import re
        
        # 1. 简单直接的规范化函数
        lines = content.split('\n')
        result_lines = []
        references = []
        i = 0
        
        # 第一步：扫描整个文档，提取所有参考资料和参考文献
        while i < len(lines):
            line = lines[i].strip()
            
            # 匹配各种可能的参考资料标记
            if (line.startswith('参考资料') or 
                line == '**参考来源**:' or line.startswith('**参考来源**:') or
                line == '参考来源:' or line.startswith('参考来源:')):
                i += 1
                # 收集直到下一个标题或结束
                while i < len(lines) and not lines[i].strip().startswith('#'):
                    if lines[i].strip().startswith('•') or lines[i].strip().startswith('-'):
                        references.append(lines[i].strip())
                    i += 1
                continue
                
            # 处理参考文献部分
            if line.startswith('## 参考文献') or line == '参考文献':
                i += 1
                # 收集已有参考文献
                while i < len(lines) and not lines[i].strip().startswith('#'):
                    if lines[i].strip().startswith('•') or lines[i].strip().startswith('-'):
                        references.append(lines[i].strip())
                    i += 1
                continue
                
            # 保留其他内容
            result_lines.append(lines[i])
            i += 1
        
        # 第二步：标准化标题层级
        processed_lines = []
        first_h1_found = False
        
        for line in result_lines:
            stripped = line.strip()
            
            # 空行直接保留
            if not stripped:
                processed_lines.append(line)
                continue
                
            # 处理标题层级
            if stripped.startswith('# '):
                if not first_h1_found:
                    first_h1_found = True
                    processed_lines.append(line)
                else:
                    # 其他H1标题降级为H2
                    processed_lines.append(line.replace('# ', '## ', 1))
            elif stripped.startswith('**') and stripped.endswith('**') and '**' not in stripped[2:-2]:
                # 独立的加粗行转为H3标题
                processed_lines.append('### ' + stripped[2:-2])
            else:
                processed_lines.append(line)
        
        # 第三步：移除重复的参考资料
        unique_references = []
        for ref in references:
            if ref not in unique_references:
                unique_references.append(ref)
        
        # 第四步：重建内容
        result = '\n'.join(processed_lines)
        
        # 规范化空行
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # 添加参考文献部分到文档末尾
        if unique_references:
            result = result.rstrip() + '\n\n## 参考文献\n\n'
            for ref in unique_references:
                result += ref + '\n'
        
        return result

    def organize_industry_insights(self, raw_results, topic, subtopics=None):
        """
        使用LLM处理器将原始搜索结果组织为结构化的行业洞察报告

        Args:
            raw_results (list): 原始搜索结果列表，每个结果包含标题、内容、URL和章节信息
            topic (str): 研究的主题/行业
            subtopics (list, optional): 子主题列表

        Returns:
            dict: 包含组织好的见解和来源的字典
        """
        if not raw_results:
            print("没有原始结果数据，无法组织内容")
            return {"content": "", "sources": []}
            
        try:
            # 尝试使用LLMProcessor处理内容
            llm_processor = self._get_llm_processor()
            
            if llm_processor:
                print(f"使用LLM处理器组织{len(raw_results)}条搜索结果数据")
                try:
                    result = llm_processor.organize_search_results(raw_results, topic)
                    # 规范化报告内容的标题结构
                    result["content"] = self._normalize_heading_structure(result["content"])
                    return result
                except Exception as llm_error:
                    print(f"LLM处理器处理失败: {str(llm_error)}")
                    import traceback
                    print(f"详细错误信息: {traceback.format_exc()}")
            
            # 如果没有LLM处理器或者LLM处理失败，使用直接整合方法
            print("使用简单整合方法处理搜索结果")
            
            # 整理分类
            sections = {}
            all_sources = []
            for result in raw_results:
                section = result.get("section", "其他信息")
                if section not in sections:
                    sections[section] = []
                sections[section].append(result)
                
                # 收集来源
                title = result.get("title", "")
                url = result.get("url", "#")
                all_sources.append({"title": title, "url": url})
            
            # 生成简单报告
            content = f"# {topic}行业洞察报告\n\n"
            structured_sections = []
            section_references = []
            
            for section_name, items in sections.items():
                if not items:
                    continue
                
                # 使用二级标题，确保标题加粗显示
                content += f"## {section_name}\n\n"
                section_content = ""
                
                # 汇总内容
                for item in items:
                    title = item.get("title", "")
                    item_content = item.get("content", "")
                    url = item.get("url", "#")
                    
                    # 使用三级标题突出小节标题
                    # 检查标题是否已经包含section_name，如果包含则不重复添加
                    clean_title = title
                    if section_name in title:
                        # 如果标题以section_name开头，则删除这部分重复内容
                        if title.startswith(section_name):
                            clean_title = title[len(section_name):].strip()
                            # 如果清理后标题以常见分隔符开头，去掉分隔符
                            for sep in [':', '：', '-', '—', '–', '|', '：']:
                                if clean_title.startswith(sep):
                                    clean_title = clean_title[1:].strip()
                                    break
                        # 使用处理后的标题
                        section_content += f"### {clean_title}\n\n"
                    else:
                        # 使用原标题
                        section_content += f"### {clean_title}\n\n"
                    
                    # 添加内容概要
                    summary = item_content[:500] + "..." if len(item_content) > 500 else item_content
                    section_content += f"{summary}\n\n"
                    
                    # 收集参考资料
                    section_references.append(f"- [{title}]({url})")
                
                content += section_content
                
                # 添加到结构化数据
                structured_sections.append({
                    "title": section_name,
                    "content": section_content
                })
            
            # 在内容末尾添加参考资料部分
            content += "\n\n参考资料:\n"
            for ref in section_references:
                content += f"{ref}\n"
            
            # 返回结构化报告
            current_date = datetime.now().strftime('%Y-%m-%d')
            result = {
                "content": content,
                "sources": all_sources,
                "sections": structured_sections,
                "date": current_date
            }
            
            # 规范化报告内容的标题结构
            result["content"] = self._normalize_heading_structure(result["content"])
            return result
                
        except Exception as e:
            print(f"组织行业洞察时出错: {str(e)}，使用系统生成的内容...")
            # 记录详细错误信息以帮助诊断
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            
            # 降级为使用备用生成方法
            insights_articles = self.generate_industry_insights_fallback(topic, subtopics)
            result = self._format_fallback_results(insights_articles)
            
            # 规范化最终生成的报告内容
            result["content"] = self._normalize_heading_structure(result["content"])
            return result

    def get_industry_trends(self, topic, days_back=7, max_results=10):
        """
        获取行业最新趋势和发展动态
        
        Args:
            topic (str): 行业主题
            days_back (int): 获取多少天内的趋势
            max_results (int): 最大结果数量
            
        Returns:
            list: 行业趋势列表
        """
        if not self.has_api_key:
            print("警告：无法执行搜索，未提供Tavily API密钥")
            return []
            
        # 创建更精准的搜索查询
        queries = [
            f"{topic} 行业 最新发展 {days_back}天",
            f"{topic} industry latest developments last {days_back} days",
            f"{topic} market trends news {days_back} days",
            f"{topic} breakthrough announcements {days_back} days",
            f"{topic} 突破 公告 最近动态 {days_back}天"
        ]
        
        all_results = []
        
        # 对每个查询使用重试机制来提高成功率
        for query in queries:
            try:
                print(f"获取{topic}行业趋势: {query}")
                
                # 使用重试机制增强搜索可靠性
                for attempt in range(3):
                    try:
                        results = self.search(query, search_depth="advanced", max_results=max_results//len(queries) + 1)
                        
                        if results:
                            # 检查是否有内容且添加元数据
                            for result in results:
                                result["topic"] = topic
                                result["query"] = query
                                result["trend_type"] = "industry_trend"
                                
                                # 检查结果是否已存在(基于URL去重)
                                if not any(r.get('url') == result.get('url') for r in all_results):
                                    all_results.append(result)
                            break  # 成功获取结果，跳出重试循环
                        else:
                            print(f"查询'{query}'尝试{attempt+1}/3失败，无结果")
                            time.sleep(2)  # 短暂暂停后重试
                    except Exception as e:
                        print(f"查询'{query}'尝试{attempt+1}/3出错: {str(e)}")
                        if attempt < 2:  # 如果不是最后一次尝试，就等待后重试
                            time.sleep(3)  # 出错后等待更长时间
            except Exception as e:
                print(f"处理查询'{query}'时出错: {str(e)}")
                
        print(f"总共获取{len(all_results)}条{topic}行业趋势信息")
        return all_results

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_government_news(self, topic, days_back=7, max_results=5):
        """
        获取与行业相关的政府政策和监管新闻
        
        Args:
            topic (str): 行业主题
            days_back (int): 获取多少天内的政策
            max_results (int): 最大结果数量
            
        Returns:
            list: 政策新闻列表
        """
        if not self.has_api_key:
            print("警告：无法执行搜索，未提供Tavily API密钥")
            return []
        
        # 构建政策相关查询
        policy_queries = [
            f"{topic} 政策 法规 监管 最新 {days_back}天",
            f"{topic} policy regulation government news {days_back} days",
            f"{topic} 产业政策 扶持 管理办法 {days_back}天"
        ]
        
        all_policy_results = []
        
        for query in policy_queries:
            try:
                print(f"获取{topic}政策新闻: {query}")
                results = self.search(query, search_depth="advanced", max_results=max_results)
                
                if results:
                    for result in results:
                        result["topic"] = topic
                        result["news_type"] = "policy"
                        
                        # 检查结果是否已存在(基于URL去重)
                        if not any(r.get('url') == result.get('url') for r in all_policy_results):
                            all_policy_results.append(result)
            except Exception as e:
                print(f"获取政策新闻时出错: {str(e)}")
        
        print(f"总共获取{len(all_policy_results)}条{topic}政策新闻")
        return all_policy_results
    
    def get_industry_news(self, topic, companies, days=7):
        """
        获取行业新闻，包括公司新闻和行业趋势
        
        Args:
            topic (str): 主题领域
            companies (list): 公司列表
            days (int): 天数范围
            
        Returns:
            dict: 包含处理后的行业新闻信息的字典
        """
        # 初始化结果字典
        result = {
            "breaking_news": [],    # 重大新闻
            "innovation_news": [],  # 创新新闻
            "trend_news": [],       # 行业趋势
            "policy_news": [],      # 政策新闻
            "investment_news": [],  # 投资新闻
            "company_news": [],     # 公司特定新闻
            "total_count": 0
        }
        
        print(f"\n=== 收集{topic}行业新闻 ===")
        
        # 1. 收集行业整体新闻
        industry_news = self.get_industry_news_direct(topic, days)
        
        # 合并行业新闻到结果中
        for news_type in ["breaking_news", "innovation_news", "trend_news", "policy_news", "investment_news"]:
            result[news_type] = industry_news.get(news_type, [])
        
        # 2. 如果有提供公司列表，收集公司特定新闻
        if companies and isinstance(companies, list):
            print(f"\n=== 收集{len(companies)}家公司相关新闻 ===")
            
            # 控制每家公司获取的新闻数量
            max_news_per_company = max(3, 15 // len(companies))
            
            # 为每家公司收集新闻
            for company in companies:
                company_news = self.get_company_news(company, topic, days, max_results=max_news_per_company)
                
                # 添加到公司新闻列表
                if company_news:
                    result["company_news"].extend(company_news)
                    print(f"找到 {len(company_news)} 条 {company} 相关新闻")
                else:
                    print(f"未找到 {company} 相关新闻")
        
        # 计算总新闻数
        total_count = sum(len(items) for items in result.values() if isinstance(items, list))
        result["total_count"] = total_count
        
        print(f"\n总计收集到 {total_count} 条高质量{topic}相关新闻")
        return result

    def get_industry_news_direct(self, topic, days=7, max_results=15):
        """
        直接搜索行业新闻，不依赖于特定公司，提供全面的行业动态
        
        Args:
            topic (str): 行业主题
            days (int): 要搜索的天数范围，默认7天
            max_results (int): 每种类型新闻的最大结果数，默认15条
            
        Returns:
            dict: 包含不同类型新闻的字典
        """
        result = {
            "breaking_news": [],    # 重大新闻
            "innovation_news": [],  # 创新新闻
            "trend_news": [],       # 行业趋势
            "policy_news": [],      # 政策新闻
            "investment_news": [],  # 投资新闻
            "total_count": 0
        }
        
        # 获取LLM处理器
        llm_processor = self._get_llm_processor()
        
        # 增强搜索策略：使用更广泛的行业关键词，强化时间约束
        current_year = datetime.now().year
        current_month = datetime.now().strftime('%Y年%m月')
        
        search_queries = {
            "breaking_news": [
                f"{topic} 行业 重大新闻 突发 重要事件 {current_year}年 最新",
                f"{topic} industry major news breaking events {current_year} latest recent",
                f"{topic} 行业 最新消息 {current_month} 重要新闻"
            ],
            "innovation_news": [
                f"{topic} 行业 技术创新 新产品 研发突破 {current_year}年 最新",
                f"{topic} industry technology innovation new products breakthrough {current_year} latest",
                f"{topic} 行业 创新应用 技术进展 {current_month} 最新"
            ],
            "trend_news": [
                f"{topic} 行业 市场趋势 发展动向 {current_year}年 最新",
                f"{topic} industry market trends developments {current_year} latest current",
                f"{topic} 行业 消费趋势 用户需求变化 {current_month} 最新"
            ],
            "policy_news": [
                f"{topic} 行业 政策法规 监管 新规 {current_year}年 最新",
                f"{topic} industry policy regulation compliance {current_year} latest new",
                f"{topic} 行业 政策支持 监管变化 {current_month} 最新"
            ],
            "investment_news": [
                f"{topic} 行业 投资 融资 并购 市场交易 {current_year}年 最新",
                f"{topic} industry investment funding acquisition market deals {current_year} latest",
                f"{topic} 行业 融资轮次 估值变化 投资方向 {current_month} 最新"
            ]
        }
        
        # 用于判断重复新闻的URL集合
        all_urls = set()
        
        # 执行各类新闻的搜索
        for news_type, queries in search_queries.items():
            try:
                raw_category_results = []
                
                # 对每个类型执行多个查询以增加覆盖面
                for query in queries:
                    print(f"搜索 {news_type}: {query}")
                    try:
                        # 使用更深入的搜索，增加初始结果数以便后续筛选
                        search_results = self.search(query, search_depth="advanced", max_results=max(8, max_results // len(queries) * 2))
                        
                        # 处理搜索结果
                        for item in search_results:
                            url = item.get("url", "")
                            
                            # 跳过已有的URL（去重）
                            if not url or url in all_urls:
                                continue
                                
                            # 添加必要的元数据
                            news_item = {
                                "title": item.get("title", "无标题"),
                                "content": item.get("content", "无内容"),
                                "url": url,
                                "source": item.get("source", "未知来源"),
                                "news_type": news_type,
                                "published_date": item.get("published_date", "未知日期"),
                                "query": query  # 记录来源查询
                            }
                            raw_category_results.append(news_item)
                            all_urls.add(url)
                    except Exception as search_error:
                        print(f"执行查询'{query}'时出错: {str(search_error)}")
                        # 单个查询失败不影响整体，继续下一个查询
                        continue
                
                # 在所有查询完成后对该类型的新闻进行整体评分
                print(f"为{news_type}评估相关性，共{len(raw_category_results)}条")
                if raw_category_results:
                    # 使用相关性评估方法对新闻进行评分和排序
                    # 具体评估标准依新闻类型有所调整
                    eval_criteria = {
                        "主题相关性": 0.35,
                        "时效性": 0.4,     # 提高时效性权重
                        "信息质量": 0.15,   # 略微降低
                        "来源可靠性": 0.1   # 保持不变
                    }
                    
                    # 对重大新闻和政策新闻更看重时效性
                    if news_type in ["breaking_news", "policy_news"]:
                        eval_criteria = {
                            "主题相关性": 0.3,
                            "时效性": 0.45,  # 进一步提高重大新闻的时效性权重
                            "信息质量": 0.15,
                            "来源可靠性": 0.1
                        }
                    # 对创新和趋势新闻更看重信息质量
                    elif news_type in ["innovation_news", "trend_news"]:
                        eval_criteria = {
                            "主题相关性": 0.35,
                            "时效性": 0.35,  # 保持较高的时效性权重
                            "信息质量": 0.2,
                            "来源可靠性": 0.1
                        }
                    # 对投资新闻使用标准权重
                    
                    # 首先进行时间过滤
                    time_filtered_results = self._filter_by_date(raw_category_results, days)
                    
                    # 然后执行评估
                    scored_news = self.evaluate_content_relevance(
                        time_filtered_results, 
                        f"{topic} {news_type.replace('_news', '')}",
                        criteria=eval_criteria,
                        llm_processor=llm_processor
                    )
                    
                    # 根据相关性得分筛选最相关的新闻
                    result[news_type] = scored_news[:max_results]
                    
                    print(f"筛选后保留 {len(result[news_type])}/{len(scored_news)} 条高相关性{news_type}")
                
            except Exception as e:
                print(f"搜索 {news_type} 新闻时出错: {str(e)}")
        
        # 尝试确保每个类别至少有一些结果（如果可能）
        for news_type, items in result.items():
            if isinstance(items, list) and not items:
                # 如果某类新闻为空，尝试更广泛的查询
                fallback_query = f"{topic} {news_type.replace('_news', '')} {days}天"
                try:
                    print(f"尝试更广泛的查询以获取 {news_type}: {fallback_query}")
                    fallback_results = self.search(fallback_query, max_results=5)
                    
                    raw_fallback_items = []
                    for item in fallback_results:
                        url = item.get("url", "")
                        if url and url not in all_urls:
                            news_item = {
                                "title": item.get("title", "无标题"),
                                "content": item.get("content", "无内容"),
                                "url": url,
                                "source": item.get("source", "未知来源"),
                                "news_type": news_type,
                                "query": fallback_query
                            }
                            raw_fallback_items.append(news_item)
                            all_urls.add(url)
                    
                    # 对补充结果也进行相关性评估
                    if raw_fallback_items:
                        scored_fallback = self.evaluate_content_relevance(
                            raw_fallback_items, 
                            f"{topic} {news_type.replace('_news', '')}",
                            llm_processor=llm_processor
                        )
                        # 保留评分最高的3条
                        result[news_type] = scored_fallback[:3]
                        
                    print(f"成功为 {news_type} 添加 {len(result[news_type])} 条高相关性补充新闻")
                except Exception as fallback_error:
                    print(f"尝试补充 {news_type} 新闻时出错: {str(fallback_error)}")
        
        # 计算总新闻数
        total_count = sum(len(items) for items in result.values() if isinstance(items, list))
        result["total_count"] = total_count
        
        print(f"共收集到 {total_count} 条不同类型的高相关性行业新闻")
        return result
    
    def _filter_by_date(self, items, days_limit):
        """
        根据时间限制过滤内容项 - 只依赖可靠的时间信息
        
        Args:
            items (list): 内容项列表
            days_limit (int): 天数限制
            
        Returns:
            list: 过滤后的内容项列表
        """
        if not items or days_limit <= 0:
            return items
            
        filtered_items = []
        cutoff_date = datetime.now() - timedelta(days=days_limit)
        current_year = datetime.now().year
        
        print(f"  🔍 开始严格时间过滤，要求最近{days_limit}天内的内容（截止日期：{cutoff_date.strftime('%Y-%m-%d')}）")
        print(f"  ⚠️ 注意：只接受有明确发布日期的内容，忽略'最新'、'今日'等关键词")
        
        for item in items:
            should_include = False
            filter_reason = ""
            
            title = item.get('title', '')
            content = item.get('content', '')
            combined_text = f"{title} {content}".lower()
            
            # 1. 首先检查是否包含明显的旧年份标识
            old_year_patterns = ['2024年', '2023年', '2022年', '2021年', '2020年']
            has_old_year = any(pattern in combined_text for pattern in old_year_patterns)
            
            if has_old_year:
                filter_reason = "包含旧年份标识"
                should_include = False
            else:
                # 2. 检查是否有可靠的发布日期信息
                published_date = item.get("published_date")
                
                if published_date and published_date != "未知日期":
                    try:
                        # 尝试解析发布日期
                        pub_date = None
                        
                        if isinstance(published_date, str):
                            # 尝试多种日期格式
                            date_formats = [
                                "%Y-%m-%d",
                                "%Y-%m-%d %H:%M:%S",
                                "%Y-%m-%dT%H:%M:%S",
                                "%Y-%m-%dT%H:%M:%S.%fZ",
                                "%Y-%m-%dT%H:%M:%SZ",
                                "%Y/%m/%d",
                                "%d/%m/%Y",
                                "%m/%d/%Y"
                            ]
                            
                            for fmt in date_formats:
                                try:
                                    pub_date = datetime.strptime(published_date, fmt)
                                    break
                                except ValueError:
                                    continue
                        
                        if pub_date:
                            # 有明确的发布日期，检查是否在时间范围内
                            if pub_date >= cutoff_date:
                                should_include = True
                                filter_reason = f"发布日期符合要求（{pub_date.strftime('%Y-%m-%d')}）"
                            else:
                                should_include = False
                                filter_reason = f"发布日期过早（{pub_date.strftime('%Y-%m-%d')}）"
                        else:
                            # 无法解析发布日期
                            should_include = False
                            filter_reason = "无法解析发布日期格式"
                            
                    except Exception as e:
                        should_include = False
                        filter_reason = f"发布日期解析失败: {str(e)}"
                        
                else:
                    # 3. 没有发布日期的情况 - 智能处理模糊日期
                    
                    # 检查是否包含模糊的日期格式（如"3月27日"、"12月15日"等）
                    import re
                    ambiguous_date_patterns = [
                        r'(\d{1,2})月(\d{1,2})日',  # 3月27日
                        r'(\d{1,2})/(\d{1,2})(?!\d)',  # 3/27 (但不是 3/27/2025)
                        r'(\d{1,2})-(\d{1,2})(?!\d)',  # 3-27 (但不是 3-27-2025)
                    ]
                    
                    ambiguous_date_match = None
                    for pattern in ambiguous_date_patterns:
                        match = re.search(pattern, combined_text)
                        if match:
                            ambiguous_date_match = match
                            break
                    
                    if ambiguous_date_match:
                        # 找到模糊日期，尝试智能判断
                        try:
                            month = int(ambiguous_date_match.group(1))
                            day = int(ambiguous_date_match.group(2))
                            
                            # 假设是当前年份，构造日期
                            current_date = datetime.now()
                            try:
                                assumed_date = datetime(current_date.year, month, day)
                                
                                # 检查这个日期是否在合理范围内
                                days_diff = (current_date - assumed_date).days
                                
                                if days_diff < 0:
                                    # 日期在未来，可能是去年的日期
                                    assumed_date = datetime(current_date.year - 1, month, day)
                                    days_diff = (current_date - assumed_date).days
                                
                                if days_diff <= days_limit:
                                    # 在时间范围内
                                    should_include = True
                                    filter_reason = f"模糊日期推测为{assumed_date.strftime('%Y-%m-%d')}，在时间范围内"
                                else:
                                    # 超出时间范围
                                    should_include = False
                                    filter_reason = f"模糊日期推测为{assumed_date.strftime('%Y-%m-%d')}，超出{days_limit}天范围"
                                    
                            except ValueError:
                                # 无效日期（如2月30日）
                                should_include = False
                                filter_reason = f"模糊日期{month}月{day}日无效"
                                
                        except (ValueError, IndexError):
                            # 解析失败
                            should_include = False
                            filter_reason = "模糊日期解析失败"
                    else:
                        # 没有模糊日期，检查是否包含当前年份的明确标识
                        current_year_patterns = [
                            f'{current_year}年',
                            f'年{current_year}',
                            f'{current_year}-',
                            f'{current_year}/'
                        ]
                        
                        has_current_year = any(pattern in combined_text for pattern in current_year_patterns)
                        
                        if has_current_year:
                            # 包含当前年份，但仍然要求是短期内的内容
                            if days_limit <= 30:
                                # 对于30天以内的要求，即使有当前年份也不够
                                should_include = False
                                filter_reason = f"包含{current_year}年但无具体日期（严格模式）"
                            else:
                                # 对于较长期的要求，可以接受
                                should_include = True
                                filter_reason = f"包含{current_year}年标识"
                        else:
                            # 既没有发布日期，也没有年份信息
                            should_include = False
                            filter_reason = "无发布日期且无年份信息"
            
            if should_include:
                filtered_items.append(item)
                if len(title) > 30:
                    print(f"    ✅ 保留: {title[:30]}... ({filter_reason})")
                else:
                    print(f"    ✅ 保留: {title} ({filter_reason})")
            else:
                if len(title) > 30:
                    print(f"    ❌ 过滤: {title[:30]}... ({filter_reason})")
                else:
                    print(f"    ❌ 过滤: {title} ({filter_reason})")
        
        original_count = len(items)
        filtered_count = len(filtered_items)
        
        if filtered_count < original_count:
            print(f"  ⏰ 严格时间过滤结果: {original_count} → {filtered_count} 条（排除了{original_count - filtered_count}条无可靠时间信息的内容）")
        else:
            print(f"  ⏰ 严格时间过滤结果: 保留全部{filtered_count}条内容")
            
        return filtered_items

    def evaluate_content_relevance(self, items, topic, criteria=None, llm_processor=None):
        """
        评估内容与主题的相关性，并返回按相关性排序的结果
        
        Args:
            items (list): 内容项列表
            topic (str): 主题
            criteria (dict, optional): 评估标准，包含权重
            llm_processor: LLM处理器实例，用于高级评分
            
        Returns:
            list: 按相关性得分排序的内容项列表
        """
        if not items:
            return []
            
        # 修改默认评估标准，提高时效性权重
        default_criteria = {
            "主题相关性": 0.35,  # 降低权重以增加时效性权重
            "时效性": 0.4,     # 提高时效性权重
            "信息质量": 0.15,   # 略微降低
            "来源可靠性": 0.1   # 保持不变
        }
        
        criteria = criteria or default_criteria
        scored_items = []
        
        print(f"正在评估{len(items)}条内容与'{topic}'的相关性...")
        
        # 使用LLM处理器进行高级相关性评分
        if llm_processor:
            try:
                for item in items:
                    # 确保内容字段的存在
                    title = item.get('title', '')
                    content = item.get('content', '')
                    if not content and not title:
                        continue
                        
                    # 创建评估提示
                    prompt = f"""
                    请评估以下内容与'{topic}'主题的相关性和信息质量，根据以下标准给出1-10分的评分：
                    
                    标题: {title}
                    内容: {content[:500]}...
                    
                    评分标准:
                    1. 主题相关性 (1-10分): 内容与'{topic}'主题的直接相关程度
                    2. 时效性 (1-10分): 内容的新鲜度和时效性
                    3. 信息质量 (1-10分): 内容的完整性、深度和信息量
                    4. 来源可靠性 (1-10分): 来源的权威性和可信度
                    
                    请以JSON格式返回评分，只包含以下字段:
                    {{
                        "主题相关性": 分数,
                        "时效性": 分数,
                        "信息质量": 分数,
                        "来源可靠性": 分数,
                        "总分": 加权总分
                    }}
                    """
                    
                    try:
                        # 使用专门的JSON API调用方法
                        system_message = "你是一位专业的内容评估专家，擅长评估内容的相关性、质量和时效性。你的回答必须是严格的JSON格式，不包含任何其他文本。"
                        
                        try:
                            # 尝试使用新的JSON专用API调用
                            scores = llm_processor.call_llm_api_json(prompt, system_message)
                            
                            # 计算加权得分
                            weighted_score = 0
                            for criterion, weight in criteria.items():
                                if criterion in scores:
                                    weighted_score += scores[criterion] * weight
                                    
                            # 如果JSON中没有提供总分，使用计算的加权分数
                            final_score = scores.get("总分", weighted_score)
                            
                            # 将分数存储到内容项中
                            item["relevance_score"] = final_score
                            item["detailed_scores"] = scores
                            
                        except AttributeError:
                            # 如果llm_processor没有call_llm_api_json方法，使用标准调用并处理结果
                            result = llm_processor.call_llm_api(prompt, system_message)
                            
                            # 尝试解析JSON
                            try:
                                # 清理可能的Markdown代码块标记
                                cleaned_result = result
                                
                                # 移除可能的代码块标记
                                if "```" in cleaned_result:
                                    import re
                                    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned_result)
                                    if code_block_match:
                                        cleaned_result = code_block_match.group(1).strip()
                                
                                # 提取JSON部分
                                json_start = cleaned_result.find('{')
                                json_end = cleaned_result.rfind('}') + 1
                                
                                if json_start >= 0 and json_end > json_start:
                                    json_text = cleaned_result[json_start:json_end]
                                    scores = json.loads(json_text)
                                else:
                                    scores = json.loads(cleaned_result)
                                
                                # 计算加权得分
                                weighted_score = 0
                                for criterion, weight in criteria.items():
                                    if criterion in scores:
                                        weighted_score += scores[criterion] * weight
                                        
                                # 使用计算的加权分数
                                final_score = scores.get("总分", weighted_score)
                                
                                # 将分数存储到内容项中
                                item["relevance_score"] = final_score
                                item["detailed_scores"] = scores
                                
                            except (json.JSONDecodeError, ValueError) as json_err:
                                print(f"无法解析评分结果: {result}")
                                print(f"JSON错误: {str(json_err)}")
                                # 失败时给默认分数
                                item["relevance_score"] = 5.0
                                item["detailed_scores"] = {
                                    "主题相关性": 5.0,
                                    "时效性": 5.0,
                                    "信息质量": 5.0,
                                    "来源可靠性": 5.0,
                                    "总分": 5.0
                                }
                        
                    except Exception as e:
                        print(f"评估内容时出错: {str(e)}")
                        # 出错时给予默认分数
                        item["relevance_score"] = 5.0
                        item["detailed_scores"] = {
                            "主题相关性": 5.0,
                            "时效性": 5.0,
                            "信息质量": 5.0,
                            "来源可靠性": 5.0,
                            "总分": 5.0
                        }
                        
                    scored_items.append(item)
                    
                # 按相关性得分排序
                scored_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
                
                print(f"使用LLM完成相关性评分，共评估{len(scored_items)}项")
                return scored_items
                
            except Exception as e:
                print(f"LLM相关性评估失败: {str(e)}，使用备用评估方法")
                # 失败时回退到简单评估方法
        
        # 如果没有LLM处理器或LLM评估失败，使用简单评估方法
        for item in items:
            score = 0
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            source = item.get('source', '').lower()
            topic_lower = topic.lower()
            
            # 简单的关键词匹配评分
            # 1. 主题相关性评分
            topic_relevance = 0
            if topic_lower in title:
                topic_relevance += 3  # 标题中包含主题加3分
            if topic_lower in content:
                # 计算主题在内容中出现的次数，最多加4分
                occurrences = content.count(topic_lower)
                topic_relevance += min(4, occurrences)
            
            # 2. 时效性评分 (基于文章发布日期或收录日期)
            recency_score = 5
            if "published_date" in item:
                published_date = item.get("published_date")
                try:
                    if isinstance(published_date, str):
                        # 尝试解析日期
                        from datetime import datetime, timedelta
                        pub_date = datetime.strptime(published_date, "%Y-%m-%d")
                        today = datetime.now()
                        hours_old = (today - pub_date).total_seconds() / 3600
                        
                        # 使用更细粒度的时效性评分
                        if hours_old <= 6:
                            recency_score = 10  # 6小时内
                        elif hours_old <= 12:
                            recency_score = 9.5  # 12小时内
                        elif hours_old <= 24:
                            recency_score = 9  # 1天内
                        elif hours_old <= 48:
                            recency_score = 8  # 2天内
                        elif hours_old <= 72:
                            recency_score = 7  # 3天内
                        elif hours_old <= 120:
                            recency_score = 6  # 5天内
                        else:
                            recency_score = 5  # 5天以上
                except:
                    # 解析日期失败，使用默认分数
                    pass
            
            # 3. 信息质量评分 (基于内容长度和完整性)
            quality_score = 0
            content_length = len(content)
            if content_length > 2000:
                quality_score = 8  # 长内容通常信息量更大
            elif content_length > 1000:
                quality_score = 7
            elif content_length > 500:
                quality_score = 6
            elif content_length > 200:
                quality_score = 5
            else:
                quality_score = 4
                
            # 4. 来源可靠性评分
            reliability_score = 5  # 默认中等可靠性
            
            # 计算加权总分
            weighted_score = (
                topic_relevance * criteria.get("主题相关性", 0.4) * 10 / 7 +  # 归一化到10分制
                recency_score * criteria.get("时效性", 0.3) +
                quality_score * criteria.get("信息质量", 0.2) +
                reliability_score * criteria.get("来源可靠性", 0.1)
            )
            
            # 保存评分到内容项
            item["relevance_score"] = weighted_score
            item["detailed_scores"] = {
                "主题相关性": topic_relevance * 10 / 7,  # 归一化到10分制
                "时效性": recency_score,
                "信息质量": quality_score,
                "来源可靠性": reliability_score,
                "总分": weighted_score
            }
            
            scored_items.append(item)
        
        # 按相关性得分排序
        scored_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        print(f"完成内容相关性评分，共评估{len(scored_items)}项")
        return scored_items