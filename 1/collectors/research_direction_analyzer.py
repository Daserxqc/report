from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class ResearchDirectionAnalyzer:
    """研究方向分析器，支持并行处理研究方向识别和趋势分析"""
    
    def __init__(self, llm_processor, max_workers=2):
        self.llm_processor = llm_processor
        self.max_workers = max_workers
        self.lock = threading.Lock()
    
    def identify_research_directions(self, research_text_with_refs: str, url_reference_list: str, topic: str) -> str:
        """识别研究方向"""
        directions_prompt = f"""
        请分析以下{topic}领域的研究文章，识别出3-5个主要研究方向或子领域，并为每个方向提供简短描述。
        
        {research_text_with_refs}
        
        URL参考列表（请严格按照此列表使用真实URL）:
        {url_reference_list}
        
        在分析时，请注意:
        1. 专注于{topic}的核心研究方向，忽略仅将其应用于其他领域的研究
        2. 确保每个研究方向都是{topic}领域自身的发展路径，而非其他学科借用{topic}方法
        3. 分析每个方向有多少篇论文支持，优先选择多篇论文共同体现的方向
        4. 考虑方向的重要性、创新性和未来发展潜力
        
        输出要求:
        1. 明确列出3-5个主要研究方向
        2. 每个方向提供10-20句话详细描述其:
           - 核心关注点和重要性
           - 最新研究进展
           - 技术难点和挑战
           - 应用场景和价值
           - 未来发展方向
        3. 按研究活跃度或前沿程度排序
        4. 对所有研究方向的来源进行标注，使用上面URL参考列表中的真实链接
        5. 采用统一的markdown格式输出:
           - 研究方向名称使用**加粗**文本
           - 使用有序列表(1., 2., 3.)标注每个方向
           - 每个研究方向的子项使用无序列表(• 或-)
           - 对重要概念进行适当强调
           - 在每个研究方向之间添加两行以上空行，确保足够的间距
           - 在要点描述之间也添加适当空行
        6. 必须使用中文输出所有内容，包括研究方向名称也应翻译成中文（可附英文原名）
        7. 当引用论文时，请使用格式：论文标题([文章X])，然后我会在后处理中将[文章X]替换为真实的链接。严禁编造任何URL，只能使用我提供的URL参考列表中的链接。
        """
        
        directions_system = f"""你是一位专业的{topic}领域研究专家，擅长分析和总结研究趋势。
请基于提供的研究文章，提取{topic}领域的主要研究方向。

重要提示:
1. 只关注真正属于{topic}核心领域的研究，忽略只是应用或浅层提及的内容
2. 区分主要研究方向与边缘应用场景
3. 确保识别的方向有足够的科研支持，不是个别论文的偶然主题
4. 确保方向之间有足够的差异性，避免重复
5. 遵循统一的格式规范:
   - 每个研究方向使用编号和**加粗标题**
   - 关键点使用• 或-列表呈现
   - 保持一致的格式和结构
   - 确保足够的空行和间距，使内容易于阅读
   - 在每个要点后添加空行
6. 所有输出内容必须使用中文，如有必要可在中文名称后附上英文原名
7. 当需要引用论文时，使用格式：论文标题([文章X])，其中X是我提供的文章编号。绝对不要编造任何URL，只使用我提供的编号系统。"""
        
        try:
            return self.llm_processor.call_llm_api(directions_prompt, directions_system)
        except Exception as e:
            with self.lock:
                print(f"识别研究方向时出错: {str(e)}")
            return f"{topic}领域的主要研究方向无法自动识别。"
    
    def analyze_future_trends(self, research_text_with_refs: str, url_reference_list: str, topic: str) -> str:
        """分析未来趋势"""
        future_prompt = f"""
        基于以下{topic}领域的最新研究文章，请分析该领域的核心发展趋势和未来研究方向。
        
        {research_text_with_refs}
        
        URL参考列表（请严格按照此列表使用真实URL）:
        {url_reference_list}
        
        请提供:
        1. {topic}领域核心技术和方法的发展趋势，而非应用领域的扩展
        2. 未来3-5年在{topic}基础理论和核心方法上可能出现的突破性进展
        3. {topic}领域本身(而非其应用)面临的主要挑战和机遇
        4. 对该领域研究者的建议，聚焦如何推动{topic}的基础发展
        
        要求:
        - 使用专业、客观的语言
        - 有理有据，避免无根据的猜测
        - 长度控制在2500-3000字
        - 必须使用中文输出除标题外的所有内容，技术术语可在中文后附上英文原名
        - 使用清晰的段落划分，每个观点之间空一行
        - 重要观点可以使用**加粗**或*斜体*强调
        - 分点表述时使用编号或项目符号，并保持一致的格式
        - 当引用论文时，请使用格式：论文标题([文章X])，然后我会在后处理中将[文章X]替换为真实的链接。严禁编造任何URL，只能使用我提供的URL参考列表中的链接。
        """
        
        future_system = f"""你是一位权威的{topic}领域趋势分析专家，擅长分析研究动态并预测未来发展。
请基于最新文献提供深入的趋势分析，专注于该领域的核心发展方向，而非应用场景。
区分{topic}领域自身的发展趋势与其在其他领域的应用趋势。
注重排版的清晰和美观，保持适当的空行和间距，使内容更易于阅读。
当需要引用论文时，使用格式：论文标题([文章X])，其中X是我提供的文章编号。绝对不要编造任何URL，只使用我提供的编号系统。"""
        
        try:
            return self.llm_processor.call_llm_api(future_prompt, future_system)
        except Exception as e:
            with self.lock:
                print(f"生成未来展望时出错: {str(e)}")
            return "暂无未来展望分析。"
    
    def analyze_directions_and_trends_parallel(self, research_text_with_refs: str, url_reference_list: str, topic: str) -> Tuple[str, str]:
        """并行分析研究方向和未来趋势"""
        print("开始并行分析研究方向和未来趋势...")
        
        research_directions = ""
        future_outlook = ""
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交两个分析任务
            future_directions = executor.submit(self.identify_research_directions, research_text_with_refs, url_reference_list, topic)
            future_trends = executor.submit(self.analyze_future_trends, research_text_with_refs, url_reference_list, topic)
            
            # 收集结果
            for future in as_completed([future_directions, future_trends]):
                try:
                    if future == future_directions:
                        research_directions = future.result()
                        print("✅ 研究方向分析完成")
                    elif future == future_trends:
                        future_outlook = future.result()
                        print("✅ 未来趋势分析完成")
                except Exception as e:
                    if future == future_directions:
                        print(f"研究方向分析失败: {str(e)}")
                        research_directions = f"{topic}领域的主要研究方向无法自动识别。"
                    elif future == future_trends:
                        print(f"未来趋势分析失败: {str(e)}")
                        future_outlook = "暂无未来展望分析。"
        
        print("研究方向和趋势分析完成")
        return research_directions, future_outlook 