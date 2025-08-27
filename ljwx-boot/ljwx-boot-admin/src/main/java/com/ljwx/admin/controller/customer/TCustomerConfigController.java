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

package com.ljwx.admin.controller.customer;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigAddDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigDeleteDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigSearchDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigUpdateDTO;
import com.ljwx.modules.customer.domain.vo.TCustomerConfigVO;
import com.ljwx.modules.customer.facade.ITCustomerConfigFacade;
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
 * @ClassName customer.controller.com.ljwx.admin.TCustomerConfigController
 * @CreateTime 2024-12-29 - 15:33:30
 */

@RestController
@Tag(name = "")
@RequiredArgsConstructor
@RequestMapping("t_customer_config")
public class TCustomerConfigController {

    @NonNull
    private ITCustomerConfigFacade tCustomerConfigFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:customer:config:page")
    @Operation(operationId = "1", summary = "获取列表")
    public Result<RPage<TCustomerConfigVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                                 @Parameter(description = "查询对象") TCustomerConfigSearchDTO tCustomerConfigSearchDTO) {
        return Result.data(tCustomerConfigFacade.listTCustomerConfigPage(pageQuery, tCustomerConfigSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:customer:config:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<TCustomerConfigVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tCustomerConfigFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:customer:config:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TCustomerConfigAddDTO tCustomerConfigAddDTO) {
        return Result.status(tCustomerConfigFacade.add(tCustomerConfigAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:customer:config:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TCustomerConfigUpdateDTO tCustomerConfigUpdateDTO) {
        return Result.status(tCustomerConfigFacade.update(tCustomerConfigUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:customer:config:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TCustomerConfigDeleteDTO tCustomerConfigDeleteDTO) {
        return Result.status(tCustomerConfigFacade.batchDelete(tCustomerConfigDeleteDTO));
    }

}