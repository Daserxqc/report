# 报告生成工具函数
import os
from pathlib import Path

def fix_existing_reports(report_dir):
    """
    修复现有的报告文件
    
    Args:
        report_dir (str): 报告目录路径
    """
    # 获取所有.md文件
    report_dir = Path(report_dir)
    report_files = list(report_dir.glob("*.md"))
    
    if not report_files:
        print(f"未在 {report_dir} 中找到任何.md文件")
        return
    
    print(f"找到 {len(report_files)} 个Markdown文件")
    
    fixed_count = 0
    for file_path in report_files:
        if "fixed" in file_path.name:
            print(f"跳过已修复的文件: {file_path.name}")
            continue
            
        print(f"处理文件: {file_path.name}")
        
        # 读取原始二进制内容
        with open(file_path, "rb") as f:
            raw_data = f.read()
            
        # 尝试不同编码读取
        success = False
        for encoding in ['utf-8', 'gbk', 'gb18030', 'latin1']:
            try:
                content = raw_data.decode(encoding)
                chinese_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                
                if chinese_count > 0:
                    print(f"  使用{encoding}解码成功，检测到{chinese_count}个中文字符")
                    
                    # 创建修复后的文件
                    fixed_path = file_path.with_name(f"{file_path.stem}_fixed.md")
                    with open(fixed_path, "w", encoding="utf-8-sig") as f:
                        f.write(content)
                        
                    print(f"  已修复并保存为: {fixed_path}")
                    fixed_count += 1
                    success = True
                    break
            except UnicodeDecodeError:
                continue
        
        if not success:
            print(f"  无法修复文件 {file_path.name}，所有编码尝试均失败")
            
    print(f"\n共处理了 {len(report_files)} 个文件，成功修复 {fixed_count} 个")

