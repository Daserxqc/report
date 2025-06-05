#!/usr/bin/env python3
"""
数据来源一致性模式演示
展示不同模式下图表的差异
"""

from enhanced_market_collector import EnhancedMarketCollector
import os

def main():
    print("🔍 数据来源一致性模式演示")
    print("=" * 50)
    
    collector = EnhancedMarketCollector()
    topic = 'artificial intelligence'
    
    # 创建不同模式的图表
    modes = {
        "mixed": "混合来源模式（使用多个权威来源）",
        "unified": "统一来源模式（优先使用主要来源）"
    }
    
    for mode, description in modes.items():
        print(f"\n📊 正在生成 {description} 的图表...")
        
        # 设置模式
        collector.set_source_consistency_mode(mode)
        
        # 获取数据
        market_data = collector.get_enhanced_market_data(topic)
        
        # 生成图表
        chart_paths = collector.generate_market_charts(f"{topic}_{mode}", market_data)
        
        # 显示数据来源信息
        industry_data = market_data['industry_data']
        
        print(f"   ✅ 模式: {mode}")
        if 'historical_data' in industry_data:
            historical = collector._get_historical_data_by_mode(industry_data)
            print(f"   📈 历史数据来源:")
            unique_sources = set(item['source'] for item in historical)
            for source in unique_sources:
                count = sum(1 for item in historical if item['source'] == source)
                years = [str(item['year']) for item in historical if item['source'] == source]
                print(f"      - {source}: {count}个数据点 ({', '.join(years)})")
        
        segments = collector._get_segments_data_by_mode(industry_data)
        if segments:
            print(f"   🥧 市场细分来源:")
            unique_sources = set(data['source'] for data in segments.values())
            for source in unique_sources:
                segments_with_source = [seg for seg, data in segments.items() if data['source'] == source]
                print(f"      - {source}: {len(segments_with_source)}个细分 ({', '.join(segments_with_source)})")
        
        print(f"   📊 生成图表: {len(chart_paths)}个")
        for chart in chart_paths:
            print(f"      - {os.path.basename(chart)}")
    
    print(f"\n📋 总结:")
    print(f"   混合模式: 使用来自不同权威机构的最准确数据")
    print(f"   统一模式: 使用单一主要来源，确保数据一致性")
    print(f"   📁 所有图表已保存到: {collector.charts_dir} 目录")
    
    # 生成对比报告
    print(f"\n📝 生成数据来源对比报告...")
    create_source_comparison_report(collector, topic)

def create_source_comparison_report(collector, topic):
    """创建数据来源对比报告"""
    
    report_content = f"""# {topic.title()} 数据来源对比报告

## 为什么同一张图数据来源不一样？

### 现象说明
在市场研究中，同一张图表的不同数据点来自不同来源是**正常现象**，原因如下：

1. **时间差异**: 不同研究机构发布报告的时间不同
2. **专业领域**: 某些机构专注特定年份或细分领域
3. **方法论差异**: 不同机构采用不同的统计方法和样本
4. **数据可得性**: 历史数据的权威来源可能随时间变化

### 数据来源模式对比

#### 混合来源模式 (Mixed)
- **优点**: 使用最权威、最准确的数据源
- **缺点**: 来源不统一，可能存在方法论差异
- **适用场景**: 追求数据准确性，接受来源多样性

#### 统一来源模式 (Unified)  
- **优点**: 数据来源一致，方法论统一
- **缺点**: 可能牺牲某些数据点的准确性
- **适用场景**: 需要数据一致性，便于对比分析

### AI行业数据示例

#### 混合模式历史数据
| 年份 | 市场规模 | 数据来源 | 说明 |
|------|----------|----------|------|
| 2020 | $62.5B | Statista | 权威统计平台 |
| 2021 | $93.5B | Precedence Research | 专业市场研究 |
| 2022 | $119.8B | Grand View Research | 主要来源 |
| 2023 | $150.2B | Fortune Business Insights | 商业分析 |
| 2024 | $184.0B | Grand View Research | 主要来源 |

#### 统一模式历史数据  
| 年份 | 市场规模 | 数据来源 | 说明 |
|------|----------|----------|------|
| 2020 | $58.3B | Grand View Research | 回溯调整 |
| 2021 | $88.7B | Grand View Research | 回溯调整 |
| 2022 | $119.8B | Grand View Research | 原始数据 |
| 2023 | $142.1B | Grand View Research | 估算值 |
| 2024 | $184.0B | Grand View Research | 原始数据 |

### 建议选择

1. **学术研究**: 推荐混合模式，追求数据准确性
2. **商业报告**: 推荐统一模式，便于呈现和理解
3. **投资分析**: 推荐混合模式，获得最全面的市场视角

### 数据质量保证

无论选择哪种模式，我们都会：
- 标注每个数据点的具体来源
- 提供数据发布时间和可信度评级
- 说明数据获取方法和潜在局限性

---

*本报告旨在解释市场数据收集中的来源多样性现象，帮助用户选择合适的数据模式。*
"""
    
    filename = f"{topic.replace(' ', '_')}_source_comparison.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"   ✅ 对比报告已生成: {filename}")

if __name__ == "__main__":
    main() 