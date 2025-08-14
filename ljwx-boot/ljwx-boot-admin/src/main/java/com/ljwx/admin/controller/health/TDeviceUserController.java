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

package com.ljwx.admin.controller.health;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserAddDTO;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserSearchDTO;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserUpdateDTO;
import com.ljwx.modules.health.domain.vo.TDeviceUserVO;
import com.ljwx.modules.health.facade.ITDeviceUserFacade;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 设备与用户关联表 Controller 控制层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName health.controller.com.ljwx.admin.TDeviceUserController
 * @CreateTime 2025-01-03 - 15:12:29
 */

@RestController
@Tag(name = "设备与用户关联表")
@RequiredArgsConstructor
@RequestMapping("t_device_user")
public class TDeviceUserController {

    @NonNull
    private ITDeviceUserFacade tDeviceUserFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:device:user:page")
    @Operation(operationId = "1", summary = "获取设备与用户关联表列表")
    public Result<RPage<TDeviceUserVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                             @Parameter(description = "查询对象") TDeviceUserSearchDTO tDeviceUserSearchDTO) {
        return Result.data(tDeviceUserFacade.listTDeviceUserPage(pageQuery, tDeviceUserSearchDTO));
    }


    @GetMapping("/{id}")
    @SaCheckPermission("t:device:user:get")
    @Operation(operationId = "2", summary = "根据ID获取设备与用户关联表详细信息")
    public Result<TDeviceUserVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tDeviceUserFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:device:user:add")
    @Operation(operationId = "3", summary = "新增设备与用户关联表")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TDeviceUserAddDTO tDeviceUserAddDTO) {
        return Result.status(tDeviceUserFacade.add(tDeviceUserAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:device:user:update")
    @Operation(operationId = "4", summary = "更新设备与用户关联表信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TDeviceUserUpdateDTO tDeviceUserUpdateDTO) {
        return Result.status(tDeviceUserFacade.update(tDeviceUserUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:device:user:delete")
    @Operation(operationId = "5", summary = "批量删除设备与用户关联表信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TDeviceUserDeleteDTO tDeviceUserDeleteDTO) {
        return Result.status(tDeviceUserFacade.batchDelete(tDeviceUserDeleteDTO));
    }

}