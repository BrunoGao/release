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

package com.ljwx.modules.alert.service.priority;

import com.ljwx.modules.alert.domain.dto.AnalyzedAlert;
import com.ljwx.modules.alert.domain.dto.PriorityInfo;
import com.ljwx.modules.system.domain.dto.OrgHierarchyInfo;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 智能优先级计算系统
 * 基于多因子模型计算告警处理优先级
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.priority.AlertPriorityCalculator
 * @CreateTime 2024-08-30 - 19:30:00
 */
@Slf4j
@Service
public class AlertPriorityCalculator {

    // 优先级权重配置
    private static final double BASE_PRIORITY_WEIGHT = 0.3;
    private static final double ORG_FACTOR_WEIGHT = 0.2;
    private static final double TIME_FACTOR_WEIGHT = 0.15;
    private static final double USER_RISK_WEIGHT = 0.15;
    private static final double DEVICE_HISTORY_WEIGHT = 0.1;
    private static final double LOCATION_FACTOR_WEIGHT = 0.1;

    /**
     * 基于多因子的优先级计算
     */
    public PriorityInfo calculatePriority(AnalyzedAlert alert, List<OrgHierarchyInfo> orgHierarchy) {
        log.info("开始智能优先级计算: alertId={}, orgCount={}", 
                alert.getAlertId(), orgHierarchy.size());
        
        long startTime = System.currentTimeMillis();
        
        try {
            // 1. 计算基础优先级
            double basePriority = getBasePriority(alert.getSeverityLevel());
            log.debug("基础优先级: {}", basePriority);
            
            // 2. 组织层级因子
            double orgFactor = calculateOrgFactor(alert, orgHierarchy);
            log.debug("组织因子: {}", orgFactor);
            
            // 3. 时间因子
            double timeFactor = calculateTimeFactor(alert.getAlertTimestamp());
            log.debug("时间因子: {}", timeFactor);
            
            // 4. 用户风险因子
            double userRiskFactor = calculateUserRiskFactor(alert);
            log.debug("用户风险因子: {}", userRiskFactor);
            
            // 5. 设备历史因子
            double deviceHistoryFactor = calculateDeviceHistoryFactor(alert);
            log.debug("设备历史因子: {}", deviceHistoryFactor);
            
            // 6. 地理位置因子
            double locationFactor = calculateLocationFactor(alert.getLatitude(), alert.getLongitude());
            log.debug("位置因子: {}", locationFactor);
            
            // 7. 综合计算最终优先级
            int finalPriority = weightedCalculation(
                    basePriority, orgFactor, timeFactor, 
                    userRiskFactor, deviceHistoryFactor, locationFactor
            );
            
            // 8. 计算处理截止时间
            LocalDateTime processingDeadline = calculateDeadline(finalPriority, alert.getAlertTimestamp());
            
            // 9. 构建升级链
            List<PriorityInfo.EscalationStep> escalationChain = buildEscalationChain(alert, orgHierarchy);
            
            // 10. 创建计算明细
            Map<String, Double> calculationBreakdown = createCalculationBreakdown(
                    basePriority, orgFactor, timeFactor, 
                    userRiskFactor, deviceHistoryFactor, locationFactor
            );
            
            PriorityInfo result = PriorityInfo.builder()
                    .priority(finalPriority)
                    .processingDeadline(processingDeadline)
                    .escalationChain(escalationChain)
                    .calculationBreakdown(calculationBreakdown)
                    .build();
            
            long calculationTime = System.currentTimeMillis() - startTime;
            log.info("优先级计算完成: alertId={}, priority={}, deadline={}, time={}ms", 
                    alert.getAlertId(), finalPriority, processingDeadline, calculationTime);
            
            return result;
            
        } catch (Exception e) {
            long calculationTime = System.currentTimeMillis() - startTime;
            log.error("优先级计算失败: alertId={}, time={}ms", alert.getAlertId(), calculationTime, e);
            
            // 返回默认优先级
            return createDefaultPriorityInfo(alert);
        }
    }

    /**
     * 获取基础优先级分数
     */
    private double getBasePriority(String severityLevel) {
        return switch (severityLevel) {
            case "CRITICAL" -> 1.0;
            case "HIGH" -> 0.8;
            case "MEDIUM" -> 0.6;
            case "LOW" -> 0.4;
            default -> 0.5;
        };
    }

