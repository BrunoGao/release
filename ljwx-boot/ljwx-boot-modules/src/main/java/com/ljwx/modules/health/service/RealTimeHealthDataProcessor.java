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

package com.ljwx.modules.health.service;

import com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO;
import com.ljwx.modules.health.domain.vo.track.TrackPointVO;
import com.ljwx.modules.realtime.service.RealTimeTrackService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 实时健康数据处理器
 * 
 * 监听健康数据变化，提取轨迹数据并触发实时推送
 * 
 * 核心约束: 必须通过 UnifiedHealthDataQueryService.queryHealthData 查询数据
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.RealTimeHealthDataProcessor
 * @CreateTime 2024-01-15 - 14:30:00
 */

@Slf4j
@Service
public class RealTimeHealthDataProcessor {

    @Autowired
    private UnifiedHealthDataQueryService unifiedHealthDataQueryService;
    
    @Autowired
    private RealTimeTrackService realTimeTrackService;
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    private static final String PROCESSED_DATA_KEY = "realtime:processed:";
    private static final String BATCH_PROCESS_LOCK = "realtime:batch_lock:";

    /**
     * 处理新的健康数据记录 (单条)
     * 
     * 当健康数据表有新数据插入时调用此方法
     * 
     * @param userId 用户ID
     * @param customerId 客户ID
     * @param timestamp 数据时间戳
     */
    @Async
    public void processNewHealthData(Long userId, Long customerId, LocalDateTime timestamp) {
        log.debug("🔄 处理新健康数据: userId={}, timestamp={}", userId, timestamp);

        try {
            // 1. 防重复处理检查
            String processKey = PROCESSED_DATA_KEY + userId + ":" + timestamp.toString();
            if (Boolean.TRUE.equals(redisTemplate.hasKey(processKey))) {
                log.debug("⏭️ 数据已处理，跳过: userId={}, timestamp={}", userId, timestamp);
                return;
            }

            // 2. 通过统一查询服务获取最新轨迹数据
            UnifiedHealthQueryDTO queryDTO = buildLatestDataQuery(userId, customerId, timestamp);
            Map<String, Object> healthDataResult = unifiedHealthDataQueryService.queryHealthData(queryDTO);

            // 3. 验证查询结果
            if (healthDataResult == null || !Boolean.TRUE.equals(healthDataResult.get("success"))) {
                log.warn("⚠️ 健康数据查询失败: userId={}, timestamp={}", userId, timestamp);
                return;
            }

            // 4. 提取轨迹数据
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> basicData = (List<Map<String, Object>>) healthDataResult.get("basicData");

            if (basicData == null || basicData.isEmpty()) {
                log.debug("📊 未查询到轨迹数据: userId={}, timestamp={}", userId, timestamp);
                return;
            }

            // 5. 转换为轨迹点
            List<TrackPointVO> trackPoints = basicData.stream()
                    .filter(this::isValidLocationData)
                    .map(this::convertToTrackPoint)
                    .sorted(Comparator.comparing(TrackPointVO::getTimestamp))
                    .collect(Collectors.toList());

            if (trackPoints.isEmpty()) {
                log.debug("📊 无有效轨迹点: userId={}, timestamp={}", userId, timestamp);
                return;
            }

            // 6. 处理最新的轨迹点
            TrackPointVO latestPoint = trackPoints.get(trackPoints.size() - 1);
            realTimeTrackService.processNewTrackPoint(latestPoint);

            // 7. 标记已处理
            redisTemplate.opsForValue().set(processKey, true, java.time.Duration.ofHours(1));

            log.debug("✅ 实时健康数据处理完成: userId={}, pointCount={}", userId, trackPoints.size());

        } catch (Exception e) {
            log.error("❌ 实时健康数据处理失败: userId={}, timestamp={}, error={}", userId, timestamp, e.getMessage(), e);
        }
    }

