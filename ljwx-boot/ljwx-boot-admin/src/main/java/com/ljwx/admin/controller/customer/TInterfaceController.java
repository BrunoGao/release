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
import com.ljwx.modules.customer.domain.dto.interfaces.TInterfaceAddDTO;
import com.ljwx.modules.customer.domain.dto.interfaces.TInterfaceDeleteDTO;
import com.ljwx.modules.customer.domain.dto.interfaces.TInterfaceSearchDTO;
import com.ljwx.modules.customer.domain.dto.interfaces.TInterfaceUpdateDTO;
import com.ljwx.modules.customer.domain.vo.TInterfaceVO;
import com.ljwx.modules.customer.facade.ITInterfaceFacade;
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
 * @ClassName customer.controller.com.ljwx.admin.TInterfaceController
 * @CreateTime 2024-12-29 - 15:33:49
 */

@RestController
@Tag(name = "")
@RequiredArgsConstructor
@RequestMapping("t_interface")
public class TInterfaceController {

    @NonNull
    private ITInterfaceFacade tInterfaceFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:interface:page")
    @Operation(operationId = "1", summary = "获取列表")
    public Result<RPage<TInterfaceVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                            @Parameter(description = "查询对象") TInterfaceSearchDTO tInterfaceSearchDTO) {
        return Result.data(tInterfaceFacade.listTInterfacePage(pageQuery, tInterfaceSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:interface:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<TInterfaceVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tInterfaceFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:interface:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TInterfaceAddDTO tInterfaceAddDTO) {
        return Result.status(tInterfaceFacade.add(tInterfaceAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:interface:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TInterfaceUpdateDTO tInterfaceUpdateDTO) {
        return Result.status(tInterfaceFacade.update(tInterfaceUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:interface:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TInterfaceDeleteDTO tInterfaceDeleteDTO) {
        return Result.status(tInterfaceFacade.batchDelete(tInterfaceDeleteDTO));
    }

}