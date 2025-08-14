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
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageAddDTO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageSearchDTO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageUpdateDTO;
import com.ljwx.modules.health.domain.vo.TDeviceMessageVO;
import com.ljwx.modules.health.facade.ITDeviceMessageFacade;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

/**
 *  Controller 控制层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName health.controller.com.ljwx.admin.TDeviceMessageController
 * @CreateTime 2024-10-24 - 13:07:24
 */

@RestController
@Tag(name = "")
@RequiredArgsConstructor
@RequestMapping("t_device_message")
public class TDeviceMessageController {

    @NonNull
    private ITDeviceMessageFacade tDeviceMessageFacade;

    @GetMapping("/page")
    @SaCheckPermission("t:device:message:page")
    @Operation(operationId = "1", summary = "获取列表")
    public Result<RPage<TDeviceMessageVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                                @Parameter(description = "查询对象") TDeviceMessageSearchDTO tDeviceMessageSearchDTO) {
        System.out.println("pageQuery: " + pageQuery);
        System.out.println("tDeviceMessageSearchDTO: " + tDeviceMessageSearchDTO.toString());
        return Result.data(tDeviceMessageFacade.listTDeviceMessagePage(pageQuery, tDeviceMessageSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:device:message:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<TDeviceMessageVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tDeviceMessageFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:device:message:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TDeviceMessageAddDTO tDeviceMessageAddDTO) {
        if (tDeviceMessageAddDTO.getSentTime() == null) {
            LocalDateTime now = LocalDateTime.now();
            tDeviceMessageAddDTO.setSentTime(now);
        }
        if (tDeviceMessageAddDTO.getReceivedTime() == null) {
            LocalDateTime now = LocalDateTime.now();
            tDeviceMessageAddDTO.setReceivedTime(now);
        }
        System.out.println("tDeviceMessageAddDTO: " + tDeviceMessageAddDTO.toString());
       
        return Result.status(tDeviceMessageFacade.add(tDeviceMessageAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:device:message:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TDeviceMessageUpdateDTO tDeviceMessageUpdateDTO) {
        return Result.status(tDeviceMessageFacade.update(tDeviceMessageUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:device:message:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TDeviceMessageDeleteDTO tDeviceMessageDeleteDTO) {
        return Result.status(tDeviceMessageFacade.batchDelete(tDeviceMessageDeleteDTO));
    }

}