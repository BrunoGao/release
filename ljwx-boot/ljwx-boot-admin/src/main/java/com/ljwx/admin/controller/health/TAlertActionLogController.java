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
import com.ljwx.modules.health.domain.dto.alert.action.log.TAlertActionLogAddDTO;
import com.ljwx.modules.health.domain.dto.alert.action.log.TAlertActionLogDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.action.log.TAlertActionLogSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.action.log.TAlertActionLogUpdateDTO;
import com.ljwx.modules.health.domain.vo.TAlertActionLogVO;
import com.ljwx.modules.health.facade.ITAlertActionLogFacade;
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
 * @ClassName health.controller.com.ljwx.admin.TAlertActionLogController
 * @CreateTime 2024-10-27 - 21:37:48
 */

@RestController
@Tag(name = "")
@RequiredArgsConstructor
@RequestMapping("t_alert_action_log")
public class TAlertActionLogController {

    @NonNull
    private ITAlertActionLogFacade tAlertActionLogFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:alert:action:log:page")
    @Operation(operationId = "1", summary = "获取列表")
    public Result<RPage<TAlertActionLogVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                                 @Parameter(description = "查询对象") TAlertActionLogSearchDTO tAlertActionLogSearchDTO) {
        return Result.data(tAlertActionLogFacade.listTAlertActionLogPage(pageQuery, tAlertActionLogSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:alert:action:log:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<TAlertActionLogVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tAlertActionLogFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:alert:action:log:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TAlertActionLogAddDTO tAlertActionLogAddDTO) {
        return Result.status(tAlertActionLogFacade.add(tAlertActionLogAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:alert:action:log:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TAlertActionLogUpdateDTO tAlertActionLogUpdateDTO) {
        return Result.status(tAlertActionLogFacade.update(tAlertActionLogUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:alert:action:log:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TAlertActionLogDeleteDTO tAlertActionLogDeleteDTO) {
        return Result.status(tAlertActionLogFacade.batchDelete(tAlertActionLogDeleteDTO));
    }

}