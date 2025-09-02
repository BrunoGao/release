# ljwx自动化测试框架

## 概述

这是一个专为ljwx智能穿戴系统设计的自动化测试框架，专注于测试重要接口的功能完整性，特别是告警生成机制、平台消息下发流程和微信通知的实际发送。

## 框架特性

### 🎯 核心功能
- **接口自动化测试**: 自动测试upload_common_event等关键接口
- **数据库验证**: 实时监控数据库变化，验证数据插入和处理
- **告警机制检查**: 深度检查告警生成、触发条件和处理流程
- **消息下发验证**: 测试平台消息的生成和下发机制
- **微信通知测试**: 验证微信企业号和公众号的通知发送

### 🔧 技术特性
- **实时监控**: 多线程实时监控数据库表变化
- **深度分析**: 分析事件处理的每个环节
- **自动清理**: 测试完成后自动清理测试数据
- **多格式报告**: 支持控制台、文件和JSON格式报告
- **灵活配置**: 支持配置文件和命令行参数

## 快速开始

### 1. 基础依赖
```bash
pip install mysql-connector-python requests
```

### 2. 基础测试
```bash
# 运行所有测试
python run_tests.py

# 运行指定测试套件
python run_tests.py -t "upload_common_event接口测试"

# 列出可用测试套件
python run_tests.py -l
```

### 3. 深度检查
```bash
# 运行深度检查测试
python test_framework/deep_inspection_test.py
```

## 框架结构

```
test_framework/
├── __init__.py                 # 包初始化
├── base_test.py               # 测试基础类
├── upload_common_event_test.py # upload_common_event接口测试
├── deep_inspection_test.py    # 深度检查测试
├── test_runner.py             # 测试运行器
├── config.json               # 配置文件
└── README.md                 # 使用说明
```

## 配置说明

### 基础配置 (config.json)
```json
{
  "api_base_url": "http://localhost:5001",
  "db_config": {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "lj-06"
  },
  "test_timeout": 30,
  "cleanup_test_data": true
}
```

### 命令行参数
- `--config, -c`: 指定配置文件路径
- `--test, -t`: 运行指定测试套件
- `--list, -l`: 列出可用测试套件
- `--no-cleanup`: 不清理测试数据
- `--timeout`: 设置测试超时时间
- `--api-url`: 设置API基础URL

## 测试类型

### 1. upload_common_event接口测试
测试事件上报接口的完整工作流：
- ✅ API基础功能测试
- ✅ 健康数据插入验证
- ✅ 告警生成检查
- ✅ 平台消息下发验证
- ✅ 微信通知发送测试

**测试事件类型:**
- SOS紧急求救 (SOS_EVENT)
- 跌倒检测 (FALLDOWN_EVENT)
- 一键报警 (ONE_KEY_ALARM)
- 穿戴状态变化 (WEAR_STATUS_CHANGED)

### 2. 深度检查测试
深入分析系统内部处理机制：
- 🔍 告警生成机制深度分析
- 🔍 消息下发流程深度检查
- 🔍 微信通知机制深度验证
- 🔍 实时监控数据库变化
- 🔍 处理器状态检查

## 测试报告

### 控制台报告
实时显示测试进度和结果：
```
🚀 开始运行自动化测试框架
⏰ 测试开始时间: 2024-01-15 10:30:00
================================================================================

🧪 执行测试套件: upload_common_event接口测试
------------------------------------------------------------
📊 upload_common_event接口测试 测试结果: ✅ PASS
   总测试数: 8
   通过数: 6
   失败数: 2
   成功率: 75.0%
   耗时: 45.23秒
```

### 详细文件报告
保存完整的测试详情到文件：
- `test_framework_report_YYYYMMDD_HHMMSS.txt`: 详细文本报告
- `test_framework_report_YYYYMMDD_HHMMSS.json`: JSON格式报告

### 深度检查报告
专门的深度分析报告：
- `deep_inspection_report_YYYYMMDD_HHMMSS.txt`: 深度检查详细报告

## 使用示例

### 示例1: 基础接口测试
```bash
# 测试upload_common_event接口
python run_tests.py -t "upload_common_event接口测试"
```

### 示例2: 自定义配置测试
```bash
# 使用自定义配置文件
python run_tests.py -c my_config.json --timeout 60
```

### 示例3: 深度检查
```bash
# 运行深度检查，不清理测试数据
python test_framework/deep_inspection_test.py --no-cleanup
```

### 示例4: 生产环境测试
```bash
# 指定生产环境API地址
python run_tests.py --api-url http://production-server:5001
```

## 扩展开发

### 添加新的测试套件

1. 继承BaseTestFramework类：
```python
from test_framework.base_test import BaseTestFramework

class MyNewTest(BaseTestFramework):
    def run_tests(self) -> List[Dict]:
        # 实现测试逻辑
        pass
```

2. 在test_runner.py中注册：
```python
runner.register_test_suite(MyNewTest, "我的新测试")
```

### 自定义监控

```python
def custom_monitor(self):
    """自定义监控逻辑"""
    while self.monitoring_active:
        # 实现监控逻辑
        time.sleep(1)
```

## 常见问题

### Q: 数据库连接失败
A: 检查config.json中的数据库配置，确保数据库服务正常运行

### Q: API调用超时
A: 增加timeout参数或检查API服务状态

### Q: 微信通知测试失败
A: 检查微信配置完整性和网络连接

### Q: 测试数据未清理
A: 确保cleanup_test_data配置为true，或手动清理测试设备数据

## 最佳实践

1. **测试环境隔离**: 使用专门的测试数据库和API环境
2. **定期运行**: 建议每日运行完整测试套件
3. **监控告警**: 设置测试失败时的告警通知
4. **版本控制**: 将测试结果纳入版本发布流程
5. **持续优化**: 根据测试结果持续优化系统性能

## 技术支持

如有问题或建议，请参考：
- 查看测试日志文件
- 检查数据库和API服务状态
- 验证配置文件正确性
- 联系开发团队获取支持 