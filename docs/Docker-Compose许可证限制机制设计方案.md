# Docker Compose 许可证限制机制设计方案

## 概述

本文档详细描述在Docker Compose交付模式下，如何通过License许可证机制来防止客户滥用系统资源，确保合规使用和商业价值保护。

## 1. 许可证控制架构

### 1.1 整体架构设计

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   License       │    │   License       │    │   Application   │
│   Server        │◄──►│   Validator     │◄──►│   Services      │
│   (云端)        │    │   (容器内)      │    │   (各微服务)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   License       │    │   Hardware      │    │   Usage         │
│   Database      │    │   Fingerprint   │    │   Metrics       │
│   (许可证数据)  │    │   (设备标识)    │    │   (使用统计)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1.2 核心组件

#### License Server (许可证服务器)
- **位置**: 云端或内网服务器
- **功能**: 
  - 许可证生成和分发
  - 许可证验证和续期
  - 使用情况监控和统计
  - 异常行为检测和处理

#### License Validator (许可证验证器)
- **位置**: Docker容器内独立服务
- **功能**:
  - 本地许可证缓存和验证
  - 硬件指纹识别和绑定
  - 使用量统计和上报
  - 服务访问控制

## 2. 许可证类型设计

### 2.1 许可证维度

```yaml
license_types:
  # 用户数量限制
  user_limits:
    max_users: 100          # 最大用户数
    max_concurrent: 50      # 最大并发用户数
    
  # 功能模块限制
  feature_limits:
    health_monitoring: true  # 健康监测功能
    alert_system: true      # 告警系统
    big_screen: false       # 大屏功能
    ai_analysis: false      # AI分析功能
    
  # 时间限制
  time_limits:
    start_date: "2025-01-01"
    end_date: "2025-12-31"
    trial_days: 30          # 试用期天数
    
  # 硬件限制
  hardware_limits:
    max_cpu_cores: 8        # 最大CPU核心数
    max_memory_gb: 16       # 最大内存GB
    max_containers: 10      # 最大容器数量
    
  # 数据量限制
  data_limits:
    max_health_records: 1000000  # 最大健康记录数
    max_devices: 200            # 最大设备数
    max_organizations: 50       # 最大组织数
```

### 2.2 许可证等级

```yaml
license_tiers:
  trial:        # 试用版
    duration: 30_days
    users: 10
    devices: 20
    features: ["basic_health", "basic_alert"]
    
  standard:     # 标准版
    duration: 1_year
    users: 100
    devices: 200
    features: ["health_monitoring", "alert_system", "basic_reports"]
    
  professional: # 专业版
    duration: 1_year
    users: 500
    devices: 1000
    features: ["all_features", "ai_analysis", "big_screen"]
    
  enterprise:   # 企业版
    duration: 3_years
    users: unlimited
    devices: unlimited
    features: ["all_features", "custom_development"]
```

## 3. 技术实现方案

### 3.1 Docker Compose 集成

#### docker-compose.yml 配置

```yaml
version: '3.8'
services:
  # 许可证验证服务
  license-validator:
    image: ljwx/license-validator:latest
    container_name: ljwx-license-validator
    environment:
      - LICENSE_SERVER_URL=${LICENSE_SERVER_URL}
      - HARDWARE_ID=${HARDWARE_ID}
      - LICENSE_CHECK_INTERVAL=300  # 5分钟检查一次
    volumes:
      - ./license:/app/license
      - /sys/class/dmi/id:/host/dmi:ro
      - /proc/cpuinfo:/host/cpuinfo:ro
    networks:
      - ljwx-internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # 主应用服务
  ljwx-boot:
    image: ljwx/boot:latest
    depends_on:
      license-validator:
        condition: service_healthy
    environment:
      - LICENSE_VALIDATOR_URL=http://license-validator:8080
    networks:
      - ljwx-internal
    restart: unless-stopped

  # 其他服务...
  ljwx-admin:
    image: ljwx/admin:latest
    depends_on:
      license-validator:
        condition: service_healthy
    environment:
      - LICENSE_VALIDATOR_URL=http://license-validator:8080
    networks:
      - ljwx-internal
    restart: unless-stopped

networks:
  ljwx-internal:
    driver: bridge
```

