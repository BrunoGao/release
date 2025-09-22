package com.ljwx.admin.controller.system;

import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaIgnore;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.dto.user.*;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.domain.vo.SysUserMapVO;
import com.ljwx.modules.system.domain.vo.SysUserResponsibilitiesVO;
import com.ljwx.modules.system.domain.vo.SysUserVO;
import com.ljwx.modules.system.facade.ISysUserFacade;
import com.ljwx.modules.system.service.ISysUserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 系统管理 - 用户管理 Controller 控制层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName system.controller.com.ljwx.admin.SysUserController
 * @CreateTime 2023/7/6 - 14:25
 */

@Slf4j
@RestController
@Tag(name = "用户管理")
@RequiredArgsConstructor
@RequestMapping("/sys_user")
public class SysUserController {

    @NonNull
    private ISysUserFacade sysUserFacade;

    @NonNull
    private ISysUserService sysUserService;

    @GetMapping("/page")
    @SaCheckPermission("sys:user:page")
    @Operation(operationId = "1", summary = "获取用户管理列表")
    public Result<RPage<SysUserVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                         @Parameter(description = "查询对象") SysUserSearchDTO sysUserSearchDTO,
                                         @Parameter(description = "视图模式: all-全部, employee-员工, admin-管理员") 
                                         @RequestParam(value = "viewMode", defaultValue = "all") String viewMode) {
        System.out.println("🔍 收到视图模式请求: " + viewMode);
        System.out.println("📊 查询参数: " + sysUserSearchDTO);
        
        RPage<SysUserVO> result;
        switch (viewMode.toLowerCase()) {
            case "employee":
                System.out.println("👥 执行员工查询...");
                result = sysUserFacade.listNonAdminUsersPage(pageQuery, sysUserSearchDTO);
                break;
            case "admin":
                System.out.println("👑 执行管理员查询...");
                result = sysUserFacade.listAdminUsersPage(pageQuery, sysUserSearchDTO);
                break;
            default:
                System.out.println("🌐 执行全部用户查询...");
                result = sysUserFacade.listSysUserPage(pageQuery, sysUserSearchDTO);
                break;
        }
        
        System.out.println("📋 查询结果数量: " + result.getRecords().size() + " / " + result.getTotal());
        System.out.println("👤 用户详情:");
        for (SysUserVO user : result.getRecords()) {
            System.out.println("  - " + user.getUserName() + " (isAdmin: " + user.getIsAdmin() + ")");
        }
        
        return Result.data(result);
    }

    @GetMapping("/{id}")
    @SaCheckPermission("sys:user:get")
    @Operation(operationId = "2", summary = "根据ID获取用户详细信息")
    public Result<SysUserVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(sysUserFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("sys:user:add")
    @Operation(operationId = "3", summary = "新增用户")
    public Result<Boolean> addUser(@Parameter(description = "新增用户对象") @RequestBody SysUserAddDTO sysUserAddDTO) {
        return Result.status(sysUserFacade.addUser(sysUserAddDTO));
    }



    @PutMapping("/")
    @SaCheckPermission("sys:user:update")
    @Operation(operationId = "4", summary = "更新用户信息")
    public Result<Boolean> updateUser(@Parameter(description = "更新用户对象") @RequestBody SysUserUpdateDTO sysUserUpdateDTO) {
        return Result.status(sysUserFacade.updateUser(sysUserUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("sys:user:delete")
    @Operation(operationId = "5", summary = "批量删除用户信息")
    public Result<Boolean> batchDeleteUser(@Parameter(description = "删除用户对象") @RequestBody SysUserDeleteDTO sysUserDeleteDTO) {
        return Result.status(sysUserFacade.batchDeleteUser(sysUserDeleteDTO));
    }

    @PostMapping("/check_device_binding")
    @SaCheckPermission("sys:user:delete")
    @Operation(operationId = "5.1", summary = "检查用户设备绑定状态")
    public Result<List<Map<String, Object>>> checkUserDeviceBinding(@Parameter(description = "删除用户对象") @RequestBody SysUserDeleteDTO sysUserDeleteDTO) {
        return Result.data(sysUserFacade.checkUserDeviceBinding(sysUserDeleteDTO));
    }



    @PutMapping("/reset_password/{userId}")
    @SaCheckPermission("sys:user:resetPassword")
    @Operation(operationId = "6", summary = "重置密码")
    public Result<String> resetPassword(@Parameter(description = "用户ID") @PathVariable("userId") Long userId) {
        return Result.data(sysUserFacade.resetPassword(userId));
    }

    @GetMapping("/responsibilities/{userId}")
    @SaCheckPermission("sys:user:responsibilities")
    @Operation(operationId = "7", summary = "根据用户ID获取用户职责信息")
    public Result<SysUserResponsibilitiesVO> queryUserResponsibilities(@Parameter(description = "ID") @PathVariable("userId") Long userId) {
        return Result.data(sysUserFacade.queryUserResponsibilitiesWithUserId(userId));
    }

    @PutMapping("/responsibilities")
    @SaCheckPermission("sys:user:responsibilities")
    @Operation(operationId = "7", summary = "更新用户职责信息")
    public Result<Boolean> updateUserResponsibilities(@Parameter(description = "用户职责对象") @RequestBody SysUserResponsibilitiesUpdateDTO updateDTO) {
        return Result.data(sysUserFacade.updateUserResponsibilities(updateDTO));
    }

    @PostMapping("/add_user_by_excel")
    @SaCheckPermission("sys:user:add")
    @Operation(operationId = "8", summary = "新增用户")
    public Result<Boolean> addUserByExcel(@Parameter(description = "新增用户对象") @RequestBody SysUserAddDTO sysUserAddDTO) {
        return Result.status(sysUserFacade.addUser(sysUserAddDTO));
    }

    @GetMapping("/get_unbind_device")
    @SaCheckPermission("sys:user:get")
    @Operation(operationId = "9", summary = "获取未绑定设备的用户")
    public Result<List> getUnbindDevice(@RequestParam("customerId") String customerId) {
        return Result.data(sysUserFacade.getUnbindDevice(Long.valueOf(customerId)));
    }


    @GetMapping("/get_bind_device")
    @SaCheckPermission("sys:user:get")
    @Operation(operationId = "9", summary = "获取未绑定设备的用户")
    public Result<List> getBindDevice(@RequestParam("customerId") Long customerId) {
        return Result.data(sysUserFacade.getBindDevice(customerId));
    }

    @Operation(summary = "根据组织ID获取用户列表(优化版本)")
    @GetMapping("/get_users_by_org_id")
    public Result<SysUserMapVO> getUsersByOrgId(
            @Parameter(description = "组织ID") @RequestParam String orgId,
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        try {
            Long orgIdLong = Long.parseLong(orgId);

            System.out.println("🔍 优化后的 getUsersByOrgId: orgIdLong=" + orgIdLong + ", customerId=" + customerId);
            long startTime = System.currentTimeMillis();
            
            List<SysUser> users = sysUserService.getUsersByOrgId(orgIdLong, customerId);
            
            long endTime = System.currentTimeMillis();
            System.out.println("✅ 服务层查询完成，耗时: " + (endTime - startTime) + "ms, 用户数量: " + users.size());
            
            Map<String, String> userMap = users.stream()
                    .collect(Collectors.toMap(
                            user -> String.valueOf(user.getId()),
                            SysUser::getUserName
                    ));
            SysUserMapVO vo = new SysUserMapVO();
            vo.setUserMap(userMap);
            return Result.data(vo);
        } catch (NumberFormatException e) {
            return Result.failure("组织ID格式不正确");
        } catch (cn.dev33.satoken.exception.NotLoginException e) {
            log.warn("⚠️ 未登录访问用户查询API: {}", e.getMessage());
            return Result.failure("未登录或登录已过期，请重新登录");
        } catch (Exception e) {
            log.error("❌ 查询组织用户失败", e);
            return Result.failure("查询组织用户失败: " + e.getMessage());
        }
    }

    @PostMapping("/batch-import")
    @SaCheckPermission("sys:user:add")
    @Operation(operationId = "10", summary = "批量导入用户")
    public Result<Map<String, Object>> batchImportUsers(
            @Parameter(description = "Excel文件") @RequestParam("file") MultipartFile file,
            @Parameter(description = "组织ID列表") @RequestParam("orgIds") String orgIds) {
        return Result.data(sysUserFacade.batchImportUsers(file, orgIds));
    }

    @GetMapping("/check_phone")
    @Operation(operationId = "11", summary = "检查手机号是否已存在(仅检查未删除用户)")
    public Result<Boolean> checkPhoneExists(
            @Parameter(description = "手机号") @RequestParam("phone") String phone,
            @Parameter(description = "排除的用户ID", required = false) @RequestParam(value = "excludeUserId", required = false) Long excludeUserId,
            @Parameter(description = "是否删除标识(0-未删除,1-已删除)", required = false) @RequestParam(value = "isDeleted", defaultValue = "0") Integer isDeleted) {
        boolean exists = sysUserService.checkPhoneExists(phone, excludeUserId, isDeleted);
        return Result.data(exists);
    }

    @GetMapping("/check_device_sn")
    @Operation(operationId = "12", summary = "检查设备序列号是否已存在(仅检查未删除用户)")
    public Result<Boolean> checkDeviceSnExists(
            @Parameter(description = "设备序列号") @RequestParam("deviceSn") String deviceSn,
            @Parameter(description = "排除的用户ID", required = false) @RequestParam(value = "excludeUserId", required = false) Long excludeUserId,
            @Parameter(description = "是否删除标识(0-未删除,1-已删除)", required = false) @RequestParam(value = "isDeleted", defaultValue = "0") Integer isDeleted) {
        boolean exists = sysUserService.checkDeviceSnExists(deviceSn, excludeUserId, isDeleted);
        return Result.data(exists);
    }


}
