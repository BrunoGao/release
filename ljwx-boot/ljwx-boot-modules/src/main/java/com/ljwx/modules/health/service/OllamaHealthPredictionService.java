package com.ljwx.modules.health.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ljwx.common.exception.BizException;
import com.ljwx.modules.health.entity.UserHealthData;
import com.ljwx.modules.health.entity.HealthBaseline;
import com.ljwx.modules.health.mapper.UserHealthDataMapper;
import com.ljwx.modules.health.mapper.HealthBaselineMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.ResourceAccessException;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Ollama 健康预测服务
 * 集成 ljwx-health-enhanced:latest 模型进行健康预测和建议
 * 
 * @author bruno.gao
 * @since 2025-10-05
 */
@Slf4j
@Service
public class OllamaHealthPredictionService {

    @Value("${ollama.api.url:http://192.168.1.83:3333}")
    private String ollamaApiUrl;
    
    @Value("${ollama.model.name:ljwx-health-enhanced:latest}")
    private String modelName;
    
    @Value("${ollama.prediction.timeout:30000}")
    private int timeoutMs;
    
    @Autowired
    @org.springframework.beans.factory.annotation.Qualifier("ollamaRestTemplate")
    private RestTemplate restTemplate;
    
    @Autowired
    private UserHealthDataMapper userHealthDataMapper;
    
    @Autowired
    private HealthBaselineMapper healthBaselineMapper;
    
    @Autowired
    private ObjectMapper objectMapper;

    /**
     * 为用户生成健康预测
     * 
     * @param userId 用户ID
     * @param days 预测天数（默认7天）
     * @return 健康预测结果
     */
    public HealthPredictionResult generateHealthPrediction(Long userId, Integer days) {
        log.info("🔮 开始为用户 {} 生成 {} 天的健康预测", userId, days != null ? days : 7);
        
        try {
            // 1. 收集用户健康数据
            UserHealthContext context = collectUserHealthContext(userId, days != null ? days : 7);
            
            // 2. 构建AI提示词
            String prompt = buildHealthPredictionPrompt(context);
            
            // 3. 调用Ollama模型
            String prediction = callOllamaModel(prompt);
            
            // 4. 解析和包装结果
            HealthPredictionResult result = parseHealthPrediction(prediction, userId, context);
            
            log.info("✅ 用户 {} 健康预测生成完成", userId);
            return result;
            
        } catch (Exception e) {
            log.error("❌ 用户 {} 健康预测生成失败: {}", userId, e.getMessage(), e);
            throw new BizException("健康预测生成失败: " + e.getMessage());
        }
    }

    /**
     * 为用户生成个性化健康建议
     * 
     * @param userId 用户ID
     * @param healthIssues 特定健康问题（可选）
     * @return 健康建议
     */
    public HealthAdviceResult generateHealthAdvice(Long userId, List<String> healthIssues) {
        log.info("📝 开始为用户 {} 生成健康建议", userId);
        
        try {
            // 1. 收集用户健康数据
            UserHealthContext context = collectUserHealthContext(userId, 30);
            
            // 2. 构建AI提示词
            String prompt = buildHealthAdvicePrompt(context, healthIssues);
            
            // 3. 调用Ollama模型
            String advice = callOllamaModel(prompt);
            
            // 4. 解析和包装结果
            HealthAdviceResult result = parseHealthAdvice(advice, userId, context);
            
            log.info("✅ 用户 {} 健康建议生成完成", userId);
            return result;
            
        } catch (Exception e) {
            log.error("❌ 用户 {} 健康建议生成失败: {}", userId, e.getMessage(), e);
            throw new BizException("健康建议生成失败: " + e.getMessage());
        }
    }

