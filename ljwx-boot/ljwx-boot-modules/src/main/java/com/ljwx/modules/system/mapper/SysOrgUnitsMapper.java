package com.ljwx.modules.system.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.system.entity.SysOrgUnits;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;
import java.util.Map;

/**
 * 系统组织单元Mapper接口
 */
@Mapper
public interface SysOrgUnitsMapper extends BaseMapper<SysOrgUnits> {

    /**
     * 根据父级ID查询子组织
     */
    @Select("SELECT * FROM sys_org_units WHERE parent_id = #{parentId} AND is_deleted = 0 ORDER BY sort_order")
    List<SysOrgUnits> getChildrenByParentId(@Param("parentId") Long parentId);

    /**
     * 根据组织代码查询组织
     */
    @Select("SELECT * FROM sys_org_units WHERE code = #{code} AND customer_id = #{customerId} AND is_deleted = 0")
    SysOrgUnits getOrgByCode(@Param("customerId") Long customerId, @Param("code") String code);

    /**
     * 查询组织树结构
     */
    List<SysOrgUnits> getOrgTree(@Param("customerId") Long customerId, @Param("parentId") Long parentId);

    /**
     * 根据用户ID查询用户所属组织
     */
    List<SysOrgUnits> getOrgsByUserId(@Param("userId") Long userId);

    /**
     * 查询组织统计信息
     */
    @Select("SELECT " +
            "COUNT(*) as total_orgs, " +
            "COUNT(CASE WHEN status = 1 THEN 1 END) as active_orgs, " +
            "MAX(level) as max_level " +
            "FROM sys_org_units WHERE customer_id = #{customerId} AND is_deleted = 0")
    Map<String, Object> getOrgStatistics(@Param("customerId") Long customerId);

    /**
     * 更新组织层级路径
     */
    void updateOrgPath(@Param("id") Long id, @Param("path") String path, @Param("level") Integer level);
}