    /**
     * 计算组织层级因子
     */
    private double calculateOrgFactor(AnalyzedAlert alert, List<OrgHierarchyInfo> orgHierarchy) {
        if (orgHierarchy.isEmpty()) {
            return 0.5; // 默认因子
        }
        
        // 分析组织结构复杂度
        int maxDepth = orgHierarchy.stream()
                .mapToInt(OrgHierarchyInfo::getDepth)
                .max()
                .orElse(1);
        
        // 统计管理员比例
        long managerCount = orgHierarchy.stream()
                .filter(info -> "1".equals(info.getPrincipal()))
                .count();
        
        double managerRatio = (double) managerCount / orgHierarchy.size();
        
        // 基于组织复杂度和管理员比例计算因子
        double complexityFactor = Math.min(1.0, maxDepth / 5.0); // 最大5层为满分
        double managerFactor = Math.min(1.0, managerRatio * 2); // 50%管理员比例为满分
        
        return (complexityFactor + managerFactor) / 2;
    }

    /**
     * 计算时间因子
     */
    private double calculateTimeFactor(LocalDateTime alertTimestamp) {
        if (alertTimestamp == null) {
            return 0.5;
        }
        
        LocalDateTime now = LocalDateTime.now();
        int currentHour = now.getHour();
        int dayOfWeek = now.getDayOfWeek().getValue();
        
        double timeFactor = 0.5; // 基础分数
        
        // 工作时间加分
        if (dayOfWeek <= 5 && currentHour >= 9 && currentHour <= 17) {
            timeFactor += 0.2;
        }
        
        // 非工作时间（夜间、周末）的紧急情况加分
        if (currentHour >= 22 || currentHour <= 6) {
            timeFactor += 0.3; // 夜间告警更紧急
        }
        
        // 周末加分
        if (dayOfWeek > 5) {
            timeFactor += 0.1;
        }
        
        return Math.min(1.0, timeFactor);
    }

    /**
     * 计算用户风险因子
     */
    private double calculateUserRiskFactor(AnalyzedAlert alert) {
        double riskFactor = 0.5; // 基础风险
        
        // 基于告警类型判断用户风险
        String alertType = alert.getAlertType();
        switch (alertType) {
            case "HEART_RATE":
            case "BLOOD_PRESSURE":
                riskFactor += 0.3; // 生命体征异常高风险
                break;
            case "FALL_DETECTION":
            case "SOS":
                riskFactor += 0.4; // 紧急求助最高风险
                break;
            case "DEVICE_OFFLINE":
                riskFactor += 0.1; // 设备离线中等风险
                break;
            default:
                riskFactor += 0.2; // 其他告警
        }
        
        // 基于AI分析结果调整
        Double confidenceScore = alert.getConfidenceScore();
        if (confidenceScore != null) {
            riskFactor += confidenceScore * 0.2;
        }
        
        return Math.min(1.0, riskFactor);
    }

    /**
     * 计算设备历史因子
     */
    private double calculateDeviceHistoryFactor(AnalyzedAlert alert) {
        double historyFactor = 0.5;
        
        // 基于上下文数据中的历史信息
        Map<String, Object> contextData = alert.getContextData();
        if (contextData != null) {
            // 设备健康度影响
            Object deviceHealth = contextData.get("deviceHealth");
            if (deviceHealth instanceof Number) {
                double health = ((Number) deviceHealth).doubleValue();
                historyFactor += (1 - health) * 0.3; // 设备健康度越低，优先级越高
            }
            
            // 告警频率影响
            Object alertFrequency = contextData.get("alertFrequency");
            if (alertFrequency instanceof Number) {
                int frequency = ((Number) alertFrequency).intValue();
                if (frequency > 10) {
                    historyFactor -= 0.1; // 过于频繁可能是误报
                } else if (frequency < 2) {
                    historyFactor += 0.2; // 罕见告警需要关注
                }
            }
        }
        
        return Math.max(0.0, Math.min(1.0, historyFactor));
    }

    /**
     * 计算地理位置因子
     */
    private double calculateLocationFactor(BigDecimal latitude, BigDecimal longitude) {
        if (latitude == null || longitude == null) {
            return 0.5; // 无位置信息默认分数
        }
        
        double locationFactor = 0.5;
        
        // 检查是否在高风险区域（这里只是示例逻辑）
        double lat = latitude.doubleValue();
        double lng = longitude.doubleValue();
        
        // 模拟医院、诊所附近加分
        if (isNearMedicalFacility(lat, lng)) {
            locationFactor += 0.2;
        }
        
        // 模拟偏远地区加分
        if (isRemoteArea(lat, lng)) {
            locationFactor += 0.3;
        }
        
        return Math.min(1.0, locationFactor);
    }

