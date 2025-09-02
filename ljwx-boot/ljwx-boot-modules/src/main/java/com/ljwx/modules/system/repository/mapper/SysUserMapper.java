package com.ljwx.modules.system.repository.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.modules.health.domain.vo.MessageResponseDetailVO;
import com.ljwx.modules.system.domain.bo.SysUserBO;
import com.ljwx.modules.system.domain.entity.SysUser;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 用户管理 Mapper 接口层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.repository.mapper.SysUserMapper
 * @CreateTime 2023/7/6 - 16:04
 */
@Mapper
public interface SysUserMapper extends BaseMapper<SysUser> {

    /**
     * 分页查询用户列表
     *
     * @param page      分页信息
     * @param sysUserBO 查询条件
     * @return {@link List }<{@link SysUser }> 查询用户集合
     * @author payne.zhuang
     * @CreateTime 2024-11-05 - 16:19:46
     */
    List<SysUser> listSysUserPage(IPage<SysUser> page, @Param("bo") SysUserBO sysUserBO);

    /**
     * 根据账号获取用户信息
     *
     * @param userName 登录用户名
     * @return {@link SysUser} 用户对象
     * @author payne.zhuang
     * @CreateTime 2023-07-18 19:18
     */
    SysUser getUserByUserName(String userName);

    /**
     * 查询是否包含管理员
     *
     * @param userIds 用户ID集合
     * @return {@link Boolean} 是否包含管理员
     * @author payne.zhuang
     * @CreateTime 2024-04-23 12:14
     */
    boolean queryIsContainAdmin(List<Long> userIds);

    /**
     * 获取未绑定设备的用户
     *
     * @return {@link List }<{@link String }> 未绑定设备的用户
     * @author payne.zhuang
     * @CreateTime 2024-07-20 - 17:08:03
     */
    List<String> getUnbindDeviceSerialNumbers(Long customerId);

    /**
     * 分页查询非管理员用户列表 - 排除管理员角色用户
     *
     * @param page      分页信息
     * @param sysUserBO 查询条件
     * @return {@link List }<{@link SysUser }> 查询用户集合
     * @author bruno.gao
     * @CreateTime 2024-12-20
     */
    List<SysUser> listNonAdminUsersPage(IPage<SysUser> page, @Param("bo") SysUserBO sysUserBO);

    /**
     * 获取非管理员用户数量
     *
     * @param sysUserBO 查询条件
     * @return {@link Long} 用户数量
     * @author bruno.gao
     * @CreateTime 2024-12-20
     */
    Long countNonAdminUsers(@Param("bo") SysUserBO sysUserBO);

    /**
     * 分页查询管理员用户列表 - 仅管理员角色用户
     *
     * @param page      分页信息
     * @param sysUserBO 查询条件
     * @return {@link List }<{@link SysUser }> 查询用户集合
     * @author bruno.gao
     * @CreateTime 2024-12-20
     */
    List<SysUser> listAdminUsersPage(IPage<SysUser> page, @Param("bo") SysUserBO sysUserBO);

    /**
     * 获取管理员用户数量
     *
     * @param sysUserBO 查询条件
     * @return {@link Long} 用户数量
     * @author bruno.gao
     * @CreateTime 2024-12-20
     */
    Long countAdminUsers(@Param("bo") SysUserBO sysUserBO);

    /**
     * 获取绑定设备的用户
     *
     * @return {@link List }<{@link String }> 未绑定设备的用户
     * @author payne.zhuang
     * @CreateTime 2024-07-20 - 17:08:03
     */
    List<String> getBindDeviceSerialNumbers(Long customerId);

    /**
     * 根据组织ID列表查询用户列表
     *
     * @param orgIds 组织ID列表
     * @return {@link List }<{@link SysUser }> 用户列表
     * @author payne.zhuang
     * @CreateTime 2024-03-21 - 10:00:00
     */
    List<SysUser> getUsersByOrgIds(List<Long> orgIds);

    @Select("SELECT ou.name as departmentName, u.user_name as userName, u.device_sn as deviceSn " +
            "FROM sys_user u " +
            "LEFT JOIN (SELECT user_id, MIN(org_id) as org_id FROM sys_user_org GROUP BY user_id) uo ON u.id = uo.user_id " +
            "LEFT JOIN sys_org_units ou ON uo.org_id = ou.id " +
            "WHERE u.device_sn = #{deviceSn} " +
            "ORDER BY u.id DESC LIMIT 1")
    MessageResponseDetailVO.NonRespondedUserVO getUserInfoByDeviceSn(@Param("deviceSn") String deviceSn);

    @Select("SELECT p.name as position FROM sys_user_position up " +
            "LEFT JOIN sys_position p ON up.position_id = p.id " +
            "WHERE up.user_id = #{userId} AND p.is_deleted = 0 order by up.create_time desc LIMIT 1")
    String getPositionNameByUserId(@Param("userId") Long userId);

}