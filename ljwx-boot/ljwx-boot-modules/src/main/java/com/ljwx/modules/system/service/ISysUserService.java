package com.ljwx.modules.system.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.common.domain.LoginUser;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.system.domain.bo.SysUserBO;
import com.ljwx.modules.system.domain.bo.SysUserResponsibilitiesBO;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.health.domain.vo.MessageResponseDetailVO;
import java.util.List;
import java.util.Map;

/**
 * 用户管理 Service 服务接口层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.ISysUserService
 * @CreateTime 2023/7/6 - 16:03
 */
public interface ISysUserService extends IService<SysUser> {

    /**
     * 用户管理 - 分页查询
     *
     * @param pageQuery 分页对象
     * @param sysUserBO BO 查询对象
     * @return {@link IPage} 分页结果
     * @author payne.zhuang
     * @CreateTime 2023-07-13 15:10
     */
    IPage<SysUser> listSysUserPage(PageQuery pageQuery, SysUserBO sysUserBO);

    /**
     * 用户管理 - 分页查询非管理员用户（排除管理员）
     *
     * @param pageQuery 分页对象
     * @param sysUserBO BO 查询对象
     * @return {@link IPage} 分页结果
     * @author bruno.gao
     * @CreateTime 2024-12-20
     */
    IPage<SysUser> listNonAdminUsersPage(PageQuery pageQuery, SysUserBO sysUserBO);

    /**
     * 用户管理 - 分页查询管理员用户（仅管理员）
     *
     * @param pageQuery 分页对象
     * @param sysUserBO BO 查询对象
     * @return {@link IPage} 分页结果
     * @author bruno.gao
     * @CreateTime 2024-12-20
     */
    IPage<SysUser> listAdminUsersPage(PageQuery pageQuery, SysUserBO sysUserBO);

    /**
     * 获取当前用户信息
     *
     * @return {@link SysUserBO} 用户信息
     * @author payne.zhuang
     * @CreateTime 2024-04-18 15:08
     */
    SysUserBO currentUserInfo();

    /**
     * 新增用户
     *
     * @param sysUserBO 用户对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2023-11-21 22:34:23
     */
    boolean addUser(SysUserBO sysUserBO);

    /**
     * 更新用户
     *
     * @param sysUserBO 用户对象
     * @return {@link Boolean} 更新结果
     * @author payne.zhuang
     * @CreateTime 2024-01-10 21:59
     */
    boolean updateUser(SysUserBO sysUserBO);

    /**
     * 当前用户修改个人资料
     *
     * @param sysUserBO 修改对象
     * @return {@link Boolean} 更新结果
     * @author payne.zhuang
     * @CreateTime 2024-01-25 15:20
     */
    boolean updateCurrentUserInfo(SysUserBO sysUserBO);

    /**
     * 用户登录
     *
     * @param sysUserBO BO 对象
     * @return {@link String} 用户 Token
     * @author payne.zhuang
     * @CreateTime 2023-07-17 17:55
     */
    Map<String, String> userLogin(SysUserBO sysUserBO);

    /**
     * 刷新用户Token
     *
     * @param refreshToken         刷新TOKEN
     * @param loginCacheKey        登录缓存Key
     * @param refreshTokenCacheKey 刷新缓存Key
     * @param loginUser            缓存用户信息
     * @return {@link Map<>} 用户 Token Map
     * @author payne.zhuang
     * @CreateTime 2023-08-12 11:00
     */
    Map<String, String> refreshToken(String refreshToken, String refreshTokenCacheKey, LoginUser loginUser);

    /**
     * 根据用户ID进行重置密码，并返回加密密码
     *
     * @param userId 用户 Id
     * @return {@link String} 加密后的密码
     * @author payne.zhuang
     * @CreateTime 2023-12-18 22:04
     */
    String resetPassword(Long userId);

    /**
     * 批量删除用户
     *
     * @param ids 用户 ID 集合
     * @return {@link Boolean} 删除结果
     * @author payne.zhuang
     * @CreateTime 2024-04-23 12:01
     */
    boolean removeBatchByIds(List<Long> ids);

    /**
     * 查询用户职责
     *
     * @param userId 用户id
     * @return {@link SysUserResponsibilitiesBO} 用户职责信息
     * @author payne.zhuang
     * @CreateTime 2024-07-20 - 14:32:07
     */
    SysUserResponsibilitiesBO queryUserResponsibilitiesWithUserId(Long userId);

    /**
     * 更新用户职责信息
     *
     * @param responsibilitiesBO 用户职责信息
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-07-20 - 17:08:58
     */
    boolean updateUserResponsibilities(SysUserResponsibilitiesBO responsibilitiesBO);

    /**
     * 获取未绑定设备的用户
     *
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-07-20 - 17:08:03
     */
    List getUnbindDevice(Long customerId);

    List<String> getBindDevice(Long customerId);

    /**
     * 根据组织ID递归查询所有下属部门的员工
     *
     * @param orgId 组织ID
     * @return {@link List }<{@link SysUser }> 用户列表
     * @author payne.zhuang
     * @CreateTime 2024-03-21 - 10:00:00
     */
    List<SysUser> getUsersByOrgId(Long orgId);

    /**
     * Get user by device SN
     * @param deviceSn device serial number
     * @return SysUser
     */
    MessageResponseDetailVO.NonRespondedUserVO getByDeviceSn(String deviceSn);

    /**
     * 判断用户是否为管理员
     * @param userId 用户ID
     * @return true-是管理员，false-不是管理员
     * @author bruno.gao
     * @CreateTime 2024-12-20
     */
    boolean isAdminUser(Long userId);

    /**
     * 判断用户是否为超级管理员(admin)
     * @param userId 用户ID
     * @return true-是超级管理员，false-不是超级管理员
     * @author bruno.gao
     * @CreateTime 2025-08-18
     */
    boolean isSuperAdmin(Long userId);

    /**
     * 判断用户是否是顶级部门的管理员
     * 条件：1. 是管理员角色 2. 所在部门是顶级部门
     */
    boolean isTopLevelDeptAdmin(Long userId);

    /**
     * 判断用户是否是下属部门的管理员  
     * 条件：1. 是管理员角色 2. 所在部门是下级部门
     */
    boolean isSubDeptAdmin(Long userId);

    /**
     * 获取用户所在的部门ID列表
     */
    List<Long> getUserOrgIds(Long userId);

    /**
     * 获取用户的租户ID
     */
    Long getUserCustomerId(Long userId);

    /**
     * 获取用户所属的顶级部门ID
     * 如果用户已经在顶级部门，返回其部门ID
     * 如果用户在子部门，返回其顶级父部门ID
     */
    Long getUserTopLevelDeptId(Long userId);


    /**
     * 检查用户设备绑定状态 #用户删除前设备绑定检查
     * @param userIds 用户ID列表
     * @return 绑定设备用户的详细信息
     * @author bruno.gao
     * @CreateTime 2025-01-19
     */
    List<Map<String, Object>> checkUserDeviceBinding(List<Long> userIds);

    /**
     * 强制删除用户并解绑设备 #用户删除设备解绑
     * @param userIds 用户ID列表
     * @param forceUnbind 是否强制解绑设备
     * @return 删除结果
     * @author bruno.gao
     * @CreateTime 2025-01-19
     */
    boolean forceRemoveBatchByIds(List<Long> userIds, boolean forceUnbind);
}
