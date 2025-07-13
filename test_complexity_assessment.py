#!/usr/bin/env python3
"""
章节复杂度评估测试工具
让用户可以测试不同大纲章节的复杂度评估结果
"""

from generate_outline_report import OutlineContentGenerator
import json

class ComplexityTester:
    def __init__(self):
        # 创建一个虚拟的内容生成器来使用其复杂度评估方法
        self.generator = OutlineContentGenerator(None)
    
    def test_complexity(self, section_title, subsections, content_items=None, topic="测试主题"):
        """
        测试章节复杂度
        
        Args:
            section_title (str): 章节标题
            subsections (list): 子章节列表
            content_items (list): 内容项列表 (可选)
            topic (str): 主题
        """
        if content_items is None:
            content_items = []
        
        # 构建章节信息结构
        section_info = {
            'title': section_title,
            'subsections': {},
            'content': content_items
        }
        
        # 将子章节转换为标准格式
        for sub in subsections:
            section_info['subsections'][sub] = {
                'title': sub,
                'items': []  # 这里假设没有详细的items
            }
        
        # 评估复杂度
        complexity = self.generator._assess_section_complexity(section_title, section_info, topic)
        word_req = self.generator._get_word_count_requirements(complexity)
        
        # 显示详细分析
        self._show_detailed_analysis(section_title, section_info, complexity, word_req)
        
        return complexity
    
    def _show_detailed_analysis(self, section_title, section_info, complexity, word_req):
        """显示详细的复杂度分析"""
        print(f"\n{'='*60}")
        print(f"📊 章节复杂度评估分析")
        print(f"{'='*60}")
        
        print(f"📝 章节标题: {section_title}")
        print(f"🎯 最终复杂度: {complexity.upper()}")
        print(f"📏 目标字数: {word_req['min_words']}-{word_req['max_words']}字")
        print(f"📖 描述: {word_req['description']}")
        
        print(f"\n🔍 详细评分分析:")
        
        # 1. 子章节数量分析 (权重30%)
        subsection_count = len(section_info.get('subsections', {}))
        if subsection_count >= 5:
            sub_score = 30
            sub_level = "高"
        elif subsection_count >= 3:
            sub_score = 20
            sub_level = "中"
        else:
            sub_score = 10
            sub_level = "低"
        
        print(f"   1️⃣ 子章节数量: {subsection_count}个 → {sub_level}分 ({sub_score}/30)")
        
        # 2. 内容要点数量分析 (权重20%)
        total_items = 0
        for sub_info in section_info.get('subsections', {}).values():
            total_items += len(sub_info.get('items', []))
        total_items += len(section_info.get('content', []))
        
        if total_items >= 15:
            item_score = 20
            item_level = "高"
        elif total_items >= 10:
            item_score = 15
            item_level = "中"
        else:
            item_score = 10
            item_level = "低"
        
        print(f"   2️⃣ 内容要点数量: {total_items}个 → {item_level}分 ({item_score}/20)")
        
        # 3. 技术关键词密度分析 (权重25%)
        tech_keywords = [
            '算法', '架构', '模型', '技术', '方法', '系统', '框架', '机制', '原理', '策略',
            '优化', '实现', '设计', '开发', '部署', '评估', '分析', '处理', '计算', '数据'
        ]
        
        text_content = f"{section_title} {' '.join(section_info.get('content', []))}"
        for sub_info in section_info.get('subsections', {}).values():
            text_content += f" {' '.join(sub_info.get('items', []))}"
        
        tech_count = sum(1 for keyword in tech_keywords if keyword in text_content)
        found_keywords = [keyword for keyword in tech_keywords if keyword in text_content]
        
        if tech_count >= 8:
            tech_score = 25
            tech_level = "高"
        elif tech_count >= 5:
            tech_score = 20
            tech_level = "中"
        elif tech_count >= 3:
            tech_score = 15
            tech_level = "中低"
        else:
            tech_score = 10
            tech_level = "低"
        
        print(f"   3️⃣ 技术关键词: {tech_count}个 → {tech_level}分 ({tech_score}/25)")
        if found_keywords:
            print(f"      发现的关键词: {', '.join(found_keywords)}")
        
        # 4. 标题长度分析 (权重25%)
        title_length = len(section_title)
        if title_length >= 15:
            title_score = 25
            title_level = "高"
        elif title_length >= 10:
            title_score = 20
            title_level = "中"
        else:
            title_score = 15
            title_level = "低"
        
        print(f"   4️⃣ 标题长度: {title_length}字符 → {title_level}分 ({title_score}/25)")
        
        # 总分计算
        total_score = sub_score + item_score + tech_score + title_score
        print(f"\n📈 总分: {total_score}/100")
        
        if total_score >= 80:
            final_level = "高复杂度 (≥80分)"
        elif total_score >= 60:
            final_level = "中等复杂度 (60-79分)"
        else:
            final_level = "低复杂度 (<60分)"
        
        print(f"🏆 最终级别: {final_level}")

