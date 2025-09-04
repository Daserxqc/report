"""
重大新闻分析器 - 并行处理版本
专门负责重大新闻的深度分析，支持并行处理
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class BreakingNewsAnalyzer:
    """重大新闻分析器 - 并行版本"""
    
    def __init__(self, llm_processor, max_workers: int = 2):
        """
        初始化重大新闻分析器
        
        Args:
            llm_processor: LLM处理器实例
            max_workers: 最大并行工作线程数
        """
        self.llm_processor = llm_processor
        self.max_workers = max_workers
        self.analysis_lock = threading.Lock()
        
    def analyze_breaking_news_parallel(self, topic: str, breaking_news: List[Dict], days: int = 7) -> str:
        """
        并行分析重大新闻
        
        Args:
            topic: 行业主题
            breaking_news: 重大新闻列表
            days: 时间范围（天数）
            
        Returns:
            格式化的重大新闻分析报告
        """
        if not breaking_news:
            return f"## 🚨 行业重大事件深度分析\n\n📊 **分析说明**: 在当前时间窗口内，暂未发现{topic}行业的重大突发事件。\n\n"
        
        start_time = time.time()
        print(f"🔍 [重大新闻分析] 开始并行分析{len(breaking_news)}条重大事件...")
        
        try:
            # 步骤1：并行生成事件摘要和深度分析
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 任务1：生成重大事件摘要
                summary_future = executor.submit(
                    self._generate_major_events_summary,
                    topic, breaking_news, days
                )
                
                # 任务2：生成深度分析
                analysis_future = executor.submit(
                    self._generate_depth_analysis,
                    topic, breaking_news, days
                )
                
                # 等待两个任务完成
                summary_section = summary_future.result()
                analysis_section = analysis_future.result()
            
            # 步骤2：整合结果
            sources = self._extract_sources(breaking_news)
            
            final_content = f"## 🚨 行业重大事件深度分析\n\n{summary_section}\n\n### 📊 综合分析与影响评估\n\n{analysis_section}"
            
            if sources:
                final_content += f"\n\n**信息来源:**\n{sources}"
            
            final_content += "\n\n"
            
            elapsed_time = time.time() - start_time
            print(f"✅ [重大新闻分析] 并行分析完成，耗时 {elapsed_time:.1f}秒")
            
            return final_content
            
        except Exception as e:
            print(f"❌ [错误] 并行重大新闻分析时出错: {str(e)}")
            return f"## 🚨 行业重大事件深度分析\n\n❌ 分析暂时不可用，请稍后重试。\n\n"
    
    def _generate_major_events_summary(self, topic: str, breaking_news: List[Dict], days: int) -> str:
        """生成重大事件摘要（第一个并行任务）"""
        print(f"  📋 [任务1] 正在筛选和总结最重要的{min(7, len(breaking_news))}个重大事件...")
        
        # 严格的时间过滤
        time_filtered_news = self._filter_by_time(breaking_news, days)
        
        if not time_filtered_news:
            return f"### 一、重大新闻摘要与关键细节\n\n⚠️ **时间过滤结果**: 在最近{days}天内暂无符合要求的重大事件，可能需要放宽时间范围或检查数据源。"
        
        # 选择最重要的5-7个事件
        selected_news = time_filtered_news[:min(7, len(time_filtered_news))]
        
        all_news_text = "\n\n".join([
            f"事件{i+1}:\n标题: {item.get('title', '无标题')}\n时间: {item.get('date', '最近')}\n内容: {item.get('content', '无内容')[:400]}...\n来源: {item.get('source', '未知来源')}\n网址: {item.get('url', '#')}"
            for i, item in enumerate(selected_news)
        ])
        
        summary_prompt = f"""
        作为{topic}行业的资深分析师，请对以下最新重大事件进行智能筛选、去重和整理。

        最新事件信息：
        {all_news_text}

        🔍 **智能筛选任务**：
        1. **去重识别**：仔细分析所有事件，识别内容相似或重复的事件（如同一事件的不同报道）
        2. **重要性评估**：评估每个事件对{topic}行业的影响程度和重要性
        3. **时效性判断**：优先选择最新、最具时效性的事件
        4. **多样性保证**：确保选出的事件涵盖不同方面（技术、政策、市场、投资等）

        📋 **输出要求** - 请从所有事件中筛选出最重要的3-5个不重复事件，按以下格式输出：

        1. [事件标题] (来源网站域名)
           ○ 事件：[用1-2句话简洁描述事件核心内容]
           ○ 关键点：[列出2-3个最重要的关键信息点]

        2. [事件标题] (来源网站域名)
           ○ 事件：[用1-2句话简洁描述事件核心内容]  
           ○ 关键点：[列出2-3个最重要的关键信息点]

        [继续相同格式...]

        🎯 **筛选标准**：
        - **去重优先**：如果多个事件讲述同一件事，只选择信息最全面、来源最权威的一个
        - **影响力优先**：优先选择对{topic}行业影响最大的事件
        - **时效性优先**：优先选择最新发生的事件
        - **多样性保证**：避免所有事件都集中在同一个子领域
        - **信息完整性**：优先选择信息详细、具体的事件

        ⚠️ **重要提醒**：
        - 如果发现多个事件是关于同一件事的不同报道，请合并信息并只输出一个事件
        - 严格按照重要性排序，最重要的事件排在前面
        - 每个事件的描述控制在100-150字以内
        - 来源网站只写域名，不要完整URL
        - 不要添加额外的标题或说明文字
        """
        
        system_msg = f"""你是{topic}行业的专业信息整理专家，擅长将复杂信息提炼成简洁实用的摘要格式。请确保输出格式准确，内容简洁有用。"""
        
        try:
            if not self.llm_processor:
                return self._generate_fallback_summary_simple(topic, selected_news)
            
            summary_analysis = self.llm_processor.call_llm_api(summary_prompt, system_msg, max_tokens=6000)
            return f"### 一、重大新闻摘要与关键细节\n\n{summary_analysis}"
            
        except Exception as e:
            print(f"    ❌ [任务1] 生成重大事件摘要时出错: {str(e)}")
            return self._generate_fallback_summary_simple(topic, selected_news)
    
    def _generate_depth_analysis(self, topic: str, breaking_news: List[Dict], days: int) -> str:
        """生成深度分析（第二个并行任务）"""
        print(f"  🔬 [任务2] 正在进行深度影响分析...")
        
        all_news_text = "\n\n".join([
            f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
            for item in breaking_news
        ])
        
        enhanced_prompt = f"""
        作为{topic}行业的首席分析师，请对以下重大事件进行深度分析：
        
        {all_news_text}
        
        分析框架：
        1. **事件重要性评估**: 按影响程度对事件进行排序和分类
        2. **多维度影响分析**: 分析对技术、市场、政策、竞争格局的影响
        3. **关联性分析**: 识别事件之间的内在联系和因果关系
        4. **趋势指向性**: 这些事件反映了什么趋势信号？
        5. **风险与机遇**: 为行业参与者带来的机遇和挑战
        
        🤔 **分析师思考过程**:
        - 首先梳理事件的时间线和逻辑关系
        - 然后评估每个事件的短期和长期影响
        - 最后综合判断对行业发展的指向意义
        
        请保持分析的客观性和前瞻性，要求深度分析，字数控制在2000-2500字。
         
         📝 **深度分析要求**:
         - 每个重大事件都要从多个角度深入剖析
         - 提供详细的背景信息和发展脉络
         - 分析事件对产业链各环节的具体影响
         - 评估短期、中期、长期的影响程度
         - 识别事件背后的深层次原因和规律
         - 提供具体的应对策略和发展建议
         - 预测后续可能的连锁反应和发展趋势
        """
        
        system_msg = f"""你是{topic}行业的资深首席分析师，具备：
        1. 敏锐的行业洞察力
        2. 系统性的分析思维
        3. 前瞻性的判断能力
        4. 客观理性的分析态度
        请展现出专业分析师的思考深度。"""
        
        try:
            if not self.llm_processor:
                return f"{topic}行业重大事件需要深度分析，但LLM处理器暂时不可用。"
            
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, system_msg, max_tokens=8000)
            return analysis
            
        except Exception as e:
            print(f"    ❌ [任务2] 生成深度分析时出错: {str(e)}")
            return f"{topic}行业重大事件深度分析暂时不可用。"
    
    def _filter_by_time(self, breaking_news: List[Dict], days: int) -> List[Dict]:
        """按时间过滤新闻"""
        from datetime import datetime, timedelta
        
        today = datetime.now()
        cutoff_date = today - timedelta(days=days)
        current_year = today.year
        
        time_filtered_news = []
        
        for item in breaking_news:
            should_include = False
            title = item.get('title', '')
            content = item.get('content', '')
            source = item.get('source', '')
            news_date = item.get('date', '') or item.get('published_date', '')
            
            # 检查是否包含明显的旧年份标识
            text_content = f"{title} {content} {source}".lower()
            old_year_patterns = ['2024年', '2023年', '2022年', '2021年', '2020年']
            has_old_year = any(pattern in text_content for pattern in old_year_patterns)
            
            if has_old_year:
                continue
            
            # 检查是否包含当前年份或最新时间词汇
            current_time_patterns = [
                f'{current_year}年', f'{current_year}', 'latest', 'recent', 
                '最新', '最近', 'breaking', '刚刚', '今日', '今天',
                today.strftime('%Y年%m月'), today.strftime('%m月')
            ]
            
            has_recent_indicators = any(pattern in text_content for pattern in current_time_patterns)
            
            # 如果有明确的发布日期，检查是否在时间范围内
            if news_date and news_date != "未知日期":
                try:
                    # 尝试解析日期
                    parsed_date = None
                    try:
                        from dateutil import parser
                        parsed_date = parser.parse(str(news_date))
                    except ImportError:
                        # 如果没有dateutil，使用基础解析
                        if isinstance(news_date, str):
                            # 尝试基础的ISO日期格式
                            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d']:
                                try:
                                    parsed_date = datetime.strptime(news_date, fmt)
                                    break
                                except ValueError:
                                    continue
                    
                    if parsed_date and parsed_date >= cutoff_date:
                        should_include = True
                    elif parsed_date:
                        continue
                    else:
                        raise ValueError("无法解析日期")
                except:
                    # 日期解析失败，使用关键词判断
                    if has_recent_indicators:
                        should_include = True
                    else:
                        continue
            else:
                # 没有发布日期，完全依靠内容关键词
                if has_recent_indicators:
                    should_include = True
                else:
                    continue
            
            if should_include:
                time_filtered_news.append(item)
        
        return time_filtered_news
    
    def _generate_fallback_summary_simple(self, topic: str, selected_news: List[Dict]) -> str:
        """备用的简洁格式事件摘要生成方法"""
        if not selected_news:
            return "### 一、重大新闻摘要与关键细节\n\n📊 **当前状况**: 在指定时间范围内暂无重大事件。"
        
        summary_text = "### 一、重大新闻摘要与关键细节\n\n"
        
        for i, event in enumerate(selected_news, 1):
            title = event.get('title', '未知事件')
            source = event.get('source', '未知来源')
            content = event.get('content', '无详细内容')[:150]
            
            # 提取域名
            source_domain = source
            if 'http' in source.lower():
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(source)
                    source_domain = parsed.netloc or source
                except:
                    source_domain = source
            
            summary_text += f"{i}. {title} ({source_domain})\n"
            summary_text += f"   ○ 事件：{content}...\n"
            summary_text += f"   ○ 关键点：{topic}行业相关重要动态，需要持续关注。\n\n"
        
        return summary_text
    
    def _extract_sources(self, breaking_news: List[Dict]) -> str:
        """提取新闻来源信息"""
        sources = []
        for item in breaking_news:
            if item.get('url', '#') != '#':
                sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
        
        return "\n".join(sources) if sources else ""
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "analyzer_type": "BreakingNewsAnalyzer",
            "max_workers": self.max_workers,
            "parallel_tasks": ["event_summary", "depth_analysis"],
            "estimated_speedup": "2x faster than sequential"
        } 