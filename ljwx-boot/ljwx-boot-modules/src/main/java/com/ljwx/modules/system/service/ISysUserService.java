package com.ljwx.modules.system.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.common.domain.LoginUser;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.system.domain.bo.SysUserBO;
import com.ljwx.modules.system.domain.bo.SysUserResponsibilitiesBO;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.health.domain.vo.MessageResponseDetailVO;
import com.ljwx.modules.health.domain.vo.NonRespondedUserVO;
import org.springframework.web.multipart.MultipartFile;
import java.util.List;
import java.util.Map;

/**
 * 用户管理 Service 服务接口层
 * 
 * <h3>重要性能优化说明</h3>
 * <p>sys_user 表已包含 org_id 和 org_name 字段，支持高性能查询：</p>
 * <ul>
 *   <li><strong>避免 JOIN sys_org 表</strong>：直接从 sys_user 获取组织信息</li>
 *   <li><strong>查询格式</strong>：SELECT u.*, u.org_id, u.org_name FROM sys_user u</li>
 *   <li><strong>性能提升</strong>：减少表连接，提升查询速度，降低数据库负载</li>
 *   <li><strong>数据一致性</strong>：通过 updateOrgNameByOrgId() 和 clearOrgInfoByOrgId() 保证同步</li>
 * </ul>
 * 
 * <h3>推荐查询模式</h3>
 * <pre>
 * // ✅ 推荐：高性能查询
 * SELECT u.*, u.org_id, u.org_name FROM sys_user u WHERE u.id = ?
 * 
 * // ❌ 避免：低效的 JOIN 查询
 * SELECT u.*, o.org_name FROM sys_user u LEFT JOIN sys_org o ON u.org_id = o.id WHERE u.id = ?
 * </pre>
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
     * 根据组织ID递归查询所有下属部门的员工(仅普通用户，不包含管理员)
     * <p>优化版本：使用组织闭包表和user_type字段直接过滤，避免多次数据库查询</p>
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @return {@link List }<{@link SysUser }> 普通用户列表
     * @author payne.zhuang
     * @CreateTime 2024-03-21 - 10:00:00
     */
    List<SysUser> getUsersByOrgId(Long orgId, Long customerId);

    /**
     * 根据组织ID获取所有用户列表(包含管理员)
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @return {@link List }<{@link SysUser }> 所有用户列表
     * @author bruno.gao
     * @CreateTime 2024-09-14
     */
    List<SysUser> getAllUsersByOrgId(Long orgId, Long customerId);

    /**
     * 根据组织ID和用户类型获取用户列表
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @param userType 用户类型 (0=普通用户, 1=部门管理员, 2=租户管理员, 3=超级管理员)
     * @return {@link List }<{@link SysUser }> 用户列表
     * @author bruno.gao
     * @CreateTime 2024-09-14
     */
    List<SysUser> getUsersByOrgIdAndUserType(Long orgId, Long customerId, Integer userType);

    /**
     * Get user by device SN
     * @param deviceSn device serial number
     * @return SysUser
     */
    NonRespondedUserVO getByDeviceSn(String deviceSn);

    /**
     * 判断用户是否为管理员（优化版本）
     * <p>使用user_type字段进行高性能查询，避免多表JOIN操作</p>
     * 
     * @param userId 用户ID
     * @return true-是管理员，false-不是管理员
     * @author bruno.gao
     * @CreateTime 2024-12-20
     */
    boolean isAdminUser(Long userId);

    /**
     * 判断用户是否为超级管理员（优化版本）
     * <p>使用user_type字段进行高性能查询</p>
     * 
     * @param userId 用户ID
     * @return true-是超级管理员，false-不是超级管理员
     * @author bruno.gao
     * @CreateTime 2024-12-20
     */
    boolean isSuperAdmin(Long userId);

    /**
     * 判断用户是否是顶级部门的管理员（优化版本）
     * <p>使用admin_level字段进行高性能查询，条件：管理级别 >= 租户级</p>
     * 
     * @param userId 用户ID
     * @return true-是顶级管理员，false-不是顶级管理员
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

    /**
     * 批量导入用户
     *
     * @param file   Excel文件
     * @param orgIds 组织ID列表（JSON字符串）
     * @return {@link Map} 导入结果，包含成功和失败的记录
     * @author bruno.gao
     * @CreateTime 2025-01-20
     */
    Map<String, Object> batchImportUsers(MultipartFile file, String orgIds);

    /**
     * 根据用户ID集合批量获取用户名映射
     *
     * @param userIds 用户ID集合
     * @return {@link Map} 用户ID到用户名的映射
     * @author bruno.gao
     * @CreateTime 2025-01-25
     */
    Map<Long, String> getUserNamesMapByIds(List<Long> userIds);

    /**
     * 根据组织ID更新用户组织名称（组织名称变更时同步）
     *
     * @param orgId 组织ID
     * @param newOrgName 新组织名称
     * @return 更新的用户数量
     * @author bruno.gao
     * @CreateTime 2025-01-26
     */
    int updateOrgNameByOrgId(Long orgId, String newOrgName);

    /**
     * 清理指定组织的用户关联信息（组织删除时清理）
     *
     * @param orgId 组织ID
     * @return 清理的用户数量
     * @author bruno.gao
     * @CreateTime 2025-01-26
     */
    int clearOrgInfoByOrgId(Long orgId);

    /**
     * 保存或更新用户时自动设置组织信息
     *
     * @param user 用户对象
     * @return 保存结果
     * @author bruno.gao
     * @CreateTime 2025-01-26
     */
    boolean saveOrUpdateUser(SysUser user);

    // ================================
    // 高性能用户-组织查询工具方法
    // ================================

    /**
     * 高性能获取用户基本信息和组织信息（避免 JOIN sys_org）
     * 
     * <p><strong>性能优势</strong>：直接从 sys_user 表获取 org_id 和 org_name，无需 JOIN 操作</p>
     * <p><strong>使用场景</strong>：健康数据查询、用户列表显示等高频场景</p>
     *
     * @param userId 用户ID
     * @return 包含用户信息和组织信息的 Map
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    Map<String, Object> getUserWithOrgInfo(Long userId);

    /**
     * 批量高性能获取用户基本信息和组织信息（避免 JOIN sys_org）
     * 
     * <p><strong>性能优势</strong>：批量查询，直接从 sys_user 表获取组织信息</p>
     * <p><strong>使用场景</strong>：健康数据批量查询、报表生成等场景</p>
     *
     * @param userIds 用户ID列表
     * @return 用户信息列表，每个用户包含组织信息
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    List<Map<String, Object>> getBatchUsersWithOrgInfo(List<Long> userIds);

    /**
     * 根据设备序列号高性能获取用户信息（避免 JOIN sys_org）
     * 
     * <p><strong>性能优势</strong>：设备用户查询优化，减少表连接</p>
     * <p><strong>使用场景</strong>：设备消息处理、健康数据关联用户等场景</p>
     *
     * @param deviceSn 设备序列号
     * @return 用户信息包含组织信息的 Map，如果未找到返回 null
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    Map<String, Object> getUserWithOrgInfoByDeviceSn(String deviceSn);

    /**
     * 根据组织ID高性能获取组织下所有用户（避免 JOIN sys_org）
     * 
     * <p><strong>性能优势</strong>：组织用户查询优化，利用 sys_user.org_id 索引</p>
     * <p><strong>使用场景</strong>：组织健康统计、部门用户管理等场景</p>
     *
     * @param orgId 组织ID
     * @return 用户信息列表，每个用户包含组织信息
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    List<Map<String, Object>> getUsersWithOrgInfoByOrgId(Long orgId);

    /**
     * 高性能用户搜索（支持姓名、用户名、组织名搜索，避免 JOIN sys_org）
     * 
     * <p><strong>性能优势</strong>：利用 sys_user 表的 org_name 字段进行组织名搜索</p>
     * <p><strong>使用场景</strong>：用户搜索、健康数据用户筛选等场景</p>
     *
     * @param keyword 搜索关键词（匹配姓名、用户名、组织名）
     * @param orgId 组织ID（部门过滤）
     * @param limit 结果限制数量
     * @return 匹配的用户信息列表
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    List<Map<String, Object>> searchUsersWithOrgInfo(String keyword, Long orgId, Integer limit);

    // ==================== 优化的管理员查询方法 ====================

    /**
     * 批量获取用户类型（高性能版本）
     * <p>使用单次查询获取多个用户的类型信息，避免N+1查询问题</p>
     *
     * @param userIds 用户ID列表
     * @return 用户ID -> 用户类型的映射
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    Map<Long, Integer> batchGetUserTypes(List<Long> userIds);

    /**
     * 批量获取管理员级别（高性能版本）
     * <p>使用单次查询获取多个用户的管理级别信息</p>
     *
     * @param userIds 用户ID列表
     * @return 用户ID -> 管理级别的映射
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    Map<Long, Integer> batchGetAdminLevels(List<Long> userIds);

    /**
     * 批量判断用户是否为管理员（高性能版本）
     * <p>一次查询判断多个用户的管理员状态</p>
     *
     * @param userIds 用户ID列表
     * @return 用户ID -> 是否管理员的映射
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    Map<Long, Boolean> batchIsAdminUser(List<Long> userIds);

    /**
     * 高效查询组织管理员
     * <p>直接查询指定组织的管理员用户，利用复合索引提升性能</p>
     *
     * @param orgId 组织ID
     * @return 组织管理员列表
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    List<SysUser> getOrgAdmins(Long orgId);

    /**
     * 高效查询租户管理员
     * <p>直接查询指定租户的管理员用户，利用复合索引提升性能</p>
     *
     * @param customerId 租户ID
     * @return 租户管理员列表
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    List<SysUser> getTenantAdmins(Long customerId);

    /**
     * 过滤掉管理员用户（高性能版本）
     * <p>从用户列表中过滤掉管理员，常用于统计场景</p>
     *
     * @param users 用户列表
     * @return 过滤后的普通用户列表
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    List<SysUser> filterOutAdminUsers(List<SysUser> users);

    /**
     * 根据用户类型查询用户
     * <p>高效查询指定类型的用户，利用索引优化性能</p>
     *
     * @param userType 用户类型
     * @param orgId 组织ID（可选）
     * @param customerId 租户ID（可选）
     * @return 符合条件的用户列表
     * @author bruno.gao
     * @CreateTime 2025-09-12
     */
    List<SysUser> getUsersByType(Integer userType, Long orgId, Long customerId);

    /**
     * 检查手机号是否已存在（仅检查未删除用户）
     * <p>用于用户创建/更新时的手机号唯一性验证</p>
     *
     * @param phone 手机号
     * @param excludeUserId 排除的用户ID（编辑时用）
     * @param isDeleted 是否删除标识(0-未删除,1-已删除)
     * @return true-已存在，false-不存在
     * @author bruno.gao
     * @CreateTime 2025-09-22
     */
    boolean checkPhoneExists(String phone, Long excludeUserId, Integer isDeleted);

    /**
     * 检查设备序列号是否已存在（仅检查未删除用户）
     * <p>用于用户创建/更新时的设备唯一性验证</p>
     *
     * @param deviceSn 设备序列号
     * @param excludeUserId 排除的用户ID（编辑时用）
     * @param isDeleted 是否删除标识(0-未删除,1-已删除)
     * @return true-已存在，false-不存在
     * @author bruno.gao
     * @CreateTime 2025-09-22
     */
    boolean checkDeviceSnExists(String deviceSn, Long excludeUserId, Integer isDeleted);
}
