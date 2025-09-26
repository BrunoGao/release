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
import com.ljwx.modules.geofence.service.impl.TGeofenceServiceImpl;
import com.ljwx.modules.health.domain.vo.track.TrackPointVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 围栏计算引擎服务
 * 
 * 扩展现有的 TGeofenceServiceImpl，增加空间计算和告警功能
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.geofence.service.GeofenceCalculatorService
 * @CreateTime 2024-01-15 - 12:00:00
 */

@Slf4j
@Service("geofenceCalculatorService") 
public class GeofenceCalculatorService extends TGeofenceServiceImpl {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    private static final String GEOFENCE_GEO_KEY = "geofence:centers";
    private static final String USER_FENCE_STATUS_KEY = "user:fence:status:";
    
    /**
     * 检测轨迹点的围栏事件
     * 
     * @param trackPoint 轨迹点
     * @return 围栏事件列表
     */
    public List<GeofenceEvent> calculateGeofenceEvents(TrackPointVO trackPoint) {
        log.debug("🔍 检测围栏事件: userId={}, 位置=({},{})", 
                trackPoint.getUserId(), trackPoint.getLatitude(), trackPoint.getLongitude());

        List<GeofenceEvent> events = new ArrayList<>();
        
        try {
            // 1. 从Redis获取附近围栏 (地理索引预筛选，1公里范围)
            List<String> nearbyFenceIds = getNearbyFences(trackPoint, 1000);
            
            if (nearbyFenceIds.isEmpty()) {
                log.debug("📍 附近无围栏");
                return events;
            }
            
            log.debug("📍 找到附近围栏: {} 个", nearbyFenceIds.size());
            
            // 2. 批量获取围栏详情 (从数据库或缓存)
            List<TGeofence> fences = getFencesFromCache(nearbyFenceIds);
            
            // 3. 精确边界检测
            for (TGeofence fence : fences) {
                try {
                    GeofenceEvent event = checkFenceBoundary(trackPoint, fence);
                    if (event != null) {
                        events.add(event);
                        log.info("🚨 围栏事件: {} - 用户{} {} 围栏{}", 
                                event.getEventType(), trackPoint.getUserId(), 
                                event.getEventType().getDescription(), fence.getName());
                    }
                } catch (Exception e) {
                    log.error("围栏{}边界检测失败: {}", fence.getId(), e.getMessage());
                }
            }
            
        } catch (Exception e) {
            log.error("❌ 围栏事件检测失败: userId={}, error={}", trackPoint.getUserId(), e.getMessage(), e);
        }
        
        return events;
    }

    /**
     * 批量检测多个用户的围栏状态
     */
    public Map<Long, List<GeofenceEvent>> batchCalculateGeofenceEvents(List<TrackPointVO> trackPoints) {
        log.info("🔍 批量检测围栏事件: {} 个轨迹点", trackPoints.size());
        
        Map<Long, List<GeofenceEvent>> result = new HashMap<>();
        
        for (TrackPointVO trackPoint : trackPoints) {
            try {
                List<GeofenceEvent> events = calculateGeofenceEvents(trackPoint);
                if (!events.isEmpty()) {
                    result.put(trackPoint.getUserId(), events);
                }
            } catch (Exception e) {
                log.error("用户{}围栏检测失败: {}", trackPoint.getUserId(), e.getMessage());
            }
        }
        
        log.info("✅ 批量围栏检测完成: {}/{} 个用户有围栏事件", result.size(), trackPoints.size());
        return result;
    }

