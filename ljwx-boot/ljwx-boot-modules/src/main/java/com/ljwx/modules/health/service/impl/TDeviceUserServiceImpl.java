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

 package com.ljwx.modules.health.service.impl;

 import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
 import com.baomidou.mybatisplus.core.metadata.IPage;
 import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
 import com.ljwx.infrastructure.page.PageQuery;
 import com.ljwx.modules.health.domain.bo.TDeviceUserBO;
 import com.ljwx.modules.health.domain.entity.TDeviceUser;
 import com.ljwx.modules.health.domain.vo.TDeviceUserVO;
 import com.ljwx.modules.health.repository.mapper.TDeviceUserMapper;
 import com.ljwx.modules.system.service.ISysUserService;
 import com.ljwx.modules.health.service.ITDeviceUserService;
 import com.ljwx.modules.system.domain.entity.SysUser;
 import org.apache.commons.lang3.ObjectUtils;
 import org.springframework.beans.BeanUtils;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.stereotype.Service;
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
 
 import java.time.LocalDateTime;
 import com.ljwx.modules.system.service.ISysOrgUnitsService;
 import com.ljwx.modules.system.domain.entity.SysOrgUnits;
 import com.ljwx.modules.system.domain.entity.SysUserOrg;
 import com.ljwx.modules.system.service.ISysUserOrgService;
 import com.ljwx.modules.health.domain.entity.TDeviceInfo;
 import com.ljwx.modules.health.service.ITDeviceInfoService;
 import org.springframework.transaction.annotation.Transactional;
 
 import java.util.List;
 import java.util.Collections;
 import java.util.ArrayList;
 import java.util.stream.Collectors;
 /**
  * 设备与用户关联表 Service 服务接口实现层
  *
  * @Author jjgao
  * @ProjectName ljwx-boot
  * @ClassName com.ljwx.modules.health.service.impl.TDeviceUserServiceImpl
  * @CreateTime 2025-01-03 - 15:12:29
  */
 
 @Service
 public class TDeviceUserServiceImpl extends ServiceImpl<TDeviceUserMapper, TDeviceUser> implements ITDeviceUserService {
 
     private static final Logger log = LoggerFactory.getLogger(TDeviceUserServiceImpl.class);
     @Autowired
     private ISysUserService sysUserService;
 
     @Autowired
     private ISysOrgUnitsService sysOrgUnitsService;
 
     @Autowired
     private ISysUserOrgService sysUserOrgService;
 
     @Autowired
     private ITDeviceInfoService deviceInfoService;
 
     @Override
     public IPage<TDeviceUserVO> listTDeviceUserPage(PageQuery pageQuery, TDeviceUserBO tDeviceUserBO) {
         // 先查询设备用户关联记录
         LambdaQueryWrapper<TDeviceUser> queryWrapper = new LambdaQueryWrapper<TDeviceUser>()
         .eq(ObjectUtils.isNotEmpty(tDeviceUserBO.getDeviceSn()), TDeviceUser::getDeviceSn, tDeviceUserBO.getDeviceSn())
         .eq(ObjectUtils.isNotEmpty(tDeviceUserBO.getUserName()), TDeviceUser::getUserName, tDeviceUserBO.getUserName())
         .eq(ObjectUtils.isNotEmpty(tDeviceUserBO.getStatus()), TDeviceUser::getStatus, tDeviceUserBO.getStatus())
         .orderByDesc(TDeviceUser::getOperateTime);
    
         if (ObjectUtils.isNotEmpty(tDeviceUserBO.getUserId()) && !tDeviceUserBO.getUserId().equals("all")) {
                     queryWrapper.eq(TDeviceUser::getUserId, tDeviceUserBO.getUserId());
         } else if (ObjectUtils.isNotEmpty(tDeviceUserBO.getDepartmentInfo())) {
                     Long deptId = Long.parseLong(tDeviceUserBO.getDepartmentInfo());
                     List<SysOrgUnits> descendants = sysOrgUnitsService.listAllDescendants(Collections.singletonList(deptId));
                     
                     List<String> allDeptIds = new ArrayList<>();
                     allDeptIds.add(tDeviceUserBO.getDepartmentInfo());
                     if (descendants != null) {
                         allDeptIds.addAll(descendants.stream()
                             .map(unit -> String.valueOf(unit.getId()))
                             .collect(Collectors.toList()));
                     }
                     
                     List<Long> userIds = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
                         .in(SysUserOrg::getOrgId, allDeptIds))
                         .stream()
                         .map(SysUserOrg::getUserId)
                         .collect(Collectors.toList());
                     System.out.println("listTDeviceUserPage::userIds: " + userIds);
                     if (!userIds.isEmpty()) {
                         queryWrapper.in(TDeviceUser::getUserId, userIds);
                     } 
             }
         IPage<TDeviceUser> page = baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
  
 
         // 转换为VO并添加用户信息
         return page.convert(deviceUser -> {
             TDeviceUserVO vo = new TDeviceUserVO();
             BeanUtils.copyProperties(deviceUser, vo);
             
             // 获取并设置用户名
             SysUser user = sysUserService.getById(deviceUser.getUserId());
             if (user != null) {
                 vo.setUserName(user.getUserName());
             }
             
             return vo;
         });
     }
 
     @Override
     @Transactional
     public boolean bindDevice(String deviceSn, String userId, String userName) {
         try {
             // 1. 保存设备用户绑定记录
             TDeviceUser deviceUser = new TDeviceUser();
             deviceUser.setDeviceSn(deviceSn);
             deviceUser.setUserId(userId);
             deviceUser.setUserName(userName);
             deviceUser.setOperateTime(LocalDateTime.now());
             deviceUser.setStatus("BIND");
             deviceUser.setIsDeleted(0);
             boolean bindResult = this.save(deviceUser);
             
             if (bindResult) {
                 // 2. 获取用户组织信息
                 Long orgId = getUserOrgId(Long.valueOf(userId));
                 
                 // 3. 更新t_device_info表的org_id和user_id
                 TDeviceInfo deviceInfo = deviceInfoService.lambdaQuery()
                     .eq(TDeviceInfo::getSerialNumber, deviceSn)
                     .one();
                 
                 if (deviceInfo != null) {
                     deviceInfo.setUserId(Long.valueOf(userId));
                     deviceInfo.setOrgId(orgId);
                     deviceInfoService.updateById(deviceInfo);
                     log.info("设备{}绑定成功，用户ID：{}，组织ID：{}", deviceSn, userId, orgId);
                 } else {
                     log.warn("设备{}在t_device_info表中不存在", deviceSn);
                 }
             }
             
             return bindResult;
         } catch (Exception e) {
             log.error("设备绑定失败", e);
             return false;
         }
     }
 
     @Override
     @Transactional
     public boolean unbindDevice(String deviceSn, String userId, String userName) {
         try {
             // 1. 保存设备用户解绑记录
             TDeviceUser deviceUser = new TDeviceUser();
             deviceUser.setDeviceSn(deviceSn);
             deviceUser.setUserId(userId);
             deviceUser.setUserName(userName);
             deviceUser.setOperateTime(LocalDateTime.now());
             deviceUser.setStatus("UNBIND");
             deviceUser.setIsDeleted(0);
             boolean unbindResult = this.save(deviceUser);
             
             if (unbindResult) {
                 // 2. 清空t_device_info表的org_id和user_id
                 TDeviceInfo deviceInfo = deviceInfoService.lambdaQuery()
                     .eq(TDeviceInfo::getSerialNumber, deviceSn)
                     .one();
                 
                 if (deviceInfo != null) {
                     deviceInfo.setUserId(null);
                     deviceInfo.setOrgId(null);
                     deviceInfoService.updateById(deviceInfo);
                     log.info("设备{}解绑成功，已清空org_id和user_id", deviceSn);
                 } else {
                     log.warn("设备{}在t_device_info表中不存在", deviceSn);
                 }
             }
             
             return unbindResult;
         } catch (Exception e) {
             log.error("设备解绑失败", e);
             return false;
         }
     }
 
     /**
      * 获取用户所属组织ID
      */
     private Long getUserOrgId(Long userId) {
         try {
             SysUserOrg userOrg = sysUserOrgService.lambdaQuery()
                 .eq(SysUserOrg::getUserId, userId)
                 .one();
             return userOrg != null ? userOrg.getOrgId() : null;
         } catch (Exception e) {
             log.error("获取用户组织信息失败，用户ID：{}", userId, e);
             return null;
         }
     }
 
 }
 
 