### 3.2 许可证验证服务实现

#### LicenseValidator 服务

```java
@RestController
@Service
@Slf4j
public class LicenseValidatorService {
    
    @Autowired
    private LicenseManager licenseManager;
    
    @Autowired
    private HardwareFingerprintService fingerprintService;
    
    @PostMapping("/validate")
    public ResponseEntity<LicenseValidationResult> validateLicense(
            @RequestBody LicenseValidationRequest request) {
        
        try {
            // 1. 检查许可证是否存在和有效
            License license = licenseManager.getCurrentLicense();
            if (license == null || license.isExpired()) {
                return ResponseEntity.status(403)
                    .body(LicenseValidationResult.failed("License expired or not found"));
            }
            
            // 2. 验证硬件指纹
            String currentFingerprint = fingerprintService.generateFingerprint();
            if (!license.isHardwareMatched(currentFingerprint)) {
                log.warn("Hardware fingerprint mismatch: expected={}, actual={}", 
                    license.getHardwareFingerprint(), currentFingerprint);
                return ResponseEntity.status(403)
                    .body(LicenseValidationResult.failed("Hardware mismatch"));
            }
            
            // 3. 检查功能权限
            if (!license.hasFeature(request.getFeature())) {
                return ResponseEntity.status(403)
                    .body(LicenseValidationResult.failed("Feature not licensed"));
            }
            
            // 4. 检查使用量限制
            UsageStats usage = licenseManager.getCurrentUsage();
            if (!license.checkLimits(usage, request)) {
                return ResponseEntity.status(403)
                    .body(LicenseValidationResult.failed("Usage limits exceeded"));
            }
            
            // 5. 记录使用情况
            licenseManager.recordUsage(request);
            
            return ResponseEntity.ok(LicenseValidationResult.success(license));
            
        } catch (Exception e) {
            log.error("License validation error", e);
            return ResponseEntity.status(500)
                .body(LicenseValidationResult.failed("Validation error"));
        }
    }
}
```

### 3.3 硬件指纹识别

#### HardwareFingerprintService

```java
@Service
@Slf4j
public class HardwareFingerprintService {
    
    public String generateFingerprint() {
        try {
            Map<String, String> hwInfo = new HashMap<>();
            
            // 1. CPU信息
            String cpuInfo = readFile("/host/cpuinfo");
            String cpuSerial = extractCpuSerial(cpuInfo);
            hwInfo.put("cpu", cpuSerial);
            
            // 2. 主板信息
            String boardSerial = readFile("/host/dmi/board_serial");
            hwInfo.put("board", boardSerial);
            
            // 3. 系统UUID
            String systemUuid = readFile("/host/dmi/product_uuid");
            hwInfo.put("uuid", systemUuid);
            
            // 4. 网络MAC地址
            String macAddress = getNetworkMacAddress();
            hwInfo.put("mac", macAddress);
            
            // 5. 生成组合指纹
            String combined = hwInfo.values().stream()
                .filter(Objects::nonNull)
                .collect(Collectors.joining("|"));
                
            return DigestUtils.sha256Hex(combined);
            
        } catch (Exception e) {
            log.error("Failed to generate hardware fingerprint", e);
            throw new RuntimeException("Hardware fingerprint generation failed", e);
        }
    }
    
    private String readFile(String path) {
        try {
            return Files.readString(Paths.get(path)).trim();
        } catch (Exception e) {
            log.warn("Could not read file: " + path, e);
            return null;
        }
    }
}
```

## 4. 使用量监控机制

