package com.ljwx.admin.controller.test;

import com.ljwx.common.api.Result;
import com.ljwx.modules.health.service.OllamaHealthPredictionService;
import com.ljwx.modules.health.service.OllamaHealthPredictionService.HealthPredictionResult;
import com.ljwx.modules.health.service.OllamaHealthPredictionService.HealthAdviceResult;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

/**
 * AI功能测试控制器 - 用于测试AI集成功能，无需权限验证
 * 
 * @author ljwx
 * @since 2025-01-06
 */
@Tag(name = "AI功能测试", description = "AI集成功能测试接口")
@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/ai_test")
public class AiTestController {

    private final OllamaHealthPredictionService ollamaHealthPredictionService;

    @GetMapping("/ping")
    @Operation(summary = "基础连通性测试")
    public Result<String> ping() {
        log.info("🏓 AI测试 - ping请求");
        return Result.data("pong - AI测试接口正常");
    }

    @GetMapping("/health")
    @Operation(summary = "AI服务健康检查(无权限)")
    public Result<Map<String, Object>> checkHealth() {
        log.info("🔍 AI测试 - 健康检查");
        
        try {
            boolean healthy = ollamaHealthPredictionService.checkOllamaHealth();
            List<String> models = ollamaHealthPredictionService.getAvailableModels();
            
            Map<String, Object> result = new HashMap<>();
            result.put("healthy", healthy);
            result.put("availableModels", models);
            result.put("checkTime", LocalDateTime.now().toString());
            result.put("testMode", true);
            
            log.info("✅ AI测试 - 健康检查完成: healthy={}, models={}", healthy, models.size());
            return Result.data(result);
        } catch (Exception e) {
            log.error("❌ AI测试 - 健康检查失败: {}", e.getMessage(), e);
            Map<String, Object> result = new HashMap<>();
            result.put("healthy", false);
            result.put("error", e.getMessage());
            result.put("checkTime", LocalDateTime.now().toString());
            result.put("testMode", true);
            return Result.data(result);
        }
    }

    @PostMapping("/mock-predict")
    @Operation(summary = "模拟AI预测(无权限)")
    public Result<HealthPredictionResult> mockPredict(
            @Parameter(description = "用户ID") @RequestParam("userId") Long userId,
            @Parameter(description = "预测天数") @RequestParam(value = "days", defaultValue = "7") Integer days) {
        
        log.info("🔮 AI测试 - 模拟预测: userId={}, days={}", userId, days);
        
        try {
            // 创建模拟的预测结果
            HealthPredictionResult result = new HealthPredictionResult();
            result.setUserId(userId);
            result.setGeneratedAt(LocalDateTime.now());
            result.setModelVersion("ljwx-health-enhanced:latest");
            result.setHealthTrend("根据您最近的健康数据分析，整体健康状况呈现稳定向好的趋势");
            result.setRiskFactors(Arrays.asList("轻度睡眠不足", "运动量略显不足"));
            result.setKeyIndicators(Arrays.asList("心率", "血氧", "睡眠质量"));
            result.setConfidence(0.85);
            result.setRecommendations(Arrays.asList(
                "建议每天保持7-8小时充足睡眠", 
                "增加适度的有氧运动，如快走或游泳",
                "注意监测心率和血氧变化"
            ));
            result.setRawResponse("模拟AI响应 - 测试模式");
            
            log.info("✅ AI测试 - 模拟预测完成");
            return Result.data(result);
        } catch (Exception e) {
            log.error("❌ AI测试 - 模拟预测失败: {}", e.getMessage(), e);
            return Result.failure("模拟预测失败: " + e.getMessage());
        }
    }

    @PostMapping("/mock-advice")
    @Operation(summary = "模拟AI建议(无权限)")
    public Result<HealthAdviceResult> mockAdvice(
            @Parameter(description = "用户ID") @RequestParam("userId") Long userId,
            @Parameter(description = "健康问题") @RequestParam(value = "healthIssues", required = false) List<String> healthIssues) {
        
        log.info("📝 AI测试 - 模拟建议: userId={}, issues={}", userId, healthIssues);
        
        try {
            // 创建模拟的建议结果
            HealthAdviceResult result = new HealthAdviceResult();
            result.setUserId(userId);
            result.setGeneratedAt(LocalDateTime.now());
            result.setModelVersion("ljwx-health-enhanced:latest");
            
            // 生活方式建议
            Map<String, List<String>> lifestyleAdvice = new HashMap<>();
            lifestyleAdvice.put("diet", Arrays.asList("增加蔬菜和水果摄入", "减少高盐高糖食物", "保持规律饮食时间"));
            lifestyleAdvice.put("exercise", Arrays.asList("每周至少150分钟中等强度运动", "结合力量训练和有氧运动", "避免长时间久坐"));
            lifestyleAdvice.put("sleep", Arrays.asList("建立规律的睡眠时间", "睡前避免使用电子设备", "保持卧室环境舒适"));
            result.setLifestyleAdvice(lifestyleAdvice);
            
            result.setRiskPrevention(Arrays.asList("定期体检", "监测血压血糖", "保持健康体重"));
            
            // 短期计划
            Map<String, Object> shortTermPlan = new HashMap<>();
            shortTermPlan.put("duration", "未来4周");
            shortTermPlan.put("goals", Arrays.asList("改善睡眠质量", "增加日常活动量"));
            shortTermPlan.put("actions", Arrays.asList("制定睡眠计划", "设置运动提醒", "记录健康数据"));
            result.setShortTermPlan(shortTermPlan);
            
            result.setLongTermGoals(Arrays.asList("维持健康体重", "提升心肺功能", "预防慢性疾病"));
            result.setPriority("高");
            result.setRawResponse("模拟AI建议响应 - 测试模式");
            
            log.info("✅ AI测试 - 模拟建议完成");
            return Result.data(result);
        } catch (Exception e) {
            log.error("❌ AI测试 - 模拟建议失败: {}", e.getMessage(), e);
            return Result.failure("模拟建议失败: " + e.getMessage());
        }
    }

    @PostMapping("/real-predict")
    @Operation(summary = "真实AI预测测试(无权限)")
    public Result<HealthPredictionResult> realPredict(
            @Parameter(description = "用户ID") @RequestParam("userId") Long userId,
            @Parameter(description = "预测天数") @RequestParam(value = "days", defaultValue = "7") Integer days) {
        
        log.info("🧠 AI测试 - 真实预测: userId={}, days={}", userId, days);
        
        try {
            HealthPredictionResult result = ollamaHealthPredictionService.generateHealthPrediction(userId, days);
            log.info("✅ AI测试 - 真实预测完成");
            return Result.data(result);
        } catch (Exception e) {
            log.error("❌ AI测试 - 真实预测失败: {}", e.getMessage(), e);
            return Result.failure("真实预测失败: " + e.getMessage());
        }
    }
}