    /**
     * 收集用户健康数据上下文
     */
    private UserHealthContext collectUserHealthContext(Long userId, int days) {
        UserHealthContext context = new UserHealthContext();
        context.setUserId(userId);
        
        LocalDateTime endTime = LocalDateTime.now();
        LocalDateTime startTime = endTime.minusDays(days);
        
        // 获取最近的健康数据
        QueryWrapper<UserHealthData> dataQuery = new QueryWrapper<>();
        dataQuery.eq("user_id", userId)
                .ge("timestamp", startTime)
                .le("timestamp", endTime)
                .eq("is_deleted", 0)
                .orderByDesc("timestamp")
                .last("LIMIT 1000"); // 限制数据量
        
        List<UserHealthData> healthDataList = userHealthDataMapper.selectList(dataQuery);
        context.setRecentHealthData(healthDataList);
        
        // 获取健康基线
        QueryWrapper<HealthBaseline> baselineQuery = new QueryWrapper<>();
        baselineQuery.eq("user_id", userId)
                    .eq("is_current", 1)
                    .eq("is_deleted", 0);
        
        List<HealthBaseline> baselines = healthBaselineMapper.selectList(baselineQuery);
        context.setBaselines(baselines);
        
        // 计算统计信息
        context.setStatistics(calculateHealthStatistics(healthDataList));
        
        return context;
    }

    /**
     * 构建健康预测提示词
     */
    private String buildHealthPredictionPrompt(UserHealthContext context) {
        StringBuilder prompt = new StringBuilder();
        
        prompt.append("你是一个专业的健康数据分析AI助手，基于用户的健康监测数据进行科学的健康预测。\n\n");
        
        // 用户基本信息
        prompt.append("=== 用户健康数据概览 ===\n");
        prompt.append(String.format("用户ID: %d\n", context.getUserId()));
        prompt.append(String.format("数据时间范围: 最近%d天\n", context.getRecentHealthData().size() > 0 ? 30 : 0));
        prompt.append(String.format("数据点数量: %d条记录\n\n", context.getRecentHealthData().size()));
        
        // 健康数据统计
        if (context.getStatistics() != null && !context.getStatistics().isEmpty()) {
            prompt.append("=== 健康指标统计 ===\n");
            context.getStatistics().forEach((key, value) -> {
                prompt.append(String.format("%s: %s\n", getFeatureDisplayName(key), value));
            });
            prompt.append("\n");
        }
        
        // 健康基线信息
        if (context.getBaselines() != null && !context.getBaselines().isEmpty()) {
            prompt.append("=== 用户健康基线 ===\n");
            for (HealthBaseline baseline : context.getBaselines()) {
                prompt.append(String.format("%s: 均值=%.2f, 标准差=%.2f\n", 
                    getFeatureDisplayName(baseline.getFeatureName()),
                    baseline.getMeanValue() != null ? baseline.getMeanValue().doubleValue() : 0.0,
                    baseline.getStdValue() != null ? baseline.getStdValue().doubleValue() : 0.0));
            }
            prompt.append("\n");
        }
        
        prompt.append("=== 预测任务 ===\n");
        prompt.append("请基于以上健康数据，生成以下预测分析：\n");
        prompt.append("1. 健康趋势预测（未来7天各项指标的可能变化）\n");
        prompt.append("2. 潜在健康风险识别\n");
        prompt.append("3. 需要关注的健康指标\n");
        prompt.append("4. 预测置信度评估\n\n");
        
        prompt.append("请以JSON格式返回结果，包含以下字段：\n");
        prompt.append("{\n");
        prompt.append("  \"healthTrend\": \"整体健康趋势描述\",\n");
        prompt.append("  \"riskFactors\": [\"风险因子1\", \"风险因子2\"],\n");
        prompt.append("  \"keyIndicators\": [\"需关注指标1\", \"需关注指标2\"],\n");
        prompt.append("  \"confidence\": 0.85,\n");
        prompt.append("  \"recommendations\": [\"建议1\", \"建议2\"],\n");
        prompt.append("  \"prediction\": {\n");
        prompt.append("    \"heart_rate\": {\"trend\": \"stable\", \"range\": [70, 80]},\n");
        prompt.append("    \"blood_oxygen\": {\"trend\": \"improving\", \"range\": [96, 99]}\n");
        prompt.append("  }\n");
        prompt.append("}\n");
        
        return prompt.toString();
    }

