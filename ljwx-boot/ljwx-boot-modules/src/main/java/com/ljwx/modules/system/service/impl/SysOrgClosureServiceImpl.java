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

package com.ljwx.modules.system.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.modules.system.domain.entity.SysOrgClosure;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysOrgManagerCache;
import com.ljwx.modules.system.domain.dto.OrgHierarchyInfo;
import com.ljwx.modules.system.repository.mapper.SysOrgClosureMapper;
import com.ljwx.modules.system.repository.mapper.SysOrgManagerCacheMapper;
import com.ljwx.modules.system.repository.mapper.SysOrgUnitsMapper;
import com.ljwx.modules.system.service.ISysOrgClosureService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;
import org.springframework.util.StringUtils;
import org.springframework.util.StopWatch;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * 组织架构闭包表服务实现类
 * 提供高效的组织层级查询服务实现
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.SysOrgClosureServiceImpl
 * @CreateTime 2025-08-30 - 16:00:00
 */

@Slf4j
@Service
public class SysOrgClosureServiceImpl extends ServiceImpl<SysOrgClosureMapper, SysOrgClosure> implements ISysOrgClosureService {

    @Autowired
    private SysOrgClosureMapper sysOrgClosureMapper;

    @Autowired
    private SysOrgManagerCacheMapper sysOrgManagerCacheMapper;

    @Autowired
    private SysOrgUnitsMapper sysOrgUnitsMapper;

    // 缓存名称
    private static final String CACHE_NAME = "org_closure";
    private static final int MAX_BATCH_SIZE = 1000;
    private static final int SLOW_QUERY_THRESHOLD_MS = 100;

