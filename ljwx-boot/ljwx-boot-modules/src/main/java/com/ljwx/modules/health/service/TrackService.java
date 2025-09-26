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
import com.ljwx.modules.health.domain.dto.track.TrackQueryDTO;
import com.ljwx.modules.health.domain.dto.track.TrackStatsDTO;
import com.ljwx.modules.health.domain.vo.track.TrackPointVO;
import com.ljwx.modules.health.domain.vo.track.TrackStatisticsVO;
import com.ljwx.modules.health.domain.vo.track.TrackStatsVO;
import com.ljwx.infrastructure.page.RPage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 轨迹服务
 * 
 * 重要约束: 所有健康数据查询必须通过 UnifiedHealthDataQueryService.queryHealthData 方法
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.TrackService
 * @CreateTime 2024-01-15 - 11:30:00
 */

@Slf4j
@Service
public class TrackService {

    @Autowired
    private UnifiedHealthDataQueryService unifiedHealthDataQueryService;

    /**
     * 查询历史轨迹
     * 
     * 严格遵循: 必须通过 UnifiedHealthDataQueryService.queryHealthData 查询数据
     * 
     * @param trackQueryDTO 轨迹查询参数
     * @return 轨迹点列表
     */
    public List<TrackPointVO> queryHistoryTrack(TrackQueryDTO trackQueryDTO) {
        log.info("🔍 查询历史轨迹: userId={}, 时间范围={} ~ {}", 
                trackQueryDTO.getUserId(), trackQueryDTO.getStartDate(), trackQueryDTO.getEndDate());

        try {
            // 1. 构建统一健康数据查询参数 (必须遵循的规范)
            UnifiedHealthQueryDTO queryDTO = buildUnifiedQueryDTO(trackQueryDTO);
            
            // 2. 通过统一查询服务获取数据 (关键约束点)
            Map<String, Object> healthDataResult = unifiedHealthDataQueryService.queryHealthData(queryDTO);
            
            // 3. 验证查询结果
            if (healthDataResult == null || !Boolean.TRUE.equals(healthDataResult.get("success"))) {
                log.warn("⚠️ 健康数据查询失败: {}", healthDataResult);
                return Collections.emptyList();
            }
            
            // 4. 提取基础数据
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> basicData = (List<Map<String, Object>>) healthDataResult.get("basicData");
            
            if (basicData == null || basicData.isEmpty()) {
                log.info("📊 未查询到轨迹数据");
                return Collections.emptyList();
            }
            
            log.info("📊 查询到 {} 条健康数据记录", basicData.size());
            
            // 5. 转换为轨迹点格式
            List<TrackPointVO> trackPoints = convertHealthDataToTrackPoints(basicData);
            
            // 6. 数据质量过滤
            trackPoints = filterTrackPoints(trackPoints, trackQueryDTO);
            
            // 7. 轨迹抽稀处理 (如果需要)
            if (trackQueryDTO.getSimplify() && trackPoints.size() > trackQueryDTO.getMaxPoints()) {
                trackPoints = simplifyTrackPoints(trackPoints, trackQueryDTO.getTolerance());
                log.info("🔧 轨迹抽稀: {} → {} 个点", basicData.size(), trackPoints.size());
            }
            
            // 8. 计算轨迹衍生数据
            calculateTrackMetrics(trackPoints);
            
            log.info("✅ 轨迹查询完成: 返回 {} 个有效轨迹点", trackPoints.size());
            return trackPoints;
            
        } catch (Exception e) {
            log.error("❌ 历史轨迹查询失败: userId={}, error={}", trackQueryDTO.getUserId(), e.getMessage(), e);
            return Collections.emptyList();
        }
    }

