#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from main import generate_insight_report

def test_insight_report_sections():
    """测试洞察报告的章节结构"""
    print("🧪 开始测试洞察报告章节结构...")
    
    # 生成报告
    topic = "人工智能在医疗领域的应用"
    result = generate_insight_report(topic)
    
    print(f"\n📊 报告总长度: {len(result)} 字符")
    
    # 分析章节结构
    lines = result.split('\n')
    sections = [line for line in lines if line.startswith('## ')]
    
    print(f"\n📋 章节数量: {len(sections)}")
    print("\n📝 章节列表:")
    for i, section in enumerate(sections, 1):
        print(f"  {i}. {section}")
    
    # 检查是否符合洞察报告的6个章节要求
    expected_sections = 6
    if len(sections) >= expected_sections:
        print(f"\n✅ 章节数量符合要求 (>= {expected_sections})")
    else:
        print(f"\n❌ 章节数量不足 (实际: {len(sections)}, 期望: >= {expected_sections})")
    
    # 保存报告到文件以便查看
    output_file = f"test_insight_report_{topic.replace(' ', '_')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"\n💾 报告已保存到: {output_file}")
    
    return len(sections)

if __name__ == "__main__":
    test_insight_report_sections()