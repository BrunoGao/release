# 健康数据处理系统

🏥 用于批量生成ljwx-boot系统中个人和部门的健康基线、评分、预测、建议和画像的自动化处理工具。

## 功能特性

### 📊 个人健康数据处理
- ✅ **健康基线生成**: 基于过去30天数据生成个人健康基线
- ✅ **健康评分计算**: 集成权重配置的综合健康评分  
- ✅ **健康预测分析**: 未来30天健康趋势和风险评估
- ✅ **健康建议生成**: 个性化健康改善建议
- ✅ **健康画像构建**: 90天健康行为和风险画像

### 🏢 部门健康数据处理  
- ✅ **组织基线生成**: 基于过去90天数据生成部门健康基线
- ✅ **组织评分计算**: 部门级健康评分和用户分布
- ✅ **组织预测分析**: 部门健康趋势和管理风险评估
- ✅ **管理建议生成**: 部门管理、政策和培训建议
- ✅ **组织画像构建**: 180天组织健康状况和合规画像

## 目录结构

```
health_processing/
├── personal_health_processor.py      # 个人健康数据处理器
├── department_health_processor.py    # 部门健康数据处理器
├── health_processing_main.py         # 主执行脚本
├── health_processing_config.json     # 配置文件
├── run_health_processing.sh          # Shell执行脚本
├── README.md                         # 说明文档
└── results/                          # 结果输出目录
    ├── personal_results_YYYYMMDD_HHMMSS.json
    ├── department_results_YYYYMMDD_HHMMSS.json
    └── health_processing_report_YYYYMMDD_HHMMSS.md
```

## 快速开始

### 1. 环境检查

```bash
# 检查Python环境和ljwx-boot服务
./run_health_processing.sh --check-env
```

### 2. 试运行

```bash
# 验证配置和参数
./run_health_processing.sh --dry-run
```

### 3. 完整执行

```bash
# 使用默认配置处理所有数据
./run_health_processing.sh

# 仅处理个人数据
./run_health_processing.sh --personal-only

# 仅处理部门数据  
./run_health_processing.sh --department-only

# 使用自定义配置
./run_health_processing.sh -c my_config.json

# 指定服务地址
./run_health_processing.sh -u http://192.168.1.100:8080
```

## 配置说明

### ljwx-boot服务配置
```json
{
  "ljwx_boot": {
    "base_url": "http://localhost:8080",
    "token": null,
    "timeout": 30
  }
}
```

### 个人数据处理配置
```json
{
  "personal_processing": {
    "enabled": true,
    "generate_baseline": true,
    "generate_score": true,
    "generate_prediction": true,
    "generate_recommendation": true,
    "generate_profile": true,
    "baseline_days": 30,        // 基线统计天数
    "score_days": 30,           // 评分统计天数
    "prediction_days": 30,      // 预测天数
    "profile_days": 90,         // 画像统计天数
    "user_days": 30,            // 获取活跃用户的天数
    "max_workers": 5            // 并发处理线程数
  }
}
```

### 部门数据处理配置
```json
{
  "department_processing": {
    "enabled": true,
    "generate_baseline": true,
    "generate_score": true,
    "generate_prediction": true,
    "generate_recommendation": true,
    "generate_profile": true,
    "baseline_days": 90,        // 组织基线需要更长时间
    "score_days": 30,
    "prediction_days": 30,
    "profile_days": 180,        // 组织画像需要更长时间
    "org_days": 30,             // 获取活跃组织的天数
    "max_workers": 3,           // 组织处理并发数相对较少
    "min_users_per_org": 2      // 组织最少用户数要求
  }
}
```

## API端点映射

### 个人健康数据API
- `POST /health/baseline/generate` - 生成个人基线
- `POST /health/score/generate` - 生成健康评分
- `POST /health/prediction/generate` - 生成健康预测
- `POST /health/recommendation/generate` - 生成健康建议
- `POST /health/profile/generate` - 生成健康画像

