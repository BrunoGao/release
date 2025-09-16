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

package com.ljwx.admin.controller.health;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataAddDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataDeleteDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataSearchDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataUpdateDTO;
import com.ljwx.modules.health.domain.vo.TUserHealthDataVO;
import com.ljwx.modules.health.domain.vo.HealthDataPageVO;
import com.ljwx.modules.health.facade.ITUserHealthDataFacade;
import com.ljwx.modules.health.service.ITUserHealthDataService;
import com.ljwx.modules.health.service.UnifiedHealthDataQueryService;
import com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.format.DateTimeParseException;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.Arrays;
/**
 *  Controller 控制层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName health.controller.com.ljwx.admin.TUserHealthDataController
 * @CreateTime 2024-12-15 - 22:04:51
 */
@Slf4j
@RestController
@Tag(name = "")
@RequiredArgsConstructor
@RequestMapping("t_user_health_data")
public class TUserHealthDataController {

    @NonNull
    private ITUserHealthDataFacade tUserHealthDataFacade;

    @NonNull
    private ITUserHealthDataService tUserHealthDataService;
    
    @NonNull
    private UnifiedHealthDataQueryService unifiedHealthDataQueryService;
    

    

    @Operation(summary = "获取用户健康信息")
    @GetMapping(value = "/getUserHealthData")
    public HttpEntity<Object> getUserHealthData(@RequestParam("orgId") String orgId,
                                                @RequestParam(value = "userId", required = false) String userId,
                                                @RequestParam("startDate") Long startDateStr,
                                                @RequestParam("endDate") Long endDateStr,
                                                @RequestParam("timeType") String timeType) {
        try {
           LocalDateTime startDateTime = Instant.ofEpochMilli(startDateStr)
                                              .atZone(ZoneId.systemDefault())
                                              .toLocalDateTime();
        LocalDateTime endDateTime = Instant.ofEpochMilli(endDateStr)
                                            .atZone(ZoneId.systemDefault())
                                            .toLocalDateTime();

        // Step 2: Adjust startDateTime to start of day and endDateTime to end of day
        LocalDateTime adjustedStartDateTime = startDateTime.toLocalDate().atStartOfDay();
        LocalDateTime adjustedEndDateTime = endDateTime.toLocalDate().atTime(LocalTime.MAX);

        // Step 3: Log or verify conversion (optional)
        System.out.println("Adjusted Start DateTime: " + adjustedStartDateTime);
        System.out.println("Adjusted End DateTime: " + adjustedEndDateTime);

            // Pass the new parameters to the service method
            return tUserHealthDataService.getUserHealthData(orgId, userId, adjustedStartDateTime, adjustedEndDateTime, timeType);

        } catch (DateTimeParseException e) {
            log.error("Error parsing dates: startDate={}, endDate={}, exception={}", startDateStr, endDateStr, e.getMessage(), e);
            return new ResponseEntity<>("Invalid date format", HttpStatus.BAD_REQUEST);
        } catch (Exception e) {
            log.error("Unexpected error: startDate={}, endDate={}, userId={}, exception={}", startDateStr, endDateStr, userId, e);
            return new ResponseEntity<>("An error occurred", HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping("/page")
    @SaCheckPermission("t:user:health:data:page")
    @Operation(operationId = "1", summary = "获取健康数据列表", 
              description = "表格图表分离架构：返回基础数据(表格)和独立的daily/weekly数据(图表)")
    public Result<Map<String,Object>> page(PageQuery pageQuery, TUserHealthDataSearchDTO dto) {
        try {
            // 转换为统一查询DTO
            UnifiedHealthQueryDTO queryDTO = new UnifiedHealthQueryDTO();
            queryDTO.setPage(pageQuery.getCurrent());
            queryDTO.setPageSize(pageQuery.getSize());
            queryDTO.setCustomerId(dto.getCustomerId());
            queryDTO.setUserId(dto.getUserId());
            queryDTO.setOrgId(dto.getOrgId());
            queryDTO.setDeviceSn(dto.getDeviceSn());
            
            // 时间戳转换
            if (dto.getStartDate() != null) {
                queryDTO.setStartDate(LocalDateTime.ofInstant(Instant.ofEpochMilli(dto.getStartDate()), ZoneId.systemDefault()));
            }
            if (dto.getEndDate() != null) {
                queryDTO.setEndDate(LocalDateTime.ofInstant(Instant.ofEpochMilli(dto.getEndDate()), ZoneId.systemDefault()));
            }
            
            // 使用统一健康数据查询服务（表格图表分离架构）
            Map<String, Object> result = unifiedHealthDataQueryService.queryHealthData(queryDTO);
            
            // 构建返回格式
            Map<String, Object> data = new HashMap<>();
            data.put("page", result.get("page"));
            data.put("pageSize", result.get("pageSize"));
            data.put("pages", result.get("total").equals(0) ? 0 : 
                (int)Math.ceil((double)(Long)result.get("total") / (Integer)result.get("pageSize")));
            data.put("total", result.get("total"));
            data.put("records", result.get("basicData")); // 基础表格数据
            
            // 独立的图表数据
            data.put("dailyData", result.get("dailyData")); // 独立daily数据用于图表
            data.put("weeklyData", result.get("weeklyData")); // 独立weekly数据用于图表
            data.put("supportedFields", result.get("supportedFields")); // 字段配置
            
            // 构建动态列配置（基于Basic Enabled Metrics）
            @SuppressWarnings("unchecked")
            Map<String, String> supportedFields = (Map<String, String>) result.get("supportedFields");
            data.put("columns", buildDynamicColumns(supportedFields));
            
            log.info("✅ 健康数据页面查询完成: 基础数据{}条, daily数据{}项, weekly数据{}项", 
                    ((List<?>)result.get("basicData")).size(),
                    ((Map<?, ?>)result.get("dailyData")).size(),
                    ((Map<?, ?>)result.get("weeklyData")).size());
            
            return Result.data(data);
            
        } catch (Exception e) {
            log.error("❌ 健康数据页面查询失败: {}", e.getMessage(), e);
            return Result.failure("查询失败: " + e.getMessage());
        }
    }
    
    /**
     * 构建动态列配置 - 基于Basic Enabled Metrics
     */
    private List<Map<String, Object>> buildDynamicColumns(Map<String, String> supportedFields) {
        List<Map<String, Object>> columns = new ArrayList<>();
        
        // 固定基础列
        columns.add(Map.of("dataIndex", "id", "title", "ID", "width", 80, "key", "id"));
        columns.add(Map.of("dataIndex", "userName", "title", "用户名称", "width", 120, "key", "userName"));
        columns.add(Map.of("dataIndex", "orgName", "title", "部门名称", "width", 150, "key", "orgName"));
        columns.add(Map.of("dataIndex", "deviceSn", "title", "设备序列号", "width", 120, "key", "deviceSn"));
        columns.add(Map.of("dataIndex", "timestamp", "title", "时间戳", "width", 160, "key", "timestamp"));
        
        // 根据配置动态添加健康指标列
        for (Map.Entry<String, String> entry : supportedFields.entrySet()) {
            String fieldKey = entry.getKey();
            String fieldType = entry.getValue();
            
            // 只添加快字段（非慢字段）
            if (!"slow".equals(fieldType)) {
                Map<String, Object> column = createHealthColumn(fieldKey);
                if (column != null) {
                    columns.add(column);
                }
            }
        }
        
        return columns;
    }
    
    /**
     * 创建健康指标列配置
     */
    private Map<String, Object> createHealthColumn(String fieldKey) {
        return switch (fieldKey) {
            case "heartRate", "heart_rate" -> Map.of("dataIndex", "heartRate", "title", "心率", "width", 80, "key", "heartRate");
            case "bloodOxygen", "blood_oxygen" -> Map.of("dataIndex", "bloodOxygen", "title", "血氧", "width", 80, "key", "bloodOxygen");
            case "temperature", "body_temperature" -> Map.of("dataIndex", "temperature", "title", "体温", "width", 80, "key", "temperature");
            case "pressureHigh", "pressure_high" -> Map.of("dataIndex", "pressureHigh", "title", "收缩压", "width", 80, "key", "pressureHigh");
            case "pressureLow", "pressure_low" -> Map.of("dataIndex", "pressureLow", "title", "舒张压", "width", 80, "key", "pressureLow");
            case "stress" -> Map.of("dataIndex", "stress", "title", "压力", "width", 80, "key", "stress");
            case "step" -> Map.of("dataIndex", "step", "title", "步数", "width", 100, "key", "step");
            case "calorie" -> Map.of("dataIndex", "calorie", "title", "卡路里", "width", 100, "key", "calorie");
            case "distance" -> Map.of("dataIndex", "distance", "title", "距离", "width", 100, "key", "distance");
            case "location" -> Map.of("dataIndex", "coordinates", "title", "坐标", "width", 200, "key", "coordinates", "render", "coordinates");
            default -> null;
        };
    }

    @GetMapping("/{id}")
    //@SaCheckPermission("t:user:health:data:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<TUserHealthDataVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tUserHealthDataFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:user:health:data:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TUserHealthDataAddDTO tUserHealthDataAddDTO) {
        return Result.status(tUserHealthDataFacade.add(tUserHealthDataAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:user:health:data:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TUserHealthDataUpdateDTO tUserHealthDataUpdateDTO) {
        return Result.status(tUserHealthDataFacade.update(tUserHealthDataUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:user:health:data:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TUserHealthDataDeleteDTO tUserHealthDataDeleteDTO) {
        return Result.status(tUserHealthDataFacade.batchDelete(tUserHealthDataDeleteDTO));
    }

}