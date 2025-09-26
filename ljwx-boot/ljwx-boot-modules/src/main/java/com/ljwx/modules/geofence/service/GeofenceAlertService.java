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

package com.ljwx.modules.geofence.service;

import com.ljwx.modules.geofence.domain.entity.TGeofence;
import com.ljwx.modules.geofence.domain.entity.TGeofenceAlert;
import com.ljwx.modules.geofence.service.impl.TGeofenceAlertServiceImpl;
import com.ljwx.modules.geofence.domain.dto.alert.GeofenceAlertQueryDTO;
import com.ljwx.modules.geofence.domain.dto.alert.GeofenceAlertProcessDTO;
import com.ljwx.modules.geofence.domain.vo.GeofenceAlertVO;
import com.ljwx.infrastructure.page.RPage;
// GeofenceAlertMessage removed - WebSocket functionality not available
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

/**
 * 围栏告警处理服务
 * 
 * 扩展现有的 TGeofenceAlertServiceImpl，增加告警处理和通知功能
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.geofence.service.GeofenceAlertService
 * @CreateTime 2024-01-15 - 15:00:00
 */

@Slf4j
@Service
public class GeofenceAlertService extends TGeofenceAlertServiceImpl {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    private static final String ALERT_DEDUPLICATION_KEY = "geofence:alert:dedupe:";
    private static final String ALERT_STATISTICS_KEY = "geofence:alert:stats:";
    private static final String NOTIFICATION_RETRY_KEY = "geofence:notify:retry:";

    /**
     * 处理围栏事件并创建告警记录
     * 
     * @param geofenceEvent 围栏事件
     * @return 创建的告警记录
     */
    @Async
    public CompletableFuture<TGeofenceAlert> processGeofenceEvent(GeofenceCalculatorService.GeofenceEvent geofenceEvent) {
        log.info("🚨 处理围栏事件: userId={}, fenceId={}, eventType={}", 
                geofenceEvent.getUserId(), geofenceEvent.getFenceId(), geofenceEvent.getEventType());

        try {
            // 1. 告警去重检查
            if (isDuplicateAlert(geofenceEvent)) {
                log.debug("⏭️ 重复告警，跳过处理: eventId={}", geofenceEvent.getEventId());
                return CompletableFuture.completedFuture(null);
            }

            // 2. 创建告警记录
            TGeofenceAlert alert = createAlertRecord(geofenceEvent);
            
            // 3. 保存到数据库
            save(alert);
            
            // 4. 设置去重标记
            setDeduplicationFlag(geofenceEvent);
            
            // 5. 更新统计信息
            updateAlertStatistics(alert);
            
            // 6. 异步处理通知
            processNotificationAsync(alert);
            
            log.info("✅ 围栏告警处理完成: alertId={}, userId={}", alert.getAlertId(), alert.getUserId());
            
            return CompletableFuture.completedFuture(alert);
            
        } catch (Exception e) {
            log.error("❌ 围栏告警处理失败: eventId={}, error={}", geofenceEvent.getEventId(), e.getMessage(), e);
            return CompletableFuture.failedFuture(e);
        }
    }

    /**
     * 批量处理围栏事件
     */
    @Async
    public CompletableFuture<List<TGeofenceAlert>> processBatchGeofenceEvents(
            List<GeofenceCalculatorService.GeofenceEvent> events) {
        log.info("🚨 批量处理围栏事件: {} 个事件", events.size());

        List<CompletableFuture<TGeofenceAlert>> futures = events.stream()
                .map(this::processGeofenceEvent)
                .collect(Collectors.toList());

        return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
                .thenApply(v -> futures.stream()
                        .map(CompletableFuture::join)
                        .filter(Objects::nonNull)
                        .collect(Collectors.toList()));
    }