    /**
     * 批量查询多用户最近轨迹 - 用于实时监控
     */
    public Map<String, List<TrackPointVO>> queryMultiUserRecentTracks(List<Long> userIds, 
                                                                     Long customerId, 
                                                                     LocalDateTime since) {
        log.info("🔍 批量查询用户最近轨迹: {} 个用户", userIds.size());
        
        Map<String, List<TrackPointVO>> result = new HashMap<>();
        
        for (Long userId : userIds) {
            try {
                // 构建查询参数
                TrackQueryDTO trackQueryDTO = new TrackQueryDTO();
                trackQueryDTO.setUserId(userId);
                trackQueryDTO.setCustomerId(customerId);
                trackQueryDTO.setStartDate(since);
                trackQueryDTO.setEndDate(LocalDateTime.now());
                trackQueryDTO.setPageSize(50); // 最近50个点
                trackQueryDTO.setValidLocationOnly(true);
                
                // 查询用户轨迹
                List<TrackPointVO> trackPoints = queryHistoryTrack(trackQueryDTO);
                result.put(userId.toString(), trackPoints);
                
            } catch (Exception e) {
                log.error("查询用户{}轨迹失败: {}", userId, e.getMessage());
                result.put(userId.toString(), Collections.emptyList());
            }
        }
        
        log.info("✅ 批量轨迹查询完成: 成功查询 {}/{} 个用户", 
                result.size(), userIds.size());
        
        return result;
    }

    /**
     * 计算轨迹统计信息
     */
    public TrackStatisticsVO calculateTrackStatistics(Long userId, Long customerId, 
                                                     LocalDateTime startDate, LocalDateTime endDate) {
        log.info("📊 计算轨迹统计: userId={}, 时间范围={} ~ {}", userId, startDate, endDate);
        
        try {
            // 查询轨迹数据
            TrackQueryDTO trackQueryDTO = new TrackQueryDTO();
            trackQueryDTO.setUserId(userId);
            trackQueryDTO.setCustomerId(customerId);
            trackQueryDTO.setStartDate(startDate);
            trackQueryDTO.setEndDate(endDate);
            trackQueryDTO.setPageSize(10000); // 获取所有数据用于统计
            trackQueryDTO.setIncludeStayPoints(true);
            
            List<TrackPointVO> trackPoints = queryHistoryTrack(trackQueryDTO);
            
            if (trackPoints.isEmpty()) {
                return createEmptyStatistics(userId, startDate, endDate);
            }
            
            // 计算统计指标
            return calculateStatisticsFromTrackPoints(trackPoints, userId, startDate, endDate);
            
        } catch (Exception e) {
            log.error("❌ 轨迹统计计算失败: userId={}, error={}", userId, e.getMessage(), e);
            return createEmptyStatistics(userId, startDate, endDate);
        }
    }

    // ============== 私有辅助方法 ==============

    /**
     * 构建统一健康数据查询DTO
     */
    private UnifiedHealthQueryDTO buildUnifiedQueryDTO(TrackQueryDTO trackQueryDTO) {
        UnifiedHealthQueryDTO queryDTO = new UnifiedHealthQueryDTO();
        
        // 基础查询参数
        queryDTO.setUserId(trackQueryDTO.getUserId());
        queryDTO.setCustomerId(trackQueryDTO.getCustomerId());
        queryDTO.setOrgId(trackQueryDTO.getOrgId());
        queryDTO.setStartDate(trackQueryDTO.getStartDate());
        queryDTO.setEndDate(trackQueryDTO.getEndDate());
        queryDTO.setPage(trackQueryDTO.getPage());
        queryDTO.setPageSize(trackQueryDTO.getPageSize());
        
        return queryDTO;
    }

