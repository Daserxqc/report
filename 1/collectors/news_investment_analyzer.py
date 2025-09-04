"""
投资动态新闻分析器 - 并行处理版本
专门负责投资动态新闻的深度分析，支持并行处理
"""

import time
from typing import List, Dict, Any, Optional
import threading

class InvestmentNewsAnalyzer:
    """投资动态新闻分析器 - 并行版本"""
    
    def __init__(self, llm_processor, max_workers: int = 2):
        """
        初始化投资动态新闻分析器
        
        Args:
            llm_processor: LLM处理器实例
            max_workers: 最大并行工作线程数
        """
        self.llm_processor = llm_processor
        self.max_workers = max_workers
        self.analysis_lock = threading.Lock()
        
    def analyze_investment_news_parallel(self, topic: str, investment_news: List[Dict]) -> str:
        """
        并行分析投资动态新闻
        
        Args:
            topic: 行业主题
            investment_news: 投资动态新闻列表
            
        Returns:
            格式化的投资动态分析报告
        """
        if not investment_news:
            return f"## 💰 投资与市场动向深度分析\n\n📊 **市场观察**: {topic}行业投资活动在当前时段相对平静。\n\n"
        
        start_time = time.time()
        print(f"💰 [投资动态分析] 开始并行分析{len(investment_news)}个投资事件...")
        
        try:
            all_news_text = "\n\n".join([
                f"标题: {item.get('title', '无标题')}\n时间: {item.get('date', '未知日期')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
                for item in investment_news
            ])
            
            enhanced_prompt = f"""
            作为{topic}行业的投资分析专家，请对以下投资动态进行智能筛选、去重和深度解读：
            
            {all_news_text}
            
            🔍 **智能筛选任务**：
            1. **去重识别**：识别相同投资事件的不同报道，合并信息保留最完整版本
            2. **重要性评估**：评估每个投资事件的规模和影响力
            3. **多样性保证**：确保涵盖不同投资类型和细分领域
            
            💰 **投资分析框架**:
            1. **资本流向分析**: 资金主要投向哪些细分领域？
            2. **投资逻辑解读**: 投资方的战略考量是什么？
            3. **估值水平评估**: 当前估值是否合理？
            4. **市场信号解读**: 这些投资反映了什么市场趋势？
            5. **风险机遇并存**: 投资者应该关注什么？
            
            🤔 **投资分析师思考过程**:
            - 首先去除重复投资事件报道，合并相同事件的信息
            - 然后梳理独特投资事件的规模和性质
            - 接着分析投资背后的商业逻辑
            - 评估对行业格局的影响
            - 最后提出投资策略建议
            
            请提供专业的投资分析，注重数据支撑，字数2000-2500字。
             
             📝 **详细要求**:
             - 如果发现相同投资事件的多个报道，请合并信息只分析一次
             - 每个独特投资事件要单独分析，包含背景、动机、影响
             - 提供具体的投资金额、估值变化、投资方背景
             - 分析投资背后的战略布局和市场判断
             - 包含风险评估和收益预期分析
             - 对比历史投资案例，识别趋势变化
             - 提供具体的投资建议和时机判断
            """
            
            system_msg = f"你是{topic}行业的资深投资分析师，具备敏锐的市场洞察力"
            
            if not self.llm_processor:
                return f"## 💰 投资与市场动向深度分析\n\n投资分析暂时不可用。\n\n"
            
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, system_msg, max_tokens=8000)
            
            # 添加信息来源
            sources = []
            for item in investment_news:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**投资资讯来源:**\n" + "\n".join(sources)
            
            elapsed_time = time.time() - start_time
            print(f"✅ [投资动态分析] 并行分析完成，耗时 {elapsed_time:.1f}秒")
            
            return f"## 💰 投资与市场动向深度分析\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 并行投资动态分析时出错: {str(e)}")
            return f"## 💰 投资与市场动向深度分析\n\n投资分析暂时不可用。\n\n"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "analyzer_type": "InvestmentNewsAnalyzer",
            "max_workers": self.max_workers,
            "parallel_tasks": ["investment_analysis"],
            "estimated_speedup": "1x (single LLM call optimized)"
        } 