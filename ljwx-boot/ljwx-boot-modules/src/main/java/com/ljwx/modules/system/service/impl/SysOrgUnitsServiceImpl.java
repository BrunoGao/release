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
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.system.domain.bo.SysOrgUnitsBO;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.repository.mapper.SysOrgUnitsMapper;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.ljwx.modules.system.event.SysOrgUnitsChangeEvent;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;
import cn.hutool.core.util.StrUtil;
/**
 * 组织/部门/子部门管理 Service 服务接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.SysOrgUnitsServiceImpl
 * @CreateTime 2024-07-16 - 16:35:30
 */

@Slf4j
@Service
public class SysOrgUnitsServiceImpl extends ServiceImpl<SysOrgUnitsMapper, SysOrgUnits> implements ISysOrgUnitsService {

    @Autowired
    private ApplicationEventPublisher eventPublisher;

    @Override
    public IPage<SysOrgUnits> listSysOrgUnitsPage(PageQuery pageQuery, SysOrgUnitsBO sysOrgUnitsBO) {
        System.out.println("🔍 SysOrgUnitsService.listSysOrgUnitsPage - 查询参数:");
        System.out.println("  id: " + sysOrgUnitsBO.getId());
        System.out.println("  name: " + sysOrgUnitsBO.getName());
        System.out.println("  status: " + sysOrgUnitsBO.getStatus());
        System.out.println("  parentId: " + sysOrgUnitsBO.getParentId());
        
        IPage<SysOrgUnits> result = baseMapper.listSysOrgUnitsPage(pageQuery.buildPage(), sysOrgUnitsBO);
        System.out.println("✅ 查询结果数量: " + result.getRecords().size());
        
        return result;
    }

    @Override
    public List<SysOrgUnits> listAllDescendants(List<Long> parentIds) {
        return baseMapper.listAllDescendants(parentIds);
    }

   @Override
    public Long getDirectParent(Long id) {
        if (id == 0) {
            return 0L;
        }
        // 获取当前组织
        SysOrgUnits currentOrg = this.getById(id);
        if (currentOrg == null) {
            return null;
        }
        
        // 获取ancestors字符串
        String ancestors = currentOrg.getAncestors();
        if (StrUtil.isBlank(ancestors)) {
            return null;
        }
        
        // 分割ancestors字符串
        String[] ancestorArray = ancestors.split(",");
        if (ancestorArray.length == 0) {
            return null;
        }
        
        // 返回最后一个数字
        return Long.parseLong(ancestorArray[ancestorArray.length - 1]);
    }

    @Override
    public Long getFirstParent(Long id) {
        if (id == 0) {
            return 0L;
        }
        // 获取当前组织
        SysOrgUnits currentOrg = this.getById(id);
        if (currentOrg == null) {
            return null;
        }
    
        // 获取 ancestors 字符串
        String ancestors = currentOrg.getAncestors();
        if (StrUtil.isBlank(ancestors)) {
            return null;
        }
    
        // 分割 ancestors 字符串
        String[] ancestorArray = ancestors.split(",");
        for (String ancestor : ancestorArray) {
            if (!"0".equals(ancestor.trim())) {
                try {
                    return Long.parseLong(ancestor.trim());
                } catch (NumberFormatException e) {
                    // 忽略非法数字
                    continue;
                }
            }
        }
    
        // 没有找到非 0 的父级
        return id;
    }

    @Override
    public List<SysOrgUnits> querySysOrgUnitsListWithStatus(String status, Long id) {
        log.debug("querySysOrgUnitsListWithStatus - status: {}, id: {}", status, id);

        LambdaQueryWrapper<SysOrgUnits> queryWrapper = new LambdaQueryWrapper<SysOrgUnits>()
                .eq(SysOrgUnits::getStatus, status);

        if (id != 0) {
            List<SysOrgUnits> descendants = baseMapper.listAllDescendants(Collections.singletonList(id));
            List<Long> descendantIds = descendants.stream()
                                                  .map(SysOrgUnits::getId)
                                                  .collect(Collectors.toList());
            descendantIds.add(id);
            log.debug("Descendant IDs for id {}: {}", id, descendantIds);
            queryWrapper.in(SysOrgUnits::getId, descendantIds);
        }

        List<SysOrgUnits> result = baseMapper.selectList(queryWrapper);
        log.debug("Query result size: {}", result);
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean save(SysOrgUnits entity) {
        boolean result = super.save(entity);
        if (result && entity.getParentId() == 0) {
            // 发布组织机构变更事件
            eventPublisher.publishEvent(new SysOrgUnitsChangeEvent(this, entity, "CREATE"));
        }
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateById(SysOrgUnits entity) {
        SysOrgUnits oldEntity = this.getById(entity.getId());
        boolean result = super.updateById(entity);

        //System.out.println("entity.getIsDeleted():" + entity.getIsDeleted());
        /* 
        if (result && entity.getParentId() == 0 && entity.getIsDeleted() == 1) {
            // 发布组织机构变更事件
            eventPublisher.publishEvent(new SysOrgUnitsChangeEvent(this, entity, "DELETE"));
        }
        */
        return result;
    }

    @Override
    public Long getTopLevelDeptIdByOrgId(Long orgId) {
        if (orgId == null) {
            return null;
        }
        
        SysOrgUnits org = this.getById(orgId);
        if (org == null) {
            return null;
        }
        
        // 解析 ancestors 字段，格式如: "0,1955920989166800898,1955921028870082561"
        String ancestors = org.getAncestors();
        if (ancestors == null || ancestors.trim().isEmpty()) {
            // 如果没有ancestors字段，判断是否为顶级部门
            return (org.getParentId() == null || org.getParentId() == 0L) ? orgId : null;
        }
        
        // 分割ancestors字符串
        String[] ancestorIds = ancestors.split(",");
        
        // 找到第一个非0的ID，这就是顶级部门ID
        for (String ancestorId : ancestorIds) {
            ancestorId = ancestorId.trim();
            if (!ancestorId.isEmpty() && !"0".equals(ancestorId)) {
                try {
                    return Long.parseLong(ancestorId);
                } catch (NumberFormatException e) {
                    System.err.println("解析祖先ID失败: " + ancestorId);
                    continue;
                }
            }
        }
        
        // 如果ancestors都是0，说明当前部门就是顶级部门
        return orgId;
    }

}

