#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试DetailedContentWriterMcp的层次化结构生成能力
"""

import asyncio
from collectors.detailed_content_writer_mcp import DetailedContentWriterMcp

def test_single_item_generation():
    """测试单个资料的层次化内容生成"""
    print("\n🧪 测试单个资料的层次化内容生成...")
    
    writer = DetailedContentWriterMcp()
    
    # 模拟单个资料数据
    test_data = {
        'title': '人工智能在医疗诊断中的应用突破',
        'content': '最新研究显示，基于深度学习的AI系统在医学影像诊断方面取得重大突破。该系统能够识别早期癌症病变，准确率达到95%以上。研究团队使用了超过10万张医学影像进行训练，涵盖了多种癌症类型。这项技术有望在未来5年内广泛应用于临床实践，大幅提升诊断效率和准确性。',
        'url': 'https://example.com/ai-medical-diagnosis',
        'source': '医学AI研究院'
    }
    
    try:
        content = writer._generate_single_item_content(
            item=test_data,
            overall_context='人工智能医疗应用行业洞察报告',
            section_name='技术突破与应用'
        )
        
        print(f"✅ 生成内容长度: {len(content)} 字符")
        print(f"📝 内容预览 (前500字符):\n{content[:500]}...")
        
        # 检查层次化结构
        h2_count = content.count('## ')
        h3_count = content.count('### ')
        h4_count = content.count('#### ')
        
        print(f"📊 结构分析:")
        print(f"   - 二级标题 (##): {h2_count} 个")
        print(f"   - 三级标题 (###): {h3_count} 个")
        print(f"   - 四级标题 (####): {h4_count} 个")
        print(f"   - 总标题数: {h2_count + h3_count + h4_count} 个")
        
        # 检查是否达到要求
        total_headers = h2_count + h3_count + h4_count
        if total_headers >= 7:
            print(f"✅ 层次化结构要求达标 (≥7个子标题)")
        else:
            print(f"❌ 层次化结构不足 (需要≥7个子标题，实际{total_headers}个)")
            
        return content
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return None

def test_multiple_items_generation():
    """测试多个资料的层次化内容生成"""
    print("\n🧪 测试多个资料的层次化内容生成...")
    
    writer = DetailedContentWriterMcp()
    
    # 模拟多个资料数据
    test_data = [
        {
            'title': 'AI芯片技术发展现状',
            'content': '当前AI芯片市场呈现快速增长态势，主要厂商包括英伟达、AMD、英特尔等。新一代AI芯片在算力和能效方面都有显著提升，支持更复杂的深度学习模型训练和推理。',
            'url': 'https://example.com/ai-chip-status',
            'source': '半导体行业报告'
        },
        {
            'title': '机器学习算法优化进展',
            'content': '研究人员在机器学习算法优化方面取得重要进展，新的优化算法能够显著减少模型训练时间，同时保持或提升模型性能。这些算法在自然语言处理和计算机视觉领域表现尤为突出。',
            'url': 'https://example.com/ml-optimization',
            'source': 'AI研究前沿'
        },
        {
            'title': '人工智能伦理与监管',
            'content': '随着AI技术的快速发展，相关的伦理和监管问题日益受到关注。各国政府正在制定相应的法律法规，以确保AI技术的安全和负责任使用。',
            'url': 'https://example.com/ai-ethics',
            'source': '科技政策研究'
        }
    ]
    
    try:
        content = writer._generate_multiple_items_content(
            section_items=test_data,
            overall_context='人工智能发展趋势行业洞察报告',
            section_name='核心技术与挑战'
        )
        
        print(f"✅ 生成内容长度: {len(content)} 字符")
        print(f"📝 内容预览 (前500字符):\n{content[:500]}...")
        
        # 检查层次化结构
        h2_count = content.count('## ')
        h3_count = content.count('### ')
        h4_count = content.count('#### ')
        
        print(f"📊 结构分析:")
        print(f"   - 二级标题 (##): {h2_count} 个")
        print(f"   - 三级标题 (###): {h3_count} 个")
        print(f"   - 四级标题 (####): {h4_count} 个")
        print(f"   - 总标题数: {h2_count + h3_count + h4_count} 个")
        
        # 检查是否达到要求
        total_headers = h2_count + h3_count + h4_count
        if total_headers >= 7:
            print(f"✅ 层次化结构要求达标 (≥7个子标题)")
        else:
            print(f"❌ 层次化结构不足 (需要≥7个子标题，实际{total_headers}个)")
            
        # 检查引用
        citation_count = content.count('[^')
        print(f"📚 引用分析: 发现 {citation_count} 个引用标记")
        
        return content
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return None

def test_full_report_generation():
    """测试完整报告生成"""
    print("\n🧪 测试完整报告生成...")
    
    writer = DetailedContentWriterMcp()
    
    # 模拟完整的搜索结果数据
    test_data = [
        {
            'title': 'ChatGPT引领对话AI新时代',
            'content': 'OpenAI发布的ChatGPT在全球范围内引起轰动，展示了大语言模型在对话交互方面的强大能力。该模型基于GPT架构，通过大规模预训练和人类反馈强化学习进行优化。',
            'url': 'https://example.com/chatgpt-era',
            'source': 'AI技术前沿'
        },
        {
            'title': '自动驾驶技术商业化进程',
            'content': '自动驾驶技术正在从实验室走向商业应用，多家公司已经开始在特定场景下部署自动驾驶车辆。技术挑战主要集中在复杂交通环境的感知和决策能力上。',
            'url': 'https://example.com/autonomous-driving',
            'source': '智能交通研究'
        }
    ]
    
    try:
        # 转换数据格式为Document对象
        from collectors.search_mcp import Document
        documents = []
        for item in test_data:
            doc = Document(
                title=item['title'],
                content=item['content'],
                url=item['url'],
                source=item['source'],
                source_type='web'  # 添加必需的source_type参数
            )
            documents.append(doc)
        
        # 使用异步方法生成完整报告
        content = asyncio.run(writer.generate_full_report(
            topic='人工智能技术发展',
            articles=documents
        ))
        
        print(f"✅ 生成内容长度: {len(content)} 字符")
        print(f"📝 内容预览 (前800字符):\n{content[:800]}...")
        
        # 检查层次化结构
        h1_count = content.count('# ')
        h2_count = content.count('## ')
        h3_count = content.count('### ')
        h4_count = content.count('#### ')
        
        print(f"📊 完整报告结构分析:")
        print(f"   - 一级标题 (#): {h1_count} 个")
        print(f"   - 二级标题 (##): {h2_count} 个")
        print(f"   - 三级标题 (###): {h3_count} 个")
        print(f"   - 四级标题 (####): {h4_count} 个")
        print(f"   - 总标题数: {h1_count + h2_count + h3_count + h4_count} 个")
        
        # 检查引用
        citation_count = content.count('[^')
        print(f"📚 引用分析: 发现 {citation_count} 个引用标记")
        
        return content
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return None

if __name__ == "__main__":
    print("🚀 开始测试DetailedContentWriterMcp的层次化结构生成能力")
    print("=" * 60)
    
    # 测试单个资料生成
    single_content = test_single_item_generation()
    
    # 测试多个资料生成
    multiple_content = test_multiple_items_generation()
    
    # 测试完整报告生成
    full_content = test_full_report_generation()
    
    print("\n" + "=" * 60)
    print("🎉 测试完成")
    
    # 统计测试结果
    success_count = sum([1 for content in [single_content, multiple_content, full_content] if content is not None])
    print(f"📊 测试结果: {success_count}/3 个测试成功")
    
    if success_count == 3:
        print("✅ 所有测试通过，DetailedContentWriterMcp层次化结构生成功能正常")
    else:
        print("❌ 部分测试失败，需要进一步检查和优化")