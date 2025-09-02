/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.modules.alert.service.ai;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

/**
 * 上下文分析器
 * 分析告警发生时的环境上下文信息
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.ai.ContextAnalyzer
 * @CreateTime 2024-08-30 - 18:40:00
 */
@Slf4j
@Service
public class ContextAnalyzer {

    private final Random random = new Random();

    /**
     * 分析告警上下文
     * 
     * @param deviceSn 设备序列号
     * @param userId 用户ID
     * @param timestamp 告警时间戳
     * @return 上下文分析结果
     */
    public Map<String, Object> analyzeContext(String deviceSn, Long userId, LocalDateTime timestamp) {
        log.debug("开始上下文分析: deviceSn={}, userId={}, timestamp={}", 
                deviceSn, userId, timestamp);
        
        Map<String, Object> context = new HashMap<>();
        
        try {
            // 1. 时间上下文分析
            Map<String, Object> timeContext = analyzeTimeContext(timestamp);
            context.putAll(timeContext);
            
            // 2. 设备上下文分析
            Map<String, Object> deviceContext = analyzeDeviceContext(deviceSn);
            context.putAll(deviceContext);
            
            // 3. 用户上下文分析
            Map<String, Object> userContext = analyzeUserContext(userId);
            context.putAll(userContext);
            
            // 4. 环境上下文分析
            Map<String, Object> environmentContext = analyzeEnvironmentContext();
            context.putAll(environmentContext);
            
            // 5. 历史上下文分析
            Map<String, Object> historicalContext = analyzeHistoricalContext(deviceSn, userId);
            context.putAll(historicalContext);
            
            // 6. 计算上下文评分
            double contextScore = calculateContextScore(context);
            context.put("contextScore", contextScore);
            
            log.debug("上下文分析完成: deviceSn={}, contextScore={}", deviceSn, contextScore);
            
        } catch (Exception e) {
            log.error("上下文分析失败: deviceSn={}, userId={}", deviceSn, userId, e);
            
            // 返回基础上下文信息
            context.put("contextScore", 0.5);
            context.put("analysisStatus", "failed");
        }
        
        return context;
    }

    /**
     * 时间上下文分析
     */
    private Map<String, Object> analyzeTimeContext(LocalDateTime timestamp) {
        Map<String, Object> timeContext = new HashMap<>();
        
        if (timestamp == null) {
            timestamp = LocalDateTime.now();
        }
        
        // 时间段分析
        int hour = timestamp.getHour();
        String timeSlot = getTimeSlot(hour);
        timeContext.put("timeSlot", timeSlot);
        
        // 工作日/周末分析
        int dayOfWeek = timestamp.getDayOfWeek().getValue();
        boolean isWeekday = dayOfWeek <= 5;
        timeContext.put("isWeekday", isWeekday);
        timeContext.put("dayOfWeek", dayOfWeek);
        
        // 时间模式
        String timePattern = determineTimePattern(hour, isWeekday);
        timeContext.put("timePattern", timePattern);
        
        // 时间相关风险评估
        double timeRiskFactor = calculateTimeRiskFactor(hour, isWeekday);
        timeContext.put("timeRiskFactor", timeRiskFactor);
        
        return timeContext;
    }

    /**
     * 设备上下文分析
     */
    private Map<String, Object> analyzeDeviceContext(String deviceSn) {
        Map<String, Object> deviceContext = new HashMap<>();
        
        if (deviceSn == null || deviceSn.isEmpty()) {
            deviceContext.put("deviceStatus", "unknown");
            return deviceContext;
        }
        
        // 模拟设备状态分析
        String deviceStatus = simulateDeviceStatus();
        deviceContext.put("deviceStatus", deviceStatus);
        
        // 设备健康度
        double deviceHealth = 0.8 + (random.nextGaussian() * 0.1);
        deviceContext.put("deviceHealth", Math.max(0.5, Math.min(1.0, deviceHealth)));
        
        // 设备使用时长
        int usageDays = random.nextInt(365) + 1;
        deviceContext.put("usageDays", usageDays);
        
        // 电池状态
        int batteryLevel = 70 + random.nextInt(30);
        deviceContext.put("batteryLevel", batteryLevel);
        
        // 连接质量
        String connectionQuality = random.nextBoolean() ? "good" : "poor";
        deviceContext.put("connectionQuality", connectionQuality);
        
        return deviceContext;
    }

    /**
     * 用户上下文分析
     */
    private Map<String, Object> analyzeUserContext(Long userId) {
        Map<String, Object> userContext = new HashMap<>();
        
        if (userId == null) {
            userContext.put("userProfile", "unknown");
            return userContext;
        }
        
        // 模拟用户档案分析
        String userProfile = simulateUserProfile();
        userContext.put("userProfile", userProfile);
        
        // 活动状态
        String activityLevel = random.nextBoolean() ? "active" : "inactive";
        userContext.put("activityLevel", activityLevel);
        
        // 用户年龄段（模拟）
        String ageGroup = getRandomAgeGroup();
        userContext.put("ageGroup", ageGroup);
        
        // 健康风险等级
        String riskLevel = calculateHealthRiskLevel(ageGroup, activityLevel);
        userContext.put("healthRiskLevel", riskLevel);
        
        return userContext;
    }

