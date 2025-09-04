"""
技术创新新闻分析器 - 并行处理版本
专门负责技术创新新闻的深度分析，支持并行处理
"""

import time
from typing import List, Dict, Any, Optional
import threading

class InnovationNewsAnalyzer:
    """技术创新新闻分析器 - 并行版本"""
    
    def __init__(self, llm_processor, max_workers: int = 2):
        """
        初始化技术创新新闻分析器
        
        Args:
            llm_processor: LLM处理器实例
            max_workers: 最大并行工作线程数
        """
        self.llm_processor = llm_processor
        self.max_workers = max_workers
        self.analysis_lock = threading.Lock()
        
    def analyze_innovation_news_parallel(self, topic: str, innovation_news: List[Dict]) -> str:
        """
        并行分析技术创新新闻
        
        Args:
            topic: 行业主题
            innovation_news: 技术创新新闻列表
            
        Returns:
            格式化的技术创新分析报告
        """
        if not innovation_news:
            return f"## 🔬 技术创新与新产品深度解析\n\n📊 **观察**: 当前时间窗口内{topic}行业技术创新活动相对平静。\n\n"
        
        start_time = time.time()
        print(f"🧪 [技术创新分析] 开始并行分析{len(innovation_news)}项技术创新...")
        
        try:
            all_news_text = "\n\n".join([
                f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
                for item in innovation_news
            ])
            
            enhanced_prompt = f"""
            作为{topic}行业的技术专家，请对以下技术创新进行智能筛选、去重和深度分析：
            
            {all_news_text}
            
            🔍 **智能筛选任务**：
            1. **去重识别**：识别相似或重复的技术创新报道，合并相同技术的不同报道
            2. **重要性评估**：评估每个技术创新的突破性和影响力
            3. **多样性保证**：确保涵盖不同技术领域和应用方向
            
            🔬 **技术分析框架**:
            1. **创新突破性评估**: 筛选出的技术的颠覆性程度如何？
            2. **技术成熟度分析**: 当前处于什么发展阶段？
            3. **商业化可行性**: 距离规模化应用还有多远？
            4. **竞争格局影响**: 对现有技术路线的冲击程度？
            5. **未来发展趋势**: 技术演进的可能方向？
            
            🤔 **分析师思考过程**:
            - 首先去除重复技术报道，保留信息最全面的版本
            - 然后评估技术的原创性和突破性
            - 接着分析技术的实用性和商业价值
            - 最后预测对行业生态的长远影响
            
            请提供客观、专业的技术解读，要求详细深入，字数1500-2000字。
             
             📝 **内容要求**:
             - 如果发现相同技术的多个报道，请合并信息只分析一次
             - 每个独特技术创新都要详细展开分析
             - 提供具体的技术细节和应用场景
             - 包含市场前景和商业化时间表
             - 分析技术的优势、局限性和发展瓶颈
             - 对比同类技术方案的差异
            """
            
            system_msg = f"你是{topic}行业的资深技术专家，具备深厚的技术洞察力"
            
            if not self.llm_processor:
                return f"## 🔬 技术创新与新产品深度解析\n\n技术分析暂时不可用。\n\n"
            
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, system_msg, max_tokens=8000)
            
            # 添加信息来源
            sources = []
            for item in innovation_news:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**技术资料来源:**\n" + "\n".join(sources)
            
            elapsed_time = time.time() - start_time
            print(f"✅ [技术创新分析] 并行分析完成，耗时 {elapsed_time:.1f}秒")
            
            return f"## 🔬 技术创新与新产品深度解析\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 并行技术创新分析时出错: {str(e)}")
            return f"## 🔬 技术创新与新产品深度解析\n\n技术分析暂时不可用。\n\n"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "analyzer_type": "InnovationNewsAnalyzer",
            "max_workers": self.max_workers,
            "parallel_tasks": ["innovation_analysis"],
            "estimated_speedup": "1x (single LLM call optimized)"
        } 