    @Override
    @Cacheable(value = CACHE_NAME, key = "'top_level_' + #customerId")
    public List<SysOrgUnits> findTopLevelOrganizations(Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        try {
            List<SysOrgUnits> result = sysOrgClosureMapper.findTopLevelOrganizations(customerId);
            
            stopWatch.stop();
            logPerformance("findTopLevelOrganizations", null, customerId, 
                stopWatch.getTotalTimeMillis(), result.size(), true, null);
            
            log.debug("查询租户{}的顶级组织完成，找到{}个组织，耗时{}ms", 
                customerId, result.size(), stopWatch.getTotalTimeMillis());
                
            return result;
        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("findTopLevelOrganizations", null, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            log.error("查询顶级组织失败: customerId={}", customerId, e);
            return new ArrayList<>();
        }
    }

    @Override
    @Cacheable(value = CACHE_NAME, key = "'all_descendants_' + #ancestorId + '_' + #customerId")
    public List<SysOrgUnits> findAllDescendants(Long ancestorId, Long customerId) {
        if (ancestorId == null) {
            return new ArrayList<>();
        }
        
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        try {
            List<SysOrgUnits> result = sysOrgClosureMapper.findAllDescendants(ancestorId, customerId);
            
            stopWatch.stop();
            logPerformance("findAllDescendants", ancestorId, customerId, 
                stopWatch.getTotalTimeMillis(), result.size(), true, null);
            
            log.debug("查询组织{}的所有子组织完成，找到{}个子组织，耗时{}ms", 
                ancestorId, result.size(), stopWatch.getTotalTimeMillis());
                
            return result;
        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("findAllDescendants", ancestorId, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            log.error("查询所有子组织失败: ancestorId={}, customerId={}", ancestorId, customerId, e);
            return new ArrayList<>();
        }
    }

    @Override
    @Cacheable(value = CACHE_NAME, key = "'direct_children_' + #ancestorId + '_' + #customerId")
    public List<SysOrgUnits> findDirectChildren(Long ancestorId, Long customerId) {
        if (ancestorId == null) {
            return new ArrayList<>();
        }
        
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        try {
            List<SysOrgUnits> result = sysOrgClosureMapper.findDirectChildren(ancestorId, customerId);
            
            stopWatch.stop();
            logPerformance("findDirectChildren", ancestorId, customerId, 
                stopWatch.getTotalTimeMillis(), result.size(), true, null);
            
            log.debug("查询组织{}的直接子组织完成，找到{}个子组织，耗时{}ms", 
                ancestorId, result.size(), stopWatch.getTotalTimeMillis());
                
            return result;
        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("findDirectChildren", ancestorId, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            log.error("查询直接子组织失败: ancestorId={}, customerId={}", ancestorId, customerId, e);
            return new ArrayList<>();
        }
    }

    @Override
    public List<SysOrgUnits> findAncestorPath(Long descendantId, Long customerId) {
        log.debug("查询组织{}的祖先路径，租户ID: {}", descendantId, customerId);
        if (descendantId == null) {
            return new ArrayList<>();
        }
        return sysOrgClosureMapper.findAncestorPath(descendantId, customerId);
    }

    @Override
    public SysOrgUnits findDirectParent(Long descendantId, Long customerId) {
        log.debug("查询组织{}的直接父组织，租户ID: {}", descendantId, customerId);
        if (descendantId == null) {
            return null;
        }
        return sysOrgClosureMapper.findDirectParent(descendantId, customerId);
    }

    @Override
    public List<SysOrgUnits> findBatchDescendants(List<Long> ancestorIds, Long customerId) {
        log.debug("批量查询组织{}的所有子组织，租户ID: {}", ancestorIds, customerId);
        if (CollectionUtils.isEmpty(ancestorIds)) {
            return new ArrayList<>();
        }
        return sysOrgClosureMapper.findBatchDescendants(ancestorIds, customerId);
    }

    @Override
    public List<SysOrgManagerCache> findOrgManagers(Long orgId, Long customerId, String roleType) {
        log.debug("查询组织{}的管理员，角色类型: {}，租户ID: {}", orgId, roleType, customerId);
        if (orgId == null) {
            return new ArrayList<>();
        }
        return sysOrgManagerCacheMapper.findOrgManagers(orgId, customerId, roleType);
    }

    @Override
    public List<SysOrgManagerCache> findEscalationManagers(Long orgId, Long customerId, String roleType) {
        log.debug("查询组织{}告警升级链管理员，角色类型: {}，租户ID: {}", orgId, roleType, customerId);
        if (orgId == null) {
            return new ArrayList<>();
        }
        return sysOrgManagerCacheMapper.findEscalationManagers(orgId, customerId, roleType);
    }

    @Override
    public List<SysOrgManagerCache> findUserManagedOrgs(Long userId, Long customerId) {
        log.debug("查询用户{}管理的组织，租户ID: {}", userId, customerId);
        if (userId == null) {
            return new ArrayList<>();
        }
        return sysOrgManagerCacheMapper.findUserManagedOrgs(userId, customerId);
    }

    @Override
    public Boolean isAncestor(Long ancestorId, Long descendantId, Long customerId) {
        log.debug("检查组织{}是否为组织{}的祖先，租户ID: {}", ancestorId, descendantId, customerId);
        if (ancestorId == null || descendantId == null) {
            return false;
        }
        return sysOrgClosureMapper.isAncestor(ancestorId, descendantId, customerId);
    }

    @Override
    public Integer getOrgDepth(Long orgId, Long customerId) {
        log.debug("获取组织{}的层级深度，租户ID: {}", orgId, customerId);
        if (orgId == null) {
            return 0;
        }
        Integer depth = sysOrgClosureMapper.getOrgDepth(orgId, customerId);
        return depth != null ? depth : 0;
    }

    @Override
    @Transactional
    public void addOrgToClosure(Long orgId, Long parentId, Long customerId) {
        log.info("添加组织{}到闭包表，父组织: {}，租户ID: {}", orgId, parentId, customerId);
        if (orgId == null || customerId == null) {
            throw new IllegalArgumentException("组织ID和租户ID不能为空");
        }

        if (parentId == null || parentId == 0) {
            // 顶级组织，只插入自身关系
            SysOrgClosure selfClosure = SysOrgClosure.builder()
                    .ancestorId(orgId)
                    .descendantId(orgId)
                    .depth(0)
                    .customerId(customerId)
                    .build();
            this.save(selfClosure);
        } else {
            // 有父组织，插入完整的闭包关系
            sysOrgClosureMapper.insertOrgClosure(orgId, parentId, customerId);
        }
        
        log.info("组织{}成功添加到闭包表", orgId);
    }

    @Override
    @Transactional
    public void removeOrgFromClosure(Long orgId, Long customerId) {
        log.info("从闭包表删除组织{}，租户ID: {}", orgId, customerId);
        if (orgId == null) {
            throw new IllegalArgumentException("组织ID不能为空");
        }
        
        sysOrgClosureMapper.deleteOrgClosure(orgId, customerId);
        sysOrgManagerCacheMapper.deleteOrgManagerCache(orgId, customerId);
        
        log.info("组织{}成功从闭包表删除", orgId);
    }

    @Override
    @Transactional
    public void moveOrgToNewParent(Long orgId, Long newParentId, Long customerId) {
        log.info("移动组织{}到新父组织{}，租户ID: {}", orgId, newParentId, customerId);
        if (orgId == null || customerId == null) {
            throw new IllegalArgumentException("组织ID和租户ID不能为空");
        }

        // 1. 删除原有的闭包关系
        removeOrgFromClosure(orgId, customerId);
        
        // 2. 重新添加闭包关系
        addOrgToClosure(orgId, newParentId, customerId);
        
        // 3. 处理子组织的闭包关系
        List<SysOrgUnits> children = findDirectChildren(orgId, customerId);
        for (SysOrgUnits child : children) {
            moveOrgToNewParent(child.getId(), orgId, customerId);
        }
        
        log.info("组织{}成功移动到新父组织{}", orgId, newParentId);
    }

    @Override
    @Transactional
    public void refreshManagerCache(Long orgId, Long customerId) {
        log.info("刷新管理员缓存，组织ID: {}，租户ID: {}", orgId, customerId);
        
        if (orgId != null) {
            // 刷新指定组织
            sysOrgManagerCacheMapper.refreshOrgManagerCache(orgId, customerId);
        } else {
            // 刷新所有组织
            LambdaQueryWrapper<SysOrgUnits> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(SysOrgUnits::getCustomerId, customerId)
                   .eq(SysOrgUnits::getIsDeleted, 0);
            
            List<SysOrgUnits> orgs = sysOrgUnitsMapper.selectList(wrapper);
            for (SysOrgUnits org : orgs) {
                sysOrgManagerCacheMapper.refreshOrgManagerCache(org.getId(), customerId);
            }
        }
        
        log.info("管理员缓存刷新完成");
    }

    @Override
    public List<String> validateConsistency(Long customerId) {
        log.info("验证闭包表数据一致性，租户ID: {}", customerId);
        List<String> inconsistencies = new ArrayList<>();
        
        try {
            // 这里应该调用数据库存储过程来进行验证
            // 为简化实现，这里只做基本检查
            
            // 检查是否有组织缺少自身关系
            LambdaQueryWrapper<SysOrgUnits> orgWrapper = new LambdaQueryWrapper<>();
            orgWrapper.eq(SysOrgUnits::getCustomerId, customerId)
                     .eq(SysOrgUnits::getIsDeleted, 0);
            
            List<SysOrgUnits> orgs = sysOrgUnitsMapper.selectList(orgWrapper);
            for (SysOrgUnits org : orgs) {
                LambdaQueryWrapper<SysOrgClosure> closureWrapper = new LambdaQueryWrapper<>();
                closureWrapper.eq(SysOrgClosure::getAncestorId, org.getId())
                             .eq(SysOrgClosure::getDescendantId, org.getId())
                             .eq(SysOrgClosure::getDepth, 0)
                             .eq(SysOrgClosure::getCustomerId, customerId);
                
                if (this.count(closureWrapper) == 0) {
                    inconsistencies.add("组织" + org.getName() + "(ID:" + org.getId() + ")缺少自身关系");
                }
            }
            
            log.info("数据一致性检查完成，发现{}个不一致问题", inconsistencies.size());
            
        } catch (Exception e) {
            log.error("验证数据一致性时出错", e);
            inconsistencies.add("验证过程出错: " + e.getMessage());
        }
        
        return inconsistencies;
    }

    @Override
    @Transactional
    public void rebuildClosureTable(Long customerId) {
        log.info("重建闭包表，租户ID: {}", customerId);
        
        try {
            // 清空指定租户的闭包表数据
            LambdaQueryWrapper<SysOrgClosure> wrapper = new LambdaQueryWrapper<>();
            if (customerId != null) {
                wrapper.eq(SysOrgClosure::getCustomerId, customerId);
            }
            this.remove(wrapper);
            
            // 重建闭包表
            LambdaQueryWrapper<SysOrgUnits> orgWrapper = new LambdaQueryWrapper<>();
            if (customerId != null) {
                orgWrapper.eq(SysOrgUnits::getCustomerId, customerId);
            }
            orgWrapper.eq(SysOrgUnits::getIsDeleted, 0)
                     .orderByAsc(SysOrgUnits::getLevel, SysOrgUnits::getId);
            
            List<SysOrgUnits> orgs = sysOrgUnitsMapper.selectList(orgWrapper);
            
            for (SysOrgUnits org : orgs) {
                rebuildOrgClosure(org);
            }
            
            // 刷新管理员缓存
            refreshManagerCache(null, customerId);
            
            log.info("闭包表重建完成，处理了{}个组织", orgs.size());
            
        } catch (Exception e) {
            log.error("重建闭包表时出错", e);
            throw new RuntimeException("重建闭包表失败: " + e.getMessage(), e);
        }
    }

    /**
     * 批量查询部门管理员 - 告警系统关键优化
     * 
     * @param orgIds 组织ID列表
     * @param customerId 租户ID
     * @return Map<部门ID, 管理员列表>
     */
    public Map<Long, List<SysOrgManagerCache>> batchFindDepartmentManagers(List<Long> orgIds, Long customerId) {
        if (CollectionUtils.isEmpty(orgIds)) {
            return Collections.emptyMap();
        }
        
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        try {
            Map<Long, List<SysOrgManagerCache>> results = new HashMap<>();
            
            // 分批处理，避免IN子句过长
            for (int i = 0; i < orgIds.size(); i += MAX_BATCH_SIZE) {
                List<Long> batch = orgIds.subList(i, Math.min(i + MAX_BATCH_SIZE, orgIds.size()));
                
                // 使用现有的管理员查询方法
                for (Long orgId : batch) {
                    List<SysOrgManagerCache> managers = findOrgManagers(orgId, customerId, "manager");
                    if (!managers.isEmpty()) {
                        results.put(orgId, managers);
                    }
                }
            }
            
            stopWatch.stop();
            logPerformance("batchFindDepartmentManagers", null, customerId, 
                stopWatch.getTotalTimeMillis(), results.size(), true, null);
            
            log.debug("批量查找部门管理员完成: 查询{}个部门, 找到{}个部门有管理员, 耗时{}ms", 
                orgIds.size(), results.size(), stopWatch.getTotalTimeMillis());
                
            return results;
            
        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("batchFindDepartmentManagers", null, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            log.error("批量查找部门管理员失败: orgIds={}, customerId={}", orgIds, customerId, e);
            return Collections.emptyMap();
        }
    }

    /**
     * 查找租户级管理员
     * 
     * @param customerId 租户ID
     * @return 管理员用户ID列表
     */
    @Cacheable(value = CACHE_NAME, key = "'tenant_admins_' + #customerId")
    public List<Long> findTenantAdmins(Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        try {
            // 查找根级别组织的主管作为租户管理员
            List<SysOrgUnits> topOrgs = findTopLevelOrganizations(customerId);
            List<Long> adminIds = new ArrayList<>();
            
            for (SysOrgUnits org : topOrgs) {
                List<SysOrgManagerCache> managers = findOrgManagers(org.getId(), customerId, "manager");
                adminIds.addAll(managers.stream()
                    .map(SysOrgManagerCache::getUserId)
                    .collect(Collectors.toList()));
            }
            
            stopWatch.stop();
            logPerformance("findTenantAdmins", null, customerId, 
                stopWatch.getTotalTimeMillis(), adminIds.size(), true, null);
                
            return adminIds;
            
        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("findTenantAdmins", null, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            log.error("查找租户管理员失败: customerId={}", customerId, e);
            return Collections.emptyList();
        }
    }

    /**
     * 清除组织相关缓存
     * 
     * @param orgId 组织ID (可选)
     * @param customerId 租户ID
     */
    @CacheEvict(value = CACHE_NAME, allEntries = true)
    public void clearOrgCache(Long orgId, Long customerId) {
        log.info("清除组织缓存: orgId={}, customerId={}", orgId, customerId);
    }

    /**
     * 为单个组织重建闭包关系
     */
    private void rebuildOrgClosure(SysOrgUnits org) {
        try {
            // 1. 插入自身关系
            SysOrgClosure selfClosure = SysOrgClosure.builder()
                    .ancestorId(org.getId())
                    .descendantId(org.getId())
                    .depth(0)
                    .customerId(org.getCustomerId())
                    .build();
            this.save(selfClosure);

            // 2. 解析ancestors字段，插入祖先关系
            if (StringUtils.hasText(org.getAncestors()) && !"0".equals(org.getAncestors().trim())) {
                String[] ancestorArray = org.getAncestors().split(",");
                int depth = 1;
                
                for (String ancestorStr : ancestorArray) {
                    try {
                        Long ancestorId = Long.parseLong(ancestorStr.trim());
                        if (ancestorId > 0 && !ancestorId.equals(org.getId())) {
                            SysOrgClosure ancestorClosure = SysOrgClosure.builder()
                                    .ancestorId(ancestorId)
                                    .descendantId(org.getId())
                                    .depth(depth)
                                    .customerId(org.getCustomerId())
                                    .build();
                            this.save(ancestorClosure);
                            depth++;
                        }
                    } catch (NumberFormatException e) {
                        log.warn("解析组织{}的ancestors字段时遇到无效数字: {}", org.getId(), ancestorStr);
                    }
                }
            }
            
        } catch (Exception e) {
            log.error("为组织{}重建闭包关系时出错", org.getId(), e);
        }
    }

    /**
     * 记录性能日志
     */
    private void logPerformance(String operation, Long orgId, Long customerId, 
                               long executionTime, int resultCount, boolean success, String errorMessage) {
        try {
            // 性能告警
            if (executionTime > SLOW_QUERY_THRESHOLD_MS) {
                log.warn("⚠️ 组织查询性能告警: operation={}, executionTime={}ms, resultCount={}", 
                    operation, executionTime, resultCount);
            }
            
            // 这里可以将性能日志写入数据库或监控系统
            // 为了保持轻量级，目前只记录日志
            if (log.isDebugEnabled()) {
                log.debug("性能指标: operation={}, orgId={}, customerId={}, time={}ms, count={}, success={}", 
                    operation, orgId, customerId, executionTime, resultCount, success);
            }
            
        } catch (Exception e) {
            // 记录性能日志失败不应影响业务逻辑
            log.debug("记录性能日志失败", e);
        }
    }

    // ===================== 告警分发优化相关方法实现 =====================

    @Override
    @Cacheable(value = "alertNotificationHierarchy", key = "#orgId + '_' + #customerId")
    public List<OrgHierarchyInfo> getNotificationHierarchy(Long orgId, Long customerId) {
        long startTime = System.currentTimeMillis();
        
        try {
            List<OrgHierarchyInfo> result = baseMapper.getNotificationHierarchy(orgId, customerId);
            
            long executionTime = System.currentTimeMillis() - startTime;
            logPerformance("getNotificationHierarchy", orgId, customerId, executionTime, 
                         result.size(), true, null);
                         
            log.debug("告警通知层级查询完成: orgId={}, customerId={}, recipients={}, time={}ms", 
                    orgId, customerId, result.size(), executionTime);
            
            return result;
        } catch (Exception e) {
            long executionTime = System.currentTimeMillis() - startTime;
            logPerformance("getNotificationHierarchy", orgId, customerId, executionTime, 
                         0, false, e.getMessage());
            log.error("获取告警通知层级信息失败", e);
            throw e;
        }
    }

    @Override
    @Cacheable(value = "alertBatchNotificationHierarchy", 
               key = "#orgIds.hashCode() + '_' + #customerId")
    public List<OrgHierarchyInfo> getBatchNotificationHierarchy(List<Long> orgIds, Long customerId) {
        if (CollectionUtils.isEmpty(orgIds)) {
            return Collections.emptyList();
        }
        
        long startTime = System.currentTimeMillis();
        
        try {
            List<OrgHierarchyInfo> result = baseMapper.getBatchNotificationHierarchy(orgIds, customerId);
            
            long executionTime = System.currentTimeMillis() - startTime;
            logPerformance("getBatchNotificationHierarchy", null, customerId, executionTime, 
                         result.size(), true, null);
                         
            log.debug("批量告警通知层级查询完成: orgCount={}, customerId={}, recipients={}, time={}ms", 
                    orgIds.size(), customerId, result.size(), executionTime);
            
            return result;
        } catch (Exception e) {
            long executionTime = System.currentTimeMillis() - startTime;
            logPerformance("getBatchNotificationHierarchy", null, customerId, executionTime, 
                         0, false, e.getMessage());
            log.error("获取批量告警通知层级信息失败", e);
            throw e;
        }
    }

    @Override
    @Cacheable(value = "userAlertScope", key = "#userId + '_' + #customerId")
    public List<Long> getUserAlertScope(Long userId, Long customerId) {
        long startTime = System.currentTimeMillis();
        
        try {
            List<Long> result = baseMapper.getUserAlertScope(userId, customerId);
            
            long executionTime = System.currentTimeMillis() - startTime;
            logPerformance("getUserAlertScope", null, customerId, executionTime, 
                         result.size(), true, null);
                         
            log.debug("用户告警权限范围查询完成: userId={}, customerId={}, scopeSize={}, time={}ms", 
                    userId, customerId, result.size(), executionTime);
            
            return result;
        } catch (Exception e) {
            long executionTime = System.currentTimeMillis() - startTime;
            logPerformance("getUserAlertScope", null, customerId, executionTime, 
                         0, false, e.getMessage());
            log.error("获取用户告警权限范围失败", e);
            throw e;
        }
    }
}