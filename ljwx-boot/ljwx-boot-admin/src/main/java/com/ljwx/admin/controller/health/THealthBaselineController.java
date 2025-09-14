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
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import com.ljwx.modules.health.service.HealthDataService;

import jakarta.validation.Valid;
import java.util.Map;

/**
 * 健康基线管理 Controller 控制层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.controller.health.THealthBaselineController
 * @CreateTime 2025-09-11
 */

@Slf4j
@RestController
@Tag(name = "健康基线管理")
@RequiredArgsConstructor
@RequestMapping("t_health_baseline")
public class THealthBaselineController {

    @NonNull
    private HealthDataService healthDataService;

    @GetMapping("/page")
    @SaCheckPermission("t:health:baseline:page")
    @Operation(operationId = "1", summary = "获取健康基线列表")
    public Result<RPage<Map<String, Object>>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                                   @RequestParam(value = "customerId", required = false) Long customerId,
                                                   @RequestParam(value = "orgId", required = false) Long orgId,
                                                   @RequestParam(value = "userId", required = false) Long userId,
                                                   @RequestParam(value = "startDate", required = false) Long startDate,
                                                   @RequestParam(value = "endDate", required = false) Long endDate,
                                                   @RequestParam(value = "dataType", required = false) String dataType) {
        log.info("获取健康基线列表 - page: {}, size: {}, customerId: {}, orgId: {}, userId: {}, startDate: {}, endDate: {}, dataType: {}", 
                pageQuery.getPage(), pageQuery.getPageSize(), customerId, orgId, userId, startDate, endDate, dataType);
        
        RPage<Map<String, Object>> result = healthDataService.getHealthBaselinePage(pageQuery, customerId, orgId, userId, startDate, endDate, dataType);
        return Result.data(result);
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:health:baseline:get")
    @Operation(operationId = "2", summary = "根据ID获取健康基线详细信息")
    public Result<Map<String, Object>> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        log.info("获取健康基线详情 - id: {}", id);
        
        Map<String, Object> result = healthDataService.getHealthBaselineById(id);
        if (result == null) {
            return Result.failure("数据不存在");
        }
        return Result.data(result);
    }

    @PostMapping("/")
    @SaCheckPermission("t:health:baseline:add")
    @Operation(operationId = "3", summary = "新增健康基线")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody Map<String, Object> data) {
        log.info("新增健康基线 - data: {}", data);
        return Result.data(true);
    }

    @PutMapping("/")
    @SaCheckPermission("t:health:baseline:update")
    @Operation(operationId = "4", summary = "修改健康基线")
    public Result<Boolean> update(@Parameter(description = "修改对象") @RequestBody Map<String, Object> data) {
        log.info("修改健康基线 - data: {}", data);
        return Result.data(true);
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:health:baseline:delete")
    @Operation(operationId = "5", summary = "删除健康基线")
    public Result<Boolean> delete(@Parameter(description = "删除对象") @RequestBody Map<String, Object> data) {
        log.info("删除健康基线 - data: {}", data);
        return Result.data(true);
    }
}