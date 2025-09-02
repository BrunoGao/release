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
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesAddDTO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesUpdateDTO;
import com.ljwx.modules.health.domain.vo.TAlertRulesVO;
import com.ljwx.modules.health.facade.ITAlertRulesFacade;
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
 * @ClassName com.ljwx.admin.controller.alert.TAlertRulesController
 * @CreateTime 2025-02-13 - 14:59:34
 */

@RestController
@Tag(name = "")
@RequiredArgsConstructor
@RequestMapping("t_alert_rules")
public class TAlertRulesController {

    @NonNull
    private ITAlertRulesFacade tAlertRulesFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:alert:rules:page")
    @Operation(operationId = "1", summary = "获取列表")
    public Result<RPage<TAlertRulesVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                             @Parameter(description = "查询对象") TAlertRulesSearchDTO tAlertRulesSearchDTO) {
        return Result.data(tAlertRulesFacade.listTAlertRulesPage(pageQuery, tAlertRulesSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:alert:rules:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<TAlertRulesVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tAlertRulesFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:alert:rules:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TAlertRulesAddDTO tAlertRulesAddDTO) {
        return Result.status(tAlertRulesFacade.add(tAlertRulesAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:alert:rules:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TAlertRulesUpdateDTO tAlertRulesUpdateDTO) {
        return Result.status(tAlertRulesFacade.update(tAlertRulesUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:alert:rules:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TAlertRulesDeleteDTO tAlertRulesDeleteDTO) {
        return Result.status(tAlertRulesFacade.batchDelete(tAlertRulesDeleteDTO));
    }

}