def safe_save_report(report_content, filename):
    """
    安全保存报告内容到文件，确保中文字符正确编码
    
    Args:
        report_content (str): 报告内容
        filename (str): 文件名
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        # 验证内容中的中文字符
        chinese_count = sum(1 for c in report_content if '\u4e00' <= c <= '\u9fff')
        print(f"报告包含 {chinese_count} 个中文字符")
        
        # 确保使用UTF-8-SIG (带BOM标记)编码保存
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write(report_content)
        print(f"报告已保存: {filename} ({os.path.getsize(filename)} 字节)")
        
        # 验证文件内容
        with open(filename, "r", encoding="utf-8-sig") as f:
            content = f.read()
            read_chinese = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            print(f"验证成功: 写入{chinese_count}个中文字符，读取到{read_chinese}个中文字符")
            
        return True
    except Exception as e:
        print(f"保存报告失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def fix_directory_encoding(directory_path, file_pattern="*.md", add_bom=True):
    """
    修复目录中所有文件的编码问题
    
    Args:
        directory_path (str): 要处理的目录路径 
        file_pattern (str): 文件匹配模式，默认处理所有markdown文件
        add_bom (bool): 是否添加BOM标记
        
    Returns:
        dict: 处理结果统计
    """
    print(f"正在处理目录: {directory_path} 中的 {file_pattern} 文件")
    
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        print(f"错误: 目录不存在或不是有效目录: {directory_path}")
        return {"error": "目录不存在", "processed": 0, "fixed": 0}
    
    # 获取所有匹配的文件
    files = list(directory.glob(file_pattern))
    print(f"找到 {len(files)} 个匹配的文件")
    
    results = {
        "processed": len(files),
        "fixed": 0,
        "already_good": 0,
        "failed": 0,
        "details": []
    }
    
    for file_path in files:
        print(f"处理文件: {file_path.name}")
        
        # 读取原始二进制内容
        with open(file_path, "rb") as f:
            raw_data = f.read()
        
        # 检查是否已有BOM
        has_bom = raw_data.startswith(b'\xef\xbb\xbf')
        
        # 如果已有BOM且不需要修改，则跳过
        if has_bom and not add_bom:
            print(f"  文件已有BOM标记，跳过处理: {file_path.name}")
            results["already_good"] += 1
            results["details"].append({
                "file": str(file_path),
                "status": "skipped",
                "reason": "already has BOM"
            })
            continue
        
        # 尝试不同编码读取
        success = False
        for encoding in ['utf-8', 'gbk', 'gb18030', 'latin1']:
            try:
                content = raw_data.decode(encoding)
                chinese_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                
                # 创建备份
                backup_path = file_path.with_name(f"{file_path.stem}_backup{file_path.suffix}")
                with open(backup_path, "wb") as f:
                    f.write(raw_data)
                
                # 使用UTF-8-SIG重新保存
                with open(file_path, "w", encoding="utf-8-sig" if add_bom else "utf-8") as f:
                    f.write(content)
                
                # 验证
                with open(file_path, "r", encoding="utf-8-sig" if add_bom else "utf-8") as f:
                    verified_content = f.read()
                    verified_chinese = sum(1 for c in verified_content if '\u4e00' <= c <= '\u9fff')
                
                print(f"  成功使用 {encoding} 解码并重新保存，中文字符: {chinese_count} -> {verified_chinese}")
                results["fixed"] += 1
                results["details"].append({
                    "file": str(file_path),
                    "status": "fixed",
                    "original_encoding": encoding,
                    "chinese_chars": chinese_count,
                    "verified_chars": verified_chinese
                })
                success = True
                break
            except UnicodeDecodeError:
                continue
        
        if not success:
            print(f"  无法修复文件 {file_path.name}，所有编码尝试均失败")
            results["failed"] += 1
            results["details"].append({
                "file": str(file_path),
                "status": "failed",
                "reason": "encoding detection failed"
            })
    
    print(f"\n处理完成: 总共 {results['processed']} 个文件")
    print(f"  - 已修复: {results['fixed']} 个")
    print(f"  - 无需修复: {results['already_good']} 个")
    print(f"  - 修复失败: {results['failed']} 个")
    
    return results

class ReportEvaluator:
    """
    报告质量评估器 - 用于评估各类报告的质量和相关性
    """
    
    def __init__(self, llm_processor=None):
        """
        初始化评估器
        
        Args:
            llm_processor: LLM处理器实例，用于高级评分
        """
        self.llm_processor = llm_processor
        if not llm_processor:
            # 尝试初始化LLM处理器
            try:
                from collectors.llm_processor import LLMProcessor
                self.llm_processor = LLMProcessor()
                print("报告评估器已初始化LLM处理器")
            except Exception as e:
                print(f"无法初始化LLM处理器: {str(e)}")
                print("将使用简单评估方法")
        
    def evaluate_report(self, report_content, report_type, topic, raw_data=None):
        """
        评估报告质量
        
        Args:
            report_content (str): 报告内容
            report_type (str): 报告类型 (news/insights/research)
            topic (str): 报告主题
            raw_data (dict, optional): 原始数据，用于对比评估
            
        Returns:
            dict: 评估结果，包含各维度得分和建议
        """
        # 定义评估维度
        dimensions = {
            "相关性": "内容与主题的相关程度",
            "全面性": "覆盖主题的各个重要方面",
            "时效性": "信息的新鲜度和时效性",
            "深度": "分析的深度和洞察力",
            "结构性": "内容组织的逻辑性和清晰度",
            "可读性": "文本的易读性和流畅度",
            "客观性": "内容的客观性和中立性",
            "参考价值": "对读者的实用性和指导价值"
        }
        
        # 根据报告类型调整权重
        weights = self._get_dimension_weights(report_type)
        
        # 使用LLM进行评估
        if self.llm_processor:
            return self._evaluate_with_llm(report_content, report_type, topic, dimensions, weights)
        else:
            # 简单评估方法
            return self._simple_evaluate(report_content, report_type, topic, dimensions, weights)
    
    def _get_dimension_weights(self, report_type):
        """根据报告类型返回不同维度的权重"""
        if report_type.lower() == "news":
            return {
                "相关性": 0.2,
                "全面性": 0.15,
                "时效性": 0.25,  # 新闻报告时效性权重最高
                "深度": 0.1,
                "结构性": 0.1,
                "可读性": 0.1,
                "客观性": 0.05,
                "参考价值": 0.05
            }
        elif report_type.lower() == "insights":
            return {
                "相关性": 0.2,
                "全面性": 0.15,
                "时效性": 0.1,
                "深度": 0.2,  # 洞察报告深度权重较高
                "结构性": 0.1,
                "可读性": 0.1,
                "客观性": 0.05,
                "参考价值": 0.1
            }
        elif report_type.lower() == "research":
            return {
                "相关性": 0.15,
                "全面性": 0.2,  # 研究报告全面性权重较高
                "时效性": 0.05,
                "深度": 0.25,  # 研究报告深度权重最高
                "结构性": 0.1,
                "可读性": 0.05,
                "客观性": 0.1,
                "参考价值": 0.1
            }
        else:
            # 默认权重
            return {dim: 0.125 for dim in ["相关性", "全面性", "时效性", "深度", "结构性", "可读性", "客观性", "参考价值"]}
    
    def _evaluate_with_llm(self, report_content, report_type, topic, dimensions, weights):
        """
        使用LLM评估报告质量
        
        Args:
            report_content: 报告内容
            report_type: 报告类型
            topic: 报告主题
            dimensions: 评估维度说明
            weights: 各维度权重
            
        Returns:
            dict: 评估结果
        """
        # 准备评估提示
        dimension_text = "\n".join([f"{dim} ({desc}): 评分标准 1-10分" for dim, desc in dimensions.items()])
        
        # 根据报告类型设置不同的评估重点
        if report_type.lower() == "news":
            focus = "时效性和相关性，评估新闻报道是否及时、全面、客观"
        elif report_type.lower() == "insights":
            focus = "深度和洞察力，评估报告是否提供有价值的行业洞察和分析"
        elif report_type.lower() == "research":
            focus = "全面性和专业深度，评估研究报告的学术质量和专业水平"
        else:
            focus = "整体质量和内容价值"
        
        # 构建评估提示
        prompt = f"""
        请作为专业的{topic}领域报告评估专家，对以下{report_type}类型报告进行全面评估，重点关注{focus}。
        
        报告内容:
        ```
        {report_content[:8000]}  # 限制内容长度
        ```
        
        请对报告按以下维度进行评分（1-10分）并给出简短理由:
        {dimension_text}
        
        评分完成后，请给出总体评价（200字以内）和改进建议（100字以内）。
        
        请以JSON格式返回评估结果:
        {{
            "scores": {{
                "相关性": {{
                    "score": 分数,
                    "reason": "评分理由"
                }},
                ... 其他维度 ...
            }},
            "overall_score": 加权总分,
            "evaluation": "总体评价",
            "suggestions": "改进建议"
        }}
        """
        
        system_message = f"""你是一位专业的{topic}行业报告评估专家，擅长评估{report_type}类型报告的质量。
