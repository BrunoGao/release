# Ollama AI 健康预测集成指南

## 概述

本文档详细介绍了如何在 ljwx-boot 健康管理系统中集成 Ollama AI 模型 `ljwx-health-enhanced:latest` 来实现智能健康预测和建议功能。

## 架构图

```
前端 (ljwx-admin)     后端 (ljwx-boot)      AI模型服务
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ AI模型管理界面   │──→│ THealthPrediction│──→│ Ollama Service  │
│ /health/ai-models│   │ Controller       │   │ :3333           │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └─────────────→│ OllamaHealth    │←─────────────┘
                        │ PredictionService│
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │ 健康数据查询    │
                        │ UserHealthData  │
                        │ HealthBaseline  │
                        └─────────────────┘
```

## 核心功能

### 1. 健康预测 (Health Prediction)
- **接口**: `POST /t_health_prediction/ai/predict`
- **功能**: 基于用户历史健康数据预测未来趋势
- **参数**:
  - `userId`: 用户ID
  - `days`: 预测天数 (默认7天)
- **返回**: 健康趋势、风险因子、关键指标、置信度等

### 2. 健康建议 (Health Advice)
- **接口**: `POST /t_health_prediction/ai/advice`
- **功能**: 生成个性化健康改善建议
- **参数**:
  - `userId`: 用户ID
  - `healthIssues`: 特定健康问题 (可选)
- **返回**: 生活方式建议、风险预防、短期计划、长期目标等

### 3. 批量预测 (Batch Prediction)
- **接口**: `POST /t_health_prediction/ai/batch-predict`
- **功能**: 为多个用户批量生成健康预测
- **参数**:
  - `userIds`: 用户ID列表
  - `days`: 预测天数
- **返回**: 用户ID到预测结果的映射

### 4. 模型管理 (Model Management)
- **接口**: `GET /t_health_prediction/ai/models`
- **功能**: 获取可用AI模型列表
- **接口**: `GET /t_health_prediction/ai/health`
- **功能**: 检查AI服务健康状态

## 技术实现

### 后端组件

#### 1. OllamaHealthPredictionService
```java
@Service
public class OllamaHealthPredictionService {
    
    // 配置参数
    @Value("${ollama.api.url:http://192.168.1.83:3333}")
    private String ollamaApiUrl;
    
    @Value("${ollama.model.name:ljwx-health-enhanced:latest}")
    private String modelName;
    
    // 核心方法
    public HealthPredictionResult generateHealthPrediction(Long userId, Integer days);
    public HealthAdviceResult generateHealthAdvice(Long userId, List<String> healthIssues);
    public boolean checkOllamaHealth();
    public List<String> getAvailableModels();
}
```

#### 2. 数据收集和处理
- **UserHealthContext**: 用户健康数据上下文
- **数据源**: UserHealthData (健康数据) + HealthBaseline (健康基线)
- **统计计算**: 平均值、范围、趋势分析

#### 3. AI 提示词构建
- 结构化的医学专业提示词
- 包含用户基本信息、健康数据统计、基线信息
- 要求返回JSON格式的结构化结果

### 前端组件

#### 1. AI 模型管理界面
- **路径**: `/src/views/health/ai-models/index.vue`
- **功能**:
  - 服务状态监控
  - 可用模型列表显示
  - 预测和建议功能测试
  - 结果可视化展示

#### 2. API 服务层
```typescript
// /src/service/api/health/ai-prediction.ts
export const aiPredictionApi = {
  predict: (userId: number, days: number = 7),
  advice: (userId: number, healthIssues?: string[]),
  getAvailableModels: (),
  checkHealth: (),
  batchPredict: (userIds: number[], days: number = 7)
};
```

#### 3. 集成点
- 在健康预测页面 (`/health/prediction`) 添加 "AI预测" 按钮
- 点击按钮打开模型管理弹窗
- 支持实时测试和结果查看

## 配置文件

### application.yml
```yaml
# Ollama 健康预测配置
ollama:
  api:
    url: ${OLLAMA_API_URL:http://192.168.1.83:3333}
  model:
    name: ${OLLAMA_MODEL_NAME:ljwx-health-enhanced:latest}
  prediction:
    timeout: ${OLLAMA_PREDICTION_TIMEOUT:30000}
  connection:
    timeout: ${OLLAMA_CONNECTION_TIMEOUT:30000}
  read:
    timeout: ${OLLAMA_READ_TIMEOUT:60000}
```

### 环境变量支持
- `OLLAMA_API_URL`: Ollama 服务地址
- `OLLAMA_MODEL_NAME`: 使用的模型名称
- `OLLAMA_PREDICTION_TIMEOUT`: 预测超时时间
- `OLLAMA_CONNECTION_TIMEOUT`: 连接超时时间
- `OLLAMA_READ_TIMEOUT`: 读取超时时间

## 部署和使用