### 4.1 监控指标

```java
@Component
public class UsageMonitor {
    
    private final MeterRegistry meterRegistry;
    private final Timer.Sample currentRequest;
    
    @EventListener
    public void onUserLogin(UserLoginEvent event) {
        // 记录用户登录
        Counter.builder("license.users.active")
            .tag("customer", event.getCustomerId())
            .register(meterRegistry)
            .increment();
    }
    
    @EventListener
    public void onDeviceConnect(DeviceConnectEvent event) {
        // 记录设备连接
        Counter.builder("license.devices.active")
            .tag("customer", event.getCustomerId())
            .register(meterRegistry)
            .increment();
    }
    
    @EventListener
    public void onHealthDataRecord(HealthDataEvent event) {
        // 记录健康数据量
        Counter.builder("license.health.records")
            .tag("customer", event.getCustomerId())
            .register(meterRegistry)
            .increment();
    }
    
    @Scheduled(fixedRate = 300000) // 每5分钟
    public void reportUsageStats() {
        UsageStats stats = collectCurrentUsage();
        licenseServer.reportUsage(stats);
    }
}
```

### 4.2 限制执行策略

```java
@Component
@Order(1)
public class LicenseEnforcementFilter implements Filter {
    
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, 
                        FilterChain chain) throws IOException, ServletException {
        
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;
        
        // 1. 检查许可证状态
        LicenseStatus status = licenseManager.getLicenseStatus();
        if (status == LicenseStatus.EXPIRED) {
            sendErrorResponse(httpResponse, 403, "License expired");
            return;
        }
        
        // 2. 检查功能权限
        String requestPath = httpRequest.getRequestURI();
        String feature = mapPathToFeature(requestPath);
        if (!licenseManager.hasFeature(feature)) {
            sendErrorResponse(httpResponse, 403, "Feature not licensed");
            return;
        }
        
        // 3. 检查并发用户限制
        if (!licenseManager.checkConcurrentUsers()) {
            sendErrorResponse(httpResponse, 503, "Concurrent user limit exceeded");
            return;
        }
        
        // 4. 通过验证，继续处理
        chain.doFilter(request, response);
    }
}
```

## 5. 安全防护措施

### 5.1 许可证加密和签名

```java
@Service
public class LicenseSecurityService {
    
    private static final String RSA_ALGORITHM = "RSA";
    private static final String SIGNATURE_ALGORITHM = "SHA256withRSA";
    
    /**
     * 生成加密的许可证
     */
    public String generateSecureLicense(LicenseData licenseData, PrivateKey privateKey) {
        try {
            // 1. 序列化许可证数据
            String jsonData = objectMapper.writeValueAsString(licenseData);
            
            // 2. 创建数字签名
            Signature signature = Signature.getInstance(SIGNATURE_ALGORITHM);
            signature.initSign(privateKey);
            signature.update(jsonData.getBytes(StandardCharsets.UTF_8));
            byte[] signatureBytes = signature.sign();
            
            // 3. 组合数据和签名
            LicenseContainer container = new LicenseContainer();
            container.setData(jsonData);
            container.setSignature(Base64.getEncoder().encodeToString(signatureBytes));
            container.setAlgorithm(SIGNATURE_ALGORITHM);
            container.setTimestamp(System.currentTimeMillis());
            
            // 4. Base64编码
            String containerJson = objectMapper.writeValueAsString(container);
            return Base64.getEncoder().encodeToString(containerJson.getBytes());
            
        } catch (Exception e) {
            throw new RuntimeException("Failed to generate secure license", e);
        }
    }
    
    /**
     * 验证和解析许可证
     */
    public LicenseData verifyAndParseLicense(String encodedLicense, PublicKey publicKey) {
        try {
            // 1. Base64解码
            byte[] containerBytes = Base64.getDecoder().decode(encodedLicense);
            String containerJson = new String(containerBytes, StandardCharsets.UTF_8);
            LicenseContainer container = objectMapper.readValue(containerJson, LicenseContainer.class);
            
            // 2. 验证数字签名
            Signature signature = Signature.getInstance(container.getAlgorithm());
            signature.initVerify(publicKey);
            signature.update(container.getData().getBytes(StandardCharsets.UTF_8));
            byte[] signatureBytes = Base64.getDecoder().decode(container.getSignature());
            
            if (!signature.verify(signatureBytes)) {
                throw new SecurityException("License signature verification failed");
            }
            
            // 3. 解析许可证数据
            return objectMapper.readValue(container.getData(), LicenseData.class);
            
        } catch (Exception e) {
            throw new RuntimeException("Failed to verify license", e);
        }
    }
}
```

