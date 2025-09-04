"""
观点对比分析器 - 并行处理版本
专门负责不同观点的对比分析，支持并行处理
"""

import time
from typing import List, Dict, Any, Optional
import threading

class PerspectiveAnalyzer:
    """观点对比分析器 - 并行版本"""
    
    def __init__(self, llm_processor, max_workers: int = 2):
        """
        初始化观点对比分析器
        
        Args:
            llm_processor: LLM处理器实例
            max_workers: 最大并行工作线程数
        """
        self.llm_processor = llm_processor
        self.max_workers = max_workers
        self.analysis_lock = threading.Lock()
        
    def analyze_perspective_parallel(self, topic: str, perspective_data: List[Dict]) -> str:
        """
        并行分析观点对比
        
        Args:
            topic: 行业主题
            perspective_data: 观点对比数据列表
            
        Returns:
            格式化的观点对比分析报告
        """
        if not perspective_data:
            return ""  # 没有观点数据时返回空字符串
        
        start_time = time.time()
        print(f"🔍 [观点对比分析] 开始并行分析{len(perspective_data)}条不同观点信息...")
        
        try:
            # 构建观点分析提示
            all_perspectives_text = "\n\n".join([
                f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
                for item in perspective_data
            ])
            
            enhanced_prompt = f"""
            作为{topic}行业的客观分析师，请对以下不同观点和争议性信息进行平衡分析：
            
            {all_perspectives_text}
            
            🎯 **观点对比分析框架**:
            1. **正面观点总结**: 支持性、乐观性的观点有哪些？
            2. **质疑声音汇总**: 批评、质疑、担忧的观点有哪些？
            3. **争议焦点识别**: 主要的分歧点在哪里？
            4. **不同立场分析**: 
               - 企业vs监管方
               - 投资者vs消费者
               - 国内vs国际视角
               - 学术界vs产业界
            5. **客观评估**: 基于现有证据，哪些观点更有说服力？
            6. **平衡建议**: 如何在不同观点间找到平衡？
            
            🤔 **分析师思考过程**:
            - 避免偏向任何一方，保持中立客观
            - 分析每种观点背后的利益考量和逻辑基础
            - 识别可能的信息偏差和局限性
            - 提供建设性的综合判断
            
            请提供客观、平衡的观点对比分析，字数控制在1500-2000字。
            
            📝 **对比分析要求**:
            - 每个重要观点都要客观呈现，不偏不倚
            - 分析观点背后的深层原因和动机
            - 识别不同观点的合理性和局限性
            - 提供基于事实的平衡判断
            - 避免绝对化表述，承认复杂性和不确定性
            - 为读者提供多元化思考角度
            """
            
            system_msg = f"""你是{topic}行业的资深客观分析师，具备：
            1. 中立客观的分析态度
            2. 多维度的思考能力  
            3. 平衡不同观点的技巧
            4. 深度的行业洞察力
            请展现出专业的客观分析能力。"""
            
            if not self.llm_processor:
                return f"## ⚖️ 多元观点对比分析\n\n暂无{topic}行业的不同观点对比分析。\n\n"
            
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, system_msg, max_tokens=8000)
            
            # 添加分析来源
            sources = []
            for item in perspective_data:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**观点来源:**\n" + "\n".join(sources)
            
            elapsed_time = time.time() - start_time
            print(f"✅ [观点对比分析] 并行分析完成，耗时 {elapsed_time:.1f}秒")
            
            return f"## ⚖️ 多元观点对比分析\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 并行观点对比分析时出错: {str(e)}")
            return f"## ⚖️ 多元观点对比分析\n\n暂无{topic}行业的不同观点对比分析。\n\n"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "analyzer_type": "PerspectiveAnalyzer",
            "max_workers": self.max_workers,
            "parallel_tasks": ["perspective_analysis"],
            "estimated_speedup": "1x (single LLM call optimized)"
        } 