"""
测试包 - 包含所有项目的测试用例

测试目录结构:
- api/: API集成测试
- collectors/: 数据收集器测试
- generators/: 报告生成器测试
- data/: 测试数据文件
- utils/: 测试工具函数
"""

# 导入所有子包
from tests.api import *
from tests.collectors import *
from tests.generators import *
from tests.utils import * 