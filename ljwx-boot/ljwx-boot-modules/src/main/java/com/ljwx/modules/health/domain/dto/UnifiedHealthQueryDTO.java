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

package com.ljwx.modules.health.domain.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.NotNull;
import java.io.Serializable;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 统一健康数据查询 DTO
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO
 * @CreateTime 2025-09-08
 */
@Data
@Schema(name = "UnifiedHealthQueryDTO", description = "统一健康数据查询参数")
public class UnifiedHealthQueryDTO implements Serializable {

    private static final long serialVersionUID = 1L;

    @Schema(description = "客户ID", required = true)
    @NotNull(message = "客户ID不能为空")
    private Long customerId;

    @Schema(description = "组织ID")
    private Long orgId;

    @Schema(description = "用户ID")
    private Long userId;

    @Schema(description = "设备序列号")
    private String deviceSn;

    @Schema(description = "开始时间", required = true)
    @NotNull(message = "开始时间不能为空")
    private LocalDateTime startDate;

    @Schema(description = "结束时间", required = true)
    @NotNull(message = "结束时间不能为空")
    private LocalDateTime endDate;

    @Schema(description = "页码，从1开始")
    private Integer page = 1;

    @Schema(description = "每页大小")
    private Integer pageSize = 20;

    @Schema(description = "是否只返回最新记录")
    private Boolean latest = false;

    @Schema(description = "指定查询的指标名称，如：heart_rate, blood_oxygen等")
    private String metric;

    @Schema(description = "指定查询的多个指标名称")
    private List<String> metrics;

    @Schema(description = "是否启用缓存")
    private Boolean enableCache = true;

    @Schema(description = "排序字段，默认按时间升序")
    private String orderBy = "timestamp";

    @Schema(description = "排序方向：asc/desc")
    private String orderDirection = "asc";

    @Schema(description = "是否包含聚合统计")
    private Boolean includeStats = false;

    @Schema(description = "是否启用分表查询")
    private Boolean enableSharding = true;

    @Schema(description = "查询模式：all(全部数据)/daily(日汇总)/weekly(周汇总)")
    private String queryMode = "all";

    /**
     * 获取有效的页码
     */
    public Integer getValidPage() {
        return page != null && page > 0 ? page : 1;
    }

    /**
     * 获取有效的页面大小
     */
    public Integer getValidPageSize() {
        if (pageSize == null || pageSize <= 0) return 20;
        // 移除1000条的硬性限制，允许更大的页面大小用于数据处理
        return pageSize;
    }

    /**
     * 计算偏移量
     */
    public Integer getOffset() {
        return (getValidPage() - 1) * getValidPageSize();
    }

    /**
     * 是否需要快表查询
     */
    public boolean needsFastTableQuery() {
        if (metric != null) {
            return isFastTableMetric(metric);
        }
        
        if (metrics != null && !metrics.isEmpty()) {
            return metrics.stream().anyMatch(this::isFastTableMetric);
        }
        
        return false;
    }

    /**
     * 判断指标是否需要查询快表
     */
    private boolean isFastTableMetric(String metricName) {
        return switch (metricName) {
            case "sleep_data", "exercise_daily_data", "workout_data", 
                 "scientific_sleep_data" -> true;
            default -> false;
        };
    }

    /**
     * 是否需要周表查询
     */
    public boolean needsWeeklyTableQuery() {
        if (metric != null) {
            return "exercise_week_data".equals(metric);
        }
        
        if (metrics != null && !metrics.isEmpty()) {
            return metrics.contains("exercise_week_data");
        }
        
        return false;
    }

    /**
     * 获取查询时间跨度（天数）
     */
    public long getQueryDaysSpan() {
        return java.time.Duration.between(startDate, endDate).toDays();
    }

    /**
     * 是否跨月查询
     */
    public boolean isCrossMonthQuery() {
        return !startDate.toLocalDate().withDayOfMonth(1)
                .equals(endDate.toLocalDate().withDayOfMonth(1));
    }
}