### 5.2 反调试和反篡改

```java
@Component
public class AntiTamperingService {
    
    @PostConstruct
    public void initializeAntiTampering() {
        // 1. 检查调试器
        if (isDebuggerAttached()) {
            System.exit(1);
        }
        
        // 2. 验证关键文件完整性
        if (!verifyFileIntegrity()) {
            System.exit(1);
        }
        
        // 3. 启动监控线程
        startTamperingMonitor();
    }
    
    private boolean isDebuggerAttached() {
        // 检查JVM调试参数
        RuntimeMXBean runtime = ManagementFactory.getRuntimeMXBean();
        List<String> args = runtime.getInputArguments();
        
        return args.stream().anyMatch(arg -> 
            arg.contains("-agentlib:jdwp") || 
            arg.contains("-Xrunjdwp") ||
            arg.contains("-Xdebug")
        );
    }
    
    private void startTamperingMonitor() {
        ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor();
        executor.scheduleAtFixedRate(() -> {
            try {
                // 检查系统时间是否被篡改
                if (isSystemTimeManipulated()) {
                    log.error("System time manipulation detected");
                    System.exit(1);
                }
                
                // 检查许可证文件是否被修改
                if (isLicenseFileModified()) {
                    log.error("License file modification detected");
                    System.exit(1);
                }
                
            } catch (Exception e) {
                log.error("Anti-tampering check failed", e);
            }
        }, 60, 60, TimeUnit.SECONDS);
    }
}
```

## 6. 部署和配置

### 6.1 环境变量配置

```bash
# .env 文件
LICENSE_SERVER_URL=https://license.ljwx.com/api
HARDWARE_ID=auto_generate
LICENSE_CHECK_INTERVAL=300
LICENSE_CACHE_TTL=3600
LICENSE_RETRY_ATTEMPTS=3
LICENSE_RETRY_DELAY=5000

# 可选的离线模式
OFFLINE_MODE=false
OFFLINE_LICENSE_PATH=/app/license/offline.lic
```

### 6.2 初始化脚本

```bash
#!/bin/bash
# init-license.sh

set -e

echo "Initializing LJWX License System..."

# 1. 检查许可证文件
if [ ! -f "/app/license/license.key" ]; then
    echo "License file not found. Please contact support."
    exit 1
fi

# 2. 生成硬件指纹
HARDWARE_ID=$(docker exec ljwx-license-validator /app/bin/generate-fingerprint)
echo "Hardware ID: $HARDWARE_ID"

# 3. 验证许可证
docker exec ljwx-license-validator /app/bin/validate-license --hardware-id="$HARDWARE_ID"

if [ $? -eq 0 ]; then
    echo "License validation successful"
else
    echo "License validation failed"
    exit 1
fi

# 4. 启动应用服务
echo "Starting application services..."
docker-compose up -d ljwx-boot ljwx-admin ljwx-bigscreen

echo "LJWX System started successfully"
```

### 6.3 监控和告警

