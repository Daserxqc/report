"""
意图理解与内容检索Agent
功能：
1. 理解用户查询意图，生成相关主题扩展
2. 调用多渠道搜索工具进行内容检索
3. 返回高度精简的JSON格式结果（50-60字）
"""

import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.tavily_collector import TavilyCollector
from collectors.google_search_collector import GoogleSearchCollector
from collectors.brave_search_collector import BraveSearchCollector

# 关闭HTTP请求日志
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class IntentSearchAgent:
    """意图理解与内容检索Agent"""
    
    def __init__(self):
        # 初始化搜索收集器
        self.collectors = {}
        
        # 只初始化Google搜索（专注于事实性、实际性内容）
        try:
            self.google_collector = GoogleSearchCollector()
            if self.google_collector.has_api_key:
                self.collectors['google'] = self.google_collector
                print("✅ Google搜索引擎已启用（专注事实性内容）")
            else:
                print("❌ Google搜索引擎API密钥未配置")
                return
        except Exception as e:
            print(f"❌ Google搜索引擎初始化失败: {str(e)}")
            return
        
        # 初始化LLM处理器（使用Google搜索的LLM处理器）
        try:
            # 尝试从Google搜索获取LLM处理器
            self.llm_processor = self.google_collector._get_llm_processor()
            print("✅ LLM处理器已启用")
        except Exception as e:
            print(f"❌ LLM处理器初始化失败: {str(e)}")
            # 如果Google搜索没有LLM处理器，尝试Tavily的
            try:
                from collectors.tavily_collector import TavilyCollector
                tavily_collector = TavilyCollector()
                self.llm_processor = tavily_collector._get_llm_processor()
                print("✅ LLM处理器已启用（使用Tavily备用）")
            except Exception as e2:
                print(f"❌ 备用LLM处理器也初始化失败: {str(e2)}")
                return
        
        print(f"🔍 搜索引擎配置完成，专注于事实性、实际性内容")
    
    def understand_intent(self, user_query):
        """
        步骤1：意图理解与主题扩展
        使用LLM理解用户意图，生成相关主题和关键词
        """
        print(f"🧠 [意图理解] 正在分析用户查询: '{user_query}'")
        
        intent_prompt = f"""
        用户查询: "{user_query}"
        
        请作为一个专业的信息搜索助手，深度理解用户的搜索意图，提供平衡的概念性和实用性内容。
        
        分析策略：
        1. 首先判断查询类型：
           - 概念性查询（如"AI Agent"、"区块链"等）：优先提供基础概念、定义、原理
           - 实用性查询（如"如何开发AI Agent"、"AI Agent教程"）：优先提供工具、方法、案例
        
        2. 对于概念性查询，搜索重点：
           - 基本定义和核心概念
           - 工作原理和技术架构
           - 主要特征和分类
           - 然后是实际应用和工具
        
        3. 对于实用性查询，搜索重点：
           - 具体工具和框架
           - 实现方法和最佳实践
           - 实际案例和应用场景
           - 避免过度商业化内容
        
        4. 搜索关键词要求：
           - 包含"概念"、"定义"、"原理"等基础性关键词
           - 避免过多特定公司名称
           - 平衡理论和实践内容
        
        请严格按照以下JSON格式返回：
        {{
            "query_type": "概念性" 或 "实用性",
            "core_intent": "用户核心意图的简要描述",
            "expanded_topics": [
                {{
                    "topic": "主题名称",
                    "keywords": ["关键词1", "关键词2", "关键词3"],
                    "search_focus": "概念性" 或 "实用性"
                }}
            ],
            "search_queries": ["搜索查询1", "搜索查询2", "搜索查询3"]
        }}
        
        示例1 - 概念性查询：
        用户查询: "AI Agent"
        返回：
        {{
            "query_type": "概念性",
            "core_intent": "了解AI Agent的基本概念、工作原理和主要特征",
            "expanded_topics": [
                {{
                    "topic": "AI Agent基本概念",
                    "keywords": ["AI Agent定义", "智能代理", "自主代理"],
                    "search_focus": "概念性"
                }},
                {{
                    "topic": "AI Agent工作原理",
                    "keywords": ["感知", "决策", "执行", "学习机制"],
                    "search_focus": "概念性"
                }},
                {{
                    "topic": "AI Agent开发框架",
                    "keywords": ["LangChain", "AutoGPT", "框架对比"],
                    "search_focus": "实用性"
                }}
            ],
            "search_queries": ["AI Agent概念定义", "AI Agent工作原理", "AI Agent开发框架"]
        }}
        
        示例2 - 实用性查询：
        用户查询: "如何开发AI Agent"
        返回：
        {{
            "query_type": "实用性",
            "core_intent": "学习AI Agent的具体开发方法和实现技术",
            "expanded_topics": [
                {{
                    "topic": "AI Agent开发教程",
                    "keywords": ["开发指南", "代码实现", "实战教程"],
                    "search_focus": "实用性"
                }}
            ],
            "search_queries": ["AI Agent开发教程", "AI Agent代码实现"]
        }}
        """
        
        try:
            response = self.llm_processor.call_llm_api(
                intent_prompt,
                "你是一个专业的搜索意图分析师，擅长理解用户需求并生成准确的搜索策略。",
                max_tokens=2000
            )
            
            # 解析JSON响应
            intent_data = self._parse_intent_response(response)
            print(f"✅ [意图理解完成] 核心意图: {intent_data['core_intent']}")
            print(f"📊 扩展主题: {len(intent_data['expanded_topics'])}个")
            return intent_data
            
        except Exception as e:
            print(f"❌ [意图理解失败] {str(e)}")
            # 返回基础的意图分析
            return self._get_fallback_intent(user_query)
    
    def _parse_intent_response(self, response):
        """解析LLM的意图理解响应"""
        try:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                raise ValueError("无法找到有效的JSON格式")
        except Exception as e:
            print(f"⚠️ [JSON解析失败] {str(e)}")
            raise
    
    def _get_fallback_intent(self, user_query):
        """备用意图分析，当LLM不可用时使用"""
        return {
            "core_intent": f"搜索关于'{user_query}'的相关信息",
            "expanded_topics": [
                {
                    "topic": f"{user_query}基础信息",
                    "keywords": [user_query, "基本概念", "定义"]
                },
                {
                    "topic": f"{user_query}最新动态",
                    "keywords": [user_query, "最新", "动态", "新闻"]
                }
            ],
            "search_queries": [f"{user_query}最新信息", f"{user_query}发展趋势"]
        }
    
    def parallel_content_search(self, intent_data, max_results=5):
        """
        步骤2：Google搜索内容检索
        基于意图分析结果，使用Google搜索进行检索，根据查询类型调整策略
        """
        query_type = intent_data.get('query_type', '概念性')
        print(f"🔍 [Google检索] 开始执行{query_type}内容检索...")
        
        # 构建搜索查询列表
        search_queries = intent_data.get('search_queries', [])
        
        # 根据查询类型和主题重点调整搜索策略
        for topic_data in intent_data.get('expanded_topics', []):
            topic = topic_data.get('topic', '')
            keywords = topic_data.get('keywords', [])
            search_focus = topic_data.get('search_focus', '概念性')
            
            if topic:
                if search_focus == '概念性':
                    # 概念性搜索：优先基础概念、定义、原理
                    search_queries.append(f"{topic} 概念")
                    search_queries.append(f"{topic} 定义")
                    if '原理' in topic or '工作原理' in topic:
                        search_queries.append(f"{topic} 详解")
                else:
                    # 实用性搜索：优先教程、实践、案例
                    search_queries.append(f"{topic} 教程")
                    search_queries.append(f"{topic} 实践")
                
                # 添加关键词搜索（限制数量）
                if keywords:
                    search_queries.append(' '.join(keywords[:2]))
        
        # 根据查询类型限制搜索数量
        if query_type == '概念性':
            search_queries = search_queries[:5]  # 概念性查询，较少但更精准
        else:
            search_queries = search_queries[:7]  # 实用性查询，更多实际内容
        
        # 去重搜索查询
        search_queries = list(dict.fromkeys(search_queries))  # 保持顺序的去重
        
        all_results = []
        
        # 使用Google搜索
        google_collector = self.collectors.get('google')
        if google_collector:
            for query in search_queries:
                try:
                    results = google_collector.search(query, max_results=max_results)
                    if results:
                        all_results.extend(results)
                        print(f"  ✅ [Google] '{query[:40]}...' -> {len(results)}条结果")
                    else:
                        print(f"  ⚠️ [Google] '{query[:40]}...' -> 无结果")
                except Exception as e:
                    print(f"  ❌ [Google] '{query[:40]}...' -> 搜索失败: {str(e)}")
        else:
            print("❌ Google搜索不可用")
            return []
        
        # 去重处理
        unique_results = self._deduplicate_results(all_results)
        print(f"📊 [检索完成] 总计获得 {len(unique_results)} 条{query_type}Google搜索结果")
        
        return unique_results
    
    def _execute_single_search(self, collector, collector_name, query, max_results):
        """执行单个搜索任务"""
        try:
            if collector_name == 'tavily':
                return collector.search(query, max_results=max_results)
            elif collector_name == 'google':
                return collector.search(query, max_results=max_results)
            elif collector_name == 'brave':
                return collector.search(query, count=max_results)
            else:
                return []
        except Exception as e:
            print(f"    ⚠️ [{collector_name}] 搜索出错: {str(e)}")
            return []
    
    def _deduplicate_results(self, results):
        """结果去重"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            title = result.get('title', '')
            
            # 基于URL去重
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
            # 如果没有URL，基于标题去重
            elif not url and title:
                existing_titles = [r.get('title', '') for r in unique_results]
                if title not in existing_titles:
                    unique_results.append(result)
        
        return unique_results
    
    def generate_concise_summary(self, intent_data, search_results, summary_length):
        """
        步骤3：生成详细摘要
        基于搜索结果生成指定长度的详细摘要，根据查询类型调整风格
        """
        query_type = intent_data.get('query_type', '概念性')
        print(f"📝 [详细摘要] 正在生成{query_type}摘要 (长度: {summary_length})...")
        
        # 根据长度范围设置参数
        length_config = self._get_length_config(summary_length)
        
        # 准备摘要数据
        summary_data = {
            "query_type": query_type,
            "core_intent": intent_data.get('core_intent', ''),
            "top_results": search_results[:length_config['result_count']],
            "expanded_topics": [t.get('topic', '') for t in intent_data.get('expanded_topics', [])]
        }
        
        # 根据查询类型调整摘要提示
        if query_type == '概念性':
            summary_style = f"""
            概念性摘要要求：
            1. 首先明确定义核心概念
            2. 解释基本工作原理或机制
            3. 列举主要特征和分类
            4. 简要提及实际应用场景
            5. 避免过多商业化内容和公司名称
            6. 重点在于帮助用户理解"这是什么"和"如何工作"
            """
        else:
            summary_style = f"""
            实用性摘要要求：
            1. 重点介绍具体工具和方法
            2. 提供实际操作步骤或指南
            3. 列举最佳实践和应用案例
            4. 包含技术细节和实现路径
            5. 突出可操作性和实用价值
            6. 重点在于帮助用户理解"怎么做"和"如何实现"
            """
        
        summary_prompt = f"""
        基于以下搜索结果，生成一个详细的{query_type}摘要：
        
        查询类型: {query_type}
        用户意图: {summary_data['core_intent']}
        相关主题: {', '.join(summary_data['expanded_topics'])}
        
        {summary_style}
        
        搜索结果:
        {self._format_search_results_for_summary(summary_data['top_results'])}
        
        请生成一个{summary_length}的详细摘要，要求：
        1. 字数严格控制在{summary_length}范围内，这是最重要的要求
        2. 如果是"50字以内"，请确保不超过50字
        3. 如果是"50-100字"，请确保在50-100字之间
        4. 如果是"100-300字"，请确保在100-300字之间
        5. 如果是"300字以上"，请确保超过300字但不超过500字
        6. 根据查询类型调整内容重点
        7. 必须是完整的句子，不能有省略号或截断
        8. 语言准确专业，逻辑清晰
        9. 避免过度商业化内容和公司堆砌
        
        格式要求：
        - 使用完整的句子结构
        - 不使用省略号(...)
        - 句子要完整，不能中途截断
        - 信息准确，逻辑清晰
        - 严格遵循字数限制
        
        请只返回摘要文本，不要其他内容。生成前请先确认字数在要求范围内。
        """
        
        try:
            summary_text = self.llm_processor.call_llm_api(
                summary_prompt,
                f"你是一个专业的{query_type}信息摘要师，擅长根据不同查询类型和长度要求生成合适的摘要。",
                max_tokens=length_config['max_tokens']
            )
            
            # 清理摘要文本
            summary_text = summary_text.strip()
            
            # 移除可能的省略号
            summary_text = summary_text.replace('...', '').replace('…', '')
            
            # 确保句子完整性
            if not summary_text.endswith(('。', '！', '？', '.', '!', '?')):
                # 如果最后一个字符不是标点符号，添加句号
                summary_text += '。'
            
            # 根据长度范围检查和调整
            summary_text = self._adjust_summary_length(summary_text, length_config)
            
            print(f"✅ [摘要完成] 长度: {len(summary_text)}字")
            return summary_text
            
        except Exception as e:
            print(f"❌ [摘要生成失败] {str(e)}")
            return self._get_fallback_summary(intent_data, search_results, summary_length)
    
    def _get_length_config(self, summary_length):
        """根据长度范围返回配置参数"""
        configs = {
            "50字以内": {"max_tokens": 150, "max_chars": 50, "min_chars": 20, "result_count": 3},
            "50-100字": {"max_tokens": 250, "max_chars": 100, "min_chars": 50, "result_count": 5},
            "100-300字": {"max_tokens": 750, "max_chars": 300, "min_chars": 100, "result_count": 8},
            "300字以上": {"max_tokens": 1000, "max_chars": 500, "min_chars": 300, "result_count": 15}
        }
        return configs.get(summary_length, configs["50-100字"])
    
    def _adjust_summary_length(self, summary_text, length_config):
        """根据长度配置调整摘要长度"""
        current_length = len(summary_text)
        max_chars = length_config['max_chars']
        min_chars = length_config['min_chars']
        
        # 如果超过最大长度，需要截断
        if current_length > max_chars:
            # 优先在句号处截断
            sentences = []
            temp_text = summary_text
            
            # 按句号分割
            sentence_endings = ['。', '！', '？', '.', '!', '?']
            current_pos = 0
            
            while current_pos < len(temp_text):
                # 找到下一个句号
                next_end = len(temp_text)
                end_char = ''
                for ending in sentence_endings:
                    pos = temp_text.find(ending, current_pos)
                    if pos != -1 and pos < next_end:
                        next_end = pos
                        end_char = ending
                
                if next_end == len(temp_text):
                    # 没有找到句号，取剩余部分
                    sentences.append(temp_text[current_pos:])
                    break
                else:
                    # 找到句号，包含句号
                    sentences.append(temp_text[current_pos:next_end + 1])
                    current_pos = next_end + 1
            
            # 重新组合句子，确保不超过最大长度
            result = ''
            for sentence in sentences:
                if len(result + sentence) <= max_chars:
                    result += sentence
                else:
                    break
            
            # 如果结果太短，至少保证有一个完整句子
            if len(result) < min_chars and sentences:
                result = sentences[0]
                # 如果第一个句子仍然太长，强制截断
                if len(result) > max_chars:
                    result = result[:max_chars-1] + '。'
            
            summary_text = result
        
        # 确保摘要以标点符号结尾
        if summary_text and not summary_text.endswith(('。', '！', '？', '.', '!', '?')):
            summary_text += '。'
        
        return summary_text
    
    def _format_search_results_for_summary(self, results):
        """格式化搜索结果用于摘要生成，提供更详细的信息"""
        formatted = []
        for i, result in enumerate(results[:5], 1):  # 使用前5个结果
            title = result.get('title', '无标题')
            snippet = result.get('snippet', result.get('content', ''))
            url = result.get('url', '')
            
            # 清理snippet
            if snippet:
                snippet = snippet.replace('...', '').replace('…', '').strip()
                # 增加snippet长度限制
                snippet = snippet[:200] + "" if len(snippet) > 200 else snippet
            
            # 构建格式化结果
            formatted_result = f"{i}. 标题: {title}"
            if snippet:
                formatted_result += f"\n   内容: {snippet}"
            if url:
                formatted_result += f"\n   来源: {url}"
            
            formatted.append(formatted_result)
        
        return '\n\n'.join(formatted)
    
    def _get_fallback_summary(self, intent_data, search_results, summary_length):
        """备用摘要生成，生成更完整的摘要"""
        core_intent = intent_data.get('core_intent', '')
        topics = intent_data.get('expanded_topics', [])
        topic_names = [t.get('topic', '') for t in topics[:3]]
        
        # 根据长度范围获取配置
        length_config = self._get_length_config(summary_length)
        
        if search_results:
            # 使用搜索结果生成摘要
            first_result = search_results[0]
            title = first_result.get('title', '')
            snippet = first_result.get('snippet', first_result.get('content', ''))
            
            # 构建详细摘要
            summary_parts = []
            
            if title:
                summary_parts.append(f"根据搜索结果，{title}")
            
            if snippet:
                # 提取snippet的关键信息
                snippet_clean = snippet.replace('...', '').replace('…', '').strip()
                if len(snippet_clean) > 60:
                    snippet_clean = snippet_clean[:60]
                summary_parts.append(snippet_clean)
            
            if topic_names:
                summary_parts.append(f"主要涉及{', '.join(topic_names)}等相关领域")
            
            if len(search_results) > 1:
                summary_parts.append(f"共找到{len(search_results)}个相关资源")
            
            # 根据长度范围调整内容详细程度
            if length_config['max_chars'] >= 200:
                # 长摘要：添加更多细节
                if len(search_results) > 2:
                    second_result = search_results[1]
                    second_title = second_result.get('title', '')
                    if second_title:
                        summary_parts.append(f"另外，{second_title}")
            
            summary = '，'.join(summary_parts)
            
            # 确保摘要完整
            if not summary.endswith(('。', '！', '？', '.', '!', '?')):
                summary += '。'
        else:
            summary = f"关于{core_intent}的信息暂时未找到相关结果。"
            if topic_names:
                summary += f"建议搜索{', '.join(topic_names)}等相关主题。"
        
        # 使用长度配置调整摘要
        summary = self._adjust_summary_length(summary, length_config)
        
        return summary
    
    def search_and_summarize(self, user_query, summary_length="50-100字"):
        """
        主要接口：执行完整的意图理解与内容检索流程
        返回JSON格式的结果
        """
        print(f"\n🚀 启动意图理解与内容检索Agent")
        print(f"🎯 用户查询: '{user_query}'")
        print("=" * 50)
        
        # 记录搜索开始时间
        start_time = datetime.now()
        
        try:
            # 步骤1：意图理解
            intent_data = self.understand_intent(user_query)
            
            # 步骤2：Google搜索内容检索
            search_results = self.parallel_content_search(intent_data, max_results=5)
            
            # 步骤3：生成详细摘要
            summary_text = self.generate_concise_summary(intent_data, search_results, summary_length)
            
            # 记录搜索结束时间
            end_time = datetime.now()
            search_duration = (end_time - start_time).total_seconds()
            
            # 构建返回结果
            result = {
                "user_query": user_query,
                "core_intent": intent_data.get('core_intent', ''),
                "expanded_topics": [t.get('topic', '') for t in intent_data.get('expanded_topics', [])],
                "summary": summary_text,
                "result_count": len(search_results),
                "search_start_time": start_time.isoformat(),
                "search_end_time": end_time.isoformat(),
                "search_duration_seconds": round(search_duration, 2),
                "summary_length": summary_length
            }
            
            print("\n" + "=" * 50)
            print("📊 检索结果:")
            print(f"🧠 核心意图: {result['core_intent']}")
            print(f"🔍 扩展主题: {', '.join(result['expanded_topics'])}")
            print(f"📝 详细摘要: {result['summary']}")
            print(f"📈 结果数量: {result['result_count']}")
            print(f"⏱️ 搜索耗时: {search_duration:.2f}秒")
            print("=" * 50)
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            search_duration = (end_time - start_time).total_seconds()
            
            print(f"❌ [流程执行失败] {str(e)}")
            return {
                "user_query": user_query,
                "core_intent": f"搜索关于'{user_query}'的信息",
                "expanded_topics": [],
                "summary": f"搜索'{user_query}'时发生错误，请稍后重试。",
                "result_count": 0,
                "search_start_time": start_time.isoformat(),
                "search_end_time": end_time.isoformat(),
                "search_duration_seconds": round(search_duration, 2),
                "error": str(e),
                "summary_length": summary_length
            }

def main():
    """主函数，用于测试和命令行调用"""
    load_dotenv()
    
    # 创建Agent实例
    agent = IntentSearchAgent()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 从命令行参数获取查询
        user_query = ' '.join(sys.argv[1:])
        print(f"🎯 执行搜索查询: '{user_query}'")
        
        # 使用默认长度范围
        result = agent.search_and_summarize(user_query, summary_length="100-300字")
        
        # 输出JSON结果
        print(f"\n📄 JSON结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    else:
        # 交互式模式 - 执行一次后退出
        print("🧪 意图理解与内容检索Agent")
        print("=" * 50)
        print("使用方法:")
        print("1. 直接输入查询内容")
        print("2. 输入 'test' 运行测试用例")
        print("3. 输入 'quit' 或 'exit' 退出")
        print("=" * 50)
        
        try:
            user_input = input("\n🔍 请输入您的查询 (或 'test'/'quit'): ").strip()
            
            if not user_input:
                print("⚠️ 请输入有效的查询内容")
                return
            
            if user_input.lower() in ['quit', 'exit']:
                print("👋 再见！")
                return
            
            if user_input.lower() == 'test':
                # 运行测试用例
                test_queries = [
                    "AI Agent",
                    "AI Agent开发框架",
                    "LangChain教程"
                ]
                
                print("🧪 开始运行实用性搜索测试用例...")
                
                for query in test_queries:
                    print(f"\n{'='*60}")
                    print(f"测试查询: {query}")
                    print('='*60)
                    
                    result = agent.search_and_summarize(query, summary_length="50-100字")
                    
                    # 输出JSON结果
                    print(f"\n📄 JSON结果:")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    
                    print(f"\n⏸️ 暂停3秒...")
                    import time
                    time.sleep(3)
                
                print("\n✅ 测试用例执行完成")
                
            else:
                # 让用户选择摘要长度
                print("\n📝 请选择摘要长度范围:")
                print("1. 50字以内 (简洁概述)")
                print("2. 50-100字 (标准摘要)")
                print("3. 100-300字 (详细摘要) [默认]")
                print("4. 300字以上 (深度摘要)")
                
                length_choice = input("\n请选择 (1-4, 直接回车使用默认): ").strip()
                
                # 映射用户选择到长度范围
                length_options = {
                    '1': "50字以内",
                    '2': "50-100字",
                    '3': "100-300字",
                    '4': "300字以上"
                }
                
                if length_choice in length_options:
                    summary_length = length_options[length_choice]
                elif length_choice == '':
                    summary_length = "100-300字"  # 默认长度
                else:
                    print("⚠️ 无效选择，使用默认长度: 100-300字")
                    summary_length = "100-300字"
                
                print(f"✅ 已选择摘要长度: {summary_length}")
                
                # 执行用户查询
                print(f"\n{'='*60}")
                print(f"执行查询: {user_input}")
                print(f"摘要长度: {summary_length}")
                print('='*60)
                
                result = agent.search_and_summarize(user_input, summary_length=summary_length)
                
                # 输出JSON结果
                print(f"\n📄 JSON结果:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
            # 执行完成后退出
            print("\n✅ 检索完成，程序退出")
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
        except Exception as e:
            print(f"❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    main() 