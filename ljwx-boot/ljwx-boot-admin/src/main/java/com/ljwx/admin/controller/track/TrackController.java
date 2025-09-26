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

package com.ljwx.admin.controller.track;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.modules.health.domain.dto.track.TrackQueryDTO;
import com.ljwx.modules.health.domain.dto.track.TrackStatsDTO;
import com.ljwx.modules.health.domain.vo.track.TrackPointVO;
import com.ljwx.modules.health.domain.vo.track.TrackStatsVO;
import com.ljwx.modules.health.service.TrackService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 运动轨迹 Controller 控制层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.controller.track.TrackController
 * @CreateTime 2025-01-27 - 14:00:00
 */

@Slf4j
@RestController
@Tag(name = "运动轨迹管理", description = "运动轨迹查询、分析和统计功能")
@RequiredArgsConstructor
@RequestMapping("/track")
public class TrackController {

    @NonNull
    private TrackService trackService;

    @PostMapping("/history")
    @SaCheckPermission("track:history:query")
    @Operation(operationId = "1", summary = "查询历史轨迹")
    public Result<List<TrackPointVO>> queryHistoryTrack(
            @Parameter(description = "轨迹查询对象", required = true) 
            @Valid @RequestBody TrackQueryDTO trackQueryDTO) {
        try {
            List<TrackPointVO> trackPoints = trackService.queryHistoryTrack(trackQueryDTO);
            log.info("📍 轨迹查询成功: 用户{}, 设备{}, 点数{}", 
                    trackQueryDTO.getUserId(), trackQueryDTO.getDeviceSn(), trackPoints.size());
            return Result.data(trackPoints);
        } catch (Exception e) {
            log.error("❌ 轨迹查询失败: {}", e.getMessage(), e);
            return Result.failure("轨迹查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/realtime")
    @SaCheckPermission("track:realtime:query")
    @Operation(operationId = "2", summary = "查询实时轨迹")
    public Result<List<TrackPointVO>> queryRealtimeTrack(
            @Parameter(description = "实时轨迹查询对象", required = true) 
            @Valid @RequestBody TrackQueryDTO trackQueryDTO) {
        try {
            List<TrackPointVO> trackPoints = trackService.queryRealtimeTrack(trackQueryDTO);
            log.info("📍 实时轨迹查询成功: 用户{}, 设备{}, 点数{}", 
                    trackQueryDTO.getUserId(), trackQueryDTO.getDeviceSn(), trackPoints.size());
            return Result.data(trackPoints);
        } catch (Exception e) {
            log.error("❌ 实时轨迹查询失败: {}", e.getMessage(), e);
            return Result.failure("实时轨迹查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/simplified")
    @SaCheckPermission("track:simplified:query")
    @Operation(operationId = "3", summary = "查询简化轨迹")
    public Result<List<TrackPointVO>> querySimplifiedTrack(
            @Parameter(description = "轨迹查询对象", required = true) 
            @Valid @RequestBody TrackQueryDTO trackQueryDTO) {
        try {
            List<TrackPointVO> trackPoints = trackService.querySimplifiedTrack(trackQueryDTO);
            log.info("📍 简化轨迹查询成功: 用户{}, 设备{}, 点数{}", 
                    trackQueryDTO.getUserId(), trackQueryDTO.getDeviceSn(), trackPoints.size());
            return Result.data(trackPoints);
        } catch (Exception e) {
            log.error("❌ 简化轨迹查询失败: {}", e.getMessage(), e);
            return Result.failure("简化轨迹查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/stats")
    @SaCheckPermission("track:stats:query")
    @Operation(operationId = "4", summary = "查询轨迹统计")
    public Result<TrackStatsVO> queryTrackStats(
            @Parameter(description = "轨迹统计查询对象", required = true) 
            @Valid @RequestBody TrackStatsDTO trackStatsDTO) {
        try {
            TrackStatsVO stats = trackService.queryTrackStats(trackStatsDTO);
            log.info("📊 轨迹统计查询成功: 用户{}, 设备{}", 
                    trackStatsDTO.getUserId(), trackStatsDTO.getDeviceSn());
            return Result.data(stats);
        } catch (Exception e) {
            log.error("❌ 轨迹统计查询失败: {}", e.getMessage(), e);
            return Result.failure("轨迹统计查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/batch")
    @SaCheckPermission("track:batch:query")
    @Operation(operationId = "5", summary = "批量查询多用户轨迹")
    public Result<Map<Long, List<TrackPointVO>>> batchQueryTracks(
            @Parameter(description = "批量轨迹查询对象", required = true) 
            @Valid @RequestBody List<TrackQueryDTO> trackQueries) {
        try {
            Map<Long, List<TrackPointVO>> result = trackService.batchQueryTracks(trackQueries);
            log.info("📍 批量轨迹查询成功: {} 个用户", result.size());
            return Result.data(result);
        } catch (Exception e) {
            log.error("❌ 批量轨迹查询失败: {}", e.getMessage(), e);
            return Result.failure("批量轨迹查询失败: " + e.getMessage());
        }
    }

    @GetMapping("/user/{userId}/latest")
    @SaCheckPermission("track:latest:query")
    @Operation(operationId = "6", summary = "获取用户最新位置")
    public Result<TrackPointVO> getLatestLocation(
            @Parameter(description = "用户ID", required = true) 
            @PathVariable Long userId,
            @Parameter(description = "设备序列号") 
            @RequestParam(required = false) String deviceSn) {
        try {
            TrackQueryDTO queryDTO = new TrackQueryDTO();
            queryDTO.setUserId(userId);
            queryDTO.setDeviceSn(deviceSn);
            queryDTO.setPageSize(1);
            
            List<TrackPointVO> trackPoints = trackService.queryRealtimeTrack(queryDTO);
            TrackPointVO latestPoint = trackPoints.isEmpty() ? null : trackPoints.get(0);
            
            log.info("📍 最新位置查询成功: 用户{}, 设备{}", userId, deviceSn);
            return Result.data(latestPoint);
        } catch (Exception e) {
            log.error("❌ 最新位置查询失败: {}", e.getMessage(), e);
            return Result.failure("最新位置查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/playback")
    @SaCheckPermission("track:playback:query")
    @Operation(operationId = "7", summary = "轨迹回放数据")
    public Result<List<TrackPointVO>> queryTrackPlayback(
            @Parameter(description = "轨迹查询对象", required = true) 
            @Valid @RequestBody TrackQueryDTO trackQueryDTO) {
        try {
            // 为回放优化查询参数
            trackQueryDTO.setSimplifyTolerance(10.0); // 10米精度简化
            trackQueryDTO.setOrderBy("timestamp");
            trackQueryDTO.setSortDirection("ASC");
            
            List<TrackPointVO> trackPoints = trackService.querySimplifiedTrack(trackQueryDTO);
            log.info("📍 轨迹回放数据查询成功: 用户{}, 设备{}, 点数{}", 
                    trackQueryDTO.getUserId(), trackQueryDTO.getDeviceSn(), trackPoints.size());
            return Result.data(trackPoints);
        } catch (Exception e) {
            log.error("❌ 轨迹回放数据查询失败: {}", e.getMessage(), e);
            return Result.failure("轨迹回放数据查询失败: " + e.getMessage());
        }
    }
}