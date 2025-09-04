import sys
import os
from pathlib import Path

# Add project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from generators.detailed_report_generator import DetailedReportGenerator

def run_true_detailed_report_test():
    """
    真正的详细报告生成器测试，用于验证内容长度和质量。
    """
    print("=" * 60)
    print("启动真正的详细报告生成器测试...")
    print("=" * 60)

    # 1. 准备测试数据
    print("\n1. 准备模拟数据和报告大纲...")
    topic = "人工智能在医疗领域的应用"
    
    # 模拟搜索到的文章数据
    articles = [
        {
            "title": "AI在医学影像诊断中的突破",
            "summary": "人工智能，特别是深度学习模型，在识别X光、CT和MRI图像中的肿瘤、病变等方面显示出超越人类专家的准确性。这大大提高了早期诊断的效率和准确率。",
            "full_content": "近年来，随着算力的提升和算法的成熟，人工智能在医学影像诊断领域取得了革命性进展。例如，Google Health开发的深度学习系统在乳腺癌筛查中的表现优于放射科医生。这些系统通过在数百万张医学图像上进行训练，学习到了人眼难以察觉的细微模式。其优势不仅在于高准确性，还在于能够7x24小时不间断工作，极大地缓解了全球放射科医生短缺的压力。然而，挑战依然存在，包括数据隐私、算法的“黑箱”问题以及在不同医院和设备间的泛化能力。",
            "url": "https://example.com/ai-medical-imaging",
            "source": "顶级医学期刊"
        },
        {
            "title": "个性化治疗：AI如何预测药物反应",
            "summary": "通过分析患者的基因组数据、生活习惯和病历，AI模型可以预测特定药物在该患者身上的疗效和副作用，从而实现真正的个性化治疗方案。",
            "full_content": "个性化医疗的核心是为每个患者提供量身定制的治疗方案。人工智能为此提供了强大的工具。通过整合基因测序数据、蛋白质组学信息、电子健康记录（EHR）以及可穿戴设备数据，机器学习模型能够构建出复杂的患者画像。基于此，AI可以预测例如某种化疗药物对特定癌症患者的有效率，或者某种降压药可能引起的副作用风险。这不仅能提升治疗效果，还能避免无效治疗带来的经济负担和身体损害。目前，该领域的研究正在从实验室走向临床，但数据的标准化和高质量数据集的获取是推广应用的主要障碍。",
            "url": "https://example.com/ai-personalized-medicine",
            "source": "基因组学研究"
        },
        {
            "title": "AI驱动的药物发现流程加速",
            "summary": "传统药物研发周期长、成本高。AI能够通过分析海量生物医学文献、筛选潜在的分子化合物，将药物发现的时间从数年缩短到数月。",
            "full_content": "药物发现是一个漫长且昂贵的过程，平均需要10-15年和数十亿美元。人工智能正在从多个环节颠覆这一流程。首先，AI可以利用自然语言处理（NLP）技术从数百万篇科研论文和专利中提取知识，构建药物靶点和疾病关联的知识图谱。其次，生成式AI模型可以设计出全新的、具有所需特性的分子结构。最后，AI可以预测分子的物理化学性质和生物活性，从而在虚拟筛选阶段就淘汰掉大量没有前景的候选药物。多家初创公司和制药巨头已经在使用AI平台来加速其研发管线，并取得了初步成功。",
            "url": "https://example.com/ai-drug-discovery",
            "source": "制药行业报告"
        },
        {
            "title": "智能虚拟助理在患者管理中的应用",
            "summary": "基于AI的聊天机器人和虚拟健康助理能够回答患者的常见问题、提醒用药、监控生命体征，并为慢性病患者提供持续的支持。",
            "full_content": "随着人口老龄化和慢性病患者数量的增加，医疗系统的压力日益增大。AI虚拟健康助理为此提供了可扩展的解决方案。这些应用通常以手机App或智能音箱的形式出现，能够与患者进行自然语言对话。它们可以提供可靠的健康信息、根据医嘱提醒患者按时服药、记录血糖和血压等数据，并在出现异常时向医生发出警报。这不仅改善了患者的自我管理能力和依从性，还让医生能将更多精力投入到复杂的病例上。用户体验和数据安全是这类应用成功的关键。",
            "url": "https://example.com/ai-virtual-assistants",
            "source": "健康科技评论"
        }
    ]

    # 2. 初始化并运行报告生成器
    print("\n2. 初始化DetailedReportGenerator并生成报告...")
    try:
        generator = DetailedReportGenerator()
        
        # 使用新方法动态生成大纲
        print("  - 正在动态生成报告大纲...")
        outline = generator._generate_outline(topic, articles)
        
        if not outline:
            print("\n❌ 无法生成大纲，测试终止。")
            return

        report = generator.generate_detailed_report(topic, articles, outline)
        
        # 3. 保存报告
        output_dir = project_root / "test_reports"
        output_dir.mkdir(exist_ok=True)
        report_path = output_dir / "true_detailed_report.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n3. 报告已成功保存到: {report_path}")

        # 4. 打印总结
        report_length = len(report)
        target_length = 30000
        completion_rate = (report_length / target_length) * 100
        
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("-" * 60)
        print(f"  - 主题: {topic}")
        print(f"  - 生成报告长度: {report_length} 字符")
        print(f"  - 目标报告长度: {target_length} 字符")
        print(f"  - 目标达成率: {completion_rate:.2f}%")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_true_detailed_report_test()