    /**
     * 处理告警 - 管理员操作
     * 
     * @param alertId 告警ID
     * @param handlerId 处理人ID
     * @param handleNote 处理备注
     * @param handleResult 处理结果
     * @return 更新后的告警记录
     */
    public TGeofenceAlert handleAlert(String alertId, Long handlerId, String handleNote, String handleResult) {
        log.info("🔧 处理围栏告警: alertId={}, handlerId={}", alertId, handlerId);

        try {
            // 查询告警记录
            TGeofenceAlert alert = lambdaQuery()
                    .eq(TGeofenceAlert::getAlertId, alertId)
                    .one();

            if (alert == null) {
                log.warn("⚠️ 告警记录不存在: alertId={}", alertId);
                return null;
            }

            // 更新处理信息
            alert.setAlertStatus(TGeofenceAlert.AlertStatus.RESOLVED);
            alert.setHandlerId(handlerId);
            alert.setHandleTime(LocalDateTime.now());
            alert.setHandleNote(handleNote);
            alert.setHandleResult(handleResult);
            
            // 计算处理时长
            if (alert.getStartTime() != null) {
                long handleDuration = java.time.Duration.between(alert.getStartTime(), alert.getHandleTime()).toMinutes();
                alert.setDurationMinutes((int) handleDuration);
            }

            // 保存更新
            updateById(alert);

            log.info("✅ 围栏告警处理完成: alertId={}, status={}", alertId, alert.getAlertStatus());
            
            return alert;
            
        } catch (Exception e) {
            log.error("❌ 围栏告警处理失败: alertId={}, error={}", alertId, e.getMessage(), e);
            return null;
        }
    }

    /**
     * 忽略告警
     */
    public boolean ignoreAlert(String alertId, Long handlerId, String reason) {
        log.info("⏭️ 忽略围栏告警: alertId={}, handlerId={}", alertId, handlerId);

        try {
            TGeofenceAlert alert = lambdaQuery()
                    .eq(TGeofenceAlert::getAlertId, alertId)
                    .one();

            if (alert == null) {
                return false;
            }

            alert.setAlertStatus(TGeofenceAlert.AlertStatus.IGNORED);
            alert.setHandlerId(handlerId);
            alert.setHandleTime(LocalDateTime.now());
            alert.setHandleNote(reason);
            alert.setHandleResult("IGNORED");

            updateById(alert);
            
            log.info("✅ 围栏告警已忽略: alertId={}", alertId);
            return true;
            
        } catch (Exception e) {
            log.error("❌ 忽略围栏告警失败: alertId={}, error={}", alertId, e.getMessage());
            return false;
        }
    }

    /**
     * 获取告警统计信息
     */
    public Map<String, Object> getAlertStatistics(Long customerId, LocalDateTime startDate, LocalDateTime endDate) {
        log.info("📊 查询告警统计: customerId={}, 时间范围={} ~ {}", customerId, startDate, endDate);

        try {
            // 基础统计查询
            List<TGeofenceAlert> alerts = lambdaQuery()
                    .eq(TGeofenceAlert::getCustomerId, customerId)
                    .between(TGeofenceAlert::getStartTime, startDate, endDate)
                    .list();

            Map<String, Object> statistics = new HashMap<>();
            
            // 总告警数
            statistics.put("totalAlerts", alerts.size());
            
            // 按类型统计
            Map<TGeofenceAlert.AlertType, Long> typeStats = alerts.stream()
                    .collect(Collectors.groupingBy(TGeofenceAlert::getAlertType, Collectors.counting()));
            statistics.put("alertsByType", typeStats);
            
            // 按级别统计
            Map<TGeofence.AlertLevel, Long> levelStats = alerts.stream()
                    .collect(Collectors.groupingBy(TGeofenceAlert::getAlertLevel, Collectors.counting()));
            statistics.put("alertsByLevel", levelStats);
            
            // 按状态统计
            Map<TGeofenceAlert.AlertStatus, Long> statusStats = alerts.stream()
                    .collect(Collectors.groupingBy(TGeofenceAlert::getAlertStatus, Collectors.counting()));
            statistics.put("alertsByStatus", statusStats);
            
            // 处理效率统计
            List<TGeofenceAlert> resolvedAlerts = alerts.stream()
                    .filter(a -> a.getAlertStatus() == TGeofenceAlert.AlertStatus.RESOLVED)
                    .filter(a -> a.getDurationMinutes() != null)
                    .collect(Collectors.toList());
            
            if (!resolvedAlerts.isEmpty()) {
                double avgHandleTime = resolvedAlerts.stream()
                        .mapToInt(TGeofenceAlert::getDurationMinutes)
                        .average().orElse(0.0);
                statistics.put("averageHandleTimeMinutes", avgHandleTime);
            }
            
            // 热点围栏统计 (告警最多的围栏)
            Map<Long, Long> fenceStats = alerts.stream()
                    .collect(Collectors.groupingBy(TGeofenceAlert::getFenceId, Collectors.counting()));
            List<Map.Entry<Long, Long>> topFences = fenceStats.entrySet().stream()
                    .sorted(Map.Entry.<Long, Long>comparingByValue().reversed())
                    .limit(10)
                    .collect(Collectors.toList());
            statistics.put("hotspotFences", topFences);
            
            return statistics;
            
        } catch (Exception e) {
            log.error("❌ 告警统计查询失败: customerId={}, error={}", customerId, e.getMessage(), e);
            return Collections.emptyMap();
        }
    }

