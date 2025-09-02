# ljwx标准化自动化测试框架

## 📋 框架概述

这是一个统一、可维护、可扩展的自动化测试框架，专为ljwx项目设计。框架采用模块化架构，支持多种运行方式，提供完整的测试追踪和报告功能。

## 🏗️ 架构设计

### 目录结构
```
tests/
├── __init__.py                 # 框架入口
├── README.md                   # 框架说明文档
├── core/                       # 核心模块
│   ├── __init__.py
│   ├── base_test.py           # 基础测试类
│   └── test_manager.py        # 测试管理器
├── suites/                     # 测试套件
│   ├── __init__.py
│   ├── test_upload_common_event.py
│   ├── test_upload_health_data.py
│   └── test_upload_device_info.py
├── config/                     # 配置文件
│   └── test_config.json       # 统一配置
├── web/                        # Web界面
│   ├── __init__.py
│   └── server.py              # Web服务器(集成到主应用)
├── cli/                        # 命令行工具
│   ├── __init__.py
│   └── runner.py              # CLI运行器
├── logs/                       # 日志目录
├── reports/                    # 报告目录
└── utils/                      # 工具模块
```

### 核心特性

#### 1. 统一基础类 (BaseTest)
- 标准化的测试生命周期管理
- 统一的API请求和数据库操作方法
- 规范化的错误处理和日志记录
- 可扩展的验证方法

#### 2. 智能测试管理器 (TestManager)
- 自动发现和注册测试用例
- 支持并行和串行执行
- 完整的结果收集和历史记录
- 灵活的报告生成

#### 3. 多种运行方式
- **Web界面**: 集成到主应用 (http://localhost:5001/test)
- **命令行**: 独立CLI工具
- **API接口**: RESTful API支持
- **编程接口**: Python模块调用

#### 4. 灵活配置系统
- JSON配置文件统一管理
- 环境变量支持
- 动态配置加载
- 多环境配置切换

#### 5. 完整追踪能力
- 详细的执行日志
- 测试结果历史
- 性能指标收集
- 错误追踪和分析

## 🚀 快速开始

### 1. Web界面使用 (推荐)

访问主应用的测试模块：
```
http://localhost:5001/test
```

功能特性：
- 📊 实时测试仪表板
- 🎯 单个/批量测试执行
- 📈 可视化结果展示
- 📄 在线报告下载

### 2. 命令行使用

```bash
# 进入测试目录
cd ljwx-bigscreen/tests

# 列出可用测试
python -m cli.runner list

# 运行单个测试
python -m cli.runner run upload_common_event

# 运行所有测试
python -m cli.runner run --all

# 并行运行
python -m cli.runner run --all --parallel

# 生成报告
python -m cli.runner report --format html --output report.html

# 查看历史
python -m cli.runner history --limit 5
```

### 3. API接口使用

```bash
# 运行测试
curl -X POST http://localhost:5001/api/test/run \
  -H "Content-Type: application/json" \
  -d '{"test_name": "upload_health_data"}'

# 获取结果
curl http://localhost:5001/api/test/results

# 获取测试用例
curl http://localhost:5001/api/test/cases
```

### 4. 编程接口使用

```python
from tests.core.test_manager import test_manager

# 运行单个测试
result = test_manager.run_test('upload_common_event')
print(f"测试状态: {result.status}")

# 运行所有测试
results = test_manager.run_all_tests(parallel=True)

# 生成报告
report = test_manager.generate_report()
```

## 🔧 配置说明

### 主配置文件 (config/test_config.json)

```json
{
  "api": {
    "base_url": "http://localhost:5001",
    "timeout": 30,
    "retry_count": 3
  },
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "ljwx"
  },
  "test_suites": {
    "upload_common_event": {
      "name": "通用事件上传测试",
      "module": "tests.suites.test_upload_common_event",
      "class": "UploadCommonEventTest",
      "enabled": true,
      "priority": 1
    }
  }
}
```

### 配置项说明

- **api**: API接口配置
- **database**: 数据库连接配置
- **test_suites**: 测试套件定义
- **web_server**: Web服务器配置
- **logging**: 日志配置
- **report**: 报告配置

## 📝 添加新测试

### 1. 创建测试类

```python
#!/usr/bin/env python3
"""新测试套件"""
from ..core.base_test import BaseTest, TestResult

class NewTest(BaseTest):
    """新测试"""
    
    def run_test(self) -> TestResult:
        """执行测试逻辑"""
        details = {}
        
        # 1. API调用
        response = self.api_request("/new_endpoint", data={})
        details["api_response"] = self.verify_api_response(response)
        
        # 2. 数据验证
        data_exists = self.verify_data_exists("table_name", "condition")
        details["data_verification"] = data_exists
        
        # 3. 判断结果
        status = "PASS" if all(details.values()) else "FAIL"
        
        return TestResult(
            test_name="新测试",
            status=status,
            execution_time=self.get_execution_time(),
            details=details
        )
```

### 2. 更新配置文件

在 `config/test_config.json` 中添加：

```json
{
  "test_suites": {
    "new_test": {
      "name": "新测试",
      "module": "tests.suites.test_new",
      "class": "NewTest",
      "enabled": true,
      "priority": 4
    }
  }
}
```

### 3. 自动发现

框架会自动发现并注册新测试，无需额外配置。

## 📊 测试报告

### 报告格式

框架支持多种报告格式：

1. **JSON格式**: 机器可读，便于集成
2. **HTML格式**: 人类可读，美观展示
3. **实时Web界面**: 动态更新，交互友好

### 报告内容

- 测试摘要统计
- 详细执行结果
- 性能指标分析
- 错误信息追踪
- 历史趋势对比
- 改进建议

## 🔍 错误排查

### 常见问题

1. **测试发现失败**
   - 检查模块路径是否正确
   - 确认类名是否匹配
   - 验证配置文件格式

2. **数据库连接失败**
   - 检查数据库配置
   - 确认网络连接
   - 验证权限设置

3. **API请求失败**
   - 检查服务是否运行
   - 确认端口配置
   - 验证请求格式

### 调试模式

```bash
# 启用详细日志
export LJWX_TEST_LOG_LEVEL=DEBUG

# 运行测试
python -m cli.runner run test_name
```

## 🔄 持续集成

### GitHub Actions

```yaml
name: 自动化测试
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: 运行测试
        run: |
          cd ljwx-bigscreen/tests
          python -m cli.runner run --all --parallel
```

### 本地钩子

```bash
# 提交前自动测试
echo "cd ljwx-bigscreen/tests && python -m cli.runner run --all" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## 📈 性能优化

### 并行执行
- 默认支持3个并发线程
- 可通过配置调整并发数
- 自动处理资源竞争

### 缓存机制
- 数据库连接池
- API响应缓存
- 配置文件缓存

### 资源管理
- 自动清理临时文件
- 内存使用监控
- 超时机制保护

## 🛡️ 最佳实践

### 测试设计
1. 单一职责原则
2. 独立性保证
3. 可重复执行
4. 明确的断言

### 数据管理
1. 使用测试专用数据
2. 测试后清理
3. 避免硬编码
4. 环境隔离

### 错误处理
1. 详细的错误信息
2. 分级错误处理
3. 自动重试机制
4. 优雅降级

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 添加测试用例
4. 提交Pull Request
5. 代码审查

## 📞 支持

- 📧 邮件: test-support@ljwx.com
- 💬 微信群: ljwx-test-group
- 📝 文档: [内部Wiki链接]
- 🐛 问题反馈: [GitHub Issues]

---

**版本**: 1.0.0  
**更新时间**: 2025-06-18  
**维护团队**: ljwx测试团队 