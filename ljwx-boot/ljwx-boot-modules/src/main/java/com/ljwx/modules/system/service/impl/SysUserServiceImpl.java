package com.ljwx.modules.system.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import cn.hutool.extra.servlet.JakartaServletUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.common.constants.RequestConstant;
import com.ljwx.common.domain.LoginUser;
import com.ljwx.common.exception.BizException;
import com.ljwx.common.pool.StringPools;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.common.util.IPUtil;
import com.ljwx.infrastructure.holder.GlobalUserHolder;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.util.RedisUtil;
import com.ljwx.infrastructure.util.ServletHolderUtil;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.ljwx.modules.health.domain.vo.MessageResponseDetailVO;
import com.ljwx.modules.health.service.ITDeviceInfoService;
import com.ljwx.modules.health.service.ITDeviceUserService;

import com.ljwx.modules.monitor.domain.entity.MonLogsLogin;
import com.ljwx.modules.monitor.service.IMonLogsLoginService;
import com.ljwx.modules.system.domain.bo.SysRoleBO;
import com.ljwx.modules.system.domain.bo.SysUserBO;
import com.ljwx.modules.system.domain.bo.SysUserOrgBO;
import com.ljwx.modules.system.domain.bo.SysPositionBO;
import com.ljwx.modules.system.domain.bo.SysUserResponsibilitiesBO;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysRole;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.domain.entity.SysUserOrg;
import com.ljwx.modules.system.domain.entity.SysUserRole;
import com.ljwx.modules.system.repository.mapper.SysUserMapper;
import com.ljwx.modules.system.service.*;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.RandomStringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 用户管理 Service 服务接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.SysUserServiceImpl
 * @CreateTime 2023/7/6 - 16:04
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SysUserServiceImpl extends ServiceImpl<SysUserMapper, SysUser> implements ISysUserService {

    @NonNull
    private ISysRoleService sysRoleService;

    @NonNull
    private ISysUserRoleService sysUserRoleService;

    @NonNull
    private ISysUserOrgService sysUserOrgService;

    @NonNull
    private ISysUserPositionService sysUserPositionService;

    @NonNull
    private IMonLogsLoginService monLogsLoginService;

    @NonNull
    private ISysOrgUnitsService sysOrgUnitsService;

    @Autowired
    private ITDeviceUserService deviceUserService;
    
    @Autowired
    private ITDeviceInfoService deviceInfoService;

    @Override
    public IPage<SysUser> listSysUserPage(PageQuery pageQuery, SysUserBO sysUserBO) {
        IPage<SysUser> iPage = pageQuery.buildPage();
        iPage.setRecords(baseMapper.listSysUserPage(iPage, sysUserBO));
        return iPage;
    }

    @Override
    public IPage<SysUser> listNonAdminUsersPage(PageQuery pageQuery, SysUserBO sysUserBO) {
        IPage<SysUser> iPage = pageQuery.buildPage();
        List<SysUser> records = baseMapper.listNonAdminUsersPage(iPage, sysUserBO);
        Long total = baseMapper.countNonAdminUsers(sysUserBO);
        iPage.setRecords(records);
        iPage.setTotal(total);
        return iPage;
    }

    @Override
    public IPage<SysUser> listAdminUsersPage(PageQuery pageQuery, SysUserBO sysUserBO) {
        IPage<SysUser> iPage = pageQuery.buildPage();
        List<SysUser> records = baseMapper.listAdminUsersPage(iPage, sysUserBO);
        Long total = baseMapper.countAdminUsers(sysUserBO);
        iPage.setRecords(records);
        iPage.setTotal(total);
        return iPage;
    }

    @Override
    public SysUserBO currentUserInfo() {
        Long userId = GlobalUserHolder.getUserId();
        // 获取用户基本信息
        SysUser user = super.getById(userId);
        if (user == null) {
            return null;
        }

        // 转换为BO对象
        SysUserBO userBO = CglibUtil.convertObj(user, SysUserBO::new);

        List<SysUserOrgBO> sysUserOrgBOList = sysUserOrgService.queryOrgUnitsListWithUserId(userId);
        if (sysUserOrgBOList.size() > 0) {
            userBO.setOrgIds(sysUserOrgBOList.stream().map(SysUserOrgBO::getOrgId).toList());
            userBO.setCustomerId(sysUserOrgBOList.get(0).getOrgId());
        }

        System.out.println("getPositionNameByUserId: " + baseMapper.getPositionNameByUserId(userId));

        userBO.setPositionName(baseMapper.getPositionNameByUserId(userId));

        System.out.println("sysUserOrgBOList: " + sysUserOrgBOList.toString());

        return userBO;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean addUser(SysUserBO sysUserBO) {
        try {
            // 密码盐值
            sysUserBO.setSalt(RandomStringUtils.randomAlphabetic(6));
            // 默认随机12位密码
            String sha256HexPwd = DigestUtils.sha256Hex(RandomStringUtils.randomAlphabetic(12));
            String password = DigestUtils.sha256Hex(sha256HexPwd + sysUserBO.getSalt());
            sysUserBO.setPassword(password);

            // 生成用户卡号
            if (ObjectUtils.isNotEmpty(sysUserBO.getOrgIds())) {
                // 获取部门code
                SysOrgUnits orgUnit = sysOrgUnitsService.getById(sysUserBO.getOrgIds().get(0));
                if (orgUnit != null) {
                    // 查询该部门现有用户数
                    Long userCount = sysUserOrgService.count(new LambdaQueryWrapper<SysUserOrg>()
                        .eq(SysUserOrg::getOrgId, orgUnit.getId()));
                    
                    // 生成卡号：部门code-序号
                    String cardNumber = orgUnit.getCode() + "-" + String.format("%03d", userCount + 1);
                    sysUserBO.setUserCardNumber(cardNumber);
                }
            }

            // 保存用户基本信息
            boolean saved = super.save(sysUserBO);
            if (!saved) {
                throw new RuntimeException("保存用户基本信息失败");
            }

            // 保存用户-部门关系
            if (ObjectUtils.isNotEmpty(sysUserBO.getOrgIds())) {
                List<SysUserOrg> userOrgs = sysUserBO.getOrgIds().stream()
                    .map(orgId -> {
                        SysUserOrg userOrg = new SysUserOrg();
                        userOrg.setUserId(sysUserBO.getId());
                        userOrg.setOrgId(orgId);
                        return userOrg;
                    })
                    .collect(Collectors.toList());
                boolean orgsSaved = sysUserOrgService.saveBatch(userOrgs);
                if (!orgsSaved) {
                    throw new RuntimeException("保存用户部门关系失败");
                }
            }

            // 处理设备绑定
            if (StringUtils.hasText(sysUserBO.getDeviceSn())) {
                TDeviceInfo deviceInfo = deviceInfoService.getOne(new LambdaQueryWrapper<TDeviceInfo>()
                    .eq(TDeviceInfo::getSerialNumber, sysUserBO.getDeviceSn()));
                if (deviceInfo != null) {
                    boolean deviceBound = deviceUserService.bindDevice(
                        deviceInfo.getSerialNumber(), 
                        sysUserBO.getId().toString(), 
                        sysUserBO.getUserName()
                    );
                    if (!deviceBound) {
                        throw new RuntimeException("设备绑定失败");
                    }
                }
            }
            
            return true;
        } catch (Exception e) {
            log.error("添加用户失败", e);
            throw new RuntimeException("添加用户失败: " + e.getMessage());
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateUser(SysUserBO sysUserBO) {
        try {
            // 1. 更新用户基本信息
            SysUser oldUser = this.getById(sysUserBO.getId());
            String newDeviceSn = sysUserBO.getDeviceSn();
            String oldDeviceSn = oldUser.getDeviceSn();
            boolean updated = super.updateById(sysUserBO);
           
            if (!updated) {
                throw new RuntimeException("更新用户基本信息失败");
            }

            // 2. 更新用户-部门关系
            if (ObjectUtils.isNotEmpty(sysUserBO.getOrgIds())) {
                // 先删除原有关系
                boolean removed = sysUserOrgService.remove(new LambdaQueryWrapper<SysUserOrg>()
                    .eq(SysUserOrg::getUserId, sysUserBO.getId()));
                if (!removed) {
                    throw new RuntimeException("删除原有部门关系失败");
                }

                // 添加新的关系
                List<SysUserOrg> userOrgs = sysUserBO.getOrgIds().stream()
                    .map(orgId -> {
                        SysUserOrg userOrg = new SysUserOrg();
                        userOrg.setUserId(sysUserBO.getId());
                        userOrg.setOrgId(orgId);
                        return userOrg;
                    })
                    .collect(Collectors.toList());
                boolean orgsSaved = sysUserOrgService.saveBatch(userOrgs);
                if (!orgsSaved) {
                    throw new RuntimeException("保存新部门关系失败");
                }
            }

            // 3. 处理设备绑定更新
            if (StringUtils.hasText(newDeviceSn)) {             
                // 先解绑原有设备
                 // 解绑旧设备
                if (StringUtils.hasText(oldDeviceSn)) {
                    TDeviceInfo oldDevice = deviceInfoService.getOne(new LambdaQueryWrapper<TDeviceInfo>()
                        .eq(TDeviceInfo::getSerialNumber, oldDeviceSn).last("limit 1"));
                    System.out.println("oldDevice: " + oldDevice);
                    if (oldDevice != null || oldDeviceSn.equals("-")) {
                        deviceUserService.unbindDevice(oldDeviceSn, sysUserBO.getId().toString(), sysUserBO.getUserName());
                    }
                }
                // 绑定新设备
                TDeviceInfo deviceInfo = deviceInfoService.getOne(new LambdaQueryWrapper<TDeviceInfo>()
                    .eq(TDeviceInfo::getSerialNumber, newDeviceSn).last("limit 1"));
                if (deviceInfo != null || newDeviceSn.equals("-")) {
                    boolean deviceBound = deviceUserService.bindDevice(
                        newDeviceSn, 
                        sysUserBO.getId().toString(), 
                        sysUserBO.getUserName()
                    );
                    if (!deviceBound) {
                        throw new RuntimeException("设备绑定失败");
                    }
                }
            }

            return true;
        } catch (Exception e) {
            log.error("更新用户失败", e);
            throw new RuntimeException("更新用户失败: " + e.getMessage());
        }
    }

    @Override
    public boolean updateCurrentUserInfo(SysUserBO sysUserBO) {
        boolean updateById = super.updateById(sysUserBO);
        // 自我更新个人资料，需要更新缓存资料
        saveUserToSession(sysUserBO, true);
        return updateById;
    }

    @Override
    public boolean removeBatchByIds(List<Long> ids) {
        if (!StpUtil.hasRole(StringPools.ADMIN.toUpperCase())) {
            throw new BizException("非管理员角色禁止删除用户");
        }
        boolean containAdmin = baseMapper.queryIsContainAdmin(ids);
        if (containAdmin) {
            throw new BizException("禁止删除《管理员》用户");
        }
        
        // 直接删除用户，如果有设备绑定则自动解绑 #删除用户自动解绑设备
        return forceRemoveBatchByIds(ids, true);
    }

    @Override
    public List<Map<String, Object>> checkUserDeviceBinding(List<Long> userIds) {
        List<Map<String, Object>> result = new ArrayList<>();
        for (Long userId : userIds) {
            SysUser user = this.getById(userId);
            // 检查用户是否绑定了设备：device_sn不为空且不为'-'才算绑定 #设备绑定状态检查
            if (user != null && user.getDeviceSn() != null && 
                !user.getDeviceSn().trim().isEmpty() && 
                !"-".equals(user.getDeviceSn().trim())) {
                Map<String, Object> bindingInfo = new HashMap<>();
                bindingInfo.put("userId", userId);
                bindingInfo.put("userName", user.getRealName() != null ? user.getRealName() : user.getUserName());
                bindingInfo.put("deviceSn", user.getDeviceSn());
                result.add(bindingInfo);
                log.info("检测到用户 {} (ID: {}) 绑定了设备: {}", user.getUserName(), userId, user.getDeviceSn());
            }
        }
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean forceRemoveBatchByIds(List<Long> userIds, boolean forceUnbind) {
        if (!StpUtil.hasRole(StringPools.ADMIN.toUpperCase())) {
            throw new BizException("非管理员角色禁止删除用户");
        }
        boolean containAdmin = baseMapper.queryIsContainAdmin(userIds);
        if (containAdmin) {
            throw new BizException("禁止删除《管理员》用户");
        }
        
        if (forceUnbind) {
            // 先解绑设备 #用户删除前设备解绑处理
            for (Long userId : userIds) {
                SysUser user = this.getById(userId);
                if (user != null && user.getDeviceSn() != null && 
                    !user.getDeviceSn().trim().isEmpty() && 
                    !"-".equals(user.getDeviceSn().trim())) {
                    
                    String originalDeviceSn = user.getDeviceSn();
                    try {
                        log.info("用户删除：开始解绑用户 {} (ID: {}) 的设备: {}", user.getUserName(), userId, originalDeviceSn);
                        
                        // 1. 记录设备解绑操作
                        boolean unbindResult = deviceUserService.unbindDevice(originalDeviceSn, userId.toString(), user.getUserName());
                        log.info("用户删除：设备解绑服务调用结果: {}", unbindResult);
                        
                        // 2. 清空用户设备绑定字段
                        user.setDeviceSn(null);
                        boolean updateResult = this.updateById(user);
                        log.info("用户删除：用户设备字段清空结果: {}", updateResult);
                        
                        log.info("用户删除：已解绑用户 {} (ID: {}) 的设备: {}", user.getUserName(), userId, originalDeviceSn);
                    } catch (Exception e) {
                        log.error("用户删除：解绑设备失败，用户: {} (ID: {}), 设备: {}", user.getUserName(), userId, originalDeviceSn, e);
                        // 即使解绑失败也要清空设备字段，确保用户可以被删除
                        try {
                            user.setDeviceSn(null);
                            boolean forceUpdateResult = this.updateById(user);
                            log.info("用户删除：强制清空设备绑定字段，用户: {} (ID: {}), 结果: {}", user.getUserName(), userId, forceUpdateResult);
                        } catch (Exception ex) {
                            log.error("用户删除：强制清空设备绑定字段失败，用户: {} (ID: {})", user.getUserName(), userId, ex);
                        }
                    }
                }
            }
        }
        
        // 执行删除操作
        return super.removeBatchByIds(userIds, true);
    }

    @Override
    public Map<String, String> userLogin(SysUserBO sysUserBO) {
        MonLogsLogin loginLogs = initLoginLog(sysUserBO);
        SysUser userForUserName = baseMapper.getUserByUserName(sysUserBO.getUserName());
        try {
            if (ObjectUtils.isEmpty(userForUserName)) {
                throw new BizException("查找不到用户名 %s".formatted(sysUserBO.getUserName()));
            }
            if (StringPools.ZERO.equals(userForUserName.getStatus())) {
                throw new BizException("当前用户 %s 已被禁止登录".formatted(sysUserBO.getUserName()));
            }
            // 密码拼接
            String inputPassword = sysUserBO.getPassword() + userForUserName.getSalt();
            // 密码比对
            if (!DigestUtils.sha256Hex(inputPassword).equals(userForUserName.getPassword())) {
                throw new BizException("登录失败，请核实用户名以及密码");
            }
            // sa token 进行登录
            StpUtil.login(userForUserName.getId());
            // 更新用户登录时间
            userForUserName.setLastLoginTime(LocalDateTime.now());
            saveUserToSession(userForUserName, false);
            loginLogs.setUserId(userForUserName.getId());
            loginLogs.setUserRealName(userForUserName.getRealName());
            super.updateById(userForUserName);
        } catch (BizException e) {
            loginLogs.setStatus(StringPools.ZERO);
            loginLogs.setMessage(e.getMessage());
            throw e;
        } finally {
            monLogsLoginService.save(loginLogs);
        }
        return Map.of("token", StpUtil.getTokenValue());
    }

    /**
     * 初始化登录日志
     *
     * @param sysUserBO 用户对象
     * @return {@linkplain MonLogsLogin} 登录日志对象
     * @author payne.zhuang
     * @CreateTime 2024-05-05 18:44
     */
    private MonLogsLogin initLoginLog(SysUserBO sysUserBO) {
        String ip = JakartaServletUtil.getClientIP(ServletHolderUtil.getRequest());
        return MonLogsLogin.builder()
                .userName(sysUserBO.getUserName())
                .status(StringPools.ONE)
                .userAgent(ServletHolderUtil.getRequest().getHeader(RequestConstant.USER_AGENT))
                .ip(ip)
                .ipAddr(IPUtil.getIpAddr(ip))
                .message("登陆成功")
                .build();
    }

    /**
     * 将用户信息存入 Session
     *
     * @param sysUser   用户对象
     * @param needCheck 是否需要查找数据库用户信息
     * @author payne.zhuang
     * @CreateTime 2024-04-21 22:19
     */
    private void saveUserToSession(SysUser sysUser, boolean needCheck) {
        if (needCheck) {
            sysUser = super.getById(sysUser.getId());
        }
        // 用户转换
        LoginUser loginUser = CglibUtil.convertObj(sysUser, LoginUser::new);
        // 获取用户角色
        List<SysRoleBO> sysRoleBOS = sysRoleService.queryRoleListWithUserId(sysUser.getId());
        loginUser.setRoleIds(sysRoleBOS.stream().map(SysRoleBO::getId).toList());
        loginUser.setRoleCodes(sysRoleBOS.stream().map(SysRoleBO::getRoleCode).toList());
        // Session 放入用户对象
        StpUtil.getSessionByLoginId(sysUser.getId()).set("user", loginUser);
    }

    @Override
    public Map<String, String> refreshToken(String refreshToken, String refreshTokenCacheKey, LoginUser loginUser) {
        // 删除 旧的 refresh token
        RedisUtil.del(refreshTokenCacheKey);
        return Map.of();
    }

    @Override
    public String resetPassword(Long userId) {
        if (!StpUtil.hasRole(StringPools.ADMIN.toUpperCase())) {
            throw new BizException("非管理员禁止重置用户密码");
        }
        SysUser sysUser = baseMapper.selectById(userId);
        if (ObjectUtils.isEmpty(sysUser)) {
            throw new BizException("查找不到用户信息");
        }
        if (StringPools.ADMIN.equalsIgnoreCase(sysUser.getUserName())) {
            throw new BizException("禁止重置《%s》账户密码".formatted(StringPools.ADMIN));
        }
        // 密码盐值
        sysUser.setSalt(RandomStringUtils.randomAlphabetic(6));
        // 默认随机12位密码
        String randomPwd = RandomStringUtils.randomAlphabetic(12);
        String sha256HexPwd = DigestUtils.sha256Hex(randomPwd);
        String password = DigestUtils.sha256Hex(sha256HexPwd + sysUser.getSalt());
        sysUser.setPassword(password);
        sysUser.setUpdatePasswordTime(LocalDateTime.now());
        super.updateById(sysUser);
        return randomPwd;
    }

    @Override
    public SysUserResponsibilitiesBO queryUserResponsibilitiesWithUserId(Long userId) {
        List<Long> userRoleIds = sysUserRoleService.queryRoleIdsWithUserId(userId);
        List<Long> userPositionIds = sysUserPositionService.queryPositionIdsWithUserId(userId);
        // 用户所属组织
        List<SysUserOrgBO> sysUserOrgBOList = sysUserOrgService.queryOrgUnitsListWithUserId(userId);
        List<Long> userOrgUnitsPrincipalIds = sysUserOrgBOList.stream()
                .filter(item -> StringPools.ONE.equals(item.getPrincipal()))
                .map(SysUserOrgBO::getOrgId).toList();
        List<Long> userOrgUnitsIds = sysUserOrgBOList.stream().map(SysUserOrgBO::getOrgId).toList();
        return SysUserResponsibilitiesBO.builder()
                .userId(userId)
                .roleIds(userRoleIds)
                .positionIds(userPositionIds)
                .orgUnitsIds(userOrgUnitsIds)
                .orgUnitsPrincipalIds(userOrgUnitsPrincipalIds)
                .build();
    }

    @Override
    public boolean updateUserResponsibilities(SysUserResponsibilitiesBO responsibilitiesBO) {
        Long userId = responsibilitiesBO.getUserId();
        boolean role = sysUserRoleService.updateUserRole(userId, responsibilitiesBO.getRoleIds());
        boolean position = sysUserPositionService.updateUserPosition(userId, responsibilitiesBO.getPositionIds());
        boolean userOrg = sysUserOrgService.updateUserOrg(userId, responsibilitiesBO.getOrgUnitsIds(), responsibilitiesBO.getOrgUnitsPrincipalIds());
        return role && position && userOrg;
    }

    @Override
    public List<String> getUnbindDevice(Long customerId) {
        return baseMapper.getUnbindDeviceSerialNumbers(customerId);
    }

    @Override
    public List<String> getBindDevice(Long customerId) {
        return baseMapper.getBindDeviceSerialNumbers(customerId);
    }

    @Override
    public List<SysUser> getUsersByOrgId(Long orgId) {
        log.info("getUsersByOrgId 被调用，orgId: {}", orgId);
        System.out.println("=== getUsersByOrgId Debug ===");
        System.out.println("orgId: " + orgId);
        
        // 获取所有子组织ID
        List<SysOrgUnits> descendants = sysOrgUnitsService.listAllDescendants(Collections.singletonList(orgId));
        List<Long> orgIds = new ArrayList<>();
        orgIds.add(orgId);
        orgIds.addAll(descendants.stream().map(SysOrgUnits::getId).toList());

        log.info("查询的组织ID列表: {}", orgIds);
        System.out.println("查询的组织ID列表: " + orgIds);

        // 如果没有找到任何组织，直接返回空列表
        if (orgIds.isEmpty()) {
            return Collections.emptyList();
        }
        
        // 查询这些组织下的所有已绑定设备的用户
        List<SysUser> allUsers = baseMapper.getUsersByOrgIds(orgIds);
        log.info("从数据库查询到的用户数量: {}", allUsers.size());
        System.out.println("从数据库查询到的用户数量: " + allUsers.size());
        
        // 过滤掉管理员用户
        List<SysUser> filteredUsers = allUsers.stream()
            .filter(user -> {
                boolean isAdmin = isAdminUser(user.getId());
                log.info("用户 {} (ID: {}) 是否管理员: {}", user.getUserName(), user.getId(), isAdmin);
                System.out.println("用户 " + user.getUserName() + " (ID: " + user.getId() + ") 是否管理员: " + isAdmin);
                return !isAdmin;
            })
            .collect(Collectors.toList());
            
        log.info("过滤后的用户数量: {}", filteredUsers.size());
        System.out.println("过滤后的用户数量: " + filteredUsers.size());
        System.out.println("=== getUsersByOrgId Debug End ===");
        return filteredUsers;
    }

    @Override
    public MessageResponseDetailVO.NonRespondedUserVO  getByDeviceSn(String deviceSn) {
        return baseMapper.getUserInfoByDeviceSn(deviceSn);
    }

    @Override
    public boolean isAdminUser(Long userId) {
        // 查询用户的所有角色，如果有任何一个角色是管理员角色，则该用户是管理员
        return sysUserRoleService.list(new LambdaQueryWrapper<SysUserRole>()
            .eq(SysUserRole::getUserId, userId)
            .eq(SysUserRole::getDeleted, false))
            .stream()
            .anyMatch(userRole -> {
                SysRole role = sysRoleService.getById(userRole.getRoleId());
                return role != null && role.getIsAdmin() != null && role.getIsAdmin() == 1;
            });
    }

    @Override
    public boolean isSuperAdmin(Long userId) {
        // 查询用户信息，检查用户名是否为admin
        SysUser user = baseMapper.selectById(userId);
        if (user == null) {
            return false;
        }
        
        // 检查用户名是否为admin（大小写不敏感）
        return StringPools.ADMIN.equalsIgnoreCase(user.getUserName());
    }

    @Override
    public boolean isTopLevelDeptAdmin(Long userId) {
        // 首先必须是管理员
        if (!isAdminUser(userId)) {
            return false;
        }
        
        // 获取用户所在的部门
        List<SysUserOrg> userOrgs = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
            .eq(SysUserOrg::getUserId, userId)
            .eq(SysUserOrg::getDeleted, false));
        
        // 检查是否在顶级部门
        return userOrgs.stream().anyMatch(userOrg -> {
            SysOrgUnits org = sysOrgUnitsService.getById(userOrg.getOrgId());
            return org != null && isTopLevelOrg(org.getParentId());
        });
    }

    @Override
    public boolean isSubDeptAdmin(Long userId) {
        // 首先必须是管理员
        if (!isAdminUser(userId)) {
            return false;
        }
        
        // 获取用户所在的部门
        List<SysUserOrg> userOrgs = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
            .eq(SysUserOrg::getUserId, userId)
            .eq(SysUserOrg::getDeleted, false));
        
        // 检查是否在下级部门
        return userOrgs.stream().anyMatch(userOrg -> {
            SysOrgUnits org = sysOrgUnitsService.getById(userOrg.getOrgId());
            return org != null && !isTopLevelOrg(org.getParentId());
        });
    }

    @Override
    public List<Long> getUserOrgIds(Long userId) {
        return sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
            .eq(SysUserOrg::getUserId, userId)
            .eq(SysUserOrg::getDeleted, false))
            .stream()
            .map(SysUserOrg::getOrgId)
            .collect(Collectors.toList());
    }

    @Override
    public Long getUserCustomerId(Long userId) {
        SysUser user = getById(userId);
        return user != null ? user.getCustomerId() : null;
    }

    @Override
    public Long getUserTopLevelDeptId(Long userId) {
        // 获取用户所在的部门
        List<SysUserOrg> userOrgs = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
            .eq(SysUserOrg::getUserId, userId)
            .eq(SysUserOrg::getDeleted, false));
        
        if (userOrgs.isEmpty()) {
            return null;
        }
        
        // 对每个用户所在的部门，找到其顶级部门
        for (SysUserOrg userOrg : userOrgs) {
            Long topLevelDeptId = sysOrgUnitsService.getTopLevelDeptIdByOrgId(userOrg.getOrgId());
            if (topLevelDeptId != null) {
                return topLevelDeptId;
            }
        }
        
        return null;
    }


    /**
     * 递归查找顶级部门ID
     */
    private Long findTopLevelDeptId(Long orgId) {
        if (orgId == null) {
            return null;
        }
        
        SysOrgUnits org = sysOrgUnitsService.getById(orgId);
        if (org == null) {
            return null;
        }
        
        // 如果是顶级部门，返回当前ID
        if (isTopLevelOrg(org.getParentId())) {
            return orgId;
        }
        
        // 否则继续向上查找
        return findTopLevelDeptId(org.getParentId());
    }

    /**
     * 判断是否是顶级组织
     */
    private boolean isTopLevelOrg(Long parentId) {
        return parentId == null || parentId == 0L || parentId == 1L;
    }
}
