/*
 * All Rights Reserved: Copyright [2024] [ljwx (paynezhuang@gmail.com)]
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
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.RestController;
import lombok.NonNull;
import jakarta.validation.Valid;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;

import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailyAddDTO;
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailyDeleteDTO;
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailySearchDTO;
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailyUpdateDTO;
import com.ljwx.modules.health.domain.vo.THealthSummaryDailyVO;
import com.ljwx.modules.health.facade.ITHealthSummaryDailyFacade;
/**
 * 用户每日健康画像汇总表 Controller 控制层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.controller.health.THealthSummaryDailyController
 * @CreateTime 2025-05-01 - 21:33:15
 */

@RestController
@Tag(name = "用户每日健康画像汇总表")
@RequiredArgsConstructor
@RequestMapping("t_health_summary_daily")
public class THealthSummaryDailyController {

    @NonNull
    private ITHealthSummaryDailyFacade tHealthSummaryDailyFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:health:summary:daily:page")
    @Operation(operationId = "1", summary = "获取用户每日健康画像汇总表列表")
    public Result<RPage<THealthSummaryDailyVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                           @Parameter(description = "查询对象") THealthSummaryDailySearchDTO tHealthSummaryDailySearchDTO) {
        return Result.data(tHealthSummaryDailyFacade.listTHealthSummaryDailyPage(pageQuery, tHealthSummaryDailySearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:health:summary:daily:get")
    @Operation(operationId = "2", summary = "根据ID获取用户每日健康画像汇总表详细信息")
    public Result<THealthSummaryDailyVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tHealthSummaryDailyFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:health:summary:daily:add")
    @Operation(operationId = "3", summary = "新增用户每日健康画像汇总表")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody THealthSummaryDailyAddDTO tHealthSummaryDailyAddDTO) {
        return Result.status(tHealthSummaryDailyFacade.add(tHealthSummaryDailyAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:health:summary:daily:update")
    @Operation(operationId = "4", summary = "更新用户每日健康画像汇总表信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody THealthSummaryDailyUpdateDTO tHealthSummaryDailyUpdateDTO) {
        return Result.status(tHealthSummaryDailyFacade.update(tHealthSummaryDailyUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:health:summary:daily:delete")
    @Operation(operationId = "5", summary = "批量删除用户每日健康画像汇总表信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody THealthSummaryDailyDeleteDTO tHealthSummaryDailyDeleteDTO) {
        return Result.status(tHealthSummaryDailyFacade.batchDelete(tHealthSummaryDailyDeleteDTO));
    }

}