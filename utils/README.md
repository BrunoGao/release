# API 自动化测试工具

用于测试 `upload_health_data`、`upload_device_info`、`upload_common_event` 三个接口的功能和性能。

## 功能特点

- 🔗 从数据库读取真实的用户和设备数据
- 🧪 功能测试：验证接口的基本功能
- ⚡ 性能测试：并发测试，统计响应时间
- 📊 详细的测试报告生成
- 🎯 支持自定义测试参数

## 环境要求

```bash
pip install -r requirements.txt
```

## 配置

### 1. 数据库配置

修改 `db_config.json` 文件：

```json
{
  "host": "localhost",
  "port": 3306,
  "database": "ljwx",
  "user": "root",
  "password": "your_password"
}
```

### 2. API 地址

默认测试地址：`http://192.168.1.83:5001`

## 使用方法

### 简单运行

```bash
python run_tests.py
```

### 高级用法

```bash
# 仅功能测试
python api_tester.py --mode functional

# 仅性能测试
python api_tester.py --mode performance --concurrent 10 --requests 20

# 指定 API 地址
python api_tester.py --url http://192.168.1.83:5001 --mode both

# 指定输出文件
python api_tester.py --output my_test_report.txt
```

### 命令行参数

- `--url`: API 基础地址 (默认: http://192.168.1.83:5001)
- `--mode`: 测试模式 (functional|performance|both, 默认: both)
- `--concurrent`: 性能测试并发用户数 (默认: 5)
- `--requests`: 每个用户的请求数 (默认: 10)
- `--output`: 输出报告文件名

## 测试接口

### 1. upload_health_data
健康数据上传接口，测试数据包括：
- 心率、血氧、体温、步数等健康指标
- GPS 位置信息
- 血压数据
- 时间戳等

### 2. upload_device_info  
设备信息上传接口，测试数据包括：
- 设备系统版本
- 网络地址信息
- 电池状态
- 设备状态等

### 3. upload_common_event
通用事件上传接口，测试数据包括：
- 各种设备事件类型
- 事件值和设备序列号
- 位置信息
- 关联的健康数据

## 测试报告

测试完成后会生成详细报告，包含：

- 📈 测试概要（成功率、响应时间等）
- 🎯 各接口详细统计
- ⏱️ 响应时间分析（平均值、最值、中位数）
- ❌ 错误详情

## 文件说明

- `api_tester.py` - 主测试工具
- `db_config.py` - 数据库连接模块
- `run_tests.py` - 简化运行脚本
- `db_config.json` - 数据库配置文件
- `requirements.txt` - Python 依赖包

## 数据来源

- 用户数据：从 `sys_user` 表获取
- 设备数据：从 `t_device_info` 表获取
- 自动生成符合接口规范的测试数据