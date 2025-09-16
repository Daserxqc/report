import json
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from collectors.llm_processor import LLMProcessor
from collectors.search_mcp_old import Document


@dataclass
class OutlineNode:
    """大纲节点数据结构"""
    title: str
    level: int                    # 层级 (1=主章节, 2=子章节, 3=子子章节)
    order: int                    # 在同级中的顺序
    description: str = ""         # 节点描述
    subsections: List['OutlineNode'] = None
    key_points: List[str] = None
    estimated_length: str = ""    # 预估长度
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []
        if self.key_points is None:
            self.key_points = []
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "title": self.title,
            "level": self.level,
            "order": self.order,
            "description": self.description,
            "subsections": [sub.to_dict() for sub in self.subsections],
            "key_points": self.key_points,
            "estimated_length": self.estimated_length
        }


class OutlineWriterMcp:
    """
    大纲撰写MCP (Model Context Protocol)
    
    用途：为特定主题和报告类型创建逻辑清晰的结构化大纲。
    
    职责：
    - 生成符合标准范式（如学术开题报告）的大纲
    - 将大纲输出为程序易于处理的层级化OutlineNode对象
    
    输入：topic: str, report_type: str, user_requirements: str = ""
    输出：OutlineNode
    
    实现要点：Prompt需强调逻辑性和结构化JSON输出。
    """
    
    def __init__(self):
        """初始化OutlineWriterMcp"""
        try:
            self.llm_processor = LLMProcessor()
            self.has_llm = True
            print("✅ OutlineWriterMcp初始化完成")
        except Exception as e:
            print(f"⚠️ LLM处理器初始化失败: {str(e)}")
            self.has_llm = False
        
        # 预定义的大纲模板
        self.outline_templates = self._load_outline_templates()
        
        # 报告类型规范
        self.report_standards = self._load_report_standards()
    
    def _load_outline_templates(self) -> Dict[str, str]:
        """加载大纲模板"""
        return {
            "academic_proposal": """
请为学术研究主题"{topic}"创建一个标准的学术开题报告大纲。

用户特殊要求：{user_requirements}

请按照学术开题报告的标准结构，创建详细的层级化大纲：

1. **研究背景与意义**
   - 研究背景
   - 研究问题
   - 研究意义

2. **文献综述**
   - 相关理论基础
   - 国内外研究现状
   - 研究空白与不足

3. **研究目标与内容**
   - 研究目标
   - 研究内容
   - 创新点

4. **研究方法与技术路线**
   - 研究方法
   - 技术路线
   - 实施方案

5. **研究计划与进度安排**
   - 研究计划
   - 时间安排
   - 预期成果

6. **参考文献**

请返回以下JSON格式：
```json
{{
    "title": "大纲总标题",
    "level": 0,
    "order": 0,
    "description": "大纲总体描述",
    "subsections": [
        {{
            "title": "主章节标题",
            "level": 1,
            "order": 1,
            "description": "章节描述和目标",
            "key_points": ["关键点1", "关键点2"],
            "estimated_length": "800-1000字",
            "subsections": [
                {{
                    "title": "子章节标题",
                    "level": 2,
                    "order": 1,
                    "description": "子章节描述",
                    "key_points": ["子要点1", "子要点2"],
                    "estimated_length": "300-400字",
                    "subsections": []
                }}
            ]
        }}
    ]
}}
```
""",

            "business_report": """
请为商业主题"{topic}"创建一个标准的商业报告大纲。

用户特殊要求：{user_requirements}

请按照商业报告的标准结构，创建详细的层级化大纲：

1. **执行摘要**
   - 核心发现
   - 主要建议
   - 关键指标

2. **市场分析**
   - 市场现状
   - 竞争格局
   - 发展趋势

3. **产品/服务分析**
   - 产品特点
   - 技术优势
   - 应用场景

4. **商业模式**
   - 价值主张
   - 收入模式
   - 成本结构

5. **风险评估**
   - 技术风险
   - 市场风险
   - 运营风险

6. **建议与结论**
   - 战略建议
   - 实施路径
   - 预期收益

请按照标准JSON格式返回结构化大纲，确保每个节点包含title、level、order、description、key_points、estimated_length、subsections字段。
""",

            "technical_report": """
请为技术主题"{topic}"创建一个标准的技术报告大纲。

用户特殊要求：{user_requirements}

请按照技术报告的标准结构，创建详细的层级化大纲：

1. **技术概述**
   - 技术背景
   - 核心概念
   - 技术特点

2. **技术原理**
   - 基础理论
   - 实现机制
   - 关键算法

3. **技术应用**
   - 应用领域
   - 实际案例
   - 部署方案

4. **性能分析**
   - 性能指标
   - 对比分析
   - 优化方案

5. **发展趋势**
   - 技术演进
   - 未来方向
   - 挑战与机遇

6. **总结与展望**
   - 技术总结
   - 应用前景
   - 发展建议

请按照标准JSON格式返回结构化大纲。
""",

            "industry_analysis": """
请为行业主题"{topic}"创建一个标准的行业分析报告大纲。

用户特殊要求：{user_requirements}

请按照行业分析报告的标准结构，创建详细的层级化大纲：

1. **行业概述**
   - 行业定义
   - 发展历程
   - 产业链结构

2. **市场规模与增长**
   - 市场规模
   - 增长趋势
   - 区域分布

3. **竞争格局**
   - 主要参与者
   - 市场份额
   - 竞争策略

4. **技术发展**
   - 关键技术
   - 技术趋势
   - 创新驱动

5. **政策环境**
   - 政策支持
   - 监管要求
   - 标准规范

6. **发展前景**
   - 机遇分析
   - 挑战识别
   - 发展预测

请按照标准JSON格式返回结构化大纲。
""",

            "comprehensive": """
请为主题"{topic}"创建一个综合性报告大纲。

报告类型：{report_type}
用户特殊要求：{user_requirements}

请根据主题特点和用户要求，创建一个逻辑清晰、结构合理的大纲。

基本结构框架：
1. **引言/概述** - 背景介绍和目标设定
2. **核心内容** - 根据主题特点组织2-4个主要章节
3. **分析讨论** - 深入分析和讨论
4. **结论建议** - 总结和建议

要求：
- 每个主章节应包含2-4个子章节
- 每个子章节应有明确的描述和关键点
- 估算每个章节的合适长度
- 确保逻辑连贯，层次分明

请按照标准JSON格式返回结构化大纲，包含完整的层级结构。
"""
        }
    
    def _load_report_standards(self) -> Dict[str, Dict]:
        """加载报告类型标准"""
        return {
            "academic_proposal": {
                "typical_sections": 6,
                "total_length": "8000-12000字",
                "key_characteristics": ["严谨性", "创新性", "可行性"],
                "required_elements": ["文献综述", "研究方法", "技术路线"]
            },
            "business_report": {
                "typical_sections": 6,
                "total_length": "6000-10000字",
                "key_characteristics": ["实用性", "数据驱动", "决策导向"],
                "required_elements": ["市场分析", "商业模式", "风险评估"]
            },
            "technical_report": {
                "typical_sections": 6,
                "total_length": "5000-8000字",
                "key_characteristics": ["技术性", "专业性", "实践性"],
                "required_elements": ["技术原理", "应用案例", "性能分析"]
            },
            "industry_analysis": {
                "typical_sections": 6,
                "total_length": "7000-12000字",
                "key_characteristics": ["全面性", "客观性", "前瞻性"],
                "required_elements": ["市场规模", "竞争格局", "发展趋势"]
            }
        }
    
    def create_outline(self, 
                      topic: str,
                      report_type: str = "comprehensive",
                      user_requirements: str = "",
                      reference_data: List[Union[Document, Dict]] = None) -> OutlineNode:
        """
        创建报告大纲
        
        Args:
            topic: 报告主题
            report_type: 报告类型
            user_requirements: 用户特殊要求
            reference_data: 参考数据
            
        Returns:
            OutlineNode: 结构化大纲
        """
        if not self.has_llm:
            return self._fallback_outline_creation(topic, report_type, user_requirements)
        
        try:
            print(f"🎯 开始创建'{report_type}'类型的'{topic}'报告大纲...")
            
            # 选择合适的模板
            template = self._select_template(report_type)
            
            # 准备模板参数
            template_params = {
                "topic": topic,
                "report_type": report_type,
                "user_requirements": user_requirements or "无特殊要求",
            }
            
            # 如果有参考数据，添加相关信息
            if reference_data:
                data_summary = self._summarize_reference_data(reference_data)
                template_params["reference_info"] = f"\n参考数据摘要：\n{data_summary}"
            else:
                template_params["reference_info"] = ""
            
            # 格式化prompt
            prompt = template.format(**template_params)
            
            # 调用LLM生成大纲
            response = self.llm_processor.call_llm_api_json(
                prompt,
                f"你是一位专业的{report_type}专家，擅长创建逻辑清晰、结构合理的报告大纲。请确保输出严格遵循JSON格式。"
            )
            
            # 解析并验证响应
            if isinstance(response, dict):
                outline = self._parse_outline_response(response)
                print(f"✅ 大纲创建完成，包含{len(outline.subsections)}个主章节")
                return outline
            else:
                raise ValueError("LLM返回格式不正确")
                
        except Exception as e:
            print(f"❌ 大纲创建失败: {str(e)}")
            return self._fallback_outline_creation(topic, report_type, user_requirements)
    
    def _select_template(self, report_type: str) -> str:
        """选择合适的模板"""
        # 映射报告类型到模板
        template_mapping = {
            "academic": "academic_proposal",
            "academic_proposal": "academic_proposal",
            "business": "business_report", 
            "business_report": "business_report",
            "technical": "technical_report",
            "technical_report": "technical_report",
            "industry": "industry_analysis",
            "industry_analysis": "industry_analysis",
            "market": "industry_analysis",
            "research": "academic_proposal"
        }
        
        template_key = template_mapping.get(report_type.lower(), "comprehensive")
        return self.outline_templates[template_key]
    
    def _parse_outline_response(self, response: Dict) -> OutlineNode:
        """解析LLM响应为OutlineNode"""
        def parse_node(node_data: Dict) -> OutlineNode:
            """递归解析节点"""
            node = OutlineNode(
                title=node_data.get("title", "未命名节点"),
                level=node_data.get("level", 1),
                order=node_data.get("order", 1),
                description=node_data.get("description", ""),
                key_points=node_data.get("key_points", []),
                estimated_length=node_data.get("estimated_length", "")
            )
            
            # 递归解析子节点
            subsections_data = node_data.get("subsections", [])
            for sub_data in subsections_data:
                sub_node = parse_node(sub_data)
                node.subsections.append(sub_node)
            
            return node
        
        return parse_node(response)
    
    def _summarize_reference_data(self, reference_data: List[Union[Document, Dict]]) -> str:
        """总结参考数据"""
        if not reference_data:
            return "无参考数据"
        
        summaries = []
        for i, item in enumerate(reference_data[:5]):  # 限制前5个
            if isinstance(item, Document):
                summary = f"[{i+1}] {item.title} - {item.content[:100]}..."
            elif isinstance(item, dict):
                title = item.get("title", f"文档{i+1}")
                content = item.get("content", "")[:100]
                summary = f"[{i+1}] {title} - {content}..."
            summaries.append(summary)
        
        return "\n".join(summaries)
    
    def refine_outline(self, 
                      outline: OutlineNode,
                      feedback: str,
                      focus_areas: List[str] = None) -> OutlineNode:
        """
        根据反馈优化大纲
        
        Args:
            outline: 原始大纲
            feedback: 用户反馈
            focus_areas: 重点关注领域
            
        Returns:
            OutlineNode: 优化后的大纲
        """
        if not self.has_llm:
            print("⚠️ 大纲优化功能需要LLM支持")
            return outline
        
        try:
            # 将现有大纲转换为文本描述
            outline_text = self._outline_to_text(outline)
            
            # 构建优化prompt
            prompt = f"""
请根据用户反馈优化以下大纲结构：

现有大纲：
{outline_text}

用户反馈：
{feedback}

重点关注领域：{', '.join(focus_areas) if focus_areas else '无特别要求'}

请保持大纲的基本逻辑结构，根据反馈进行调整和优化，并按照标准JSON格式返回优化后的大纲。

要求：
1. 充分考虑用户反馈
2. 保持逻辑连贯性
3. 确保内容完整性
4. 优化章节标题和描述
"""
            
            response = self.llm_processor.call_llm_api_json(
                prompt,
                "你是一位专业的大纲优化专家，擅长根据反馈改进大纲结构和内容。"
            )
            
            if isinstance(response, dict):
                refined_outline = self._parse_outline_response(response)
                print("✅ 大纲优化完成")
                return refined_outline
            else:
                print("❌ 大纲优化失败，返回原始大纲")
                return outline
                
        except Exception as e:
            print(f"❌ 大纲优化出错: {str(e)}")
            return outline
    
    def _outline_to_text(self, outline: OutlineNode, indent: int = 0) -> str:
        """将大纲转换为文本描述"""
        text_parts = []
        
        # 当前节点
        indent_str = "  " * indent
        text_parts.append(f"{indent_str}{outline.title}")
        if outline.description:
            text_parts.append(f"{indent_str}  描述: {outline.description}")
        if outline.key_points:
            text_parts.append(f"{indent_str}  要点: {', '.join(outline.key_points)}")
        
        # 子节点
        for sub in outline.subsections:
            sub_text = self._outline_to_text(sub, indent + 1)
            text_parts.append(sub_text)
        
        return '\n'.join(text_parts)
    
    def generate_outline_variations(self, 
                                   topic: str,
                                   report_type: str = "comprehensive",
                                   count: int = 3) -> List[OutlineNode]:
        """
        生成多个大纲变体
        
        Args:
            topic: 主题
            report_type: 报告类型
            count: 生成数量
            
        Returns:
            List[OutlineNode]: 大纲变体列表
        """
        variations = []
        
        # 不同的结构重点
        variation_focuses = [
            "理论导向，注重概念和原理分析",
            "实践导向，注重应用和案例研究", 
            "综合导向，平衡理论与实践",
            "前瞻导向，注重趋势和未来发展",
            "问题导向，注重挑战和解决方案"
        ]
        
        for i in range(min(count, len(variation_focuses))):
            try:
                focus = variation_focuses[i]
                requirements = f"变体{i+1}：{focus}"
                
                outline = self.create_outline(
                    topic=topic,
                    report_type=report_type,
                    user_requirements=requirements
                )
                
                variations.append(outline)
                print(f"  ✅ 大纲变体{i+1}生成完成")
                
            except Exception as e:
                print(f"  ❌ 大纲变体{i+1}生成失败: {str(e)}")
        
        return variations
    
    def validate_outline_structure(self, outline: OutlineNode) -> Dict[str, any]:
        """
        验证大纲结构的合理性
        
        Args:
            outline: 要验证的大纲
            
        Returns:
            Dict: 验证结果
        """
        validation_result = {
            "is_valid": True,
            "issues": [],
            "suggestions": [],
            "statistics": {}
        }
        
        # 统计信息
        stats = self._calculate_outline_statistics(outline)
        validation_result["statistics"] = stats
        
        # 结构验证
        issues = []
        suggestions = []
        
        # 检查章节数量
        if stats["main_sections"] < 3:
            issues.append("主章节数量过少，建议至少3个主章节")
        elif stats["main_sections"] > 8:
            issues.append("主章节数量过多，建议不超过8个主章节")
        
        # 检查层级深度
        if stats["max_depth"] > 4:
            issues.append(f"层级过深({stats['max_depth']}级)，建议不超过4级")
        
        # 检查内容完整性
        empty_descriptions = stats["empty_descriptions"]
        if empty_descriptions > stats["total_nodes"] * 0.3:
            issues.append("缺乏描述的节点过多，建议补充节点描述")
        
        # 检查章节平衡性
        section_counts = [len(sub.subsections) for sub in outline.subsections]
        if section_counts and max(section_counts) > min(section_counts) * 3:
            suggestions.append("主章节之间的子章节数量差异较大，建议调整平衡")
        
        # 更新验证结果
        validation_result["issues"] = issues
        validation_result["suggestions"] = suggestions
        validation_result["is_valid"] = len(issues) == 0
        
        return validation_result
    
    def _calculate_outline_statistics(self, outline: OutlineNode) -> Dict[str, int]:
        """计算大纲统计信息"""
        stats = {
            "total_nodes": 0,
            "main_sections": len(outline.subsections),
            "max_depth": 0,
            "empty_descriptions": 0,
            "nodes_with_key_points": 0
        }
        
        def count_recursive(node: OutlineNode, depth: int):
            stats["total_nodes"] += 1
            stats["max_depth"] = max(stats["max_depth"], depth)
            
            if not node.description:
                stats["empty_descriptions"] += 1
            
            if node.key_points:
                stats["nodes_with_key_points"] += 1
            
            for sub in node.subsections:
                count_recursive(sub, depth + 1)
        
        count_recursive(outline, 1)
        
        return stats
    
    def _fallback_outline_creation(self, topic: str, report_type: str, user_requirements: str) -> OutlineNode:
        """备用大纲创建方法"""
        # 创建基本大纲结构
        root = OutlineNode(
            title=f"{topic}报告",
            level=0,
            order=0,
            description=f"关于{topic}的{report_type}报告"
        )
        
        # 根据报告类型创建基本结构
        if "academic" in report_type.lower():
            sections = [
                ("研究背景", "介绍研究背景和意义"),
                ("文献综述", "回顾相关研究和理论基础"),
                ("研究方法", "说明研究方法和技术路线"),
                ("预期结果", "描述预期成果和创新点"),
                ("参考文献", "列出主要参考文献")
            ]
        elif "business" in report_type.lower():
            sections = [
                ("市场分析", "分析市场现状和发展趋势"),
                ("产品服务", "描述产品或服务特点"),
                ("商业模式", "说明商业模式和盈利模式"),
                ("风险评估", "识别和评估主要风险"),
                ("建议结论", "提出建议和结论")
            ]
        else:
            sections = [
                ("概述", f"介绍{topic}的基本情况"),
                ("现状分析", f"分析{topic}的现状"),
                ("发展趋势", f"探讨{topic}的发展趋势"),
                ("挑战机遇", f"识别{topic}面临的挑战和机遇"),
                ("总结建议", "总结和建议")
            ]
        
        # 创建章节节点
        for i, (title, desc) in enumerate(sections):
            section = OutlineNode(
                title=title,
                level=1,
                order=i + 1,
                description=desc,
                estimated_length="800-1200字"
            )
            root.subsections.append(section)
        
        return root