    /**
     * 加权计算最终优先级
     */
    private int weightedCalculation(double basePriority, double orgFactor, double timeFactor,
                                  double userRisk, double deviceHistory, double locationFactor) {
        
        double weightedScore = basePriority * BASE_PRIORITY_WEIGHT +
                              orgFactor * ORG_FACTOR_WEIGHT +
                              timeFactor * TIME_FACTOR_WEIGHT +
                              userRisk * USER_RISK_WEIGHT +
                              deviceHistory * DEVICE_HISTORY_WEIGHT +
                              locationFactor * LOCATION_FACTOR_WEIGHT;
        
        // 将0-1的分数映射到1-10的优先级（1最高，10最低）
        int priority = (int) Math.ceil((1.0 - weightedScore) * 9) + 1;
        return Math.max(1, Math.min(10, priority));
    }

    /**
     * 计算处理截止时间
     */
    private LocalDateTime calculateDeadline(int priority, LocalDateTime alertTimestamp) {
        if (alertTimestamp == null) {
            alertTimestamp = LocalDateTime.now();
        }
        
        long minutesToAdd = switch (priority) {
            case 1, 2 -> 5;   // 紧急：5分钟
            case 3, 4 -> 15;  // 重要：15分钟
            case 5, 6 -> 60;  // 普通：1小时
            case 7, 8 -> 240; // 低：4小时
            default -> 480;   // 很低：8小时
        };
        
        return alertTimestamp.plusMinutes(minutesToAdd);
    }

    /**
     * 构建升级链
     */
    private List<PriorityInfo.EscalationStep> buildEscalationChain(AnalyzedAlert alert, 
                                                                 List<OrgHierarchyInfo> orgHierarchy) {
        
        Map<Integer, List<OrgHierarchyInfo>> levelGroups = orgHierarchy.stream()
                .collect(Collectors.groupingBy(OrgHierarchyInfo::getDepth));
        
        List<PriorityInfo.EscalationStep> escalationChain = new ArrayList<>();
        
        // 按层级从低到高构建升级链
        levelGroups.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .forEach(entry -> {
                    Integer level = entry.getKey();
                    List<OrgHierarchyInfo> levelOrgs = entry.getValue();
                    
                    // 获取该层级的管理员
                    List<Long> managerIds = levelOrgs.stream()
                            .filter(info -> "1".equals(info.getPrincipal()))
                            .map(OrgHierarchyInfo::getUserId)
                            .distinct()
                            .collect(Collectors.toList());
                    
                    if (!managerIds.isEmpty()) {
                        PriorityInfo.EscalationStep step = PriorityInfo.EscalationStep.builder()
                                .level(level)
                                .orgId(levelOrgs.get(0).getOrgId())
                                .orgName(levelOrgs.get(0).getOrgName())
                                .managerIds(managerIds)
                                .delayMinutes(calculateEscalationDelay(level))
                                .build();
                        
                        escalationChain.add(step);
                    }
                });
        
        return escalationChain;
    }

    /**
     * 计算升级延迟
     */
    private long calculateEscalationDelay(Integer level) {
        return 30 + (level * 15); // 基础30分钟，每层级增加15分钟
    }

    /**
     * 创建计算明细
     */
    private Map<String, Double> createCalculationBreakdown(double base, double org, double time,
                                                         double user, double device, double location) {
        Map<String, Double> breakdown = new HashMap<>();
        breakdown.put("base", base);
        breakdown.put("org", org);
        breakdown.put("time", time);
        breakdown.put("user", user);
        breakdown.put("device", device);
        breakdown.put("location", location);
        return breakdown;
    }

    /**
     * 创建默认优先级信息
     */
    private PriorityInfo createDefaultPriorityInfo(AnalyzedAlert alert) {
        return PriorityInfo.builder()
                .priority(5) // 默认中等优先级
                .processingDeadline(LocalDateTime.now().plusHours(1))
                .escalationChain(new ArrayList<>())
                .calculationBreakdown(new HashMap<>())
                .build();
    }

    // 辅助方法
    private boolean isNearMedicalFacility(double lat, double lng) {
        // 这里应该查询地理信息数据库或调用地图服务API
        // 暂时返回随机结果作为示例
        return Math.random() < 0.1; // 10%概率在医疗机构附近
    }

    private boolean isRemoteArea(double lat, double lng) {
        // 这里应该基于实际地理数据判断
        // 暂时返回随机结果作为示例
        return Math.random() < 0.05; // 5%概率在偏远地区
    }
}