    /**
     * 健康数据转轨迹点
     * 
     * 关键转换逻辑: 将 UnifiedHealthDataQueryService 返回的 Map 数据转换为 TrackPointVO
     */
    private List<TrackPointVO> convertHealthDataToTrackPoints(List<Map<String, Object>> healthData) {
        return healthData.stream()
                .filter(data -> isValidLocationData(data)) // 过滤有效位置数据
                .map(this::mapToTrackPoint)
                .sorted(Comparator.comparing(TrackPointVO::getTimestamp)) // 按时间排序
                .collect(Collectors.toList());
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
    private TrackPointVO mapToTrackPoint(Map<String, Object> data) {
        TrackPointVO point = new TrackPointVO();
        
        // 基础字段 (现有字段)
        point.setUserId(getLongValue(data, "userId"));
        point.setUserName(getStringValue(data, "userName"));
        point.setLongitude(getDoubleValue(data, "longitude"));
        point.setLatitude(getDoubleValue(data, "latitude"));
        point.setAltitude(getDoubleValue(data, "altitude"));
        point.setTimestamp(getTimestampValue(data, "timestamp"));
        point.setDeviceSn(getStringValue(data, "deviceSn"));
        point.setUploadMethod(getStringValue(data, "uploadMethod"));
        
        // 新增轨迹字段
        point.setSpeed(getDoubleValue(data, "speed"));
        point.setBearing(getDoubleValue(data, "bearing"));
        point.setAccuracy(getDoubleValue(data, "accuracy"));
        point.setLocationType(getIntegerValue(data, "locationType"));
        
        // 计算衍生字段 (后续计算)
        point.setCumulativeDistance(0.0);
        point.setSegmentDistance(0.0);
        point.setTimeInterval(0);
        point.setIsStayPoint(false);
        
        return point;
    }

    /**
     * 轨迹点质量过滤
     */
    private List<TrackPointVO> filterTrackPoints(List<TrackPointVO> trackPoints, TrackQueryDTO queryDTO) {
        return trackPoints.stream()
                .filter(point -> filterBySpeed(point, queryDTO))
                .filter(point -> filterByAccuracy(point, queryDTO))
                .filter(point -> filterByLocationType(point, queryDTO))
                .collect(Collectors.toList());
    }

    private boolean filterBySpeed(TrackPointVO point, TrackQueryDTO queryDTO) {
        if (point.getSpeed() == null) return true;
        return point.getSpeed() >= queryDTO.getMinSpeed() && 
               point.getSpeed() <= queryDTO.getMaxSpeed();
    }

    private boolean filterByAccuracy(TrackPointVO point, TrackQueryDTO queryDTO) {
        if (point.getAccuracy() == null) return true;
        return point.getAccuracy() <= queryDTO.getMaxAccuracy();
    }

    private boolean filterByLocationType(TrackPointVO point, TrackQueryDTO queryDTO) {
        if (point.getLocationType() == null || queryDTO.getLocationTypes() == null) return true;
        return Arrays.stream(queryDTO.getLocationTypes().split(","))
                .anyMatch(type -> type.trim().equals(point.getLocationType().toString()));
    }

    /**
     * 轨迹抽稀算法 (Douglas-Peucker)
     */
    private List<TrackPointVO> simplifyTrackPoints(List<TrackPointVO> trackPoints, Double tolerance) {
        if (trackPoints.size() <= 2) return trackPoints;
        
        // 简化实现：按距离阈值抽稀
        List<TrackPointVO> simplified = new ArrayList<>();
        simplified.add(trackPoints.get(0)); // 保留起点
        
        TrackPointVO lastPoint = trackPoints.get(0);
        for (int i = 1; i < trackPoints.size() - 1; i++) {
            TrackPointVO currentPoint = trackPoints.get(i);
            double distance = calculateDistance(lastPoint, currentPoint);
            
            if (distance >= tolerance) {
                simplified.add(currentPoint);
                lastPoint = currentPoint;
            }
        }
        
        simplified.add(trackPoints.get(trackPoints.size() - 1)); // 保留终点
        return simplified;
    }

    /**
     * 计算轨迹衍生指标
     */
    private void calculateTrackMetrics(List<TrackPointVO> trackPoints) {
        if (trackPoints.size() < 2) return;
        
        double cumulativeDistance = 0;
        
        for (int i = 1; i < trackPoints.size(); i++) {
            TrackPointVO prev = trackPoints.get(i - 1);
            TrackPointVO curr = trackPoints.get(i);
            
            // 计算分段距离
            double segmentDistance = calculateDistance(prev, curr);
            curr.setSegmentDistance(segmentDistance);
            
            // 计算累计距离
            cumulativeDistance += segmentDistance / 1000; // 转换为公里
            curr.setCumulativeDistance(cumulativeDistance);
            
            // 计算时间间隔
            if (prev.getTimestamp() != null && curr.getTimestamp() != null) {
                long seconds = java.time.Duration.between(prev.getTimestamp(), curr.getTimestamp()).getSeconds();
                curr.setTimeInterval((int) seconds);
            }
        }
    }

    /**
     * 计算两点间距离 (米)
     */
    private double calculateDistance(TrackPointVO p1, TrackPointVO p2) {
        if (p1.getLatitude() == null || p1.getLongitude() == null ||
            p2.getLatitude() == null || p2.getLongitude() == null) {
            return 0;
        }
        
        double lat1 = Math.toRadians(p1.getLatitude());
        double lat2 = Math.toRadians(p2.getLatitude());
        double deltaLat = Math.toRadians(p2.getLatitude() - p1.getLatitude());
        double deltaLng = Math.toRadians(p2.getLongitude() - p1.getLongitude());
        
        double a = Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
                   Math.cos(lat1) * Math.cos(lat2) *
                   Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        
        return 6371000 * c; // 地球半径 6371km
    }

    /**
     * 从统计数据计算轨迹统计信息
     */
    private TrackStatisticsVO calculateStatisticsFromTrackPoints(List<TrackPointVO> trackPoints, 
                                                               Long userId, 
                                                               LocalDateTime startTime, 
                                                               LocalDateTime endTime) {
        TrackStatisticsVO statistics = new TrackStatisticsVO();
        
        // 基础信息
        statistics.setUserId(userId);
        statistics.setUserName(trackPoints.get(0).getUserName());
        statistics.setStartTime(startTime);
        statistics.setEndTime(endTime);
        
        // 点数统计
        statistics.setTotalPoints(trackPoints.size());
        statistics.setValidPoints(trackPoints.size()); // 已经过滤
        
        // 距离统计
        TrackPointVO lastPoint = trackPoints.get(trackPoints.size() - 1);
        statistics.setTotalDistance(lastPoint.getCumulativeDistance());
        
        // 速度统计
        List<Double> speeds = trackPoints.stream()
                .map(TrackPointVO::getSpeed)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
        
        if (!speeds.isEmpty()) {
            statistics.setAverageSpeed(speeds.stream().mapToDouble(Double::doubleValue).average().orElse(0));
            statistics.setMaxSpeed(speeds.stream().mapToDouble(Double::doubleValue).max().orElse(0));
            statistics.setMinSpeed(speeds.stream().mapToDouble(Double::doubleValue).min().orElse(0));
        }
        
        // 时间统计
        if (trackPoints.size() >= 2) {
            long durationSeconds = java.time.Duration.between(
                trackPoints.get(0).getTimestamp(),
                trackPoints.get(trackPoints.size() - 1).getTimestamp()
            ).getSeconds();
            statistics.setTotalDuration((int) (durationSeconds / 60)); // 转换为分钟
        }
        
        // 定位质量统计
        calculateLocationQualityStats(trackPoints, statistics);
        
        // 边界信息
        calculateBoundingBox(trackPoints, statistics);
        
        return statistics;
    }

    private void calculateLocationQualityStats(List<TrackPointVO> trackPoints, TrackStatisticsVO statistics) {
        List<Double> accuracies = trackPoints.stream()
                .map(TrackPointVO::getAccuracy)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
        
        if (!accuracies.isEmpty()) {
            statistics.setAverageAccuracy(accuracies.stream().mapToDouble(Double::doubleValue).average().orElse(0));
            
            long highAccuracyCount = accuracies.stream()
                    .mapToLong(acc -> acc <= 10 ? 1 : 0)
                    .sum();
            statistics.setHighAccuracyRate((double) highAccuracyCount / accuracies.size() * 100);
        }
        
        // 定位类型统计
        Map<Integer, Long> locationTypeCount = trackPoints.stream()
                .filter(p -> p.getLocationType() != null)
                .collect(Collectors.groupingBy(TrackPointVO::getLocationType, Collectors.counting()));
        
        statistics.setGpsPoints(locationTypeCount.getOrDefault(1, 0L).intValue());
        statistics.setWifiPoints(locationTypeCount.getOrDefault(2, 0L).intValue());
        statistics.setCellPoints(locationTypeCount.getOrDefault(3, 0L).intValue());
    }

    private void calculateBoundingBox(List<TrackPointVO> trackPoints, TrackStatisticsVO statistics) {
        DoubleSummaryStatistics latStats = trackPoints.stream()
                .mapToDouble(TrackPointVO::getLatitude)
                .summaryStatistics();
        
        DoubleSummaryStatistics lngStats = trackPoints.stream()
                .mapToDouble(TrackPointVO::getLongitude)
                .summaryStatistics();
        
        TrackStatisticsVO.BoundingBoxVO boundingBox = new TrackStatisticsVO.BoundingBoxVO();
        boundingBox.setMinLat(latStats.getMin());
        boundingBox.setMaxLat(latStats.getMax());
        boundingBox.setMinLng(lngStats.getMin());
        boundingBox.setMaxLng(lngStats.getMax());
        boundingBox.setCenterLat((latStats.getMin() + latStats.getMax()) / 2);
        boundingBox.setCenterLng((lngStats.getMin() + lngStats.getMax()) / 2);
        boundingBox.setSpanLat(latStats.getMax() - latStats.getMin());
        boundingBox.setSpanLng(lngStats.getMax() - lngStats.getMin());
        
        statistics.setBoundingBox(boundingBox);
        
        // 设置起点终点
        statistics.setStartPoint(trackPoints.get(0));
        statistics.setEndPoint(trackPoints.get(trackPoints.size() - 1));
    }

    private TrackStatisticsVO createEmptyStatistics(Long userId, LocalDateTime startTime, LocalDateTime endTime) {
        TrackStatisticsVO statistics = new TrackStatisticsVO();
        statistics.setUserId(userId);
        statistics.setStartTime(startTime);
        statistics.setEndTime(endTime);
        statistics.setTotalPoints(0);
        statistics.setValidPoints(0);
        statistics.setTotalDistance(0.0);
        return statistics;
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
    
    /**
     * 分页查询轨迹
     */
    public RPage<TrackPointVO> queryTracksPage(Object pageQuery, TrackQueryDTO trackQueryDTO) {
        log.info("分页查询轨迹: {}", trackQueryDTO);
        
        try {
            // 这里应该实现真正的分页查询逻辑
            return new RPage<>(1L, 20L, Collections.emptyList(), 0L, 0L);
        } catch (Exception e) {
            log.error("分页查询轨迹失败: {}", e.getMessage());
            return new RPage<>(1L, 20L, Collections.emptyList(), 0L, 0L);
        }
    }
    
    /**
     * 查询轨迹统计
     */
    public TrackStatsVO queryTrackStats(TrackStatsDTO trackStatsDTO) {
        log.info("查询轨迹统计: {}", trackStatsDTO);
        
        try {
            // 这里应该实现统计查询逻辑
            return new TrackStatsVO();
        } catch (Exception e) {
            log.error("查询轨迹统计失败: {}", e.getMessage());
            return new TrackStatsVO();
        }
    }
    
    /**
     * 批量查询轨迹
     */
    public Map<Long, List<TrackPointVO>> batchQueryTracks(List<TrackQueryDTO> trackQueryDTOs) {
        log.info("批量查询轨迹: {} 个", trackQueryDTOs.size());
        
        try {
            // 这里应该实现批量查询逻辑
            Map<Long, List<TrackPointVO>> result = new HashMap<>();
            for (TrackQueryDTO dto : trackQueryDTOs) {
                result.put(dto.getUserId(), Collections.emptyList());
            }
            return result;
        } catch (Exception e) {
            log.error("批量查询轨迹失败: {}", e.getMessage());
            return Collections.emptyMap();
        }
    }
    
    /**
     * 查询实时轨迹
     */
    public List<TrackPointVO> queryRealtimeTrack(TrackQueryDTO trackQueryDTO) {
        log.info("查询实时轨迹: {}", trackQueryDTO);
        
        try {
            // 这里应该实现实时轨迹查询逻辑
            return Collections.emptyList();
        } catch (Exception e) {
            log.error("查询实时轨迹失败: {}", e.getMessage());
            return Collections.emptyList();
        }
    }
    
    /**
     * 查询简化轨迹
     */
    public List<TrackPointVO> querySimplifiedTrack(TrackQueryDTO trackQueryDTO) {
        log.info("查询简化轨迹: {}", trackQueryDTO);
        
        try {
            // 这里应该实现简化轨迹查询逻辑
            return Collections.emptyList();
        } catch (Exception e) {
            log.error("查询简化轨迹失败: {}", e.getMessage());
            return Collections.emptyList();
        }
    }
}