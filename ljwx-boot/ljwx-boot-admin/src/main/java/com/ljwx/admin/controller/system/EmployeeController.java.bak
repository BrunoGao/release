package com.ljwx.admin.controller.system;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.dto.user.SysUserSearchDTO;
import com.ljwx.modules.system.domain.vo.SysUserVO;
import com.ljwx.modules.system.facade.ISysUserFacade;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 员工管理 Controller 控制层 - 排除管理员的员工统计
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.controller.system.EmployeeController
 * @CreateTime 2024-12-20
 */
@RestController
@Tag(name = "员工管理")
@RequiredArgsConstructor
@RequestMapping("/employee")
public class EmployeeController {

    @NonNull
    private ISysUserFacade sysUserFacade;

    @GetMapping("/page")
    @SaCheckPermission("employee:page")
    @Operation(operationId = "1", summary = "员工分页查询（排除管理员）")
    public Result<RPage<SysUserVO>> employeePage(
            @Parameter(description = "分页参数") PageQuery pageQuery,
            @Parameter(description = "查询参数") SysUserSearchDTO sysUserSearchDTO) {
        return Result.data(sysUserFacade.listNonAdminUsersPage(pageQuery, sysUserSearchDTO));
    }

    @GetMapping("/list")
    @SaCheckPermission("employee:list")
    @Operation(operationId = "2", summary = "获取所有员工列表（排除管理员）")
    public Result<RPage<SysUserVO>> employeeList(
            @Parameter(description = "查询参数") SysUserSearchDTO sysUserSearchDTO) {
        // 设置一个较大的分页参数获取所有员工
        PageQuery pageQuery = new PageQuery();
        pageQuery.setPageSize(10000);
        return Result.data(sysUserFacade.listNonAdminUsersPage(pageQuery, sysUserSearchDTO));
    }
} 