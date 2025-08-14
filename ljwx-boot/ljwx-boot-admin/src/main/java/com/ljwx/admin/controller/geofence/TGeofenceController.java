/*
 * All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
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

package com.ljwx.admin.controller.geofence;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceAddDTO;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceDeleteDTO;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceSearchDTO;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceUpdateDTO;
import com.ljwx.modules.geofence.domain.vo.TGeofenceVO;
import com.ljwx.modules.geofence.facade.ITGeofenceFacade;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 *  Controller 控制层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName geofence.controller.com.ljwx.admin.TGeofenceController
 * @CreateTime 2025-01-07 - 19:44:06
 */

@RestController
@Tag(name = "")
@RequiredArgsConstructor
@RequestMapping("t_geofence")
public class TGeofenceController {

    @NonNull
    private ITGeofenceFacade tGeofenceFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:geofence:page")
    @Operation(operationId = "1", summary = "获取列表")
    public Result<RPage<TGeofenceVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                           @Parameter(description = "查询对象") TGeofenceSearchDTO tGeofenceSearchDTO) {
        return Result.data(tGeofenceFacade.listTGeofencePage(pageQuery, tGeofenceSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:geofence:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<TGeofenceVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tGeofenceFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:geofence:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TGeofenceAddDTO tGeofenceAddDTO) {
        return Result.status(tGeofenceFacade.add(tGeofenceAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:geofence:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TGeofenceUpdateDTO tGeofenceUpdateDTO) {
        return Result.status(tGeofenceFacade.update(tGeofenceUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:geofence:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TGeofenceDeleteDTO tGeofenceDeleteDTO) {
        return Result.status(tGeofenceFacade.batchDelete(tGeofenceDeleteDTO));
    }
}