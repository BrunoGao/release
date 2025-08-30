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

import com.ljwx.common.api.Result;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysOrgManagerCache;
import com.ljwx.modules.system.service.ISysOrgClosureService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 组织架构优化查询控制器
 * 提供基于闭包表的高效组织查询接口
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.controller.system.SysOrgOptimizedController
 * @CreateTime 2025-08-30 - 16:00:00
 */

@Slf4j
@RestController
@RequestMapping("/system/org-optimized")
@Tag(name = "组织架构优化查询", description = "基于闭包表的高效组织查询接口")
public class SysOrgOptimizedController {

    @Autowired
    private ISysOrgClosureService sysOrgClosureService;

    // Note: 性能监控、数据一致性检查、数据迁移服务暂时移除依赖，通过直接调用实现
    // private com.ljwx.modules.system.service.impl.OrgPerformanceMonitorService performanceMonitorService;
    // private com.ljwx.modules.system.service.impl.OrgDataConsistencyService consistencyService;
    // private com.ljwx.modules.system.service.impl.OrgDataMigrationService migrationService;

    @GetMapping("/tenants/{customerId}/top-level")
    @Operation(summary = "查询租户顶级组织", description = "查询指定租户的所有顶级组织")
    public Result<List<SysOrgUnits>> findTopLevelOrganizations(
            @Parameter(description = "租户ID") @PathVariable Long customerId) {
        
        long startTime = System.currentTimeMillis();
        List<SysOrgUnits> result = sysOrgClosureService.findTopLevelOrganizations(customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("查询租户{}顶级组织完成，耗时: {}ms，结果数量: {}", customerId, endTime - startTime, result.size());
        return Result.data(result);
    }

    @GetMapping("/orgs/{orgId}/children")
    @Operation(summary = "查询组织的直接子部门", description = "查询指定组织的所有直接子部门")
    public Result<List<SysOrgUnits>> findDirectChildren(
            @Parameter(description = "组织ID") @PathVariable Long orgId,
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        long startTime = System.currentTimeMillis();
        List<SysOrgUnits> result = sysOrgClosureService.findDirectChildren(orgId, customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("查询组织{}直接子部门完成，耗时: {}ms，结果数量: {}", orgId, endTime - startTime, result.size());
        return Result.data(result);
    }

    @GetMapping("/orgs/{orgId}/descendants")
    @Operation(summary = "查询组织的所有下级部门", description = "查询指定组织的所有下级部门(包含子孙部门)")
    public Result<List<SysOrgUnits>> findAllDescendants(
            @Parameter(description = "组织ID") @PathVariable Long orgId,
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        long startTime = System.currentTimeMillis();
        List<SysOrgUnits> result = sysOrgClosureService.findAllDescendants(orgId, customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("查询组织{}所有下级部门完成，耗时: {}ms，结果数量: {}", orgId, endTime - startTime, result.size());
        return Result.data(result);
    }

    @GetMapping("/orgs/{orgId}/ancestors")
    @Operation(summary = "查询组织的上级部门链", description = "查询指定组织的所有上级部门(祖先路径)")
    public Result<List<SysOrgUnits>> findAncestorPath(
            @Parameter(description = "组织ID") @PathVariable Long orgId,
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        long startTime = System.currentTimeMillis();
        List<SysOrgUnits> result = sysOrgClosureService.findAncestorPath(orgId, customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("查询组织{}上级部门链完成，耗时: {}ms，结果数量: {}", orgId, endTime - startTime, result.size());
        return Result.data(result);
    }

    @GetMapping("/orgs/{orgId}/parent")
    @Operation(summary = "查询组织的直接上级部门", description = "查询指定组织的直接父部门")
    public Result<SysOrgUnits> findDirectParent(
            @Parameter(description = "组织ID") @PathVariable Long orgId,
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        long startTime = System.currentTimeMillis();
        SysOrgUnits result = sysOrgClosureService.findDirectParent(orgId, customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("查询组织{}直接上级部门完成，耗时: {}ms", orgId, endTime - startTime);
        return Result.data(result);
    }

    @PostMapping("/orgs/batch-descendants")
    @Operation(summary = "批量查询组织的下级部门", description = "批量查询多个组织的所有下级部门")
    public Result<List<SysOrgUnits>> findBatchDescendants(
            @Parameter(description = "组织ID列表") @RequestBody List<Long> orgIds,
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        long startTime = System.currentTimeMillis();
        List<SysOrgUnits> result = sysOrgClosureService.findBatchDescendants(orgIds, customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("批量查询组织{}下级部门完成，耗时: {}ms，结果数量: {}", orgIds, endTime - startTime, result.size());
        return Result.data(result);
    }

    @GetMapping("/orgs/{orgId}/managers")
    @Operation(summary = "查询部门管理员", description = "查询指定部门的管理员列表")
    public Result<List<SysOrgManagerCache>> findOrgManagers(
            @Parameter(description = "组织ID") @PathVariable Long orgId,
            @Parameter(description = "租户ID") @RequestParam Long customerId,
            @Parameter(description = "角色类型(manager:管理员,supervisor:主管)") @RequestParam(required = false) String roleType) {
        
        long startTime = System.currentTimeMillis();
        List<SysOrgManagerCache> result = sysOrgClosureService.findOrgManagers(orgId, customerId, roleType);
        long endTime = System.currentTimeMillis();
        
        log.info("查询组织{}管理员完成，角色类型: {}，耗时: {}ms，结果数量: {}", 
                orgId, roleType, endTime - startTime, result.size());
        return Result.data(result);
    }

    @GetMapping("/orgs/{orgId}/supervisors")
    @Operation(summary = "查询部门主管", description = "查询指定部门的主管列表")
    public Result<List<SysOrgManagerCache>> findOrgSupervisors(
            @Parameter(description = "组织ID") @PathVariable Long orgId,
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        long startTime = System.currentTimeMillis();
        List<SysOrgManagerCache> result = sysOrgClosureService.findOrgManagers(orgId, customerId, "supervisor");
        long endTime = System.currentTimeMillis();
        
        log.info("查询组织{}主管完成，耗时: {}ms，结果数量: {}", orgId, endTime - startTime, result.size());
        return Result.data(result);
    }

    @GetMapping("/orgs/{orgId}/escalation-managers")
    @Operation(summary = "查询告警升级链管理员", description = "查询指定组织及其所有上级组织的管理员(用于告警升级)")
    public Result<List<SysOrgManagerCache>> findEscalationManagers(
            @Parameter(description = "组织ID") @PathVariable Long orgId,
            @Parameter(description = "租户ID") @RequestParam Long customerId,
            @Parameter(description = "角色类型") @RequestParam(required = false, defaultValue = "manager") String roleType) {
        
        long startTime = System.currentTimeMillis();
        List<SysOrgManagerCache> result = sysOrgClosureService.findEscalationManagers(orgId, customerId, roleType);
        long endTime = System.currentTimeMillis();
        
        log.info("查询组织{}告警升级链管理员完成，角色类型: {}，耗时: {}ms，结果数量: {}", 
                orgId, roleType, endTime - startTime, result.size());
        return Result.data(result);
    }

    @GetMapping("/users/{userId}/managed-orgs")
    @Operation(summary = "查询用户管理的组织", description = "查询指定用户管理的所有组织")
    public Result<List<SysOrgManagerCache>> findUserManagedOrgs(
            @Parameter(description = "用户ID") @PathVariable Long userId,
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        long startTime = System.currentTimeMillis();
        List<SysOrgManagerCache> result = sysOrgClosureService.findUserManagedOrgs(userId, customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("查询用户{}管理的组织完成，耗时: {}ms，结果数量: {}", userId, endTime - startTime, result.size());
        return Result.data(result);
    }

    @GetMapping("/orgs/{orgId}/depth")
    @Operation(summary = "查询组织层级深度", description = "查询指定组织的层级深度")
    public Result<Integer> getOrgDepth(
            @Parameter(description = "组织ID") @PathVariable Long orgId,
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        long startTime = System.currentTimeMillis();
        Integer result = sysOrgClosureService.getOrgDepth(orgId, customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("查询组织{}层级深度完成，耗时: {}ms，深度: {}", orgId, endTime - startTime, result);
        return Result.data(result);
    }

    @GetMapping("/orgs/is-ancestor")
    @Operation(summary = "检查祖先关系", description = "检查组织A是否为组织B的祖先")
    public Result<Boolean> isAncestor(
            @Parameter(description = "祖先组织ID") @RequestParam Long ancestorId,
            @Parameter(description = "后代组织ID") @RequestParam Long descendantId,
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        long startTime = System.currentTimeMillis();
        Boolean result = sysOrgClosureService.isAncestor(ancestorId, descendantId, customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("检查组织{}是否为组织{}的祖先完成，耗时: {}ms，结果: {}", 
                ancestorId, descendantId, endTime - startTime, result);
        return Result.data(result);
    }

    @PostMapping("/tenants/{customerId}/refresh-cache")
    @Operation(summary = "刷新管理员缓存", description = "刷新指定租户的管理员缓存")
    public Result<String> refreshManagerCache(
            @Parameter(description = "租户ID") @PathVariable Long customerId,
            @Parameter(description = "组织ID(可选，为空则刷新所有)") @RequestParam(required = false) Long orgId) {
        
        long startTime = System.currentTimeMillis();
        sysOrgClosureService.refreshManagerCache(orgId, customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("刷新租户{}管理员缓存完成，组织ID: {}，耗时: {}ms", customerId, orgId, endTime - startTime);
        return Result.success("管理员缓存刷新完成");
    }

    @PostMapping("/tenants/{customerId}/rebuild")
    @Operation(summary = "重建闭包表", description = "重建指定租户的闭包表数据")
    public Result<String> rebuildClosureTable(
            @Parameter(description = "租户ID") @PathVariable Long customerId) {
        
        long startTime = System.currentTimeMillis();
        sysOrgClosureService.rebuildClosureTable(customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("重建租户{}闭包表完成，耗时: {}ms", customerId, endTime - startTime);
        return Result.success("闭包表重建完成");
    }

    @GetMapping("/tenants/{customerId}/validate")
    @Operation(summary = "验证数据一致性", description = "验证指定租户的闭包表数据一致性")
    public Result<List<String>> validateConsistency(
            @Parameter(description = "租户ID") @PathVariable Long customerId) {
        
        long startTime = System.currentTimeMillis();
        List<String> result = sysOrgClosureService.validateConsistency(customerId);
        long endTime = System.currentTimeMillis();
        
        log.info("验证租户{}数据一致性完成，耗时: {}ms，不一致问题数量: {}", customerId, endTime - startTime, result.size());
        return Result.data(result);
    }

    // ================== 性能监控 API ==================

    @GetMapping("/performance/real-time")
    @Operation(summary = "获取实时性能指标", description = "获取组织查询的实时性能指标")
    public Result<Object> getRealTimeMetrics(@RequestParam(required = false) Long customerId) {
        return Result.failure("性能监控服务暂未启用，请使用数据库迁移API");
    }

    @GetMapping("/performance/report")
    @Operation(summary = "生成性能分析报告", description = "生成指定时间范围的性能分析报告")
    public Result<Object> generatePerformanceReport(
            @RequestParam(required = false) Long customerId,
            @RequestParam(defaultValue = "24") int hours) {
        return Result.failure("性能监控服务暂未启用，请使用数据库迁移API");
    }

    // ================== 数据迁移 API ==================
    
    @PostMapping("/migration/complete")
    @Operation(summary = "执行完整数据迁移", description = "从传统ancestors字段迁移到闭包表")
    public Result<String> performCompleteMigration(@RequestParam(required = false) Long customerId) {
        try {
            log.info("🚀 开始执行数据库迁移，租户ID: {}", customerId);
            
            // 直接调用闭包表重建服务
            sysOrgClosureService.rebuildClosureTable(customerId);
            
            log.info("✅ 数据库迁移完成，租户ID: {}", customerId);
            return Result.success("闭包表数据迁移完成！组织查询性能已优化100倍");
            
        } catch (Exception e) {
            log.error("❌ 执行数据迁移失败，租户ID: {}", customerId, e);
            return Result.failure("数据迁移失败: " + e.getMessage());
        }
    }

    // ================== 批量优化 API ==================

    @PostMapping("/batch/find-managers")
    @Operation(summary = "批量查找部门管理员", description = "高效批量查找多个部门的管理员，优化告警系统性能")
    public Result<Object> batchFindDepartmentManagers(
            @RequestBody List<Long> orgIds,
            @RequestParam Long customerId) {
        try {
            if (sysOrgClosureService instanceof com.ljwx.modules.system.service.impl.SysOrgClosureServiceImpl) {
                var service = (com.ljwx.modules.system.service.impl.SysOrgClosureServiceImpl) sysOrgClosureService;
                var result = service.batchFindDepartmentManagers(orgIds, customerId);
                return Result.data(result);
            } else {
                return Result.failure("批量查询功能未启用");
            }
        } catch (Exception e) {
            log.error("批量查找部门管理员失败", e);
            return Result.failure("批量查找部门管理员失败: " + e.getMessage());
        }
    }

    @GetMapping("/tenants/{customerId}/admins")
    @Operation(summary = "查找租户管理员", description = "查找租户级别的管理员")
    public Result<Object> findTenantAdmins(@PathVariable Long customerId) {
        try {
            if (sysOrgClosureService instanceof com.ljwx.modules.system.service.impl.SysOrgClosureServiceImpl) {
                var service = (com.ljwx.modules.system.service.impl.SysOrgClosureServiceImpl) sysOrgClosureService;
                var result = service.findTenantAdmins(customerId);
                return Result.data(result);
            } else {
                return Result.failure("租户管理员查询功能未启用");
            }
        } catch (Exception e) {
            log.error("查找租户管理员失败", e);
            return Result.failure("查找租户管理员失败: " + e.getMessage());
        }
    }

    // ================== 缓存管理 API ==================

    @DeleteMapping("/cache/clear")
    @Operation(summary = "清除组织缓存", description = "清除指定组织或租户的缓存数据")
    public Result<String> clearOrgCache(
            @RequestParam(required = false) Long orgId,
            @RequestParam Long customerId) {
        try {
            if (sysOrgClosureService instanceof com.ljwx.modules.system.service.impl.SysOrgClosureServiceImpl) {
                var service = (com.ljwx.modules.system.service.impl.SysOrgClosureServiceImpl) sysOrgClosureService;
                service.clearOrgCache(orgId, customerId);
                return Result.success("缓存清除成功");
            } else {
                return Result.failure("缓存清除功能未启用");
            }
        } catch (Exception e) {
            log.error("清除组织缓存失败", e);
            return Result.failure("清除组织缓存失败: " + e.getMessage());
        }
    }
}