    /**
     * 环境上下文分析
     */
    private Map<String, Object> analyzeEnvironmentContext() {
        Map<String, Object> envContext = new HashMap<>();
        
        // 模拟环境因素
        String weather = getRandomWeather();
        envContext.put("weather", weather);
        
        double temperature = 15 + random.nextInt(20); // 15-35度
        envContext.put("temperature", temperature);
        
        String season = getCurrentSeason();
        envContext.put("season", season);
        
        // 环境风险因子
        double envRiskFactor = calculateEnvironmentRiskFactor(weather, temperature);
        envContext.put("environmentRiskFactor", envRiskFactor);
        
        return envContext;
    }

    /**
     * 历史上下文分析
     */
    private Map<String, Object> analyzeHistoricalContext(String deviceSn, Long userId) {
        Map<String, Object> historicalContext = new HashMap<>();
        
        // 模拟历史告警频率
        int alertFrequency = random.nextInt(20); // 0-19
        historicalContext.put("alertFrequency", alertFrequency);
        
        // 历史告警类型分布
        boolean hasHistoricalAlerts = alertFrequency > 0;
        historicalContext.put("hasHistoricalAlerts", hasHistoricalAlerts);
        
        // 最近告警时间（小时）
        if (hasHistoricalAlerts) {
            int hoursSinceLastAlert = random.nextInt(168); // 0-168小时(一周)
            historicalContext.put("hoursSinceLastAlert", hoursSinceLastAlert);
        }
        
        // 告警解决率
        double resolutionRate = 0.7 + (random.nextDouble() * 0.25);
        historicalContext.put("alertResolutionRate", resolutionRate);
        
        // 用户响应模式
        String responsePattern = random.nextBoolean() ? "responsive" : "delayed";
        historicalContext.put("userResponsePattern", responsePattern);
        
        return historicalContext;
    }

    /**
     * 计算上下文评分
     */
    private double calculateContextScore(Map<String, Object> context) {
        double score = 0.5; // 基础分数
        
        // 时间风险因子影响
        Object timeRiskFactor = context.get("timeRiskFactor");
        if (timeRiskFactor instanceof Number) {
            score += ((Number) timeRiskFactor).doubleValue() * 0.2;
        }
        
        // 环境风险因子影响
        Object envRiskFactor = context.get("environmentRiskFactor");
        if (envRiskFactor instanceof Number) {
            score += ((Number) envRiskFactor).doubleValue() * 0.15;
        }
        
        // 历史告警频率影响
        Object alertFreq = context.get("alertFrequency");
        if (alertFreq instanceof Number) {
            int frequency = ((Number) alertFreq).intValue();
            if (frequency > 10) {
                score -= 0.1; // 频繁告警降低评分
            } else if (frequency < 2) {
                score += 0.1; // 罕见告警提高评分
            }
        }
        
        // 设备健康度影响
        Object deviceHealth = context.get("deviceHealth");
        if (deviceHealth instanceof Number) {
            double health = ((Number) deviceHealth).doubleValue();
            score += (health - 0.8) * 0.5; // 设备健康度影响
        }
        
        return Math.max(0.0, Math.min(1.0, score));
    }

    private String getTimeSlot(int hour) {
        if (hour >= 6 && hour < 12) return "morning";
        if (hour >= 12 && hour < 18) return "afternoon";
        if (hour >= 18 && hour < 22) return "evening";
        return "night";
    }

    private String determineTimePattern(int hour, boolean isWeekday) {
        if (isWeekday && hour >= 9 && hour <= 17) {
            return "work_hours";
        } else if (hour >= 22 || hour <= 6) {
            return "sleep_hours";
        } else {
            return "normal_hours";
        }
    }

    private double calculateTimeRiskFactor(int hour, boolean isWeekday) {
        // 夜间和凌晨风险较高
        if (hour >= 22 || hour <= 6) {
            return 0.3;
        }
        // 工作时间风险较低
        if (isWeekday && hour >= 9 && hour <= 17) {
            return -0.1;
        }
        return 0.0;
    }

    private String simulateDeviceStatus() {
        String[] statuses = {"normal", "warning", "error", "maintenance"};
        return statuses[random.nextInt(statuses.length)];
    }

    private String simulateUserProfile() {
        String[] profiles = {"healthy", "at_risk", "chronic_condition", "monitoring"};
        return profiles[random.nextInt(profiles.length)];
    }

    private String getRandomAgeGroup() {
        String[] ageGroups = {"young", "middle_aged", "elderly"};
        return ageGroups[random.nextInt(ageGroups.length)];
    }

    private String calculateHealthRiskLevel(String ageGroup, String activityLevel) {
        if ("elderly".equals(ageGroup) && "inactive".equals(activityLevel)) {
            return "high";
        } else if ("elderly".equals(ageGroup) || "inactive".equals(activityLevel)) {
            return "medium";
        } else {
            return "low";
        }
    }

    private String getRandomWeather() {
        String[] weathers = {"sunny", "cloudy", "rainy", "snowy", "windy"};
        return weathers[random.nextInt(weathers.length)];
    }

    private String getCurrentSeason() {
        int month = LocalDateTime.now().getMonthValue();
        if (month >= 3 && month <= 5) return "spring";
        if (month >= 6 && month <= 8) return "summer";
        if (month >= 9 && month <= 11) return "autumn";
        return "winter";
    }

    private double calculateEnvironmentRiskFactor(String weather, double temperature) {
        double risk = 0.0;
        
        // 极端天气增加风险
        if ("rainy".equals(weather) || "snowy".equals(weather)) {
            risk += 0.1;
        }
        
        // 极端温度增加风险
        if (temperature < 5 || temperature > 35) {
            risk += 0.1;
        }
        
        return risk;
    }
}