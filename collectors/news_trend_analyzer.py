"""
行业趋势新闻分析器 - 并行处理版本
专门负责行业趋势新闻的深度分析，支持并行处理
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading

class TrendNewsAnalyzer:
    """行业趋势新闻分析器 - 并行版本"""
    
    def __init__(self, llm_processor, max_workers: int = 2):
        """
        初始化行业趋势新闻分析器
        
        Args:
            llm_processor: LLM处理器实例
            max_workers: 最大并行工作线程数
        """
        self.llm_processor = llm_processor
        self.max_workers = max_workers
        self.analysis_lock = threading.Lock()
        
    def analyze_trend_news_parallel(self, topic: str, trend_news: List[Dict], days: int = 7) -> str:
        """
        并行分析行业趋势新闻
        
        Args:
            topic: 行业主题
            trend_news: 行业趋势新闻列表
            days: 时间范围（天数）
            
        Returns:
            格式化的行业趋势分析报告
        """
        if not trend_news:
            return f"## 📈 行业趋势深度分析\n\n📊 **趋势观察**: 基于最近{days}天的数据，{topic}行业趋势分析有限。\n\n"
        
        start_time = time.time()
        print(f"📈 [行业趋势分析] 开始并行分析{len(trend_news)}个行业趋势...")
        
        try:
            # 计算时间范围
            today = datetime.now()
            start_date = today - timedelta(days=days)
            time_range = f"{start_date.strftime('%Y年%m月%d日')} 至 {today.strftime('%Y年%m月%d日')}"
            
            all_news_text = "\n\n".join([
                f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
                for item in trend_news
            ])
            
            enhanced_prompt = f"""
            作为{topic}行业的首席趋势分析师，请对以下**{time_range}**（最近{days}天）期间的行业趋势进行深度分析：
            
            {all_news_text}
            
            ⚠️ **时间范围限制**: 本分析严格聚焦于{time_range}这个时间窗口内的趋势信号，不涉及更早期的历史趋势。
            
            📈 **趋势分析框架**:
            1. **近期趋势识别**: 最近{days}天内{topic}行业出现了哪些新的发展趋势？
            2. **驱动因素分析**: 什么力量在推动这些最新趋势？
            3. **影响程度评估**: 这些新趋势对行业格局的即时和短期影响？
            4. **发展轨迹预测**: 基于近期信号，这些趋势的下一步发展方向？
            5. **机遇挑战并存**: 新趋势带来的即时机遇和风险？
            
            🤔 **趋势分析师思考过程**:
            - 首先从最新数据中识别趋势信号
            - 然后分析近期趋势之间的相互关系
            - 接着评估趋势的紧迫性和影响力
            - 最后基于最新变化预测短期发展轨迹
            
            请提供基于近期数据的前瞻性趋势分析，要有具体的数据支撑和案例说明，字数1500-2000字。
            
            📝 **分析要求**:
            - **严格聚焦时间范围**: 只分析{time_range}内的趋势信号
            - 构建基于最新数据的趋势分析框架
            - 每个趋势都要详细展开，包含最新驱动因素和发展阶段
            - 提供基于近期变化的具体预测和量化指标
            - 分析最新趋势之间的相互关系和协同效应
            - 识别潜在的新兴变化和突发因素
            - 构建基于当前状况的应对策略
            - 提供短期内的关键时间节点和发展路径
            
            🚫 **避免内容**: 
            - 不要引用{time_range}之外的历史趋势数据
            - 不要进行长期历史趋势的回顾分析
            - 专注于当前时间窗口内的具体趋势变化
            """
            
            system_msg = f"你是{topic}行业的资深趋势分析专家，具备卓越的前瞻性判断能力"
            
            if not self.llm_processor:
                return f"## 📈 行业趋势深度分析\n\n趋势分析暂时不可用。\n\n"
            
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, system_msg, max_tokens=8000)
            
            # 添加信息来源
            sources = []
            for item in trend_news:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**趋势数据来源:**\n" + "\n".join(sources)
            
            elapsed_time = time.time() - start_time
            print(f"✅ [行业趋势分析] 并行分析完成，耗时 {elapsed_time:.1f}秒")
            
            return f"## 📈 行业趋势深度分析\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 并行行业趋势分析时出错: {str(e)}")
            return f"## 📈 行业趋势深度分析\n\n趋势分析暂时不可用。\n\n"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "analyzer_type": "TrendNewsAnalyzer",
            "max_workers": self.max_workers,
            "parallel_tasks": ["trend_analysis"],
            "estimated_speedup": "1x (single LLM call optimized)"
        } 