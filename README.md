# 行业趋势报告生成系统

这是一个自动化的行业趋势报告生成系统，可以基于多种数据源收集和分析行业信息，并生成结构化的Markdown格式报告。

## 功能特点

系统支持生成三种类型的报告：

1. **行业最新动态报告** - 收集并分析主要公司和组织的最新新闻和动态
2. **研究方向报告** - 整理学术论文和研究资料，分析领域内的研究趋势
3. **行业洞察报告** - 提供深入的行业分析，包括市场规模、技术趋势、政策、案例研究等
4. **完整报告** - 将上述三种报告合并为一个全面的行业趋势报告

## 使用方法

### 交互式模式（推荐）

最简单的方式是使用交互式模式，系统会引导您输入各种参数：

```bash
python generate_all_reports.py -i
```

### 命令行参数

您也可以通过命令行参数直接运行：

```bash
# 生成完整报告
python generate_all_reports.py --topic "人工智能" --subtopics "机器学习" "深度学习" --companies "OpenAI" "谷歌" "百度"

# 仅生成行业动态报告
python generate_all_reports.py --topic "人工智能" --type news --companies "OpenAI" "谷歌" "百度"

# 仅生成研究方向报告
python generate_all_reports.py --topic "人工智能" --type research --subtopics "机器学习" "深度学习"

# 仅生成行业洞察报告
python generate_all_reports.py --topic "人工智能" --type insights
```

### 直接使用独立脚本

您也可以直接使用三个独立的脚本分别生成不同类型的报告：

```bash
# 生成行业动态报告
python generate_news_report.py --topic "人工智能" --companies "OpenAI" "谷歌" "百度"

# 生成研究方向报告
python generate_research_report.py --topic "人工智能" --subtopics "机器学习" "深度学习"

# 生成行业洞察报告
python generate_insights_report.py --topic "人工智能" --subtopics "机器学习" "深度学习"
```

### 评估报告质量

```bash
python evaluate_report.py --report "reports/AI行业动态报告.md" --type news --topic "人工智能"
```

参数说明：
- `--report`, `-r`: 报告文件路径
- `--type`, `-t`: 报告类型 (news:新闻报告, insights:洞察报告, research:研究报告)
- `--topic`, `-p`: 报告主题，如不提供则尝试从文件名猜测

评估工具会对报告进行全面分析，评估相关性、全面性、时效性、深度、结构性等维度，并给出总体评价和改进建议。评估结果将同时显示在控制台并保存为文本文件。

## 参数说明

- `--topic`: 报告的主题，如"人工智能"、"区块链"等（必需）
- `--subtopics`: 相关子主题，如"机器学习"、"深度学习"等（可选）
- `--companies`: 要追踪的公司，如"OpenAI"、"谷歌"等（可选，默认追踪主要科技公司）
- `--days`: 搜索的时间范围，单位为天（可选，默认为7天）
- `--type`: 报告类型，可选值为`all`（全部）、`news`（行业动态）、`research`（研究方向）、`insights`（行业洞察）（可选，默认为`all`）
- `--output`: 输出文件名（可选，默认使用主题名称和当前日期命名）
- `-i, --interactive`: 使用交互式模式（推荐初次使用）

## 报告输出

所有生成的报告将保存在`reports`目录下，使用Markdown格式（.md文件）。您可以使用任何支持Markdown的阅读器查看报告，或将其转换为PDF、Word等格式。

不同类型的报告将使用不同的文件名前缀：
- 行业动态报告: `{topic}_news_report_{date}.md`
- 研究方向报告: `{topic}_research_report_{date}.md`
- 行业洞察报告: `{topic}_insights_report_{date}.md`
- 完整报告: `{topic}_complete_report_{date}.md`

## 系统依赖

本系统依赖以下外部服务：
- Tavily API（用于网络搜索和信息收集）
- OpenAI/DeepSeek API（用于内容处理和生成）
- ArXiv API（用于学术论文搜索）

请确保已在`.env`文件中配置以下环境变量：
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，如果使用代理
TAVILY_API_KEY=your_tavily_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key  # 可选
DEEPSEEK_BASE_URL=https://api.deepseek.com # 可选
```

## 示例

以下是使用系统生成"人工智能"行业报告的示例：

```bash
python generate_all_reports.py -i
# 然后按照提示输入"人工智能"作为主题
```

生成的报告将包含：
1. 行业最新动态 - 如OpenAI、Google等公司的最新进展
2. 研究方向 - 如大语言模型、多模态AI等学术研究进展
3. 行业洞察 - 如市场规模、投资趋势、应用场景分析等

## 注意事项

- 生成完整报告可能需要较长时间，取决于搜索内容的多少和API响应速度
- API使用可能会产生费用，请注意控制使用频率
- 如遇到API限制，系统会尝试使用替代方法生成内容
- 确保所有API密钥都已正确配置
- 报告生成需要网络连接
- 报告生成过程可能受API限制影响
- 生成复杂的研究报告可能需要较长时间

希望这个工具能帮助您更高效地了解行业趋势和动态！ 