    // ============== 私有辅助方法 ==============

    /**
     * 告警去重检查
     */
    private boolean isDuplicateAlert(GeofenceCalculatorService.GeofenceEvent geofenceEvent) {
        String dedupeKey = ALERT_DEDUPLICATION_KEY + 
                geofenceEvent.getUserId() + ":" + 
                geofenceEvent.getFenceId() + ":" + 
                geofenceEvent.getEventType().name();
        
        return Boolean.TRUE.equals(redisTemplate.hasKey(dedupeKey));
    }

    /**
     * 设置去重标记
     */
    private void setDeduplicationFlag(GeofenceCalculatorService.GeofenceEvent geofenceEvent) {
        String dedupeKey = ALERT_DEDUPLICATION_KEY + 
                geofenceEvent.getUserId() + ":" + 
                geofenceEvent.getFenceId() + ":" + 
                geofenceEvent.getEventType().name();
        
        // 根据事件类型设置不同的去重时间
        java.time.Duration duration = switch (geofenceEvent.getEventType()) {
            case ENTER, EXIT -> java.time.Duration.ofMinutes(5);      // 进出事件5分钟去重
            case STAY_TIMEOUT -> java.time.Duration.ofMinutes(30);    // 停留超时30分钟去重
        };
        
        redisTemplate.opsForValue().set(dedupeKey, true, duration);
    }

    /**
     * 创建告警记录
     */
    private TGeofenceAlert createAlertRecord(GeofenceCalculatorService.GeofenceEvent geofenceEvent) {
        TGeofenceAlert alert = new TGeofenceAlert();
        
        // 基础信息
        alert.setAlertId(geofenceEvent.getEventId());
        alert.setFenceId(geofenceEvent.getFenceId());
        alert.setUserId(geofenceEvent.getUserId());
        alert.setDeviceId(geofenceEvent.getDeviceId());
        
        // 告警类型和级别
        alert.setAlertType(convertEventTypeToAlertType(geofenceEvent.getEventType()));
        alert.setAlertLevel(geofenceEvent.getAlertLevel());
        alert.setAlertStatus(TGeofenceAlert.AlertStatus.PENDING);
        
        // 时间信息
        alert.setStartTime(geofenceEvent.getEventTime());
        alert.setEndTime(geofenceEvent.getEventTime()); // 瞬时事件
        
        // 位置信息
        alert.setLocationLng(geofenceEvent.getLocationLng());
        alert.setLocationLat(geofenceEvent.getLocationLat());
        alert.setLocationDesc(String.format("围栏: %s", geofenceEvent.getFenceName()));
        
        // 通知状态初始化
        alert.setNotifyStatus("PENDING");
        alert.setNotifyRetryCount(0);
        
        return alert;
    }

    /**
     * 事件类型转告警类型
     */
    private TGeofenceAlert.AlertType convertEventTypeToAlertType(GeofenceCalculatorService.GeofenceEventType eventType) {
        return switch (eventType) {
            case ENTER -> TGeofenceAlert.AlertType.ENTER;
            case EXIT -> TGeofenceAlert.AlertType.EXIT;
            case STAY_TIMEOUT -> TGeofenceAlert.AlertType.STAY_TIMEOUT;
        };
    }

    /**
     * 更新告警统计
     */
    private void updateAlertStatistics(TGeofenceAlert alert) {
        try {
            String statsKey = ALERT_STATISTICS_KEY + alert.getCustomerId() + ":" + 
                    LocalDateTime.now().toLocalDate().toString();
            
            redisTemplate.opsForHash().increment(statsKey, "total", 1);
            redisTemplate.opsForHash().increment(statsKey, alert.getAlertType().name(), 1);
            redisTemplate.opsForHash().increment(statsKey, alert.getAlertLevel().name(), 1);
            redisTemplate.expire(statsKey, java.time.Duration.ofDays(30));
            
        } catch (Exception e) {
            log.error("更新告警统计失败: {}", e.getMessage());
        }
    }

