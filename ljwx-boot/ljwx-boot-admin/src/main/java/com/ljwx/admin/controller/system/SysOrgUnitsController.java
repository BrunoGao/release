package com.ljwx.admin.controller.system;

import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.stp.StpUtil;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.dto.org.units.SysOrgUnitsAddDTO;
import com.ljwx.modules.system.domain.dto.org.units.SysOrgUnitsDeleteDTO;
import com.ljwx.modules.system.domain.dto.org.units.SysOrgUnitsSearchDTO;
import com.ljwx.modules.system.domain.dto.org.units.SysOrgUnitsUpdateDTO;
import com.ljwx.modules.system.domain.dto.org.units.DepartmentDeletePreCheckDTO;
import com.ljwx.modules.system.domain.vo.SysOrgUnitsTreeVO;
import com.ljwx.modules.system.domain.vo.SysOrgUnitsVO;
import com.ljwx.modules.system.facade.ISysOrgUnitsFacade;
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
 * 组织/部门/子部门管理 Controller 控制层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName system.controller.com.ljwx.admin.SysOrgUnitsController
 * @CreateTime 2024-07-16 - 16:35:30
 */

@RestController
@Tag(name = "租户/部门管理")
@RequiredArgsConstructor
@RequestMapping("/sys_org_units")
public class SysOrgUnitsController {

    @NonNull
    private ISysOrgUnitsFacade sysOrgUnitsFacade;
    
    @NonNull
    private ISysUserService sysUserService;

