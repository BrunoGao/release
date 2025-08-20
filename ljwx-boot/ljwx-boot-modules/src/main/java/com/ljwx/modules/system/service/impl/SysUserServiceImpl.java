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
import com.ljwx.modules.system.domain.entity.SysPosition;
import com.ljwx.modules.system.domain.entity.SysUserPosition;
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
import org.springframework.web.multipart.MultipartFile;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.InputStream;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Arrays;
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
    private ISysPositionService sysPositionService;

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

    @Override
    @Transactional
    public Map<String, Object> batchImportUsers(MultipartFile file, String orgIds) {
        List<Map<String, Object>> successList = new ArrayList<>();
        List<Map<String, Object>> failedList = new ArrayList<>();
        
        try {
            // 解析组织ID列表
            List<Long> orgIdList = parseOrgIds(orgIds);
            
            // 解析Excel文件
            List<Map<String, Object>> userData = parseExcelFile(file);
            
            // 逐行处理用户数据
            for (int i = 0; i < userData.size(); i++) {
                Map<String, Object> row = userData.get(i);
                int rowNum = i + 2; // Excel从第2行开始
                
                try {
                    // 验证数据格式
                    validateUserData(row, rowNum);
                    
                    // 创建用户
                    Long userId = createUserFromRow(row, orgIdList);
                    
                    // 记录成功
                    Map<String, Object> success = new HashMap<>();
                    success.put("row", rowNum);
                    success.put("name", row.get("姓名"));
                    success.put("userId", userId);
                    successList.add(success);
                    
                } catch (Exception e) {
                    // 记录失败
                    Map<String, Object> failed = new HashMap<>();
                    failed.put("row", rowNum);
                    failed.put("reason", e.getMessage());
                    failed.put("data", row);
                    failedList.add(failed);
                    log.error("导入第{}行用户失败: {}", rowNum, e.getMessage());
                }
            }
            
        } catch (Exception e) {
            log.error("批量导入用户失败", e);
            Map<String, Object> failed = new HashMap<>();
            failed.put("row", 1);
            failed.put("reason", "文件解析失败: " + e.getMessage());
            failedList.add(failed);
        }
        
        Map<String, Object> result = new HashMap<>();
        result.put("success", successList);
        result.put("failed", failedList);
        result.put("total", successList.size() + failedList.size());
        
        return result;
    }

    private List<Long> parseOrgIds(String orgIds) {
        List<Long> result = new ArrayList<>();
        try {
            ObjectMapper mapper = new ObjectMapper();
            List<String> orgIdStrList = mapper.readValue(orgIds, List.class);
            for (String orgIdStr : orgIdStrList) {
                result.add(Long.parseLong(orgIdStr));
            }
        } catch (Exception e) {
            log.error("解析组织ID失败: {}", e.getMessage());
        }
        return result;
    }

    private List<Map<String, Object>> parseExcelFile(MultipartFile file) throws Exception {
        List<Map<String, Object>> result = new ArrayList<>();
        String fileName = file.getOriginalFilename();
        
        if (fileName == null) {
            throw new RuntimeException("文件名不能为空");
        }
        
        String lowerFileName = fileName.toLowerCase();
        
        if (lowerFileName.endsWith(".csv")) {
            // 处理CSV文件
            result = parseCSVFile(file);
        } else if (lowerFileName.endsWith(".xlsx") || lowerFileName.endsWith(".xls")) {
            // 处理Excel文件
            result = parseExcelWorkbook(file);
        } else {
            throw new RuntimeException("不支持的文件格式，请上传Excel文件(.xlsx, .xls)或CSV文件");
        }
        
        return result;
    }
    
    private List<Map<String, Object>> parseCSVFile(MultipartFile file) throws Exception {
        List<Map<String, Object>> result = new ArrayList<>();
        
        try (InputStream inputStream = file.getInputStream()) {
            // 读取CSV文件内容
            String content = new String(inputStream.readAllBytes(), "UTF-8");
            if (content.startsWith("\uFEFF")) {
                content = content.substring(1); // 移除BOM
            }
            
            String[] lines = content.split("\n");
            if (lines.length < 2) {
                throw new RuntimeException("文件内容不足，至少需要表头和一行数据");
            }
            
            // 解析表头
            String[] headers = parseCSVLine(lines[0]);
            List<String> headerList = Arrays.asList(headers);
            
            // 验证必要的列
            validateHeaders(headerList);
            
            // 解析数据行
            for (int i = 1; i < lines.length; i++) {
                String line = lines[i].trim();
                if (line.isEmpty()) continue;
                
                String[] values = parseCSVLine(line);
                Map<String, Object> data = new HashMap<>();
                
                for (int j = 0; j < headers.length && j < values.length; j++) {
                    data.put(headers[j], values[j]);
                }
                
                // 跳过空行
                if (!isEmptyRow(data)) {
                    result.add(data);
                }
            }
        }
        
        return result;
    }
    
    private List<Map<String, Object>> parseExcelWorkbook(MultipartFile file) throws Exception {
        List<Map<String, Object>> result = new ArrayList<>();
        
        try (InputStream inputStream = file.getInputStream()) {
            Workbook workbook = null;
            String fileName = file.getOriginalFilename();
            
            if (fileName != null && fileName.toLowerCase().endsWith(".xlsx")) {
                workbook = new XSSFWorkbook(inputStream);
            } else if (fileName != null && fileName.toLowerCase().endsWith(".xls")) {
                workbook = new HSSFWorkbook(inputStream);
            } else {
                throw new RuntimeException("不支持的Excel文件格式");
            }
            
            Sheet sheet = workbook.getSheetAt(0);
            Row headerRow = sheet.getRow(0);
            
            if (headerRow == null) {
                throw new RuntimeException("Excel文件格式错误，缺少表头");
            }
            
            // 读取表头
            List<String> headers = new ArrayList<>();
            for (Cell cell : headerRow) {
                headers.add(getCellValueAsString(cell));
            }
            
            // 验证必要的列
            validateHeaders(headers);
            
            // 读取数据行
            for (int i = 1; i <= sheet.getLastRowNum(); i++) {
                Row row = sheet.getRow(i);
                if (row == null) continue;
                
                Map<String, Object> data = new HashMap<>();
                for (int j = 0; j < headers.size() && j < row.getLastCellNum(); j++) {
                    Cell cell = row.getCell(j);
                    data.put(headers.get(j), getCellValueAsString(cell));
                }
                
                // 跳过空行
                if (!isEmptyRow(data)) {
                    result.add(data);
                }
            }
            
            workbook.close();
        }
        
        return result;
    }
    
    private void validateHeaders(List<String> headers) {
        String[] requiredHeaders = {"姓名", "性别", "年龄", "工龄", "手机号码", "部门", "岗位"};
        for (String required : requiredHeaders) {
            if (!headers.contains(required)) {
                throw new RuntimeException("文件缺少必要的列: " + required);
            }
        }
    }
    
    private String getCellValueAsString(Cell cell) {
        if (cell == null) return "";
        
        switch (cell.getCellType()) {
            case STRING:
                return cell.getStringCellValue().trim();
            case NUMERIC:
                if (DateUtil.isCellDateFormatted(cell)) {
                    return cell.getDateCellValue().toString();
                } else {
                    return String.valueOf((long) cell.getNumericCellValue());
                }
            case BOOLEAN:
                return String.valueOf(cell.getBooleanCellValue());
            case FORMULA:
                return cell.getCellFormula();
            default:
                return "";
        }
    }
    
    private String[] parseCSVLine(String line) {
        List<String> result = new ArrayList<>();
        boolean inQuotes = false;
        StringBuilder field = new StringBuilder();
        
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            
            if (c == '"') {
                inQuotes = !inQuotes;
            } else if (c == ',' && !inQuotes) {
                result.add(field.toString().trim());
                field.setLength(0);
            } else {
                field.append(c);
            }
        }
        
        result.add(field.toString().trim());
        return result.toArray(new String[0]);
    }

    private boolean isEmptyRow(Map<String, Object> data) {
        return data.values().stream()
                .allMatch(value -> value == null || value.toString().trim().isEmpty());
    }

    private void validateUserData(Map<String, Object> data, int rowNum) {
        // 验证必填字段
        String[] requiredFields = {"姓名", "性别", "年龄", "工龄", "手机号码", "部门", "岗位"};
        for (String field : requiredFields) {
            String value = (String) data.get(field);
            if (value == null || value.trim().isEmpty()) {
                throw new RuntimeException("第" + rowNum + "行: " + field + "不能为空");
            }
        }
        
        // 验证年龄格式
        try {
            int age = Integer.parseInt(((String) data.get("年龄")).trim());
            if (age < 0 || age > 120) {
                throw new RuntimeException("第" + rowNum + "行: 年龄必须在0-120之间");
            }
        } catch (NumberFormatException e) {
            throw new RuntimeException("第" + rowNum + "行: 年龄格式不正确");
        }
        
        // 验证工龄格式
        try {
            int workingYears = Integer.parseInt(((String) data.get("工龄")).trim());
            if (workingYears < 0) {
                throw new RuntimeException("第" + rowNum + "行: 工龄不能为负数");
            }
        } catch (NumberFormatException e) {
            throw new RuntimeException("第" + rowNum + "行: 工龄格式不正确");
        }
        
        // 验证手机号格式
        String phone = ((String) data.get("手机号码")).trim();
        if (!phone.matches("^1[3-9]\\d{9}$")) {
            throw new RuntimeException("第" + rowNum + "行: 手机号码格式不正确");
        }
        
        // 验证性别
        String gender = ((String) data.get("性别")).trim();
        if (!gender.equals("男") && !gender.equals("女")) {
            throw new RuntimeException("第" + rowNum + "行: 性别只能是'男'或'女'");
        }
    }

    private Long createUserFromRow(Map<String, Object> data, List<Long> orgIdList) {
        // 查找部门
        String deptName = ((String) data.get("部门")).trim();
        Long deptId = findDepartmentByName(deptName, orgIdList);
        if (deptId == null) {
            throw new RuntimeException("部门'" + deptName + "'不存在或不唯一");
        }
        
        // 查找岗位
        String positionName = ((String) data.get("岗位")).trim();
        Long positionId = findPositionByName(positionName);
        if (positionId == null) {
            throw new RuntimeException("岗位'" + positionName + "'不存在或不唯一");
        }
        
        // 检查手机号是否已存在
        String phone = ((String) data.get("手机号码")).trim();
        if (checkPhoneExists(phone)) {
            throw new RuntimeException("手机号码'" + phone + "'已存在");
        }
        
        // 创建用户
        SysUser user = new SysUser();
        user.setUserName(generateUserName(phone));
        user.setRealName(((String) data.get("姓名")).trim());
        user.setGender("男".equals(((String) data.get("性别")).trim()) ? "1" : "2");
        user.setWorkingYears(Integer.parseInt(((String) data.get("工龄")).trim()));
        user.setPhone(phone);
        user.setEmail(phone + "@example.com"); // 设置默认邮箱，避免数据库字段缺失错误
        user.setPassword(DigestUtils.md5Hex("123456")); // 默认密码，使用MD5加密
        user.setStatus("1"); // 启用状态
        
        // 设备序列号（可选）
        String deviceSn = (String) data.get("设备序列号");
        if (deviceSn != null && !deviceSn.trim().isEmpty()) {
            user.setDeviceSn(deviceSn.trim());
        }
        
        // 备注字段在SysUser中不存在，跳过
        
        // 保存用户
        this.save(user);
        
        // 建立用户-部门关系
        createUserOrgRelation(user.getId(), deptId);
        
        // 建立用户-岗位关系
        createUserPositionRelation(user.getId(), positionId);
        
        return user.getId();
    }

    private String generateUserName(String phone) {
        // 使用手机号后6位作为用户名
        return "user" + phone.substring(phone.length() - 6);
    }

    private boolean checkPhoneExists(String phone) {
        return this.lambdaQuery()
                .eq(SysUser::getPhone, phone)
                .exists();
    }

    private Long findDepartmentByName(String deptName, List<Long> orgIdList) {
        // 首先尝试按ID查找（如果输入的是数字）
        try {
            Long deptId = Long.parseLong(deptName.trim());
            return sysOrgUnitsService.lambdaQuery()
                    .eq(SysOrgUnits::getId, deptId)
                    .in(!orgIdList.isEmpty(), SysOrgUnits::getId, orgIdList)
                    .oneOpt()
                    .map(SysOrgUnits::getId)
                    .orElse(null);
        } catch (NumberFormatException e) {
            // 如果不是数字，按名称查找
            return sysOrgUnitsService.lambdaQuery()
                    .eq(SysOrgUnits::getName, deptName)
                    .in(!orgIdList.isEmpty(), SysOrgUnits::getId, orgIdList)
                    .oneOpt()
                    .map(SysOrgUnits::getId)
                    .orElse(null);
        }
    }

    private Long findPositionByName(String positionName) {
        // 首先尝试按ID查找（如果输入的是数字）
        try {
            Long positionId = Long.parseLong(positionName.trim());
            return sysPositionService.lambdaQuery()
                    .eq(SysPosition::getId, positionId)
                    .oneOpt()
                    .map(SysPosition::getId)
                    .orElse(null);
        } catch (NumberFormatException e) {
            // 如果不是数字，按名称查找
            return sysPositionService.lambdaQuery()
                    .eq(SysPosition::getName, positionName)
                    .oneOpt()
                    .map(SysPosition::getId)
                    .orElse(null);
        }
    }

    private void createUserOrgRelation(Long userId, Long orgId) {
        SysUserOrg userOrg = new SysUserOrg();
        userOrg.setUserId(userId);
        userOrg.setOrgId(orgId);
        sysUserOrgService.save(userOrg);
    }

    private void createUserPositionRelation(Long userId, Long positionId) {
        SysUserPosition userPosition = new SysUserPosition();
        userPosition.setUserId(userId);
        userPosition.setPositionId(positionId);
        sysUserPositionService.save(userPosition);
    }
}