你的评估应客观、公正、专业，基于报告内容给出准确的评分和有建设性的反馈。
你的回答必须是严格的JSON格式，不包含任何其他文本。"""
        
        try:
            # 使用JSON专用API调用
            evaluation = self.llm_processor.call_llm_api_json(prompt, system_message)
            
            # 计算加权总分（如果没有提供）
            if "overall_score" not in evaluation:
                weighted_score = 0
                scores = evaluation.get("scores", {})
                for dim, weight in weights.items():
                    if dim in scores:
                        dim_score = scores[dim].get("score", 5)
                        weighted_score += dim_score * weight
                
                evaluation["overall_score"] = round(weighted_score, 1)
            
            return evaluation
            
        except Exception as e:
            print(f"LLM评估报告时出错: {str(e)}")
            # 失败时使用简单评估
            return self._simple_evaluate(report_content, report_type, topic, dimensions, weights)
    
    def _simple_evaluate(self, report_content, report_type, topic, dimensions, weights):
        """
        使用简单规则评估报告质量
        
        Args:
            report_content: 报告内容
            report_type: 报告类型
            topic: 报告主题
            dimensions: 评估维度说明
            weights: 各维度权重
            
        Returns:
            dict: 评估结果
        """
        scores = {}
        topic_lower = topic.lower()
        content_lower = report_content.lower()
        
        # 相关性评分
        topic_relevance = 0
        topic_relevance += content_lower.count(topic_lower) * 0.5
        topic_relevance = min(10, max(1, topic_relevance))
        scores["相关性"] = {
            "score": topic_relevance,
            "reason": f"报告中提到主题词'{topic}'的频率适中" if topic_relevance > 5 else f"报告中很少提及主题词'{topic}'"
        }
        
        # 全面性评分（基于内容长度和结构）
        content_length = len(report_content)
        headings_count = report_content.count('#')
        if report_type.lower() == "research":
            comprehensiveness = min(10, max(1, content_length / 5000 * 5 + headings_count / 10 * 5))
        else:
            comprehensiveness = min(10, max(1, content_length / 3000 * 5 + headings_count / 7 * 5))
        
        scores["全面性"] = {
            "score": comprehensiveness,
            "reason": f"报告长度({content_length}字符)和结构({headings_count}个标题)适当" if comprehensiveness > 5 else "报告内容或结构不够全面"
        }
        
        # 结构性评分
        structure_score = min(10, max(1, headings_count * 1.0))
        scores["结构性"] = {
            "score": structure_score,
            "reason": "报告结构清晰" if structure_score > 5 else "报告结构可以优化"
        }
        
        # 可读性评分（基于句子长度和段落数）
        sentences = content_lower.count('。') + content_lower.count('.') + content_lower.count('!') + content_lower.count('！')
        paragraphs = content_lower.count('\n\n')
        avg_sentence_length = content_length / max(1, sentences)
        readability = min(10, max(1, 10 - (avg_sentence_length - 50) / 10 + paragraphs / 20 * 5))
        
        scores["可读性"] = {
            "score": readability,
            "reason": "句子长度适中，段落划分合理" if readability > 5 else "句子可能过长或段落划分不够合理"
        }
        
        # 其他维度使用中等分数
        for dim in dimensions:
            if dim not in scores:
                scores[dim] = {
                    "score": 5,
                    "reason": "使用简单评估方法，无法准确评估该维度"
                }
        
        # 计算加权总分
        weighted_score = 0
        for dim, weight in weights.items():
            weighted_score += scores[dim]["score"] * weight
        
        return {
            "scores": scores,
            "overall_score": round(weighted_score, 1),
            "evaluation": f"{report_type}报告质量一般，内容长度{content_length}字符，包含{headings_count}个标题，结构基本合理。",
            "suggestions": "建议增加内容深度，改善报告结构，并确保更紧密关联主题。"
        }
    
    def compare_reports(self, reports, topic):
        """
        比较多份报告的质量
        
        Args:
            reports: 字典，键为报告类型，值为报告内容
            topic: 报告主题
            
        Returns:
            dict: 比较结果
        """
        results = {}
        
        # 评估每份报告
        for report_type, content in reports.items():
            results[report_type] = self.evaluate_report(content, report_type, topic)
        
        # 计算综合得分
        combined_score = 0
        type_weights = {
            "news": 0.3,
            "insights": 0.3,
            "research": 0.4
        }
        
        for report_type, result in results.items():
            weight = type_weights.get(report_type.lower(), 0.33)
            combined_score += result["overall_score"] * weight
        
        # 找出最强和最弱的报告
        strongest = max(results.items(), key=lambda x: x[1]["overall_score"])
        weakest = min(results.items(), key=lambda x: x[1]["overall_score"])
        
        return {
            "results": results,
            "combined_score": round(combined_score, 1),
            "strongest_report": {
                "type": strongest[0],
                "score": strongest[1]["overall_score"]
            },
            "weakest_report": {
                "type": weakest[0],
                "score": weakest[1]["overall_score"]
            },
            "summary": f"三份报告的综合质量评分为{round(combined_score, 1)}/10。{strongest[0]}报告表现最佳，得分{strongest[1]['overall_score']}；{weakest[0]}报告需要改进，得分{weakest[1]['overall_score']}。"
        }

if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        # 如果提供了参数，使用参数作为报告目录路径
        report_dir = sys.argv[1]
        print(f"正在处理目录: {report_dir}")
        fix_directory_encoding(report_dir)
    else:
        # 没有参数，使用默认目录
        default_dirs = ["reports", "output"]
        for d in default_dirs:
            if Path(d).exists():
                print(f"正在处理默认目录: {d}")
                fix_directory_encoding(d)
                break
        else:
            print(f"未找到默认目录: {default_dirs}")
            print("请运行: python report_utils.py <reports_directory>")
