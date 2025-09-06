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
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoAddDTO;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoUpdateDTO;
import com.ljwx.modules.health.domain.vo.TAlertInfoVO;
import com.ljwx.modules.health.facade.ITAlertInfoFacade;
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
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName health.controller.com.ljwx.admin.TAlertInfoController
 * @CreateTime 2024-10-27 - 20:37:23
 */

@RestController
@Tag(name = "")
@RequiredArgsConstructor
@RequestMapping("t_alert_info")
public class TAlertInfoController {

    @NonNull
    private ITAlertInfoFacade tAlertInfoFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:alert:info:page")
    @Operation(operationId = "1", summary = "获取列表")
    public Result<RPage<TAlertInfoVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                            @Parameter(description = "查询对象") TAlertInfoSearchDTO tAlertInfoSearchDTO) {
        return Result.data(tAlertInfoFacade.listTAlertInfoPage(pageQuery, tAlertInfoSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:alert:info:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<TAlertInfoVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tAlertInfoFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:alert:info:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TAlertInfoAddDTO tAlertInfoAddDTO) {
        return Result.status(tAlertInfoFacade.add(tAlertInfoAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:alert:info:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TAlertInfoUpdateDTO tAlertInfoUpdateDTO) {
        return Result.status(tAlertInfoFacade.update(tAlertInfoUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:alert:info:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TAlertInfoDeleteDTO tAlertInfoDeleteDTO) {
        return Result.status(tAlertInfoFacade.batchDelete(tAlertInfoDeleteDTO));
    }

    @PostMapping("/deal")
    @SaCheckPermission("t:alert:info:deal")
    @Operation(operationId = "6", summary = "一键处理告警")
    public Result<Boolean> dealAlert(@Parameter(description = "告警ID") @RequestParam Long alertId) {
        return Result.status(tAlertInfoFacade.dealAlert(alertId));
    }

    @PostMapping("/deal/batch")
    @SaCheckPermission("t:alert:info:deal")
    @Operation(operationId = "7", summary = "批量处理告警")
    public Result<String> batchDealAlert(@Parameter(description = "告警ID列表") @RequestBody TAlertInfoDeleteDTO alertIds) {
        return Result.data(tAlertInfoFacade.batchDealAlert(alertIds.getIds()));
    }

}