    /**
     * 构建健康建议提示词
     */
    private String buildHealthAdvicePrompt(UserHealthContext context, List<String> healthIssues) {
        StringBuilder prompt = new StringBuilder();
        
        prompt.append("你是一个专业的健康顾问AI，基于用户的健康数据提供个性化的健康建议和生活方式指导。\n\n");
        
        // 用户健康数据概览（简化版）
        prompt.append("=== 用户健康状况 ===\n");
        if (context.getStatistics() != null && !context.getStatistics().isEmpty()) {
            context.getStatistics().forEach((key, value) -> {
                prompt.append(String.format("%s: %s\n", getFeatureDisplayName(key), value));
            });
        }
        prompt.append("\n");
        
        // 特定健康问题
        if (healthIssues != null && !healthIssues.isEmpty()) {
            prompt.append("=== 用户关注的健康问题 ===\n");
            healthIssues.forEach(issue -> prompt.append("- ").append(issue).append("\n"));
            prompt.append("\n");
        }
        
        prompt.append("=== 建议生成要求 ===\n");
        prompt.append("请生成个性化的健康建议，包含：\n");
        prompt.append("1. 生活方式建议（饮食、运动、作息）\n");
        prompt.append("2. 健康风险预防措施\n");
        prompt.append("3. 短期改善计划（1-4周）\n");
        prompt.append("4. 长期健康目标建议\n\n");
        
        prompt.append("请以JSON格式返回，包含以下结构：\n");
        prompt.append("{\n");
        prompt.append("  \"lifestyle\": {\n");
        prompt.append("    \"diet\": [\"饮食建议1\", \"饮食建议2\"],\n");
        prompt.append("    \"exercise\": [\"运动建议1\", \"运动建议2\"],\n");
        prompt.append("    \"sleep\": [\"睡眠建议1\", \"睡眠建议2\"]\n");
        prompt.append("  },\n");
        prompt.append("  \"riskPrevention\": [\"预防措施1\", \"预防措施2\"],\n");
        prompt.append("  \"shortTermPlan\": {\n");
        prompt.append("    \"duration\": \"2周\",\n");
        prompt.append("    \"goals\": [\"目标1\", \"目标2\"],\n");
        prompt.append("    \"actions\": [\"行动1\", \"行动2\"]\n");
        prompt.append("  },\n");
        prompt.append("  \"longTermGoals\": [\"长期目标1\", \"长期目标2\"],\n");
        prompt.append("  \"priority\": \"high|medium|low\"\n");
        prompt.append("}\n");
        
        return prompt.toString();
    }