### 部门健康数据API
- `POST /health/baseline/organization/generate` - 生成组织基线
- `POST /health/score/organization/generate` - 生成组织评分
- `POST /health/prediction/organization/generate` - 生成组织预测
- `POST /health/recommendation/organization/generate` - 生成组织建议
- `POST /health/profile/organization/generate` - 生成组织画像

## 输出结果

### 个人健康结果
```json
{
  "user_id": 123,
  "baseline_success": true,
  "score_success": true,
  "prediction_success": true,
  "recommendation_success": true,
  "profile_success": true,
  "baseline_data": { /* 基线数据 */ },
  "score_data": { /* 评分数据 */ },
  "prediction_data": { /* 预测数据 */ },
  "recommendation_data": { /* 建议数据 */ },
  "profile_data": { /* 画像数据 */ },
  "errors": []
}
```

### 部门健康结果
```json
{
  "org_id": 456,
  "org_name": "技术部",
  "user_count": 25,
  "baseline_success": true,
  "score_success": true,
  "prediction_success": true,
  "recommendation_success": true,
  "profile_success": true,
  "baseline_data": { /* 组织基线数据 */ },
  "score_data": { /* 组织评分数据 */ },
  "prediction_data": { /* 组织预测数据 */ },
  "recommendation_data": { /* 管理建议数据 */ },
  "profile_data": { /* 组织画像数据 */ },
  "errors": []
}
```

### 汇总报告
生成Markdown格式的处理汇总报告，包含:
- 处理统计信息
- 成功率分析
- 错误信息汇总
- 配置信息记录

## 性能特性

### 并发处理
- 个人数据: 默认5个并发线程
- 部门数据: 默认3个并发线程  
- 可通过配置调整并发数

### 错误处理
- 自动重试机制
- 详细错误日志记录
- 部分失败不影响整体处理

### 资源优化
- 分批处理避免内存溢出
- 连接池管理减少连接开销
- 合理的超时设置

## 监控和日志

### 日志输出
- 控制台实时输出处理进度
- 文件详细记录处理过程
- 结构化错误信息

### 处理统计
- 成功/失败数量统计
- 处理时间分析
- 资源使用情况

## 使用场景

### 定期数据处理
```bash
# 每日凌晨执行个人数据处理
0 2 * * * /path/to/run_health_processing.sh --personal-only

# 每周执行部门数据处理  
0 3 * * 0 /path/to/run_health_processing.sh --department-only
```

### 数据迁移
```bash
# 批量处理历史数据
./run_health_processing.sh -c migration_config.json
```

### 健康检查
```bash
# 验证系统状态
./run_health_processing.sh --check-env --dry-run
```

## 故障排除

### 常见问题

1. **连接失败**
   ```
   检查ljwx-boot服务是否启动
   验证网络连接和防火墙设置
   ```

2. **认证错误**  
   ```
   确认token配置正确
   检查用户权限设置
   ```

3. **数据不足**
   ```
   调整统计天数配置
   检查源数据完整性
   ```

4. **处理超时**
   ```
   增加timeout配置值
   减少并发线程数
   ```

### 调试模式
```bash
# 启用详细输出
./run_health_processing.sh --verbose

# 查看详细日志
tail -f results/health_processing_*.log
```

## 注意事项

1. **数据依赖**: 确保ljwx-boot系统中有足够的历史健康数据
2. **服务状态**: 处理前确认ljwx-boot服务正常运行
3. **权限配置**: 确保API调用有足够权限访问用户和组织数据
4. **资源规划**: 大量数据处理时注意CPU和内存使用情况
5. **备份策略**: 重要结果数据建议定期备份

## 技术支持

如遇问题，请检查:
- 系统日志文件
- ljwx-boot服务状态  
- 网络连接情况
- 配置文件格式

联系方式: bruno.gao <gaojunivas@gmail.com>