    /**
     * 批量处理健康数据 (用于数据补发或批量同步)
     * 
     * @param userIds 用户ID列表
     * @param customerId 客户ID
     * @param startTime 开始时间
     * @param endTime 结束时间
     */
    @Async
    public void processBatchHealthData(List<Long> userIds, Long customerId, 
                                      LocalDateTime startTime, LocalDateTime endTime) {
        log.info("🔄 批量处理健康数据: {} 个用户, 时间范围={} ~ {}", userIds.size(), startTime, endTime);

        String lockKey = BATCH_PROCESS_LOCK + customerId;
        
        try {
            // 1. 获取分布式锁 (防止重复批处理)
            Boolean lockAcquired = redisTemplate.opsForValue().setIfAbsent(lockKey, "processing", 
                    java.time.Duration.ofMinutes(30));
            
            if (!Boolean.TRUE.equals(lockAcquired)) {
                log.warn("⚠️ 批量处理锁已存在，跳过: customerId={}", customerId);
                return;
            }

            // 2. 逐个用户处理
            List<TrackPointVO> allTrackPoints = new ArrayList<>();
            
            for (Long userId : userIds) {
                try {
                    // 构建查询参数
                    UnifiedHealthQueryDTO queryDTO = buildBatchDataQuery(userId, customerId, startTime, endTime);
                    Map<String, Object> healthDataResult = unifiedHealthDataQueryService.queryHealthData(queryDTO);

                    if (healthDataResult != null && Boolean.TRUE.equals(healthDataResult.get("success"))) {
                        @SuppressWarnings("unchecked")
                        List<Map<String, Object>> basicData = (List<Map<String, Object>>) healthDataResult.get("basicData");

                        if (basicData != null && !basicData.isEmpty()) {
                            List<TrackPointVO> userTrackPoints = basicData.stream()
                                    .filter(this::isValidLocationData)
                                    .map(this::convertToTrackPoint)
                                    .collect(Collectors.toList());
                            
                            allTrackPoints.addAll(userTrackPoints);
                        }
                    }
                } catch (Exception e) {
                    log.error("批量处理用户{}数据失败: {}", userId, e.getMessage());
                }
            }

            // 3. 批量推送
            if (!allTrackPoints.isEmpty()) {
                realTimeTrackService.processBatchTrackPoints(allTrackPoints);
                log.info("✅ 批量健康数据处理完成: {} 个轨迹点", allTrackPoints.size());
            }

        } finally {
            // 释放锁
            redisTemplate.delete(lockKey);
        }
    }