### 1. 前置条件
- Ollama 服务运行在 `http://192.168.1.83:11434` (标准端口)
- 模型 `ljwx-health-enhanced:latest` 已加载 ✅
- ljwx-boot 系统正常运行 ✅

### 2. 启动服务
```bash
# 启动后端服务
cd ljwx-boot
./run-local.sh start

# 启动前端服务
cd ljwx-admin
npm run dev
```

### 3. 访问功能
1. 登录 ljwx-admin 管理系统
2. 导航到 "健康管理" → "健康预测"
3. 点击 "AI预测" 按钮
4. 在弹出的模型管理界面中:
   - 查看服务状态
   - 测试预测功能
   - 查看建议结果

### 4. 快速测试
```bash
# 运行AI集成测试脚本
cd /Users/brunogao/work/codes/917/release
./test_ai_integration.sh

# 手动API测试
curl -X GET "http://localhost:9998/t_health_prediction/ai/health"
curl -X POST "http://localhost:9998/t_health_prediction/ai/predict?userId=1&days=7"
curl -X POST "http://localhost:9998/t_health_prediction/ai/advice?userId=1"

# 基础测试接口
curl -X GET "http://localhost:9998/ai_test/ping"
curl -X POST "http://localhost:9998/ai_test/mock-predict?userId=1&days=7"

# 直接测试Ollama模型
curl -X POST http://192.168.1.83:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "ljwx-health-enhanced:latest", "prompt": "你好", "stream": false}'
```

## 数据流程

### 预测流程
1. **数据收集**: 从数据库收集用户最近30天健康数据
2. **上下文构建**: 计算统计信息，获取健康基线
3. **提示词生成**: 构建医学专业的AI提示词
4. **模型调用**: 调用Ollama模型进行推理
5. **结果解析**: 解析JSON结果，提取关键信息
6. **响应返回**: 返回结构化的预测结果

### 建议流程
1. **健康评估**: 分析用户当前健康状态
2. **问题识别**: 识别潜在健康风险和改善点
3. **方案生成**: 生成个性化的改善建议
4. **计划制定**: 制定短期和长期健康计划
5. **优先级排序**: 根据重要性和可行性排序

## 错误处理

### 常见错误
1. **连接失败**: Ollama服务不可用
   - 检查服务状态: `curl http://192.168.1.83:3333/api/tags`
   - 检查网络连接

2. **模型未找到**: 指定的模型不存在
   - 确认模型已正确加载
   - 检查模型名称配置

3. **数据不足**: 用户健康数据太少
   - 提示用户需要更多数据
   - 使用默认建议

4. **解析失败**: AI返回格式不正确
   - 使用原始响应作为后备
   - 记录详细错误日志

### 日志监控
```bash
# 查看相关日志
tail -f logs/ljwx-boot.log | grep -E "(Ollama|AI|🔮|📝)"
```

## 性能优化

### 1. 缓存策略
- 用户健康数据缓存30分钟
- 健康基线缓存1小时
- AI预测结果缓存6小时

### 2. 批量处理
- 支持批量用户预测
- 避免重复数据查询
- 并发控制防止过载

### 3. 超时控制
- 连接超时: 30秒
- 读取超时: 60秒
- 预测超时: 30秒

## 扩展性

### 1. 多模型支持
- 配置多个AI模型
- 模型负载均衡
- A/B测试支持

### 2. 自定义提示词
- 可配置的提示词模板
- 特定场景的专用提示词
- 多语言支持

### 3. 结果后处理
- 医学知识库验证
- 建议可行性评估
- 个性化调整

## 安全考虑

### 1. 数据隐私
- 敏感信息脱敏
- 最小化数据传输
- 访问权限控制

### 2. API安全
- 身份验证和授权
- 请求频率限制
- 输入参数验证

### 3. 模型安全
- 提示词注入防护
- 输出内容检查
- 错误信息过滤

## 维护和监控

### 1. 健康检查
- 定期检查AI服务状态
- 监控响应时间和成功率
- 自动故障切换

### 2. 数据质量
- 监控预测准确性
- 用户反馈收集
- 模型效果评估

### 3. 系统监控
- API调用统计
- 错误率监控
- 性能指标追踪

## 总结

本集成实现了 ljwx-boot 健康管理系统与 Ollama AI 模型的深度融合，提供了：

✅ **完整的API接口**: 支持预测、建议、批量处理等功能
✅ **友好的管理界面**: 可视化的模型管理和测试工具
✅ **灵活的配置**: 支持环境变量和动态配置
✅ **健壮的错误处理**: 完善的异常处理和降级方案
✅ **良好的扩展性**: 支持多模型和自定义扩展

通过这个集成，用户可以：
- 获得基于AI的个性化健康预测
- 接收智能的健康改善建议
- 进行批量的健康风险评估
- 实时监控AI服务状态

这为ljwx健康管理平台增加了强大的AI能力，提升了用户体验和健康管理的智能化水平。