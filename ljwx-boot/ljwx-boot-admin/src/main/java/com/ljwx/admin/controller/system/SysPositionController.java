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

package com.ljwx.admin.controller.system;

import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.stp.StpUtil;
import com.ljwx.common.api.Result;
import com.ljwx.common.domain.Options;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.dto.position.SysPositionAddDTO;
import com.ljwx.modules.system.domain.dto.position.SysPositionDeleteDTO;
import com.ljwx.modules.system.domain.dto.position.SysPositionSearchDTO;
import com.ljwx.modules.system.domain.dto.position.SysPositionUpdateDTO;
import com.ljwx.modules.system.domain.vo.SysPositionVO;
import com.ljwx.modules.system.facade.ISysPositionFacade;
import com.ljwx.modules.system.service.ISysUserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 岗位管理 Controller 控制层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName system.controller.com.ljwx.admin.SysPositionController
 * @CreateTime 2024-06-27 - 21:26:12
 */

@RestController
@Tag(name = "岗位管理")
@RequiredArgsConstructor
@RequestMapping("/sys_position")
public class SysPositionController {

    @NonNull
    private ISysPositionFacade sysPositionFacade;
    
    @NonNull
    private ISysUserService sysUserService;

    @GetMapping("/page")
    @SaCheckPermission("sys:position:page")
    @Operation(operationId = "1", summary = "获取岗位管理列表")
    public Result<RPage<SysPositionVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                             @Parameter(description = "查询对象") SysPositionSearchDTO sysPositionSearchDTO) {
        // 权限检查：超级管理员 + 顶级部门管理员 + 下属部门管理员
        if (!hasPositionViewPermission()) {
            return Result.failure("无权限访问岗位管理");
        }
        return Result.data(sysPositionFacade.listSysPositionPage(pageQuery, sysPositionSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("sys:position:get")
    @Operation(operationId = "2", summary = "根据ID获取岗位管理详细信息")
    public Result<SysPositionVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        // 权限检查：超级管理员 + 顶级部门管理员 + 下属部门管理员
        if (!hasPositionViewPermission()) {
            return Result.failure("无权限查看岗位详情");
        }
        return Result.data(sysPositionFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("sys:position:add")
    @Operation(operationId = "3", summary = "新增岗位管理")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody SysPositionAddDTO sysPositionAddDTO) {
        // 权限检查：超级管理员 + 顶级部门管理员
        if (!hasPositionEditPermission()) {
            return Result.failure("无权限新增岗位");
        }
        
        // 添加精度检查日志
        System.out.println("接收到的 orgId: " + sysPositionAddDTO.getOrgId());
        System.out.println("orgId 类型: " + (sysPositionAddDTO.getOrgId() != null ? sysPositionAddDTO.getOrgId().getClass().getSimpleName() : "null"));
        
        return Result.status(sysPositionFacade.add(sysPositionAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("sys:position:update")
    @Operation(operationId = "4", summary = "更新岗位管理信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody SysPositionUpdateDTO sysPositionUpdateDTO) {
        // 权限检查：超级管理员 + 顶级部门管理员
        if (!hasPositionEditPermission()) {
            return Result.failure("无权限修改岗位");
        }
        return Result.status(sysPositionFacade.update(sysPositionUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("sys:position:delete")
    @Operation(operationId = "5", summary = "批量删除岗位管理信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody SysPositionDeleteDTO sysPositionDeleteDTO) {
        // 权限检查：超级管理员 + 顶级部门管理员
        if (!hasPositionEditPermission()) {
            return Result.failure("无权限删除岗位");
        }
        return Result.status(sysPositionFacade.batchDelete(sysPositionDeleteDTO));
    }

    @GetMapping("/all_positions")
    @SaCheckPermission("sys:position:allPositions")
    @Operation(operationId = "7", summary = "获取所有岗位信息集合")
    public Result<List<Options<Long>>> queryAllPositionOptions(@Parameter(description = "组织ID") @RequestParam("orgId") Long orgId) {
        System.out.println("queryAllPositionOptions.orgId: " + orgId);
        return Result.data(sysPositionFacade.queryAllPositionListConvertOptions(orgId));
    }


    /**
     * 检查岗位查看权限
     * 权限：超级管理员 + 顶级部门管理员 + 下属部门管理员
     */
    private boolean hasPositionViewPermission() {
        try {
            Long userId = Long.parseLong(StpUtil.getLoginIdAsString());
            return sysUserService.isAdminUser(userId) || 
                   sysUserService.isTopLevelDeptAdmin(userId) || 
                   sysUserService.isSubDeptAdmin(userId);
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * 检查岗位编辑权限
     * 权限：超级管理员 + 顶级部门管理员
     */
    private boolean hasPositionEditPermission() {
        try {
            Long userId = Long.parseLong(StpUtil.getLoginIdAsString());
            return sysUserService.isAdminUser(userId) || 
                   sysUserService.isTopLevelDeptAdmin(userId);
        } catch (Exception e) {
            return false;
        }
    }
}