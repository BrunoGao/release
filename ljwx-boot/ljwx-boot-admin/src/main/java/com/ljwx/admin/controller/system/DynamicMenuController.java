package com.ljwx.admin.controller.system;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.modules.system.domain.dto.menu.DynamicMenuConfigDTO;
import com.ljwx.modules.system.domain.dto.menu.DynamicMenuScanDTO;
import com.ljwx.modules.system.domain.dto.menu.MenuBatchUpdateDTO;
import com.ljwx.modules.system.domain.vo.DynamicMenuVO;
import com.ljwx.modules.system.domain.vo.MenuScanResultVO;
import com.ljwx.modules.system.service.IDynamicMenuService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 动态菜单管理控制器
 * 支持自动扫描路由、灵活配置菜单、批量操作等功能
 * 
 * @author bruno.gao
 */
@RestController
@Tag(name = "动态菜单管理")
@RequiredArgsConstructor
@RequestMapping("/sys_menu/dynamic")
public class DynamicMenuController {

    private final IDynamicMenuService dynamicMenuService;

    @PostMapping("/scan")
    @SaCheckPermission("sys:menu:dynamic:scan")
    @Operation(operationId = "1", summary = "扫描前端路由文件")
    public Result<MenuScanResultVO> scanRoutes(@Valid @RequestBody DynamicMenuScanDTO scanDTO) {
        MenuScanResultVO result = dynamicMenuService.scanFrontendRoutes(scanDTO);
        return Result.data(result);
    }

    @PostMapping("/auto-sync")
    @SaCheckPermission("sys:menu:dynamic:sync")
    @Operation(operationId = "2", summary = "自动同步菜单配置")
    public Result<String> autoSyncMenus(@Valid @RequestBody DynamicMenuScanDTO scanDTO) {
        String result = dynamicMenuService.autoSyncMenus(scanDTO);
        return Result.data(result);
    }

    @GetMapping("/config")
    @SaCheckPermission("sys:menu:dynamic:config")
    @Operation(operationId = "3", summary = "获取动态菜单配置")
    public Result<List<DynamicMenuVO>> getDynamicMenuConfig(
            @Parameter(description = "租户ID") @RequestParam(required = false) Long customerId) {
        List<DynamicMenuVO> menus = dynamicMenuService.getDynamicMenuConfig(customerId);
        return Result.data(menus);
    }

    @PutMapping("/config")
    @SaCheckPermission("sys:menu:dynamic:config")
    @Operation(operationId = "4", summary = "更新动态菜单配置")
    public Result<String> updateDynamicMenuConfig(@Valid @RequestBody DynamicMenuConfigDTO configDTO) {
        String result = dynamicMenuService.updateDynamicMenuConfig(configDTO);
        return Result.data(result);
    }

    @PutMapping("/batch")
    @SaCheckPermission("sys:menu:dynamic:batch")
    @Operation(operationId = "5", summary = "批量更新菜单")
    public Result<String> batchUpdateMenus(@Valid @RequestBody MenuBatchUpdateDTO batchDTO) {
        String result = dynamicMenuService.batchUpdateMenus(batchDTO);
        return Result.data(result);
    }

    @PutMapping("/reorder")
    @SaCheckPermission("sys:menu:dynamic:reorder")
    @Operation(operationId = "6", summary = "重新排序菜单")
    public Result<String> reorderMenus(@RequestBody List<Long> menuIds) {
        String result = dynamicMenuService.reorderMenus(menuIds);
        return Result.data(result);
    }

    @PostMapping("/preset")
    @SaCheckPermission("sys:menu:dynamic:preset")
    @Operation(operationId = "7", summary = "应用预设菜单模板")
    public Result<String> applyPresetTemplate(
            @Parameter(description = "模板名称") @RequestParam String templateName,
            @Parameter(description = "租户ID") @RequestParam(required = false) Long customerId) {
        String result = dynamicMenuService.applyPresetTemplate(templateName, customerId);
        return Result.data(result);
    }

    @DeleteMapping("/cache")
    @SaCheckPermission("sys:menu:dynamic:cache")
    @Operation(operationId = "8", summary = "清除菜单缓存")
    public Result<String> clearMenuCache(@RequestParam(required = false) Long customerId) {
        String result = dynamicMenuService.clearMenuCache(customerId);
        return Result.data(result);
    }

    @GetMapping("/preview")
    @SaCheckPermission("sys:menu:dynamic:preview")
    @Operation(operationId = "9", summary = "预览菜单配置")
    public Result<List<DynamicMenuVO>> previewMenuConfig(
            @Parameter(description = "租户ID") @RequestParam(required = false) Long customerId,
            @Parameter(description = "角色ID") @RequestParam(required = false) Long roleId) {
        List<DynamicMenuVO> preview = dynamicMenuService.previewMenuConfig(customerId, roleId);
        return Result.data(preview);
    }

    @PostMapping("/import")
    @SaCheckPermission("sys:menu:dynamic:import")
    @Operation(operationId = "10", summary = "导入菜单配置")
    public Result<String> importMenuConfig(@Valid @RequestBody List<DynamicMenuConfigDTO> configList) {
        String result = dynamicMenuService.importMenuConfig(configList);
        return Result.data(result);
    }

    @GetMapping("/export")
    @SaCheckPermission("sys:menu:dynamic:export")
    @Operation(operationId = "11", summary = "导出菜单配置")
    public Result<List<DynamicMenuConfigDTO>> exportMenuConfig(
            @Parameter(description = "租户ID") @RequestParam(required = false) Long customerId) {
        List<DynamicMenuConfigDTO> config = dynamicMenuService.exportMenuConfig(customerId);
        return Result.data(config);
    }
}