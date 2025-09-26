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

package com.ljwx.modules.realtime.service;

import com.ljwx.modules.geofence.service.GeofenceCalculatorService;
import com.ljwx.modules.health.domain.vo.track.TrackPointVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 实时轨迹服务 (简化版 - 无WebSocket依赖)
 * 
 * 处理实时轨迹数据和围栏告警
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.realtime.service.RealTimeTrackService
 * @CreateTime 2024-01-15 - 16:10:00
 */

@Slf4j
@Service
public class RealTimeTrackService {
    
    @Autowired
    private GeofenceCalculatorService geofenceCalculatorService;
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    private static final String LAST_TRACK_KEY = "realtime:last_track:";
    
    // 在线用户缓存
    private final Map<Long, TrackPointVO> userLastTrackMap = new ConcurrentHashMap<>();

    /**
     * 处理新的轨迹点数据
     * 
     * @param trackPoint 新轨迹点
     */
    @Async
    public void processNewTrackPoint(TrackPointVO trackPoint) {
        log.debug("🔄 处理实时轨迹点: userId={}, 位置=({},{})", 
                trackPoint.getUserId(), trackPoint.getLatitude(), trackPoint.getLongitude());

        try {
            // 1. 围栏事件检测
            List<GeofenceCalculatorService.GeofenceEvent> geofenceEvents = 
                    geofenceCalculatorService.calculateGeofenceEvents(trackPoint);
            
            // 2. 更新缓存
            updateTrackCache(trackPoint);
            
            // 3. 记录围栏事件 (如果有)
            if (!geofenceEvents.isEmpty()) {
                logGeofenceEvents(trackPoint, geofenceEvents);
            }
            
        } catch (Exception e) {
            log.error("❌ 实时轨迹处理失败: userId={}, error={}", trackPoint.getUserId(), e.getMessage(), e);
        }
    }

    /**
     * 批量处理轨迹点
     */
    @Async
    public void processBatchTrackPoints(List<TrackPointVO> trackPoints) {
        log.info("🔄 批量处理实时轨迹: {} 个点", trackPoints.size());
        
        for (TrackPointVO trackPoint : trackPoints) {
            try {
                processNewTrackPoint(trackPoint);
            } catch (Exception e) {
                log.error("批量处理轨迹点失败: userId={}, error={}", trackPoint.getUserId(), e.getMessage());
            }
        }
    }

    /**
     * 获取用户最新轨迹
     */
    public TrackPointVO getUserLatestTrack(Long userId) {
        try {
            // 先从内存缓存获取
            TrackPointVO memoryTrack = userLastTrackMap.get(userId);
            if (memoryTrack != null) {
                return memoryTrack;
            }
            
            // 从Redis获取
            String cacheKey = LAST_TRACK_KEY + userId;
            Object cachedTrack = redisTemplate.opsForValue().get(cacheKey);
            if (cachedTrack instanceof TrackPointVO) {
                TrackPointVO redisTrack = (TrackPointVO) cachedTrack;
                userLastTrackMap.put(userId, redisTrack); // 回写内存缓存
                return redisTrack;
            }
            
        } catch (Exception e) {
            log.error("获取用户最新轨迹失败: userId={}, error={}", userId, e.getMessage());
        }
        
        return null;
    }

    /**
     * 获取多用户最新轨迹
     */
    public Map<Long, TrackPointVO> getMultiUserLatestTracks(List<Long> userIds) {
        Map<Long, TrackPointVO> result = new HashMap<>();
        
        for (Long userId : userIds) {
            TrackPointVO latestTrack = getUserLatestTrack(userId);
            if (latestTrack != null) {
                result.put(userId, latestTrack);
            }
        }
        
        return result;
    }

    /**
     * 清理用户轨迹缓存
     */
    public void clearUserTrackCache(Long userId) {
        try {
            userLastTrackMap.remove(userId);
            String cacheKey = LAST_TRACK_KEY + userId;
            redisTemplate.delete(cacheKey);
            log.info("🧹 清理用户轨迹缓存: userId={}", userId);
        } catch (Exception e) {
            log.error("清理用户轨迹缓存失败: userId={}, error={}", userId, e.getMessage());
        }
    }

    /**
     * 获取服务统计信息
     */
    public Map<String, Object> getServiceStatistics() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("cachedUsers", userLastTrackMap.size());
        stats.put("lastUpdateTime", LocalDateTime.now());
        return stats;
    }

    // ============== 私有辅助方法 ==============

    /**
     * 更新轨迹缓存
     */
    private void updateTrackCache(TrackPointVO trackPoint) {
        try {
            // 内存缓存
            userLastTrackMap.put(trackPoint.getUserId(), trackPoint);
            
            // Redis缓存
            String cacheKey = LAST_TRACK_KEY + trackPoint.getUserId();
            redisTemplate.opsForValue().set(cacheKey, trackPoint, java.time.Duration.ofHours(24));
        } catch (Exception e) {
            log.error("更新轨迹缓存失败: userId={}, error={}", trackPoint.getUserId(), e.getMessage());
        }
    }

    /**
     * 记录围栏事件
     */
    private void logGeofenceEvents(TrackPointVO trackPoint, List<GeofenceCalculatorService.GeofenceEvent> events) {
        for (GeofenceCalculatorService.GeofenceEvent event : events) {
            log.info("🚨 围栏事件: userId={}, fenceId={}, eventType={}, fenceName={}", 
                    trackPoint.getUserId(), event.getFenceId(), event.getEventType(), event.getFenceName());
            
            // 这里可以添加其他处理逻辑，如发送通知、保存到数据库等
            // 由于没有WebSocket，暂时只记录日志
        }
    }
}