    @GetMapping("/page")
    @SaCheckPermission("sys:org:units:page")
    @Operation(operationId = "1", summary = "获取租户/部门列表")
    public Result<RPage<SysOrgUnitsTreeVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                                 @Parameter(description = "查询对象") SysOrgUnitsSearchDTO sysOrgUnitsSearchDTO) {
        System.out.println("🔍 SysOrgUnitsController.page - 接收到查询参数:");
        System.out.println("  id: " + sysOrgUnitsSearchDTO.getId());
        System.out.println("  name: " + sysOrgUnitsSearchDTO.getName());
        System.out.println("  status: " + sysOrgUnitsSearchDTO.getStatus());
        System.out.println("  customerId: " + sysOrgUnitsSearchDTO.getCustomerId());
        return Result.data(sysOrgUnitsFacade.listSysOrgUnitsPage(pageQuery, sysOrgUnitsSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("sys:org:units:get")
    @Operation(operationId = "2", summary = "根据ID获取租户/部门详细信息")
    public Result<SysOrgUnitsVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(sysOrgUnitsFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("sys:org:units:add")
    @Operation(operationId = "3", summary = "新增租户/部门")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody SysOrgUnitsAddDTO sysOrgUnitsAddDTO) {
        // 检查权限：只有管理员才能创建顶级租户（parentId为0或1）
        if (isTopLevelOrg(sysOrgUnitsAddDTO.getParentId()) && !isAdminUser()) {
            return Result.failure("只有管理员才能创建租户，普通用户只能在自己的租户下创建部门");
        }
        
        return Result.status(sysOrgUnitsFacade.add(sysOrgUnitsAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("sys:org:units:update")
    @Operation(operationId = "4", summary = "更新租户/部门信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody SysOrgUnitsUpdateDTO sysOrgUnitsUpdateDTO) {
        return Result.status(sysOrgUnitsFacade.update(sysOrgUnitsUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("sys:org:units:delete")
    @Operation(operationId = "5", summary = "批量删除部门信息（不包括租户级别）")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody SysOrgUnitsDeleteDTO sysOrgUnitsDeleteDTO) {
        // 检查是否包含租户级别的删除操作
        if (containsTenantLevelDeletion(sysOrgUnitsDeleteDTO.getIds())) {
            return Result.failure("组织管理页面不允许删除租户级别的组织，请在客户配置页面进行租户管理操作");
        }
        
        return Result.status(sysOrgUnitsFacade.batchDelete(sysOrgUnitsDeleteDTO));
    }

    @GetMapping("/tree")
    @SaCheckPermission("sys:org:units:tree")
    @Operation(operationId = "6", summary = "获取租户/部门树结构数据")
    public Result<List<SysOrgUnitsTreeVO>> tree(@RequestParam(value = "id", required = false) Long id,
                                               @RequestParam(value = "customerId", required = false) Long customerId) {
        System.out.println("🔍 SysOrgUnitsController.tree - 接收到参数:");
        System.out.println("  id: " + id);
        System.out.println("  customerId: " + customerId);
        
        if (customerId != null) {
            // 如果传入了customerId，返回该租户下属的部门树结构（不包含租户节点本身）
            System.out.println("  返回租户下属部门树结构，customerId: " + customerId);
            return Result.data(sysOrgUnitsFacade.queryTenantDepartmentsTree(customerId));
        } else {
            // 否则使用原有逻辑
            System.out.println("  使用原有树结构查询，id: " + id);
            return Result.data(sysOrgUnitsFacade.queryAllOrgUnitsListConvertToTree(id));
        }
    }

    @PostMapping("/delete-precheck")
    @SaCheckPermission("sys:org:units:delete")
    @Operation(operationId = "7", summary = "删除部门前置检查 - 分析影响的用户和设备（不包括租户级别）")
    public Result<DepartmentDeletePreCheckDTO> deletePreCheck(@Parameter(description = "删除对象") @RequestBody SysOrgUnitsDeleteDTO sysOrgUnitsDeleteDTO) {
        // 检查是否包含租户级别的删除操作
        if (containsTenantLevelDeletion(sysOrgUnitsDeleteDTO.getIds())) {
            return Result.failure("组织管理页面不允许删除租户级别的组织，请在客户配置页面进行租户管理操作");
        }
        
        return Result.data(sysOrgUnitsFacade.deletePreCheck(sysOrgUnitsDeleteDTO));
    }

    @DeleteMapping("/cascade-delete")
    @SaCheckPermission("sys:org:units:delete")
    @Operation(operationId = "8", summary = "级联删除部门 - 包含用户和设备释放（不包括租户级别）")
    public Result<Boolean> cascadeDelete(@Parameter(description = "删除对象") @RequestBody SysOrgUnitsDeleteDTO sysOrgUnitsDeleteDTO) {
        // 检查是否包含租户级别的删除操作
        if (containsTenantLevelDeletion(sysOrgUnitsDeleteDTO.getIds())) {
            return Result.failure("组织管理页面不允许删除租户级别的组织，请在客户配置页面进行租户管理操作");
        }
        
        return Result.status(sysOrgUnitsFacade.cascadeDelete(sysOrgUnitsDeleteDTO));
    }
    
    /**
     * 判断是否是顶级组织（租户）
     */
    private boolean isTopLevelOrg(Long parentId) {
        return parentId == null || parentId == 0L || parentId == 1L;
    }
    
    /**
     * 判断当前用户是否是管理员
     */
    private boolean isAdminUser() {
        try {
            String loginId = StpUtil.getLoginIdAsString();
            return sysUserService.isAdminUser(Long.parseLong(loginId));
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * 检查删除列表中是否包含租户级别的组织
     * 租户级别组织的特征：parentId 为 0 或 1
     */
    private boolean containsTenantLevelDeletion(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return false;
        }
        
        try {
            // 查询这些ID对应的组织信息，检查是否有租户级别的
            for (Long id : ids) {
                var orgUnit = sysOrgUnitsFacade.get(id);
                if (orgUnit != null && isTopLevelOrg(orgUnit.getParentId())) {
                    return true; // 发现租户级别的组织
                }
            }
            return false;
        } catch (Exception e) {
            // 如果查询失败，为了安全起见，禁止删除操作
            return true;
        }
    }

}