def show_examples():
    """显示一些示例测试案例"""
    print("\n" + "="*60)
    print("📚 复杂度评估示例")
    print("="*60)
    
    tester = ComplexityTester()
    
    examples = [
        {
            "name": "简单章节示例",
            "title": "基础概念",
            "subsections": ["定义", "特点"],
            "content": ["简单介绍"],
            "topic": "测试主题"
        },
        {
            "name": "中等复杂度章节示例", 
            "title": "深度学习算法与实现技术",
            "subsections": ["神经网络架构", "训练方法", "优化策略", "评估指标"],
            "content": ["算法原理", "系统设计", "数据处理"],
            "topic": "人工智能"
        },
        {
            "name": "高复杂度章节示例",
            "title": "分布式机器学习系统架构设计与优化实现", 
            "subsections": [
                "分布式计算框架", "模型并行化策略", "数据分片机制", 
                "通信优化算法", "容错处理系统", "性能评估方法"
            ],
            "content": [
                "系统架构设计", "算法优化实现", "性能分析评估", 
                "技术框架选择", "部署策略制定"
            ],
            "topic": "分布式系统"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n🔸 示例 {i}: {example['name']}")
        tester.test_complexity(
            example["title"], 
            example["subsections"], 
            example["content"],
            example["topic"]
        )

def interactive_test():
    """交互式测试"""
    print("\n" + "="*60)
    print("🎮 交互式复杂度测试")
    print("="*60)
    print("请输入你的章节信息来测试复杂度评估:")
    
    tester = ComplexityTester()
    
    while True:
        try:
            print(f"\n{'-'*40}")
            
            # 输入章节信息
            section_title = input("📝 请输入章节标题: ").strip()
            if not section_title:
                break
            
            topic = input("🎯 请输入主题 (可选，按回车跳过): ").strip()
            if not topic:
                topic = "测试主题"
            
            print("📋 请输入子章节 (每行一个，输入空行结束):")
            subsections = []
            while True:
                sub = input("   - ").strip()
                if not sub:
                    break
                subsections.append(sub)
            
            print("📃 请输入内容项 (每行一个，输入空行结束，可选):")
            content_items = []
            while True:
                item = input("   * ").strip()
                if not item:
                    break
                content_items.append(item)
            
            # 测试复杂度
            complexity = tester.test_complexity(section_title, subsections, content_items, topic)
            
            # 询问是否继续
            continue_test = input(f"\n继续测试? (y/n): ").strip().lower()
            if continue_test != 'y':
                break
                
        except KeyboardInterrupt:
            print(f"\n\n👋 测试结束")
            break

def main():
    print("🚀 章节复杂度评估测试工具")
    print("="*60)
    print("此工具可以帮助你理解系统如何评估章节复杂度")
    print("\n复杂度评估标准:")
    print("🔹 子章节数量 (权重30%): 数量越多分数越高")
    print("🔹 内容要点数量 (权重20%): 要点越多分数越高") 
    print("🔹 技术关键词密度 (权重25%): 技术词汇越多分数越高")
    print("🔹 标题长度 (权重25%): 标题越长分数越高")
    print("\n分级标准:")
    print("🟢 低复杂度 (<60分): 2000-3000字")
    print("🟡 中等复杂度 (60-79分): 2500-3500字") 
    print("🔴 高复杂度 (≥80分): 3500-5000字")
    
    while True:
        print(f"\n{'='*40}")
        print("请选择测试模式:")
        print("1. 查看示例")
        print("2. 交互式测试")
        print("3. 退出")
        
        choice = input("请输入选项 (1-3): ").strip()
        
        if choice == "1":
            show_examples()
        elif choice == "2":
            interactive_test()
        elif choice == "3":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    main() 