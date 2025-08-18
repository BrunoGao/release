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
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigAddDTO;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigUpdateDTO;
import com.ljwx.modules.health.domain.vo.TWechatAlertConfigVO;
import com.ljwx.modules.health.facade.ITWechatAlertConfigFacade;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * Table to store WeChat alert configuration Controller 控制层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName health.controller.com.ljwx.admin.TWechatAlertConfigController
 * @CreateTime 2025-01-02 - 13:17:05
 */

@RestController
@Tag(name = "Table to store WeChat alert configuration")
@RequiredArgsConstructor
@RequestMapping("t_wechat_alarm_config")
public class TWechatAlertConfigController {

    @NonNull
    private ITWechatAlertConfigFacade tWechatAlertConfigFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:wechat:alarm:config:page")
    @Operation(operationId = "1", summary = "获取Table to store WeChat alert configuration列表")
    public Result<RPage<TWechatAlertConfigVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                                    @Parameter(description = "查询对象") TWechatAlertConfigSearchDTO tWechatAlertConfigSearchDTO) {
        return Result.data(tWechatAlertConfigFacade.listTWechatAlertConfigPage(pageQuery, tWechatAlertConfigSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:wechat:alarm:config:get")
    @Operation(operationId = "2", summary = "根据ID获取Table to store WeChat alert configuration详细信息")
    public Result<TWechatAlertConfigVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tWechatAlertConfigFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:wechat:alarm:config:add")
    @Operation(operationId = "3", summary = "新增Table to store WeChat alert configuration")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TWechatAlertConfigAddDTO tWechatAlertConfigAddDTO) {
        return Result.status(tWechatAlertConfigFacade.add(tWechatAlertConfigAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:wechat:alarm:config:update")
    @Operation(operationId = "4", summary = "更新Table to store WeChat alert configuration信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TWechatAlertConfigUpdateDTO tWechatAlertConfigUpdateDTO) {
        return Result.status(tWechatAlertConfigFacade.update(tWechatAlertConfigUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:wechat:alarm:config:delete")
    @Operation(operationId = "5", summary = "批量删除Table to store WeChat alert configuration信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TWechatAlertConfigDeleteDTO tWechatAlertConfigDeleteDTO) {
        return Result.status(tWechatAlertConfigFacade.batchDelete(tWechatAlertConfigDeleteDTO));
    }

}