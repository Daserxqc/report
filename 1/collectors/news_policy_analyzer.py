"""
政策监管新闻分析器 - 并行处理版本
专门负责政策监管新闻的深度分析，支持并行处理
"""

import time
from typing import List, Dict, Any, Optional
import threading

class PolicyNewsAnalyzer:
    """政策监管新闻分析器 - 并行版本"""
    
    def __init__(self, llm_processor, max_workers: int = 2):
        """
        初始化政策监管新闻分析器
        
        Args:
            llm_processor: LLM处理器实例
            max_workers: 最大并行工作线程数
        """
        self.llm_processor = llm_processor
        self.max_workers = max_workers
        self.analysis_lock = threading.Lock()
        
    def analyze_policy_news_parallel(self, topic: str, policy_news: List[Dict]) -> str:
        """
        并行分析政策监管新闻
        
        Args:
            topic: 行业主题
            policy_news: 政策监管新闻列表
            
        Returns:
            格式化的政策监管分析报告
        """
        if not policy_news:
            return f"## 📜 政策与监管动态深度解读\n\n📊 **政策监测**: {topic}行业政策环境在当前时段保持稳定。\n\n"
        
        start_time = time.time()
        print(f"📜 [政策监管分析] 开始并行分析{len(policy_news)}项政策动态...")
        
        try:
            all_news_text = "\n\n".join([
                f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
                for item in policy_news
            ])
            
            enhanced_prompt = f"""
            作为{topic}行业的政策分析专家，请对以下政策动态进行智能筛选、去重和深度解读：
            
            {all_news_text}
            
            🔍 **智能筛选任务**：
            1. **去重识别**：识别相同政策的不同报道，合并信息保留最权威版本
            2. **重要性评估**：评估每项政策对{topic}行业的影响程度
            3. **多样性保证**：确保涵盖不同层级和类型的政策动态
            
            📜 **政策分析框架**:
            1. **政策内容解读**: 核心政策措施和规定是什么？
            2. **政策意图分析**: 政府希望达到什么目标？
            3. **行业影响评估**: 对{topic}行业各环节的具体影响？
            4. **企业应对策略**: 企业应该如何调整战略？
            5. **政策趋势预判**: 未来政策走向如何？
            
            🤔 **政策分析师思考过程**:
            - 首先去除重复政策报道，合并相同政策的信息
            - 然后理解独特政策的背景和目标
            - 接着分析政策的实施路径和时间节点
            - 评估对不同企业的差异化影响
            - 最后提出合规和发展建议
            
            请提供权威、客观的政策解读，字数1800-2200字。
             
             📝 **深度要求**:
             - 如果发现相同政策的多个报道，请合并信息只分析一次
             - 每项独特政策都要详细解读条文内容和实施细则
             - 分析政策出台的背景、目标和预期效果
             - 评估对不同类型企业的差异化影响
             - 提供具体的合规建议和操作指南
             - 预测政策执行过程中可能的挑战和机遇
             - 对比国际同类政策的经验和启示
            """
            
            system_msg = f"你是{topic}行业的政策分析专家，具备深厚的政策理解能力"
            
            if not self.llm_processor:
                return f"## 📜 政策与监管动态深度解读\n\n政策分析暂时不可用。\n\n"
            
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, system_msg, max_tokens=8000)
            
            # 添加信息来源
            sources = []
            for item in policy_news:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**政策信息来源:**\n" + "\n".join(sources)
            
            elapsed_time = time.time() - start_time
            print(f"✅ [政策监管分析] 并行分析完成，耗时 {elapsed_time:.1f}秒")
            
            return f"## 📜 政策与监管动态深度解读\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 并行政策监管分析时出错: {str(e)}")
            return f"## 📜 政策与监管动态深度解读\n\n政策分析暂时不可用。\n\n"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "analyzer_type": "PolicyNewsAnalyzer",
            "max_workers": self.max_workers,
            "parallel_tasks": ["policy_analysis"],
            "estimated_speedup": "1x (single LLM call optimized)"
        } 