    /**
     * 初始化围栏地理索引 (简化版)
     */
    public void initializeGeofenceGeoIndex() {
        log.info("🚀 初始化围栏索引...");
        
        try {
            // 查询所有活跃围栏
            List<TGeofence> activeFences = list().stream()
                    .filter(fence -> Boolean.TRUE.equals(fence.getIsActive()))
                    .collect(Collectors.toList());
            
            log.info("📊 找到 {} 个活跃围栏", activeFences.size());
            
            // 简化实现：将围栏ID缓存到Redis Set中
            String cacheKey = GEOFENCE_GEO_KEY + "active_fences";
            redisTemplate.delete(cacheKey);
            
            for (TGeofence fence : activeFences) {
                if (fence.getCenterLng() != null && fence.getCenterLat() != null) {
                    redisTemplate.opsForSet().add(cacheKey, fence.getId().toString());
                }
            }
            
            log.info("✅ 围栏索引初始化完成: {} 个围栏", activeFences.size());
            
        } catch (Exception e) {
            log.error("❌ 围栏索引初始化失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 更新围栏地理索引 (简化版)
     */
    public void updateGeofenceGeoIndex(TGeofence fence) {
        try {
            String cacheKey = GEOFENCE_GEO_KEY + "active_fences";
            String fenceKey = fence.getId().toString();
            
            // 先移除旧的
            redisTemplate.opsForSet().remove(cacheKey, fenceKey);
            
            // 如果围栏活跃且有中心点，添加到缓存
            if (Boolean.TRUE.equals(fence.getIsActive()) && 
                fence.getCenterLng() != null && fence.getCenterLat() != null) {
                
                redisTemplate.opsForSet().add(cacheKey, fenceKey);
                
                log.info("📍 更新围栏{}索引: ({},{})", fence.getId(), 
                        fence.getCenterLng(), fence.getCenterLat());
            }
            
        } catch (Exception e) {
            log.error("围栏{}索引更新失败: {}", fence.getId(), e.getMessage());
        }
    }

    // ============== 私有辅助方法 ==============

    /**
     * 获取附近围栏 (简化版 - 查询所有活跃围栏)
     */
    private List<String> getNearbyFences(TrackPointVO trackPoint, double radiusMeters) {
        try {
            // 简化实现：获取所有活跃围栏ID
            // 在实际项目中，可以通过数据库查询或其他方式实现地理索引
            List<TGeofence> activeFences = list().stream()
                    .filter(fence -> Boolean.TRUE.equals(fence.getIsActive()))
                    .collect(Collectors.toList());
            
            return activeFences.stream()
                    .map(fence -> fence.getId().toString())
                    .collect(Collectors.toList());
                    
        } catch (Exception e) {
            log.error("获取附近围栏失败: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    /**
     * 批量获取围栏详情
     */
    private List<TGeofence> getFencesFromCache(List<String> fenceIds) {
        List<Long> ids = fenceIds.stream()
                .map(Long::parseLong)
                .collect(Collectors.toList());
        
        return listByIds(ids); // 使用父类方法批量查询
    }

    /**
     * 检测单个围栏边界
     */
    private GeofenceEvent checkFenceBoundary(TrackPointVO trackPoint, TGeofence fence) {
        // 获取用户当前在此围栏的状态
        String statusKey = USER_FENCE_STATUS_KEY + trackPoint.getUserId() + ":" + fence.getId();
        Boolean wasInside = (Boolean) redisTemplate.opsForValue().get(statusKey);
        if (wasInside == null) wasInside = false;
        
        // 计算当前是否在围栏内
        boolean isInside = isPointInsideFence(trackPoint, fence);
        
        GeofenceEvent event = null;
        
        // 检测状态变化
        if (!wasInside && isInside) {
            // 进入围栏
            if (Boolean.TRUE.equals(fence.getAlertOnEnter())) {
                event = createGeofenceEvent(trackPoint, fence, GeofenceEventType.ENTER);
            }
        } else if (wasInside && !isInside) {
            // 离开围栏
            if (Boolean.TRUE.equals(fence.getAlertOnExit())) {
                event = createGeofenceEvent(trackPoint, fence, GeofenceEventType.EXIT);
            }
        } else if (isInside) {
            // 持续在围栏内，检查停留时间
            if (Boolean.TRUE.equals(fence.getAlertOnStay())) {
                event = checkStayTimeout(trackPoint, fence, statusKey);
            }
        }
        
        // 更新状态
        redisTemplate.opsForValue().set(statusKey, isInside, 
                java.time.Duration.ofHours(24)); // 24小时过期
        
        return event;
    }

    /**
     * 判断点是否在围栏内
     */
    private boolean isPointInsideFence(TrackPointVO point, TGeofence fence) {
        double lng = point.getLongitude();
        double lat = point.getLatitude();
        
        switch (fence.getFenceType()) {
            case CIRCLE:
                return isPointInsideCircle(lng, lat, fence);
            case RECTANGLE:
                return isPointInsideRectangle(lng, lat, fence);
            case POLYGON:
                return isPointInsidePolygon(lng, lat, fence);
            default:
                log.warn("未知围栏类型: {}", fence.getFenceType());
                return false;
        }
    }

    /**
     * 圆形围栏判定
     */
    private boolean isPointInsideCircle(double lng, double lat, TGeofence fence) {
        if (fence.getCenterLng() == null || fence.getCenterLat() == null || fence.getRadius() == null) {
            return false;
        }
        
        double centerLng = fence.getCenterLng().doubleValue();
        double centerLat = fence.getCenterLat().doubleValue();
        double radius = fence.getRadius();
        
        double distance = calculateDistance(lat, lng, centerLat, centerLng);
        return distance <= radius;
    }

    /**
     * 矩形围栏判定 (简化实现)
     */
    private boolean isPointInsideRectangle(double lng, double lat, TGeofence fence) {
        // 简化实现：解析area字段中的矩形坐标
        // 实际项目中应该解析存储的矩形边界坐标
        try {
            String area = fence.getArea();
            if (area != null && area.startsWith("RECTANGLE")) {
                // 解析 RECTANGLE(minLng minLat, maxLng maxLat) 格式
                // 这里简化处理，实际需要更完整的解析逻辑
                return parseAndCheckRectangle(lng, lat, area);
            }
        } catch (Exception e) {
            log.error("矩形围栏解析失败: {}", e.getMessage());
        }
        return false;
    }

    /**
     * 多边形围栏判定 (射线法)
     */
    private boolean isPointInsidePolygon(double lng, double lat, TGeofence fence) {
        try {
            String area = fence.getArea();
            if (area == null) return false;
            
            List<double[]> polygon = parsePolygonCoordinates(area);
            if (polygon.size() < 3) return false;
            
            return pointInPolygon(lng, lat, polygon);
            
        } catch (Exception e) {
            log.error("多边形围栏解析失败: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 射线法判断点在多边形内
     */
    private boolean pointInPolygon(double x, double y, List<double[]> polygon) {
        int intersections = 0;
        int n = polygon.size();
        
        for (int i = 0; i < n; i++) {
            double[] p1 = polygon.get(i);
            double[] p2 = polygon.get((i + 1) % n);
            
            if (rayIntersectsSegment(x, y, p1[0], p1[1], p2[0], p2[1])) {
                intersections++;
            }
        }
        
        return intersections % 2 == 1;
    }

    private boolean rayIntersectsSegment(double x, double y, double x1, double y1, double x2, double y2) {
        if (y1 > y != y2 > y) {
            double intersectX = (x2 - x1) * (y - y1) / (y2 - y1) + x1;
            if (x < intersectX) {
                return true;
            }
        }
        return false;
    }

    /**
     * 解析多边形坐标
     */
    private List<double[]> parsePolygonCoordinates(String area) {
        List<double[]> coordinates = new ArrayList<>();
        
        // 简化解析逻辑，实际项目中应使用专门的GeoJSON/WKT解析库
        if (area.contains("POLYGON")) {
            // 解析 WKT 格式: POLYGON((lng lat, lng lat, ...))
            String coordsStr = area.substring(area.indexOf("((") + 2, area.lastIndexOf("))"));
            String[] pairs = coordsStr.split(",");
            
            for (String pair : pairs) {
                String[] coords = pair.trim().split("\\s+");
                if (coords.length == 2) {
                    double lng = Double.parseDouble(coords[0]);
                    double lat = Double.parseDouble(coords[1]);
                    coordinates.add(new double[]{lng, lat});
                }
            }
        }
        
        return coordinates;
    }

    private boolean parseAndCheckRectangle(double lng, double lat, String area) {
        // 简化实现，实际需要完整的矩形解析
        return false;
    }

    /**
     * 检查停留超时
     */
    private GeofenceEvent checkStayTimeout(TrackPointVO trackPoint, TGeofence fence, String statusKey) {
        String enterTimeKey = statusKey + ":enter_time";
        String enterTimeStr = (String) redisTemplate.opsForValue().get(enterTimeKey);
        
        if (enterTimeStr == null) {
            // 记录进入时间
            redisTemplate.opsForValue().set(enterTimeKey, 
                    trackPoint.getTimestamp().toString(), 
                    java.time.Duration.ofHours(24));
            return null;
        }
        
        try {
            LocalDateTime enterTime = LocalDateTime.parse(enterTimeStr);
            long stayMinutes = java.time.Duration.between(enterTime, trackPoint.getTimestamp()).toMinutes();
            
            if (stayMinutes >= fence.getStayDurationMinutes()) {
                // 清除进入时间，避免重复告警
                redisTemplate.delete(enterTimeKey);
                return createGeofenceEvent(trackPoint, fence, GeofenceEventType.STAY_TIMEOUT);
            }
        } catch (Exception e) {
            log.error("停留时间计算失败: {}", e.getMessage());
        }
        
        return null;
    }

    /**
     * 创建围栏事件
     */
    private GeofenceEvent createGeofenceEvent(TrackPointVO trackPoint, TGeofence fence, GeofenceEventType eventType) {
        GeofenceEvent event = new GeofenceEvent();
        event.setEventId(UUID.randomUUID().toString());
        event.setFenceId(fence.getId());
        event.setFenceName(fence.getName());
        event.setUserId(trackPoint.getUserId());
        event.setEventType(eventType);
        event.setEventTime(trackPoint.getTimestamp());
        event.setLocationLng(BigDecimal.valueOf(trackPoint.getLongitude()));
        event.setLocationLat(BigDecimal.valueOf(trackPoint.getLatitude()));
        event.setAlertLevel(fence.getAlertLevel());
        event.setDeviceId(trackPoint.getDeviceSn());
        
        return event;
    }

    /**
     * 计算两点间距离 (米)
     */
    private double calculateDistance(double lat1, double lng1, double lat2, double lng2) {
        double R = 6371000; // 地球半径（米）
        
        double lat1Rad = Math.toRadians(lat1);
        double lat2Rad = Math.toRadians(lat2);
        double deltaLat = Math.toRadians(lat2 - lat1);
        double deltaLng = Math.toRadians(lng2 - lng1);
        
        double a = Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
                   Math.cos(lat1Rad) * Math.cos(lat2Rad) *
                   Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        
        return R * c;
    }

    // ============== 内部类定义 ==============

    /**
     * 围栏事件
     */
    public static class GeofenceEvent {
        private String eventId;
        private Long fenceId;
        private String fenceName;
        private Long userId;
        private GeofenceEventType eventType;
        private LocalDateTime eventTime;
        private BigDecimal locationLng;
        private BigDecimal locationLat;
        private TGeofence.AlertLevel alertLevel;
        private String deviceId;

        // Getters and Setters
        public String getEventId() { return eventId; }
        public void setEventId(String eventId) { this.eventId = eventId; }
        
        public Long getFenceId() { return fenceId; }
        public void setFenceId(Long fenceId) { this.fenceId = fenceId; }
        
        public String getFenceName() { return fenceName; }
        public void setFenceName(String fenceName) { this.fenceName = fenceName; }
        
        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        
        public GeofenceEventType getEventType() { return eventType; }
        public void setEventType(GeofenceEventType eventType) { this.eventType = eventType; }
        
        public LocalDateTime getEventTime() { return eventTime; }
        public void setEventTime(LocalDateTime eventTime) { this.eventTime = eventTime; }
        
        public BigDecimal getLocationLng() { return locationLng; }
        public void setLocationLng(BigDecimal locationLng) { this.locationLng = locationLng; }
        
        public BigDecimal getLocationLat() { return locationLat; }
        public void setLocationLat(BigDecimal locationLat) { this.locationLat = locationLat; }
        
        public TGeofence.AlertLevel getAlertLevel() { return alertLevel; }
        public void setAlertLevel(TGeofence.AlertLevel alertLevel) { this.alertLevel = alertLevel; }
        
        public String getDeviceId() { return deviceId; }
        public void setDeviceId(String deviceId) { this.deviceId = deviceId; }
    }

    /**
     * 围栏事件类型
     */
    public enum GeofenceEventType {
        ENTER("进入围栏"),
        EXIT("离开围栏"),
        STAY_TIMEOUT("停留超时");

        private final String description;

        GeofenceEventType(String description) {
            this.description = description;
        }

        public String getDescription() {
            return description;
        }
    }
}