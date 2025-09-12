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
 import com.baomidou.mybatisplus.extension.toolkit.Db;
 import com.google.common.collect.Sets;
 import com.ljwx.common.pool.StringPools;
 import com.ljwx.common.util.CglibUtil;
 import com.ljwx.common.util.CollectionUtil;
 import com.ljwx.common.util.StringUtil;
 import com.ljwx.infrastructure.page.PageQuery;
 import com.ljwx.modules.system.domain.bo.SysUserOrgBO;
 import com.ljwx.modules.system.domain.entity.SysUserOrg;
 import com.ljwx.modules.system.domain.entity.SysUser;
 import com.ljwx.modules.system.domain.entity.SysOrgUnits;
 import com.ljwx.modules.system.repository.mapper.SysUserOrgMapper;
 import com.ljwx.modules.system.service.ISysUserOrgService;
 import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.service.IUserTypeSyncService;
 import lombok.extern.slf4j.Slf4j;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.stereotype.Service;
 import org.springframework.util.CollectionUtils;
 import org.springframework.jdbc.core.JdbcTemplate;
 
 import java.util.List;
 import java.util.Set;
 import java.util.concurrent.atomic.AtomicBoolean;
 import java.util.stream.Collectors;
 
 /**
  * 用户组织/部门/子部门管理 Service 服务接口实现层
  *
  * @Author bruno.gao <gaojunivas@gmail.com>
  * @ProjectName ljwx-boot
  * @ClassName com.ljwx.modules.system.service.impl.SysUserOrgServiceImpl
  * @CreateTime 2024-07-16 - 16:35:30
  */
 
 @Slf4j
 @Service
 public class SysUserOrgServiceImpl extends ServiceImpl<SysUserOrgMapper, SysUserOrg> implements ISysUserOrgService {

     @Autowired
     private ISysOrgUnitsService sysOrgUnitsService;
     
     @Autowired
     private JdbcTemplate jdbcTemplate;
     
     @Autowired
     private IUserTypeSyncService userTypeSyncService;
 
     @Override
     public IPage<SysUserOrg> listSysUserOrgPage(PageQuery pageQuery, SysUserOrgBO sysUserOrgBO) {
         return baseMapper.selectPage(pageQuery.buildPage(), new LambdaQueryWrapper<>());
     }
 
     @Override
     public List<SysUserOrgBO> queryOrgUnitsListWithUserId(Long userId) {
         List<SysUserOrg> sysUserOrgList = baseMapper.listUserOrgWithUserId(userId);
         return CglibUtil.convertList(sysUserOrgList, SysUserOrgBO::new);
     }
 
     @Override
     public List<Long> queryOrgUnitsIdsWithUserId(Long userId) {
         List<SysUserOrgBO> sysUserOrgBOList = queryOrgUnitsListWithUserId(userId);
         return sysUserOrgBOList.stream().map(SysUserOrg::getOrgId).toList();
     }
 
     
 
     @Override
     public List<Long> queryOrgUnitsPrincipalWithUserId(Long userId) {
         List<SysUserOrgBO> sysUserOrgBOList = queryOrgUnitsListWithUserId(userId);
         return sysUserOrgBOList.stream()
                 .filter(item -> StringPools.ONE.equals(item.getPrincipal()))
                 .map(SysUserOrg::getOrgId).toList();
     }
 
     @Override
     public boolean updateUserOrg(Long userId, List<Long> orgIds, List<Long> principalIds) {
         List<Long> originUserOrgIds = queryOrgUnitsIdsWithUserId(userId);
         // 处理数据
         Set<Long> orgIdSet = Sets.newHashSet(orgIds);
         Set<Long> principalSet = Sets.newHashSet(principalIds);
         // 处理结果
         AtomicBoolean saveResult = new AtomicBoolean(true);
         CollectionUtil.handleDifference(
                 Sets.newHashSet(originUserOrgIds),
                 orgIdSet,
                 // 处理增加和删除的数据
                 (addOrgIdSet, removeOrgIdSet) -> {
                     // 如有删除，则进行删除数据
                     if (!CollectionUtils.isEmpty(removeOrgIdSet)) {
                         LambdaQueryWrapper<SysUserOrg> removeQueryWrapper = new LambdaQueryWrapper<SysUserOrg>()
                                 .eq(SysUserOrg::getUserId, userId)
                                 .in(SysUserOrg::getOrgId, removeOrgIdSet);
                         baseMapper.delete(removeQueryWrapper);
                     }
                     // 进行新增数据
                     if (!CollectionUtils.isEmpty(addOrgIdSet)) {
                         List<SysUserOrg> sysUserOrgList = addOrgIdSet.stream()
                                 .map(orgId -> {
                                     SysUserOrg sysUserOrg = new SysUserOrg();
                                     sysUserOrg.setUserId(userId);
                                     sysUserOrg.setOrgId(orgId);
                                     sysUserOrg.setPrincipal(StringUtil.boolToString(principalSet.contains(orgId)));
                                     sysUserOrg.setCustomerId(0L); // 默认租户ID
                                     return sysUserOrg;
                                 })
                                 .collect(Collectors.toList());
                         saveResult.set(Db.saveBatch(sysUserOrgList));
                     }
                 }
         );
         // 更新主管标记：先清除再设置
         baseMapper.clearPrincipal(userId);//清除所有主管标记
         if(!principalSet.isEmpty())baseMapper.setPrincipal(userId,principalSet);//设置新主管标记
         
         // 同步更新 sys_user 表的 org_id、org_name 和 customer_id 字段（性能优化）
         if (!orgIds.isEmpty()) {
             try {
                 Long primaryOrgId = orgIds.get(0); // 取第一个作为主要组织
                 SysOrgUnits primaryOrg = sysOrgUnitsService.getById(primaryOrgId);
                 if (primaryOrg != null) {
                     String updateSql = "UPDATE sys_user SET org_id = ?, org_name = ?, customer_id = ?, update_time = NOW() WHERE id = ?";
                     int updatedRows = jdbcTemplate.update(updateSql, primaryOrgId, primaryOrg.getName(), primaryOrg.getCustomerId(), userId);
                     
                     if (updatedRows > 0) {
                         log.info("✅ 已同步更新用户组织信息: userId={}, orgId={}, orgName={}, customerId={}", 
                                 userId, primaryOrgId, primaryOrg.getName(), primaryOrg.getCustomerId());
                     } else {
                         log.warn("⚠️ 同步更新用户组织信息失败: userId={}, orgId={}", userId, primaryOrgId);
                     }
                 }
             } catch (Exception e) {
                 log.error("❌ 同步更新用户组织信息异常: userId={}, error={}", userId, e.getMessage(), e);
             }
         }
         
         
        // 同步更新用户类型信息（组织关系变更可能影响管理级别）
        if (saveResult.get()) {
            try {
                userTypeSyncService.recalculateUserAdminLevel(userId);
                log.info("✅ 组织关系更新后重新计算用户管理级别成功: userId={}", userId);
            } catch (Exception e) {
                log.error("❌ 组织关系更新后重新计算用户管理级别失败: userId={}, error={}", userId, e.getMessage(), e);
            }
        }
        
        return saveResult.get();
     }
 
 }
 
 