# Redis缓存告警系统部署指南

## 📋 部署概述

本指南用于部署基于Redis的告警规则缓存同步系统，实现ljwx-boot和ljwx-bigscreen之间的高效数据同步。

## 🏗️ 系统架构

```
ljwx-admin → ljwx-boot (Redis DB=1) → MySQL
                ↓ pub/sub
            Redis服务器
                ↓ 订阅监听
        ljwx-bigscreen (Redis DB=0) → generate_alerts
```

## ✅ 部署前检查

### 1. 系统要求
- **Redis版本**: 5.0+
- **Python版本**: 3.7+
- **Java版本**: JDK 8+
- **内存要求**: 至少2GB可用内存

### 2. 现有组件确认
```bash
# 检查Redis服务状态
redis-cli ping

# 检查ljwx-boot Redis配置
grep -n "redis" ljwx-boot/ljwx-boot-admin/src/main/resources/application-local.yml

# 检查ljwx-bigscreen Redis配置
python3 ljwx-bigscreen/bigscreen/redis_config.py
```

### 3. 网络连通性测试
```bash
# 测试Redis连接
redis-cli -h 127.0.0.1 -p 6379 -a 123456 ping

# 测试跨DB通信
redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 0 ping
redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 1 ping
```

## 🚀 部署步骤

### 步骤1: 更新ljwx-boot缓存策略

1. **备份现有文件**
```bash
cd ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/facade/impl/
cp TAlertRulesFacadeImpl.java TAlertRulesFacadeImpl.java.backup
```

2. **应用更新**
- 文件已在实施过程中更新
- 新增版本控制和分布式锁机制
- TTL设置为24小时（86400秒）

3. **验证更新**
```bash
# 重启ljwx-boot服务
cd ljwx-boot && ./run-local.sh restart

# 检查日志
tail -f ljwx-boot/logs/ljwx-boot-local.log | grep "告警规则缓存"
```

### 步骤2: 部署Python缓存管理器

1. **安装缓存管理器**
```bash
# 文件已创建在以下位置
ls -la ljwx-bigscreen/bigscreen/alert_rules_cache_manager.py
```

2. **安装依赖**
```bash
cd ljwx-bigscreen/bigscreen
pip3 install redis dataclasses typing
```

3. **权限设置**
```bash
chmod +x alert_rules_cache_manager.py
```

### 步骤3: 部署优化版生成器

1. **安装生成器**
```bash
# 文件已创建
ls -la utils/redis_cache_generate_alerts.py
chmod +x utils/redis_cache_generate_alerts.py
```

2. **测试基础功能**
```bash
cd utils
python3 redis_cache_generate_alerts.py
```

### 步骤4: 部署监控和测试工具

1. **部署测试套件**
```bash
ls -la utils/test_redis_cache_alerts.py
chmod +x utils/test_redis_cache_alerts.py
```

2. **部署监控工具**
```bash
ls -la utils/monitor_alert_cache_performance.py
chmod +x utils/monitor_alert_cache_performance.py
```

## 🧪 部署验证

### 1. 运行完整测试
```bash
cd utils
python3 test_redis_cache_alerts.py
```

**期望输出**:
```
🧪 启动Redis缓存告警系统完整测试
✅ PASS - Redis连接测试
✅ PASS - 告警规则获取测试
✅ PASS - 告警生成测试
✅ PASS - 批量处理性能测试
✅ PASS - 缓存统计测试
✅ PASS - 边界情况测试

总计: 6 | 通过: 6 | 失败: 0 | 通过率: 100.0%
🎉 测试通过！Redis缓存告警系统运行正常
```

### 2. 性能基准测试
```bash
# 监控10分钟并生成报告
python3 monitor_alert_cache_performance.py -d 600 -r
```

## 🔧 配置优化

### 1. Redis配置优化
```bash
# 编辑Redis配置文件
sudo vim /etc/redis/redis.conf

# 关键配置项
maxmemory 2gb
maxmemory-policy allkeys-lru
notify-keyspace-events Ex
save 900 1
save 300 10
save 60 10000
```

### 2. ljwx-boot配置调优
```yaml
# application-local.yml
spring:
  data:
    redis:
      url: redis://default:123456@localhost:6379/1
      connect-timeout: 10000ms
      timeout: 30000ms
      lettuce:
        pool:
          max-active: 20
          max-idle: 10
          min-idle: 5
```

### 3. ljwx-bigscreen配置调优
```python
# redis_config.py
class RedisConfig:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 6379
        self.db = 0
        self.password = '123456'
        self.socket_timeout = 30
        self.retry_on_timeout = True
```

## 📊 性能目标

### 目标指标
- **缓存命中率**: >95%
- **告警规则TTL**: 24小时
- **处理延迟**: <5ms/record
- **QPS**: >1000 records/sec
- **Redis连接稳定性**: >99.9%