```yaml
# monitoring/docker-compose.yml
version: '3.8'
services:
  license-monitor:
    image: ljwx/license-monitor:latest
    environment:
      - ALERT_WEBHOOK_URL=${WEBHOOK_URL}
      - ALERT_EMAIL=${ALERT_EMAIL}
    volumes:
      - ./alerts:/app/alerts
    depends_on:
      - license-validator
    restart: unless-stopped
```

## 7. 客户使用指南

### 7.1 初次部署

```bash
# 1. 下载部署包
wget https://releases.ljwx.com/ljwx-system-v1.0.tar.gz
tar -xzf ljwx-system-v1.0.tar.gz
cd ljwx-system

# 2. 配置许可证
cp your-license.key ./license/license.key

# 3. 配置环境
cp .env.example .env
# 编辑 .env 文件

# 4. 启动系统
./scripts/init-license.sh
```

### 7.2 许可证续期

```bash
# 1. 下载新许可证
# 2. 替换许可证文件
cp new-license.key ./license/license.key

# 3. 重启许可证验证器
docker-compose restart license-validator

# 4. 验证新许可证
./scripts/verify-license.sh
```

### 7.3 故障排除

```bash
# 检查许可证状态
docker exec ljwx-license-validator /app/bin/license-status

# 检查硬件指纹
docker exec ljwx-license-validator /app/bin/hardware-info

# 查看许可证日志
docker logs ljwx-license-validator

# 重新生成硬件指纹
docker exec ljwx-license-validator /app/bin/regenerate-fingerprint
```

## 8. 商业策略建议

### 8.1 定价策略

```yaml
pricing_strategy:
  trial:
    price: $0
    duration: 30_days
    conversion_target: 15%
    
  standard:
    price: $2000/year
    max_users: 100
    target_market: "中小企业"
    
  professional:
    price: $8000/year  
    max_users: 500
    target_market: "中大型企业"
    
  enterprise:
    price: $20000/year
    max_users: unlimited
    target_market: "大型企业/集团"
```

### 8.2 合规性检查

```java
@Service
public class ComplianceAuditService {
    
    @Scheduled(cron = "0 0 2 * * *") // 每天凌晨2点
    public void performComplianceAudit() {
        
        AuditReport report = new AuditReport();
        
        // 1. 检查许可证使用情况
        report.setLicenseUsage(auditLicenseUsage());
        
        // 2. 检查功能使用合规性
        report.setFeatureCompliance(auditFeatureUsage());
        
        // 3. 检查数据量合规性
        report.setDataCompliance(auditDataUsage());
        
        // 4. 生成报告并发送
        generateAndSendReport(report);
    }
    
    private void generateAndSendReport(AuditReport report) {
        // 发送给内部监控系统
        monitoringService.submitAuditReport(report);
        
        // 如果发现违规，发送告警
        if (report.hasViolations()) {
            alertService.sendComplianceAlert(report);
        }
    }
}
```

## 9. 总结

该许可证限制机制通过以下方式有效防止客户滥用：

### 9.1 技术防护
- **硬件绑定**: 防止许可证在多台机器上使用
- **加密签名**: 防止许可证被篡改
- **实时验证**: 定期检查许可证有效性
- **使用量监控**: 实时跟踪系统使用情况

### 9.2 商业控制
- **分层许可**: 根据客户需求提供不同版本
- **功能限制**: 精确控制可用功能模块
- **时间限制**: 强制许可证续期
- **用量限制**: 防止超出授权范围使用

### 9.3 运维保障
- **自动化部署**: 简化客户部署流程
- **监控告警**: 及时发现异常使用
- **故障排查**: 提供完整的诊断工具
- **合规审计**: 定期检查许可证合规性

通过这套完整的许可证控制机制，可以有效保护软件知识产权，确保客户合规使用，同时为不同层次的客户提供灵活的授权方案。

---

**文档版本**: v1.0  
**创建日期**: 2025-08-31  
**最后更新**: 2025-08-31  
**作者**: LJWX开发团队  
**审核**: 技术架构师