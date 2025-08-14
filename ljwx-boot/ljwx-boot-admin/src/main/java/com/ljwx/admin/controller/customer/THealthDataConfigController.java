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

package com.ljwx.admin.controller.customer;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigAddDTO;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigDeleteDTO;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigSearchDTO;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigUpdateDTO;
import com.ljwx.modules.customer.domain.vo.THealthDataConfigVO;
import com.ljwx.modules.customer.facade.ITHealthDataConfigFacade;
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
 * @ClassName customer.controller.com.ljwx.admin.THealthDataConfigController
 * @CreateTime 2024-12-29 - 15:02:31
 */

@RestController
@Tag(name = "")
@RequiredArgsConstructor
@RequestMapping("t_health_data_config")
public class THealthDataConfigController {

    @NonNull
    private ITHealthDataConfigFacade tHealthDataConfigFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:health:data:config:page")
    @Operation(operationId = "1", summary = "获取列表")
    public Result<RPage<THealthDataConfigVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                                   @Parameter(description = "查询对象") THealthDataConfigSearchDTO tHealthDataConfigSearchDTO) {
        return Result.data(tHealthDataConfigFacade.listTHealthDataConfigPage(pageQuery, tHealthDataConfigSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:health:data:config:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<THealthDataConfigVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tHealthDataConfigFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:health:data:config:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody THealthDataConfigAddDTO tHealthDataConfigAddDTO) {
        return Result.status(tHealthDataConfigFacade.add(tHealthDataConfigAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:health:data:config:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody THealthDataConfigUpdateDTO tHealthDataConfigUpdateDTO) {
        System.out.println("tHealthDataConfigUpdateDTO: " + tHealthDataConfigUpdateDTO.getId());
        return Result.status(tHealthDataConfigFacade.update(tHealthDataConfigUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:health:data:config:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody THealthDataConfigDeleteDTO tHealthDataConfigDeleteDTO) {
        return Result.status(tHealthDataConfigFacade.batchDelete(tHealthDataConfigDeleteDTO));
    }

}