### 监控命令
```bash
# 实时性能监控
python3 monitor_alert_cache_performance.py -i 5

# 生成性能报告
python3 monitor_alert_cache_performance.py -d 3600 -r
```

## 🔒 安全配置

### 1. Redis安全
```bash
# 设置Redis密码
redis-cli CONFIG SET requirepass "your_secure_password"

# 禁用危险命令
redis-cli CONFIG SET rename-command FLUSHALL ""
redis-cli CONFIG SET rename-command EVAL ""
```

### 2. 网络安全
```bash
# 限制Redis访问IP
# 在redis.conf中配置
bind 127.0.0.1 192.168.1.0/24
protected-mode yes
```

## 🚨 故障排除

### 常见问题

#### 1. Redis连接失败
```bash
# 检查Redis服务状态
systemctl status redis

# 检查端口占用
netstat -tulpn | grep 6379

# 查看Redis日志
tail -f /var/log/redis/redis-server.log
```

#### 2. 缓存命中率低
```bash
# 检查缓存键
redis-cli -n 1 keys "alert_rules_*"

# 检查TTL
redis-cli -n 1 TTL "alert_rules_1"

# 检查订阅通道
redis-cli PUBSUB CHANNELS
```

#### 3. 订阅者不工作
```python
# 测试订阅者
python3 -c "
from ljwx_bigscreen.bigscreen.alert_rules_cache_manager import get_alert_rules_cache_manager
manager = get_alert_rules_cache_manager()
manager.start_subscriber()
import time; time.sleep(10)
print(manager.get_cache_stats())
"
```

### 诊断脚本
```bash
# 运行完整诊断
cat > diagnose_redis_cache.sh << 'EOF'
#!/bin/bash
echo "🔍 Redis缓存系统诊断"
echo "===================="

echo "1. Redis服务状态:"
systemctl status redis --no-pager

echo -e "\n2. Redis连接测试:"
redis-cli -h 127.0.0.1 -p 6379 -a 123456 ping

echo -e "\n3. DB分离测试:"
redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 0 ping
redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 1 ping

echo -e "\n4. 缓存键检查:"
redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 1 keys "alert_rules_*"

echo -e "\n5. 订阅通道检查:"
redis-cli -h 127.0.0.1 -p 6379 -a 123456 PUBSUB CHANNELS

echo -e "\n6. Python组件测试:"
python3 utils/test_redis_cache_alerts.py

echo "===================="
echo "✅ 诊断完成"
EOF

chmod +x diagnose_redis_cache.sh
./diagnose_redis_cache.sh
```

## 📈 监控和维护

### 日常监控
```bash
# 启动持续监控（后台运行）
nohup python3 monitor_alert_cache_performance.py -i 30 > monitor.log 2>&1 &

# 定期生成报告
crontab -e
# 添加以下行，每小时生成一次报告
0 * * * * cd /path/to/utils && python3 monitor_alert_cache_performance.py -d 3600 -r
```

### 维护任务
```bash
# 每日维护脚本
cat > daily_maintenance.sh << 'EOF'
#!/bin/bash
echo "📅 每日Redis缓存维护 - $(date)"

# 清理过期键
redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 0 --scan --pattern "*" | xargs -I {} redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 0 EXPIRE {} 86400

# 生成性能报告
cd /path/to/utils
python3 monitor_alert_cache_performance.py -d 600 -r

# 检查系统健康
python3 test_redis_cache_alerts.py > daily_test_$(date +%Y%m%d).log

echo "✅ 维护完成"
EOF

chmod +x daily_maintenance.sh
```

## 🔄 回滚方案

如果需要回滚到原始版本：

### 1. 恢复ljwx-boot
```bash
cd ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/facade/impl/
cp TAlertRulesFacadeImpl.java.backup TAlertRulesFacadeImpl.java
cd ljwx-boot && ./run-local.sh restart
```

### 2. 停用Python组件
```bash
# 停止监控
pkill -f monitor_alert_cache_performance.py

# 移除缓存管理器（可选）
mv ljwx-bigscreen/bigscreen/alert_rules_cache_manager.py ljwx-bigscreen/bigscreen/alert_rules_cache_manager.py.disabled
```

### 3. 清理Redis缓存
```bash
redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 1 keys "alert_rules_*" | xargs redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 1 DEL
redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 1 keys "alert_rules_version_*" | xargs redis-cli -h 127.0.0.1 -p 6379 -a 123456 -n 1 DEL
```

## 📚 相关文档

- [告警规则缓存同步方案](./alert_rules_cache_sync_solutions.md)
- [generate_alerts性能分析](./generate_alerts_analysis.md)
- [Redis配置最佳实践](https://redis.io/documentation)

---

**部署负责人**: 系统架构团队  
**最后更新**: 2025-09-09  
**版本**: v1.0