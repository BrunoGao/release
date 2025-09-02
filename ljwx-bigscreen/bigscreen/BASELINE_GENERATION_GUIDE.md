# 健康基线数据生成指南

## 问题说明

当调用 `/health_data/chart/baseline` 接口时返回大量 `null` 值，这是因为 `t_health_baseline` 表中缺少基线数据。

## 解决方案

### 1. 自动生成基线数据

使用我们提供的脚本从 `t_user_health_data` 表生成基线数据并插入 `t_health_baseline` 表：

```bash
# 检查基线数据状态
python3 auto_generate_baseline.py --mode status

# 手动生成最近7天的基线数据
python3 auto_generate_baseline.py --mode manual --days 7

# 启动定时调度器（每天自动生成）
python3 auto_generate_baseline.py --mode schedule
```

### 2. 通过API接口生成

```bash
# 生成单日基线数据
curl -X POST "http://localhost:5001/api/baseline/generate" \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2025-05-29"}'

# 生成基线任务（自动选择日期）
curl -X POST "http://localhost:5001/api/baseline/task"
```

### 3. 快速批量生成

使用初始数据生成脚本：

```bash
python3 generate_baseline_data.py
```

## 基线生成原理

### 数据流程

1. **从健康数据计算基线**：
   ```
   t_user_health_data → 统计计算 → t_health_baseline
   ```

2. **支持的指标**：
   - heart_rate (心率)
   - blood_oxygen (血氧)
   - temperature (体温)
   - pressure_high (收缩压)
   - pressure_low (舒张压)  
   - stress (压力)

3. **统计方法**：
   - 平均值 (mean_value)
   - 标准差 (std_value)
   - 最小值 (min_value)
   - 最大值 (max_value)
   - 样本数量 (sample_count)

### 生成条件

- 每个用户每天至少需要3个数据点才能生成基线
- 用户基线生成后，才能生成对应的组织基线
- 基线按日期生成，每天一条记录

## 数据库表结构

### t_health_baseline (用户基线)
```sql
CREATE TABLE t_health_baseline (
  baseline_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  device_sn VARCHAR(50) NOT NULL,
  user_id BIGINT,
  feature_name VARCHAR(50) NOT NULL,  -- 指标名称
  baseline_date DATE NOT NULL,        -- 基线日期
  mean_value FLOAT,                   -- 平均值
  std_value FLOAT,                    -- 标准差
  min_value FLOAT,                    -- 最小值
  max_value FLOAT,                    -- 最大值
  sample_count INT DEFAULT 0,         -- 样本数量
  is_current BOOLEAN NOT NULL,        -- 是否当前有效
  baseline_time DATETIME NOT NULL,    -- 生成时间
  create_time DATETIME DEFAULT NOW(),
  update_time DATETIME DEFAULT NOW() ON UPDATE NOW()
);
```

### t_org_health_baseline (组织基线)
```sql  
CREATE TABLE t_org_health_baseline (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  org_id BIGINT NOT NULL,
  feature_name VARCHAR(50) NOT NULL,
  baseline_date DATE NOT NULL,
  mean_value FLOAT,
  std_value FLOAT,
  min_value FLOAT,
  max_value FLOAT,
  user_count INT DEFAULT 0,          -- 用户数量
  sample_count INT DEFAULT 0,        -- 总样本数量
  create_time DATETIME DEFAULT NOW(),
  update_time DATETIME DEFAULT NOW() ON UPDATE NOW()
);
```

## 定时任务配置

### 使用crontab设置定时生成

```bash
# 编辑crontab
crontab -e

# 添加每天凌晨1点执行的任务
0 1 * * * cd /path/to/bigscreen && python3 auto_generate_baseline.py --mode manual --days 1
```

### 使用systemd服务

创建服务文件 `/etc/systemd/system/baseline-generator.service`：

```ini
[Unit]
Description=Health Baseline Generator
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bigscreen
ExecStart=/usr/bin/python3 auto_generate_baseline.py --mode schedule
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable baseline-generator
sudo systemctl start baseline-generator
```

## 验证基线数据

### 检查数据覆盖率

```bash
python3 auto_generate_baseline.py --mode status
```

### 测试API响应

```bash
# 测试基线图表接口
curl "http://localhost:5001/health_data/chart/baseline?orgId=1&startDate=2025-05-01&endDate=2025-05-29"

# 检查非null数据点数量
curl -s "http://localhost:5001/health_data/chart/baseline?orgId=1&startDate=2025-05-23&endDate=2025-05-29" \
  | jq '.metrics[0].values | map(select(. != null)) | length'
```

## 常见问题

### Q: 为什么某些日期没有基线数据？
A: 可能的原因：
1. 该日期没有足够的健康数据（少于3个数据点）
2. 用户设备未上报数据
3. 基线生成脚本未运行

解决方法：检查对应日期的 `t_user_health_data` 表数据，手动生成基线。

### Q: 组织基线为空怎么办？
A: 组织基线依赖用户基线，需要：
1. 确保用户基线已生成
2. 检查用户与组织的关联关系
3. 重新生成组织基线

### Q: 基线数据更新频率？
A: 建议：
- 生产环境：每天生成前一天的基线数据
- 开发环境：按需手动生成
- 历史数据：一次性批量生成

## 性能优化

### 批量生成优化

对于历史数据的大批量生成，建议：

```python
# 并行生成多天数据
from concurrent.futures import ThreadPoolExecutor

def parallel_generate(days=30):
    with ThreadPoolExecutor(max_workers=4) as executor:
        dates = [date.today() - timedelta(days=i) for i in range(1, days+1)]
        futures = [executor.submit(generator.generate_daily_baseline, d) for d in dates]
        results = [f.result() for f in futures]
    return results
```

### 数据库索引优化

确保关键字段有索引：

```sql
-- 用户基线表索引
CREATE INDEX idx_baseline_device_date ON t_health_baseline(device_sn, baseline_date);
CREATE INDEX idx_baseline_feature_date ON t_health_baseline(feature_name, baseline_date);

-- 组织基线表索引  
CREATE INDEX idx_org_baseline_org_date ON t_org_health_baseline(org_id, baseline_date);
CREATE INDEX idx_org_baseline_feature_date ON t_org_health_baseline(feature_name, baseline_date);
```

## 总结

通过以上方案，可以有效解决基线数据缺失问题：

1. **立即解决**：运行 `python3 generate_baseline_data.py` 生成历史基线数据
2. **持续维护**：设置定时任务每天自动生成新的基线数据  
3. **监控验证**：定期检查基线数据覆盖率和API响应

基线数据生成后，`/health_data/chart/baseline` 接口将返回完整的非null数据，为健康数据分析提供可靠的基础。 