    /**
     * 用户上线处理 - 推送最近轨迹
     */
    public void handleUserOnline(Long userId, Long customerId) {
        log.info("👤 用户上线处理: userId={}, customerId={}", userId, customerId);

        try {
            // 查询最近轨迹 (最近2小时)
            LocalDateTime since = LocalDateTime.now().minusHours(2);
            UnifiedHealthQueryDTO queryDTO = buildRecentDataQuery(userId, customerId, since);
            Map<String, Object> healthDataResult = unifiedHealthDataQueryService.queryHealthData(queryDTO);

            if (healthDataResult != null && Boolean.TRUE.equals(healthDataResult.get("success"))) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> basicData = (List<Map<String, Object>>) healthDataResult.get("basicData");

                if (basicData != null && !basicData.isEmpty()) {
                    List<TrackPointVO> recentTracks = basicData.stream()
                            .filter(this::isValidLocationData)
                            .map(this::convertToTrackPoint)
                            .sorted(Comparator.comparing(TrackPointVO::getTimestamp))
                            .collect(Collectors.toList());

                    if (!recentTracks.isEmpty()) {
                        realTimeTrackService.processBatchTrackPoints(recentTracks);
                        log.info("📤 用户上线轨迹推送: userId={}, pointCount={}", userId, recentTracks.size());
                    }
                }
            }
        } catch (Exception e) {
            log.error("用户上线处理失败: userId={}, error={}", userId, e.getMessage());
        }
    }

    // ============== 私有辅助方法 ==============

    /**
     * 构建最新数据查询参数
     */
    private UnifiedHealthQueryDTO buildLatestDataQuery(Long userId, Long customerId, LocalDateTime timestamp) {
        UnifiedHealthQueryDTO queryDTO = new UnifiedHealthQueryDTO();
        queryDTO.setUserId(userId);
        queryDTO.setCustomerId(customerId);
        queryDTO.setStartDate(timestamp.minusMinutes(1));
        queryDTO.setEndDate(timestamp.plusMinutes(1));
        queryDTO.setPageSize(10);
        return queryDTO;
    }

    /**
     * 构建批量数据查询参数
     */
    private UnifiedHealthQueryDTO buildBatchDataQuery(Long userId, Long customerId, 
                                                     LocalDateTime startTime, LocalDateTime endTime) {
        UnifiedHealthQueryDTO queryDTO = new UnifiedHealthQueryDTO();
        queryDTO.setUserId(userId);
        queryDTO.setCustomerId(customerId);
        queryDTO.setStartDate(startTime);
        queryDTO.setEndDate(endTime);
        queryDTO.setPageSize(1000);
        return queryDTO;
    }

    /**
     * 构建最近数据查询参数
     */
    private UnifiedHealthQueryDTO buildRecentDataQuery(Long userId, Long customerId, LocalDateTime since) {
        UnifiedHealthQueryDTO queryDTO = new UnifiedHealthQueryDTO();
        queryDTO.setUserId(userId);
        queryDTO.setCustomerId(customerId);
        queryDTO.setStartDate(since);
        queryDTO.setEndDate(LocalDateTime.now());
        queryDTO.setPageSize(200);
        return queryDTO;
    }

    /**
     * 验证位置数据有效性
     */
    private boolean isValidLocationData(Map<String, Object> data) {
        Double lat = getDoubleValue(data, "latitude");
        Double lng = getDoubleValue(data, "longitude");
        
        return lat != null && lng != null && 
               lat >= -90 && lat <= 90 && 
               lng >= -180 && lng <= 180;
    }

    /**
     * Map数据转TrackPointVO
     */
    private TrackPointVO convertToTrackPoint(Map<String, Object> data) {
        TrackPointVO point = new TrackPointVO();
        
        // 基础字段
        point.setUserId(getLongValue(data, "userId"));
        point.setUserName(getStringValue(data, "userName"));
        point.setLongitude(getDoubleValue(data, "longitude"));
        point.setLatitude(getDoubleValue(data, "latitude"));
        point.setAltitude(getDoubleValue(data, "altitude"));
        point.setTimestamp(getTimestampValue(data, "timestamp"));
        point.setDeviceSn(getStringValue(data, "deviceSn"));
        point.setUploadMethod(getStringValue(data, "uploadMethod"));
        
        // 轨迹专用字段
        point.setSpeed(getDoubleValue(data, "speed"));
        point.setBearing(getDoubleValue(data, "bearing"));
        point.setAccuracy(getDoubleValue(data, "accuracy"));
        point.setLocationType(getIntegerValue(data, "locationType"));
        
        return point;
    }

    // ============== 数据类型转换工具方法 ==============

    private Long getLongValue(Map<String, Object> data, String key) {
        Object value = data.get(key);
        if (value == null) return null;
        if (value instanceof Number) {
            return ((Number) value).longValue();
        }
        try {
            return Long.parseLong(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private Double getDoubleValue(Map<String, Object> data, String key) {
        Object value = data.get(key);
        if (value == null) return null;
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        try {
            return Double.parseDouble(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private Integer getIntegerValue(Map<String, Object> data, String key) {
        Object value = data.get(key);
        if (value == null) return null;
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        try {
            return Integer.parseInt(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private String getStringValue(Map<String, Object> data, String key) {
        Object value = data.get(key);
        return value != null ? value.toString() : null;
    }

    private java.time.LocalDateTime getTimestampValue(Map<String, Object> data, String key) {
        Object value = data.get(key);
        if (value == null) return null;
        
        if (value instanceof java.time.LocalDateTime) {
            return (java.time.LocalDateTime) value;
        }
        
        if (value instanceof java.sql.Timestamp) {
            return ((java.sql.Timestamp) value).toLocalDateTime();
        }
        
        if (value instanceof java.util.Date) {
            return java.time.LocalDateTime.ofInstant(
                ((java.util.Date) value).toInstant(),
                java.time.ZoneId.systemDefault()
            );
        }
        
        return null;
    }
}