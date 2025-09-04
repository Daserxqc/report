import json
import re
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class PaperRelevanceAnalyzer:
    """论文相关性分析器，支持并行处理"""
    
    def __init__(self, llm_processor, max_workers=3):
        self.llm_processor = llm_processor
        self.max_workers = max_workers
        self.lock = threading.Lock()
    
    def analyze_batch_relevance(self, batch: List[Dict], topic: str, english_topic: str) -> List[Dict]:
        """分析一批论文的相关性"""
        if not batch:
            return batch
            
        batch_text = ""
        for idx, item in enumerate(batch):
            title = item.get('title', '无标题')
            summary = item.get('summary', '无摘要')
            batch_text += f"论文{idx+1}:\n标题: {title}\n摘要: {summary}\n\n"
        
        system_prompt = f"""你是一位专业的{topic}领域研究专家，擅长识别真正相关的研究工作。
你的任务是评估每篇论文是否直接研究{topic}/{english_topic}领域的核心问题，而不仅仅是在其他领域中应用或浅层提及这个主题。
请特别注意区分:
1. 核心研究: 直接研究{topic}的基础理论、方法、算法、架构等
2. 应用研究: 将{topic}应用于其他领域的研究
3. 浅层提及: 仅在背景或参考中提及{topic}"""

        prompt = f"""请评估以下{len(batch)}篇论文是否真正属于{topic}/{english_topic}领域的核心研究，而非仅仅应用或提及。
对于每篇论文，给出:
1. 相关性分数(0-10，10为最高)
2. 分类(核心/应用/提及)
3. 一句话解释理由

{batch_text}

请以JSON格式回答，使用如下结构:
{{
  "评估": [
    {{
      "论文编号": 1,
      "相关性": 8,
      "分类": "核心",
      "理由": "该论文直接研究新型神经网络架构..."
    }},
    ...
  ]
}}"""

        try:
            response = self.llm_processor.call_llm_api(prompt, system_prompt)
            
            # 解析JSON响应
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                try:
                    evaluation = json.loads(json_str)
                    
                    # 处理每篇论文的评估结果
                    for eval_item in evaluation.get("评估", []):
                        paper_idx = eval_item.get("论文编号", 0) - 1
                        if 0 <= paper_idx < len(batch):
                            batch[paper_idx]["relevance_score"] = eval_item.get("相关性", 0)
                            batch[paper_idx]["research_type"] = eval_item.get("分类", "未知")
                            batch[paper_idx]["relevance_reason"] = eval_item.get("理由", "")
                    
                    return batch
                except json.JSONDecodeError:
                    print(f"无法解析评估结果JSON，跳过此批次")
                    return batch
            else:
                print(f"评估结果不包含有效JSON，跳过此批次")
                return batch
                
        except Exception as e:
            print(f"评估批次出错: {str(e)}")
            return batch
    
    def preprocess_research_items(self, research_items: List[Dict], topic: str) -> List[Dict]:
        """
        预处理学术论文，评估与主题的相关性，并筛选出最相关的论文
        支持并行处理
        """
        if not self.llm_processor or len(research_items) <= 10:
            return research_items
            
        print(f"正在评估{len(research_items)}篇论文与'{topic}'的相关性...")
        
        # 获取英文主题
        english_topic = topic
        if any('\u4e00' <= char <= '\u9fff' for char in topic):
            try:
                english_topic = self.llm_processor.translate_text(topic, "English")
            except:
                pass
        
        # 批处理评估，支持并行
        batch_size = 5
        batches = [research_items[i:i+batch_size] for i in range(0, len(research_items), batch_size)]
        processed_items = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有批次任务
            future_to_batch = {
                executor.submit(self.analyze_batch_relevance, batch, topic, english_topic): batch 
                for batch in batches
            }
            
            # 收集结果
            for future in as_completed(future_to_batch):
                try:
                    batch_result = future.result()
                    processed_items.extend(batch_result)
                except Exception as e:
                    print(f"批次处理出错: {str(e)}")
                    # 添加原始批次数据
                    original_batch = future_to_batch[future]
                    processed_items.extend(original_batch)
        
        # 按相关性分数排序
        def sort_key(item):
            score = item.get("relevance_score", 0)
            type_score = {"核心": 2, "应用": 1, "提及": 0, "未知": 0}
            return (score, type_score.get(item.get("research_type", "未知"), 0))
        
        processed_items.sort(key=sort_key, reverse=True)
        
        # 输出评估结果统计
        core_count = sum(1 for item in processed_items if item.get("research_type") == "核心")
        app_count = sum(1 for item in processed_items if item.get("research_type") == "应用")
        mention_count = sum(1 for item in processed_items if item.get("research_type") == "提及")
        
        print(f"论文相关性评估结果: 核心研究 {core_count} 篇, 应用研究 {app_count} 篇, 浅层提及 {mention_count} 篇")
        
        # 筛选逻辑
        filtered_items = [
            item for item in processed_items 
            if item.get("research_type") == "核心" or 
               (item.get("research_type") == "应用" and item.get("relevance_score", 0) >= 7)
        ]
        
        if len(filtered_items) < 20:
            filtered_items = [
                item for item in processed_items 
                if item.get("relevance_score", 0) >= 4
            ]
        
        if len(filtered_items) < 15:
            filtered_items = [
                item for item in processed_items 
                if item.get("relevance_score", 0) >= 3
            ]
        
        print(f"筛选后保留 {len(filtered_items)} 篇最相关论文")
        return filtered_items 