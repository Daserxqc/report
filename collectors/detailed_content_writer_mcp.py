from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from collectors.llm_processor import LLMProcessor
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'search_mcp', 'src'))
from search_mcp.models import Document
from collectors.outline_writer_mcp import OutlineNode


@dataclass
class ContentWritingConfig:
    """内容写作配置"""
    writing_style: str = "professional"     # 写作风格
    target_audience: str = "通用"           # 目标受众
    tone: str = "objective"                 # 语调
    depth_level: str = "detailed"           # 深度级别
    include_examples: bool = True           # 是否包含案例
    include_citations: bool = True          # 是否包含引用
    max_section_length: int = 2000          # 最大章节长度
    min_section_length: int = 500           # 最小章节长度


class DetailedContentWriterMcp:
    """
    详细内容撰写MCP (Model Context Protocol)
    
    用途：报告内容撰写的主力，负责填充各个章节。
    
    职责：
    - 根据章节标题和参考资料撰写详细内容
    - 可被并行调用，同时为多个章节生成内容
    - 在生成内容时，可根据指令添加引用标记
    
    输入：section_title: str, content_data: list[Document], overall_report_context: str
    输出：str (章节内容文本)
    
    实现要点：Prompt需非常紧凑，包含角色扮演（"你是一位...分析师"）、章节标题、参考资料和全局上下文。
    """
    
    def __init__(self):
        """初始化DetailedContentWriterMcp"""
        try:
            self.llm_processor = LLMProcessor()
            self.has_llm = True
            print("✅ DetailedContentWriterMcp初始化完成")
        except Exception as e:
            print(f"⚠️ LLM处理器初始化失败: {str(e)}")
            self.has_llm = False
        
        # 预定义的写作模板
        self.writing_templates = self._load_writing_templates()
        
        # 角色定义
        self.role_definitions = self._load_role_definitions()
    
    def _load_writing_templates(self) -> Dict[str, str]:
        """加载写作模板"""
        return {
            "standard": """
你是一位专业的{role}，正在撰写关于"{overall_topic}"的{section_title}章节。

章节要求：
- 目标受众：{target_audience}
- 写作风格：{writing_style}
- 内容深度：{depth_level}
- 字数要求：{word_count_requirement}

参考资料：
{reference_content}

全局报告上下文：
{overall_report_context}

撰写要求：
1. **专业深度**：基于参考资料提供深入、专业的分析
2. **逻辑结构**：内容应有清晰的逻辑层次和段落结构
3. **实用价值**：突出实际应用价值和现实意义
4. **引用规范**：在引用参考资料时使用[1]、[2]等标记
5. **语言表达**：使用{tone}的语调，适合{target_audience}阅读

章节结构建议：
- 开篇：简要介绍本章节的核心议题
- 主体：围绕关键要点展开详细分析
- 实例：{example_instruction}
- 总结：概括本章节的主要观点

请撰写完整的章节内容，确保信息准确、逻辑清晰、表达流畅。
""",

            "academic": """
你是一位资深的{role}，正在撰写学术报告中的"{section_title}"章节。

研究主题：{overall_topic}
章节定位：{section_context}

参考文献和资料：
{reference_content}

学术写作要求：
1. **理论基础**：建立坚实的理论框架
2. **文献综述**：充分回顾和引用相关研究
3. **方法论述**：清晰说明研究方法和逻辑
4. **客观分析**：保持学术的客观性和严谨性
5. **创新观点**：提出有价值的见解和观点

写作规范：
- 使用学术语言和专业术语
- 遵循学术引用规范 [1]、[2] 等
- 字数控制在 {word_count_requirement} 
- 逻辑严密，论证充分

请按照学术写作标准撰写本章节内容。
""",

            "business": """
你是一位经验丰富的{role}，正在为商业报告撰写"{section_title}"章节。

商业主题：{overall_topic}
商业背景：{business_context}

市场数据和资料：
{reference_content}

商业写作要求：
1. **商业洞察**：提供深刻的商业洞察和分析
2. **数据驱动**：使用具体数据支撑观点
3. **实用导向**：关注实际应用和商业价值
4. **决策支持**：为决策者提供有价值的信息
5. **风险意识**：识别和分析潜在风险

内容结构：
- 现状分析：基于数据的客观分析
- 趋势洞察：识别关键趋势和机会
- 战略建议：提出可行的战略建议
- 风险提示：指出需要注意的风险点

字数要求：{word_count_requirement}
目标受众：{target_audience}

请撰写具有商业价值的章节内容。
""",

            "technical": """
你是一位专业的{role}，正在撰写技术报告中的"{section_title}"章节。

技术主题：{overall_topic}
技术背景：{technical_context}

技术资料和参考：
{reference_content}

技术写作要求：
1. **技术准确性**：确保技术信息的准确性
2. **原理阐述**：清楚解释技术原理和机制
3. **实现细节**：描述关键的实现方法和技术路径
4. **性能分析**：分析技术性能和优劣势
5. **应用场景**：说明实际应用场景和案例

内容组织：
- 技术概述：介绍核心技术概念
- 原理分析：深入分析技术原理
- 实现方案：描述技术实现方法
- 应用实例：提供具体应用案例
- 发展趋势：分析技术发展方向

写作风格：技术性强但易于理解
字数要求：{word_count_requirement}

请撰写专业且实用的技术章节内容。
"""
        }
    
    def _load_role_definitions(self) -> Dict[str, str]:
        """加载角色定义"""
        return {
            "academic": "学术研究专家和教授",
            "business": "商业分析师和战略顾问", 
            "technical": "技术专家和架构师",
            "industry": "行业分析师和咨询顾问",
            "market": "市场研究专家和投资分析师",
            "policy": "政策分析专家和研究员",
            "general": "专业内容分析师"
        }
    
    def write_section_content(self,
                             section_title: str,
                             content_data: List[Union[Document, Dict]],
                             overall_report_context: str,
                             config: ContentWritingConfig = None) -> str:
        """
        撰写章节详细内容
        
        Args:
            section_title: 章节标题
            content_data: 参考内容数据
            overall_report_context: 整体报告上下文
            config: 写作配置
            
        Returns:
            str: 章节内容
        """
        if not self.has_llm:
            return self._fallback_content_generation(section_title, content_data)
        
        if config is None:
            config = ContentWritingConfig()
        
        try:
            print(f"✍️ 开始撰写章节: {section_title}")
            
            # 准备参考内容
            reference_content = self._prepare_reference_content(content_data)
            
            # 确定写作角色
            role = self._determine_writing_role(section_title, overall_report_context)
            
            # 选择合适的模板
            template = self._select_writing_template(config.writing_style, role)
            
            # 准备模板参数
            template_params = self._prepare_template_params(
                section_title, overall_report_context, reference_content, config, role
            )
            
            # 格式化prompt
            prompt = template.format(**template_params)
            
            # 计算token限制
            max_tokens = min(config.max_section_length * 2, 4000)
            
            # 调用LLM生成内容
            content = self.llm_processor.call_llm_api(
                prompt,
                f"你是一位专业的内容创作专家，专门负责撰写高质量的{config.writing_style}风格内容。",
                temperature=0.3,
                max_tokens=max_tokens
            )
            
            # 后处理内容
            processed_content = self._post_process_content(content, config)
            
            print(f"✅ 章节'{section_title}'撰写完成，长度: {len(processed_content)}字符")
            return processed_content
            
        except Exception as e:
            print(f"❌ 章节'{section_title}'撰写失败: {str(e)}")
            return self._fallback_content_generation(section_title, content_data)
    
    def _prepare_reference_content(self, content_data: List[Union[Document, Dict]]) -> str:
        """准备参考内容"""
        if not content_data:
            return "无参考资料"
        
        reference_parts = []
        
        for i, item in enumerate(content_data[:8]):  # 限制前8个参考资料
            if isinstance(item, Document):
                ref_text = f"[{i+1}] {item.title}\n来源: {item.source} ({item.source_type})\n内容: {item.content[:300]}..."
                if item.authors:
                    ref_text += f"\n作者: {', '.join(item.authors)}"
                if item.publish_date:
                    ref_text += f"\n发布时间: {item.publish_date}"
                    
            elif isinstance(item, dict):
                title = item.get("title", f"参考资料{i+1}")
                content = item.get("content", item.get("summary", ""))[:300]
                source = item.get("source", "未知来源")
                ref_text = f"[{i+1}] {title}\n来源: {source}\n内容: {content}..."
                
            reference_parts.append(ref_text)
        
        return "\n\n".join(reference_parts)
    
    def _determine_writing_role(self, section_title: str, context: str) -> str:
        """根据章节标题和上下文确定写作角色"""
        title_lower = section_title.lower()
        context_lower = context.lower()
        
        # 学术相关关键词
        if any(keyword in title_lower for keyword in ["研究", "理论", "方法", "文献", "学术"]):
            return "academic"
        
        # 商业相关关键词  
        if any(keyword in title_lower for keyword in ["市场", "商业", "投资", "收益", "策略", "竞争"]):
            return "business"
        
        # 技术相关关键词
        if any(keyword in title_lower for keyword in ["技术", "算法", "架构", "实现", "系统", "开发"]):
            return "technical"
        
        # 政策相关关键词
        if any(keyword in title_lower for keyword in ["政策", "法规", "监管", "标准", "规范"]):
            return "policy"
        
        # 行业相关关键词
        if any(keyword in title_lower for keyword in ["行业", "产业", "发展", "趋势", "现状"]):
            return "industry"
        
        # 根据上下文判断
        if "学术" in context_lower or "研究" in context_lower:
            return "academic"
        elif "商业" in context_lower or "市场" in context_lower:
            return "business"
        elif "技术" in context_lower:
            return "technical"
        
        return "general"
    
    def _select_writing_template(self, writing_style: str, role: str) -> str:
        """选择写作模板"""
        # 根据角色选择模板
        if role == "academic":
            return self.writing_templates["academic"]
        elif role == "business":
            return self.writing_templates["business"]
        elif role == "technical":
            return self.writing_templates["technical"]
        else:
            return self.writing_templates["standard"]
    
    def _prepare_template_params(self, section_title: str, overall_report_context: str, 
                                reference_content: str, config: ContentWritingConfig, role: str) -> Dict[str, str]:
        """准备模板参数"""
        # 提取整体主题
        overall_topic = self._extract_overall_topic(overall_report_context)
        
        # 角色描述
        role_description = self.role_definitions.get(role, self.role_definitions["general"])
        
        # 字数要求描述
        word_count_requirement = f"{config.min_section_length}-{config.max_section_length}字"
        
        # 示例指导
        example_instruction = "结合具体案例和实例进行说明" if config.include_examples else "重点进行理论分析"
        
        # 语调描述
        tone_descriptions = {
            "objective": "客观、中性",
            "analytical": "分析性、深入",
            "professional": "专业、正式",
            "engaging": "生动、引人入胜",
            "authoritative": "权威、可信"
        }
        
        return {
            "role": role_description,
            "overall_topic": overall_topic,
            "section_title": section_title,
            "target_audience": config.target_audience,
            "writing_style": config.writing_style,
            "depth_level": config.depth_level,
            "word_count_requirement": word_count_requirement,
            "reference_content": reference_content,
            "overall_report_context": overall_report_context,
            "tone": tone_descriptions.get(config.tone, "客观、专业"),
            "example_instruction": example_instruction,
            "section_context": f"作为整体报告的重要组成部分",
            "business_context": overall_report_context if role == "business" else "",
            "technical_context": overall_report_context if role == "technical" else ""
        }
    
    def _extract_overall_topic(self, context: str) -> str:
        """从上下文中提取整体主题"""
        # 简单的主题提取逻辑
        lines = context.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('•', '-', '*', '1.', '2.')):
                # 取第一个非列表项的行作为主题
                return line[:50] + ("..." if len(line) > 50 else "")
        
        return "相关主题"
    
    def _post_process_content(self, content: str, config: ContentWritingConfig) -> str:
        """后处理生成的内容"""
        if not content:
            return "内容生成失败"
        
        # 清理格式
        content = content.strip()
        
        # 移除可能的标题重复
        lines = content.split('\n')
        if lines and lines[0].strip().startswith('#'):
            content = '\n'.join(lines[1:]).strip()
        
        # 检查长度
        if len(content) < config.min_section_length:
            print(f"⚠️ 内容长度({len(content)})低于最小要求({config.min_section_length})")
        elif len(content) > config.max_section_length:
            print(f"⚠️ 内容长度({len(content)})超过最大限制({config.max_section_length})")
        
        # 确保引用格式正确
        if config.include_citations:
            content = self._normalize_citations(content)
        
        return content
    
    def _normalize_citations(self, content: str) -> str:
        """规范化引用格式"""
        import re
        
        # 统一引用格式为 [数字]
        content = re.sub(r'\[(\d+)\]', r'[\1]', content)
        content = re.sub(r'（(\d+)）', r'[\1]', content)
        content = re.sub(r'\((\d+)\)', r'[\1]', content)
        
        return content
    
    def write_multiple_sections(self,
                               sections: List[Dict[str, any]],
                               overall_context: str,
                               config: ContentWritingConfig = None) -> Dict[str, str]:
        """
        批量撰写多个章节
        
        Args:
            sections: 章节信息列表，每个包含 title, content_data 等
            overall_context: 整体上下文
            config: 写作配置
            
        Returns:
            Dict[str, str]: 章节标题到内容的映射
        """
        if config is None:
            config = ContentWritingConfig()
        
        results = {}
        
        for i, section_info in enumerate(sections):
            try:
                section_title = section_info.get("title", f"章节{i+1}")
                content_data = section_info.get("content_data", [])
                
                # 为该章节创建特定配置
                section_config = config
                if "config" in section_info:
                    # 允许为每个章节自定义配置
                    section_config = ContentWritingConfig(**section_info["config"])
                
                content = self.write_section_content(
                    section_title=section_title,
                    content_data=content_data, 
                    overall_report_context=overall_context,
                    config=section_config
                )
                
                results[section_title] = content
                print(f"  ✅ [{i+1}/{len(sections)}] '{section_title}' 完成")
                
            except Exception as e:
                print(f"  ❌ [{i+1}/{len(sections)}] '{section_title}' 失败: {str(e)}")
                results[section_title] = f"章节内容生成失败: {str(e)}"
        
        return results
    
    def enhance_section_content(self,
                               existing_content: str,
                               section_title: str,
                               enhancement_type: str = "depth",
                               additional_data: List[Union[Document, Dict]] = None) -> str:
        """
        增强现有章节内容
        
        Args:
            existing_content: 现有内容
            section_title: 章节标题
            enhancement_type: 增强类型 (depth, examples, analysis, citations)
            additional_data: 额外数据
            
        Returns:
            str: 增强后的内容
        """
        if not self.has_llm:
            print("⚠️ 内容增强功能需要LLM支持")
            return existing_content
        
        try:
            enhancement_instructions = {
                "depth": "增加内容的深度和专业性，补充更多技术细节和理论分析",
                "examples": "添加更多具体案例和实例，增强内容的实用性",
                "analysis": "增强分析性内容，加入更多批判性思考和深入见解",
                "citations": "完善引用和参考资料，增加内容的权威性"
            }
            
            instruction = enhancement_instructions.get(enhancement_type, enhancement_instructions["depth"])
            
            # 准备额外参考内容
            additional_ref = ""
            if additional_data:
                additional_ref = f"\n补充参考资料：\n{self._prepare_reference_content(additional_data)}"
            
            prompt = f"""
请对以下章节内容进行增强优化：

章节标题：{section_title}
增强要求：{instruction}

现有内容：
{existing_content}
{additional_ref}

优化要求：
1. 保持原有内容的核心结构和观点
2. {instruction}
3. 确保增强后的内容逻辑连贯
4. 增强后长度应比原内容增加30-50%
5. 保持专业性和准确性

请输出增强后的完整章节内容。
"""
            
            enhanced_content = self.llm_processor.call_llm_api(
                prompt,
                f"你是一位专业的内容编辑专家，擅长优化和增强技术文档内容。",
                temperature=0.3,
                max_tokens=4000
            )
            
            print(f"✅ 章节内容增强完成，原长度: {len(existing_content)}, 新长度: {len(enhanced_content)}")
            return enhanced_content.strip()
            
        except Exception as e:
            print(f"❌ 内容增强失败: {str(e)}")
            return existing_content
    
    def _fallback_content_generation(self, section_title: str, content_data: List) -> str:
        """备用内容生成方法"""
        try:
            # 基于标题和数据生成简单内容
            content_parts = [f"## {section_title}\n"]
            
            if content_data:
                content_parts.append("基于现有资料分析，本章节主要内容包括：\n")
                
                for i, item in enumerate(content_data[:3]):
                    if isinstance(item, Document):
                        summary = item.content[:200] + "..." if len(item.content) > 200 else item.content
                        content_parts.append(f"### {item.title}\n{summary}\n")
                    elif isinstance(item, dict):
                        title = item.get("title", f"要点{i+1}")
                        content = item.get("content", "")[:200]
                        content_parts.append(f"### {title}\n{content}\n")
            else:
                content_parts.append(f"本章节将详细介绍{section_title}的相关内容，包括基本概念、发展现状、应用场景等方面。\n")
            
            content_parts.append("更多详细内容有待进一步研究和分析。")
            
            return '\n'.join(content_parts)
            
        except Exception as e:
            return f"## {section_title}\n\n内容生成失败: {str(e)}\n\n本章节需要进一步完善。" 