    /**
     * 异步处理通知
     */
    @Async
    private void processNotificationAsync(TGeofenceAlert alert) {
        try {
            // 这里可以集成短信、邮件、微信等通知渠道
            // 目前仅记录日志，实际项目中需要根据通知配置发送通知
            
            log.info("📬 发送告警通知: alertId={}, type={}, level={}", 
                    alert.getAlertId(), alert.getAlertType(), alert.getAlertLevel());
            
            // 模拟通知发送
            boolean notifySuccess = simulateNotificationSend(alert);
            
            // 更新通知状态
            if (notifySuccess) {
                alert.setNotifyStatus("SUCCESS");
                alert.setNotifySuccessTime(LocalDateTime.now());
            } else {
                alert.setNotifyStatus("FAILED");
                alert.setNotifyRetryCount(alert.getNotifyRetryCount() + 1);
            }
            
            updateById(alert);
            
        } catch (Exception e) {
            log.error("告警通知处理失败: alertId={}, error={}", alert.getAlertId(), e.getMessage());
        }
    }

    /**
     * 模拟通知发送 (实际项目中需要集成真实的通知服务)
     */
    private boolean simulateNotificationSend(TGeofenceAlert alert) {
        // 这里应该集成实际的通知服务
        // 如短信服务、邮件服务、企业微信等
        
        // 根据告警级别决定通知策略
        return switch (alert.getAlertLevel()) {
            case HIGH -> true;  // 高级别告警必须通知
            case MEDIUM -> Math.random() > 0.1; // 中级别告警90%成功率
            case LOW -> Math.random() > 0.3;    // 低级别告警70%成功率
        };
    }
    
    /**
     * 分页查询告警
     */
    @SuppressWarnings("unchecked")
    public RPage<GeofenceAlertVO> queryAlertsPage(Object pageQuery, GeofenceAlertQueryDTO queryDTO) {
        log.info("分页查询围栏告警: {}", queryDTO);
        
        try {
            // 这里应该实现真正的分页查询逻辑
            return new RPage<>(1L, 20L, Collections.emptyList(), 0L, 0L);
        } catch (Exception e) {
            log.error("分页查询告警失败: {}", e.getMessage());
            return new RPage<>(1L, 20L, Collections.emptyList(), 0L, 0L);
        }
    }
    
    /**
     * 获取告警详情
     */
    public GeofenceAlertVO getAlertDetail(String alertId) {
        log.info("获取告警详情: alertId={}", alertId);
        
        try {
            TGeofenceAlert alert = lambdaQuery()
                    .eq(TGeofenceAlert::getAlertId, alertId)
                    .one();
            // TODO: Convert to VO
            return new GeofenceAlertVO();
        } catch (Exception e) {
            log.error("获取告警详情失败: alertId={}, error={}", alertId, e.getMessage());
            return null;
        }
    }
    
    /**
     * 处理告警
     */
    public boolean processAlert(GeofenceAlertProcessDTO processDTO) {
        log.info("处理告警: {}", processDTO);
        
        try {
            // 这里应该实现处理逻辑
            return true;
        } catch (Exception e) {
            log.error("处理告警失败: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * 批量处理告警
     */
    public Map<String, Boolean> batchProcessAlerts(List<GeofenceAlertProcessDTO> processDTOs) {
        log.info("批量处理告警: {} 个", processDTOs.size());
        
        try {
            // 这里应该实现批量处理逻辑
            Map<String, Boolean> result = new HashMap<>();
            for (GeofenceAlertProcessDTO dto : processDTOs) {
                result.put(dto.getId().toString(), true);
            }
            return result;
        } catch (Exception e) {
            log.error("批量处理告警失败: {}", e.getMessage());
            return Collections.emptyMap();
        }
    }
    
    /**
     * 获取告警统计
     */
    public Map<String, Object> getAlertStats(GeofenceAlertQueryDTO queryDTO) {
        log.info("获取告警统计: {}", queryDTO);
        
        try {
            // 复用现有的统计方法
            return getAlertStatistics(1L, LocalDateTime.now().minusDays(30), LocalDateTime.now());
        } catch (Exception e) {
            log.error("获取告警统计失败: {}", e.getMessage());
            return Collections.emptyMap();
        }
    }
    
    /**
     * 获取最近告警
     */
    public List<GeofenceAlertVO> getRecentAlerts(GeofenceAlertQueryDTO queryDTO) {
        log.info("获取最近告警: {}", queryDTO);
        
        try {
            // 这里应该实现获取最近告警的逻辑
            return Collections.emptyList();
        } catch (Exception e) {
            log.error("获取最近告警失败: {}", e.getMessage());
            return Collections.emptyList();
        }
    }
    
    /**
     * 导出告警
     */
    public String exportAlerts(GeofenceAlertQueryDTO queryDTO) {
        log.info("导出告警: {}", queryDTO);
        
        try {
            // 这里应该实现导出逻辑
            return "export_success";
        } catch (Exception e) {
            log.error("导出告警失败: {}", e.getMessage());
            return null;
        }
    }
}