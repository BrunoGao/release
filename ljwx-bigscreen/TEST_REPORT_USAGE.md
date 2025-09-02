# ljwx接口自动化测试报告系统使用说明

## 🚀 快速开始

### 启动服务器
```bash
cd ljwx-bigscreen
python test_report_server.py
```

### 访问地址
- **Web界面**: http://localhost:5002/test/upload_common_event.html
- **通用报告**: http://localhost:5002/test/report.html
- **API基础地址**: http://localhost:5002/api/test/

## 📊 Web界面功能

### 主要特性
- ✅ 实时测试结果展示
- 📈 测试成功率图表统计
- 📋 详细测试用例结果
- 🔄 自动刷新和手动刷新
- 📄 测试报告下载
- 📊 历史测试趋势图

### 操作按钮
- **🚀 运行upload_common_event测试**: 执行主要接口测试
- **🧪 运行所有测试**: 执行所有配置的测试用例
- **🔄 刷新报告**: 手动刷新测试结果
- **📄 下载报告**: 下载JSON格式的详细报告

## 🔧 API接口说明

### 获取测试结果
```bash
curl http://localhost:5002/api/test/results
```

### 运行特定测试
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"test_name": "upload_common_event"}' \
  http://localhost:5002/api/test/run
```

### 运行所有测试
```bash
curl -X POST http://localhost:5002/api/test/run_all
```

### 获取测试用例列表
```bash
curl http://localhost:5002/api/test/cases
```

### 获取测试历史
```bash
curl http://localhost:5002/api/test/history
```

### 下载测试报告
```bash
curl http://localhost:5002/api/test/download_report -o test_report.json
```

## 📋 测试用例配置

### 当前支持的测试用例

#### 1. upload_common_event接口测试
- **描述**: 验证上传通用事件接口的完整流程
- **事件类型**: SOS_EVENT, FALLDOWN_EVENT, ONE_KEY_ALARM, WEAR_STATUS_CHANGED
- **验证项目**:
  - API响应状态
  - 健康数据插入
  - 告警生成
  - 消息下发
  - 微信通知发送

#### 2. 健康数据同步测试
- **描述**: 验证健康数据同步接口
- **事件类型**: HEALTH_SYNC
- **验证项目**:
  - API响应状态
  - 数据存储
  - 数据验证

#### 3. 健康数据上传接口测试
- **描述**: 验证健康数据上传接口的完整流程
- **事件类型**: HEALTH_DATA_UPLOAD
- **验证项目**:
  - API响应状态
  - 数据存储验证
  - 数据完整性检查

#### 4. 设备信息上传接口测试
- **描述**: 验证设备信息上传和状态更新接口
- **事件类型**: DEVICE_INFO_UPLOAD
- **验证项目**:
  - API响应状态
  - 设备注册/更新
  - 设备状态更新
  - 网络信息更新

### 添加新测试用例
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "test_id": "new_test",
    "config": {
      "name": "新测试用例",
      "description": "测试描述",
      "test_file": "test_script.py",
      "event_types": ["EVENT_TYPE"],
      "expected_results": {
        "api_response": true,
        "data_validation": true
      },
      "timeout": 300
    }
  }' \
  http://localhost:5002/api/test/add_case
```

## 🎯 测试结果解读

### 状态说明
- **PASS**: 测试通过 ✅
- **FAIL**: 测试失败 ❌
- **SKIP**: 测试跳过 ⏭️

### 详细验证项
- **健康数据**: 数据是否成功插入到t_user_health_data表
- **告警生成**: 是否成功生成告警记录到t_alert_info表
- **消息下发**: 是否成功发送设备消息到t_device_message表
- **微信通知**: 是否成功发送微信通知

## 🔍 故障排查

### 常见问题

#### 1. 服务器启动失败
```bash
# 检查端口占用
lsof -i :5002

# 更换端口启动
python test_report_server.py --port 5003
```

#### 2. 测试执行失败
```bash
# 检查测试文件是否存在
ls -la final_upload_event_test.py

# 手动运行测试
python final_upload_event_test.py
```

#### 3. 数据库连接问题
- 检查数据库配置: `test_config.json`
- 验证数据库连接: `mysql -h127.0.0.1 -uroot -p lj-06`

### 日志查看
```bash
# 服务器运行日志
tail -f test_server.log

# 测试执行日志
tail -f test_execution.log
```

## 📈 性能监控

### 测试执行时间
- upload_common_event: ~5-6秒
- upload_health_data: ~3-4秒
- upload_device_info: ~3-4秒
- 健康数据同步: ~10-30秒

### 成功率统计
- 目标成功率: ≥95%
- 告警阈值: <80%

## 🔧 自定义配置

### 修改测试配置
编辑 `test_config.json` 文件:
```json
{
  "test_cases": {
    "custom_test": {
      "name": "自定义测试",
      "description": "测试描述",
      "test_file": "custom_test.py",
      "event_types": ["CUSTOM_EVENT"],
      "expected_results": {
        "api_response": true
      },
      "timeout": 300
    }
  },
  "database": {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "your_password",
    "database": "lj-06"
  }
}
```

### 自定义测试脚本
测试脚本需要输出特定格式的结果:
```python
print("✅ 测试名称 测试通过")
print("✅ 健康数据插入成功")
print("✅ 告警生成成功") 
print("✅ 设备消息发送成功")
print("✅ 微信通知发送成功")
```

## 📞 技术支持

### 联系方式
- 开发团队: ljwx技术团队
- 邮箱: support@ljwx.com
- 文档: 查看项目README.md

### 更新日志
- v1.0.0: 基础测试报告功能
- v1.1.0: 添加通用测试管理器
- v1.2.0: 增强Web界面和图表展示

---
**注意**: 本系统为开发测试环境，生产环境使用请联系技术团队。 