    /**
     * 调用Ollama模型
     */
    private String callOllamaModel(String prompt) {
        try {
            String url = ollamaApiUrl + "/api/generate";
            
            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", modelName);
            requestBody.put("prompt", prompt);
            requestBody.put("stream", false);
            requestBody.put("options", Map.of(
                "temperature", 0.3,
                "top_p", 0.9,
                "max_tokens", 2000
            ));
            
            // 设置请求头
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setAccept(Collections.singletonList(MediaType.APPLICATION_JSON));
            
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);
            
            log.debug("🚀 调用Ollama模型: {} -> {}", modelName, url);
            
            // 发送请求
            ResponseEntity<String> response = restTemplate.exchange(
                url, HttpMethod.POST, entity, String.class
            );
            
            if (response.getStatusCode().is2xxSuccessful()) {
                return response.getBody();
            } else {
                throw new BizException("Ollama模型调用失败: HTTP " + response.getStatusCode());
            }
            
        } catch (ResourceAccessException e) {
            log.error("🚫 Ollama服务连接失败: {}", e.getMessage());
            throw new BizException("无法连接到Ollama服务，请检查服务状态");
        } catch (Exception e) {
            log.error("🚫 Ollama模型调用异常: {}", e.getMessage(), e);
            throw new BizException("模型调用失败: " + e.getMessage());
        }
    }

    /**
     * 解析健康预测结果
     */
    private HealthPredictionResult parseHealthPrediction(String response, Long userId, UserHealthContext context) {
        try {
            // 尝试解析JSON响应
            JsonNode jsonResponse = objectMapper.readTree(response);
            JsonNode predictionNode = jsonResponse.has("response") ? 
                objectMapper.readTree(jsonResponse.get("response").asText()) : jsonResponse;
            
            HealthPredictionResult result = new HealthPredictionResult();
            result.setUserId(userId);
            result.setGeneratedAt(LocalDateTime.now());
            result.setModelVersion(modelName);
            
            // 解析预测内容
            if (predictionNode.has("healthTrend")) {
                result.setHealthTrend(predictionNode.get("healthTrend").asText());
            }
            
            if (predictionNode.has("riskFactors")) {
                List<String> risks = new ArrayList<>();
                predictionNode.get("riskFactors").forEach(node -> risks.add(node.asText()));
                result.setRiskFactors(risks);
            }
            
            if (predictionNode.has("keyIndicators")) {
                List<String> indicators = new ArrayList<>();
                predictionNode.get("keyIndicators").forEach(node -> indicators.add(node.asText()));
                result.setKeyIndicators(indicators);
            }
            
            if (predictionNode.has("confidence")) {
                result.setConfidence(predictionNode.get("confidence").asDouble());
            }
            
            if (predictionNode.has("recommendations")) {
                List<String> recommendations = new ArrayList<>();
                predictionNode.get("recommendations").forEach(node -> recommendations.add(node.asText()));
                result.setRecommendations(recommendations);
            }
            
            // 设置原始响应
            result.setRawResponse(response);
            
            return result;
            
        } catch (Exception e) {
            log.warn("⚠️ 解析模型响应失败，使用原始文本: {}", e.getMessage());
            
            // 如果JSON解析失败，创建基础结果
            HealthPredictionResult result = new HealthPredictionResult();
            result.setUserId(userId);
            result.setGeneratedAt(LocalDateTime.now());
            result.setModelVersion(modelName);
            result.setHealthTrend("基于AI模型分析的健康预测");
            result.setRawResponse(response);
            result.setConfidence(0.7);
            
            return result;
        }
    }

    /**
     * 解析健康建议结果
     */
    private HealthAdviceResult parseHealthAdvice(String response, Long userId, UserHealthContext context) {
        try {
            JsonNode jsonResponse = objectMapper.readTree(response);
            JsonNode adviceNode = jsonResponse.has("response") ? 
                objectMapper.readTree(jsonResponse.get("response").asText()) : jsonResponse;
            
            HealthAdviceResult result = new HealthAdviceResult();
            result.setUserId(userId);
            result.setGeneratedAt(LocalDateTime.now());
            result.setModelVersion(modelName);
            
            // 解析生活方式建议
            if (adviceNode.has("lifestyle")) {
                JsonNode lifestyle = adviceNode.get("lifestyle");
                Map<String, List<String>> lifestyleAdvice = new HashMap<>();
                
                if (lifestyle.has("diet")) {
                    List<String> diet = new ArrayList<>();
                    lifestyle.get("diet").forEach(node -> diet.add(node.asText()));
                    lifestyleAdvice.put("diet", diet);
                }
                
                if (lifestyle.has("exercise")) {
                    List<String> exercise = new ArrayList<>();
                    lifestyle.get("exercise").forEach(node -> exercise.add(node.asText()));
                    lifestyleAdvice.put("exercise", exercise);
                }
                
                if (lifestyle.has("sleep")) {
                    List<String> sleep = new ArrayList<>();
                    lifestyle.get("sleep").forEach(node -> sleep.add(node.asText()));
                    lifestyleAdvice.put("sleep", sleep);
                }
                
                result.setLifestyleAdvice(lifestyleAdvice);
            }
            
            // 解析风险预防
            if (adviceNode.has("riskPrevention")) {
                List<String> prevention = new ArrayList<>();
                adviceNode.get("riskPrevention").forEach(node -> prevention.add(node.asText()));
                result.setRiskPrevention(prevention);
            }
            
            // 解析短期计划
            if (adviceNode.has("shortTermPlan")) {
                JsonNode plan = adviceNode.get("shortTermPlan");
                Map<String, Object> shortTermPlan = new HashMap<>();
                
                if (plan.has("duration")) {
                    shortTermPlan.put("duration", plan.get("duration").asText());
                }
                
                if (plan.has("goals")) {
                    List<String> goals = new ArrayList<>();
                    plan.get("goals").forEach(node -> goals.add(node.asText()));
                    shortTermPlan.put("goals", goals);
                }
                
                if (plan.has("actions")) {
                    List<String> actions = new ArrayList<>();
                    plan.get("actions").forEach(node -> actions.add(node.asText()));
                    shortTermPlan.put("actions", actions);
                }
                
                result.setShortTermPlan(shortTermPlan);
            }
            
            // 解析长期目标
            if (adviceNode.has("longTermGoals")) {
                List<String> longTermGoals = new ArrayList<>();
                adviceNode.get("longTermGoals").forEach(node -> longTermGoals.add(node.asText()));
                result.setLongTermGoals(longTermGoals);
            }
            
            // 解析优先级
            if (adviceNode.has("priority")) {
                result.setPriority(adviceNode.get("priority").asText());
            }
            
            result.setRawResponse(response);
            return result;
            
        } catch (Exception e) {
            log.warn("⚠️ 解析建议响应失败，使用原始文本: {}", e.getMessage());
            
            HealthAdviceResult result = new HealthAdviceResult();
            result.setUserId(userId);
            result.setGeneratedAt(LocalDateTime.now());
            result.setModelVersion(modelName);
            result.setRawResponse(response);
            result.setPriority("medium");
            
            return result;
        }
    }

    /**
     * 计算健康数据统计信息
     */
    private Map<String, String> calculateHealthStatistics(List<UserHealthData> healthDataList) {
        Map<String, String> statistics = new HashMap<>();
        
        if (healthDataList == null || healthDataList.isEmpty()) {
            return statistics;
        }
        
        // 心率统计
        List<Integer> heartRates = healthDataList.stream()
            .filter(data -> data.getHeartRate() != null && data.getHeartRate() > 0)
            .map(UserHealthData::getHeartRate)
            .collect(Collectors.toList());
        
        if (!heartRates.isEmpty()) {
            double avgHeartRate = heartRates.stream().mapToInt(Integer::intValue).average().orElse(0.0);
            statistics.put("heart_rate", String.format("平均 %.1f bpm (范围: %d-%d)", 
                avgHeartRate, Collections.min(heartRates), Collections.max(heartRates)));
        }
        
        // 血氧统计
        List<Integer> bloodOxygens = healthDataList.stream()
            .filter(data -> data.getBloodOxygen() != null && data.getBloodOxygen() > 0)
            .map(UserHealthData::getBloodOxygen)
            .collect(Collectors.toList());
        
        if (!bloodOxygens.isEmpty()) {
            double avgBloodOxygen = bloodOxygens.stream().mapToInt(Integer::intValue).average().orElse(0.0);
            statistics.put("blood_oxygen", String.format("平均 %.1f%% (范围: %d%%-%d%%)", 
                avgBloodOxygen, Collections.min(bloodOxygens), Collections.max(bloodOxygens)));
        }
        
        // 步数统计
        List<Integer> steps = healthDataList.stream()
            .filter(data -> data.getStep() != null && data.getStep() > 0)
            .map(UserHealthData::getStep)
            .collect(Collectors.toList());
        
        if (!steps.isEmpty()) {
            double avgSteps = steps.stream().mapToInt(Integer::intValue).average().orElse(0.0);
            statistics.put("step", String.format("日均 %.0f 步", avgSteps));
        }
        
        // 睡眠统计
        List<Integer> sleeps = healthDataList.stream()
            .filter(data -> data.getSleep() != null && data.getSleep() > 0)
            .map(UserHealthData::getSleep)
            .collect(Collectors.toList());
        
        if (!sleeps.isEmpty()) {
            double avgSleep = sleeps.stream().mapToInt(Integer::intValue).average().orElse(0.0);
            statistics.put("sleep", String.format("平均 %.1f 小时", avgSleep / 60.0));
        }
        
        return statistics;
    }

    /**
     * 获取特征显示名称
     */
    private String getFeatureDisplayName(String featureName) {
        Map<String, String> featureNames = Map.of(
            "heart_rate", "心率",
            "blood_oxygen", "血氧",
            "temperature", "体温",
            "pressure_high", "收缩压", 
            "pressure_low", "舒张压",
            "stress", "压力指数",
            "step", "步数",
            "sleep", "睡眠",
            "calorie", "卡路里",
            "distance", "距离"
        );
        
        return featureNames.getOrDefault(featureName, featureName);
    }

    /**
     * 检查Ollama服务状态
     */
    public boolean checkOllamaHealth() {
        try {
            String url = ollamaApiUrl + "/api/tags";
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            log.warn("⚠️ Ollama健康检查失败: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 获取可用模型列表
     */
    public List<String> getAvailableModels() {
        try {
            String url = ollamaApiUrl + "/api/tags";
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            
            if (response.getStatusCode().is2xxSuccessful()) {
                JsonNode jsonResponse = objectMapper.readTree(response.getBody());
                List<String> models = new ArrayList<>();
                
                if (jsonResponse.has("models")) {
                    jsonResponse.get("models").forEach(model -> {
                        if (model.has("name")) {
                            models.add(model.get("name").asText());
                        }
                    });
                }
                
                return models;
            }
        } catch (Exception e) {
            log.error("❌ 获取模型列表失败: {}", e.getMessage());
        }
        
        return Collections.emptyList();
    }

    // === 内部数据类 ===

    /**
     * 用户健康数据上下文
     */
    public static class UserHealthContext {
        private Long userId;
        private List<UserHealthData> recentHealthData;
        private List<HealthBaseline> baselines;
        private Map<String, String> statistics;

        // Getters and Setters
        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        
        public List<UserHealthData> getRecentHealthData() { return recentHealthData; }
        public void setRecentHealthData(List<UserHealthData> recentHealthData) { this.recentHealthData = recentHealthData; }
        
        public List<HealthBaseline> getBaselines() { return baselines; }
        public void setBaselines(List<HealthBaseline> baselines) { this.baselines = baselines; }
        
        public Map<String, String> getStatistics() { return statistics; }
        public void setStatistics(Map<String, String> statistics) { this.statistics = statistics; }
    }

    /**
     * 健康预测结果
     */
    public static class HealthPredictionResult {
        private Long userId;
        private LocalDateTime generatedAt;
        private String modelVersion;
        private String healthTrend;
        private List<String> riskFactors;
        private List<String> keyIndicators;
        private Double confidence;
        private List<String> recommendations;
        private String rawResponse;

        // Getters and Setters
        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        
        public LocalDateTime getGeneratedAt() { return generatedAt; }
        public void setGeneratedAt(LocalDateTime generatedAt) { this.generatedAt = generatedAt; }
        
        public String getModelVersion() { return modelVersion; }
        public void setModelVersion(String modelVersion) { this.modelVersion = modelVersion; }
        
        public String getHealthTrend() { return healthTrend; }
        public void setHealthTrend(String healthTrend) { this.healthTrend = healthTrend; }
        
        public List<String> getRiskFactors() { return riskFactors; }
        public void setRiskFactors(List<String> riskFactors) { this.riskFactors = riskFactors; }
        
        public List<String> getKeyIndicators() { return keyIndicators; }
        public void setKeyIndicators(List<String> keyIndicators) { this.keyIndicators = keyIndicators; }
        
        public Double getConfidence() { return confidence; }
        public void setConfidence(Double confidence) { this.confidence = confidence; }
        
        public List<String> getRecommendations() { return recommendations; }
        public void setRecommendations(List<String> recommendations) { this.recommendations = recommendations; }
        
        public String getRawResponse() { return rawResponse; }
        public void setRawResponse(String rawResponse) { this.rawResponse = rawResponse; }
    }

    /**
     * 健康建议结果
     */
    public static class HealthAdviceResult {
        private Long userId;
        private LocalDateTime generatedAt;
        private String modelVersion;
        private Map<String, List<String>> lifestyleAdvice;
        private List<String> riskPrevention;
        private Map<String, Object> shortTermPlan;
        private List<String> longTermGoals;
        private String priority;
        private String rawResponse;

        // Getters and Setters
        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        
        public LocalDateTime getGeneratedAt() { return generatedAt; }
        public void setGeneratedAt(LocalDateTime generatedAt) { this.generatedAt = generatedAt; }
        
        public String getModelVersion() { return modelVersion; }
        public void setModelVersion(String modelVersion) { this.modelVersion = modelVersion; }
        
        public Map<String, List<String>> getLifestyleAdvice() { return lifestyleAdvice; }
        public void setLifestyleAdvice(Map<String, List<String>> lifestyleAdvice) { this.lifestyleAdvice = lifestyleAdvice; }
        
        public List<String> getRiskPrevention() { return riskPrevention; }
        public void setRiskPrevention(List<String> riskPrevention) { this.riskPrevention = riskPrevention; }
        
        public Map<String, Object> getShortTermPlan() { return shortTermPlan; }
        public void setShortTermPlan(Map<String, Object> shortTermPlan) { this.shortTermPlan = shortTermPlan; }
        
        public List<String> getLongTermGoals() { return longTermGoals; }
        public void setLongTermGoals(List<String> longTermGoals) { this.longTermGoals = longTermGoals; }
        
        public String getPriority() { return priority; }
        public void setPriority(String priority) { this.priority = priority; }
        
        public String getRawResponse() { return rawResponse; }
        public void setRawResponse(String rawResponse) { this.rawResponse = rawResponse; }
    }
}