import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys - 使用 dashscope 作为默认配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-5b73166a137b4a93add9e4ffe6d68aa6")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
IEEE_API_KEY = os.getenv("IEEE_API_KEY")

# Google Search API settings
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")  # Custom Search Engine ID
GOOGLE_SEARCH_ENABLED = False  # 暂时禁用Google搜索以避免429错误

# Brave Search API settings
BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "BSA4bcKQe6t46PvsVgwVmTNSSvynmbI")

# ArXiv settings
ARXIV_MAX_RESULTS = 50
ARXIV_SORT_BY = "submittedDate"
ARXIV_SORT_ORDER = "descending"

# 学术论文搜索设置
ACADEMIC_SEARCH_ENABLED = True  # 是否启用其他学术源搜索
ACADEMIC_MIN_PAPERS = 5         # 最少需要的学术论文数量
ACADEMIC_MAX_PAPERS = 50        # 最多收集的学术论文数量

# News API settings
NEWS_MAX_RESULTS = 40
NEWS_LANGUAGE = "zh"
NEWS_COUNTRY = "cn"
NEWS_SORT_BY = "publishedAt"

# 默认RSS源
DEFAULT_RSS_FEEDS = [
    # 中文新闻RSS源
    "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml",  # BBC中文
    "https://www.zaobao.com/rss/realtime/china",       # 联合早报中国
    "https://www.36kr.com/feed",                       # 36氪
    "https://www.pingwest.com/feed/all",               # 品玩
    "https://www.ifanr.com/feed",                      # 爱范儿
    "https://sspai.com/feed",                          # 少数派
    "http://www.geekpark.net/rss",                     # 极客公园
    "https://www.tmtpost.com/rss",                     # 钛媒体
    # 英文新闻RSS源
    "https://news.google.com/rss",                     # Google News
    "http://rss.cnn.com/rss/edition.rss",              # CNN
    "https://feeds.skynews.com/feeds/rss/technology.xml", # Sky News Tech
    "https://www.wired.com/feed/rss",                  # Wired
    "https://techcrunch.com/feed/",                    # TechCrunch
    "https://www.theverge.com/rss/index.xml",          # The Verge
    "https://www.technologyreview.com/topnews.rss",    # MIT Technology Review
]

# Tavily search settings
TAVILY_MAX_RESULTS = 15
TAVILY_SEARCH_DEPTH = "advanced"

# Report settings
MAX_ARTICLES_PER_CATEGORY = 8
REPORT_TITLE_FORMAT = "{topic} Industry Trends Report ({date})"
OUTPUT_DIR = "reports"

# 报告文件名格式化设置
FILENAME_DATE_FORMAT = "%Y%m%d"  # 文件名中的日期格式
FILE_NAMING_TEMPLATE = "{topic}_{report_type}_{date}"  # 文件名模板

# Report section structure
REPORT_SECTIONS = [
    "Industry Latest News",    # Company/government news
    "Research Directions",     # Academic research
    "Industry Insights"        # General insights from web search
]

# LLM settings
LLM_MODEL = "deepseek-v3"  # 默认使用 dashscope 的 deepseek-v3 模型
MAX_TOKENS = 8192
TEMPERATURE = 0.3

# CORE API settings
CORE_API_KEY = os.getenv("CORE_API_KEY")
CORE_API_URL = "https://api.core.ac.uk/v3"
CORE_MAX_RESULTS = 40 