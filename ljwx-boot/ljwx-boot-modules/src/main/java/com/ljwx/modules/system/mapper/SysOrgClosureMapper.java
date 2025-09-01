package com.ljwx.modules.system.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.system.entity.SysOrgClosure;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 组织闭包表Mapper接口
 */
@Mapper
public interface SysOrgClosureMapper extends BaseMapper<SysOrgClosure> {

    /**
     * 查询组织的所有子孙节点
     */
    @Select("SELECT descendant_id FROM sys_org_closure " +
            "WHERE ancestor_id = #{ancestorId} AND customer_id = #{customerId} AND is_deleted = 0")
    List<Long> getDescendantIds(@Param("customerId") Long customerId, @Param("ancestorId") Long ancestorId);

    /**
     * 查询组织的所有祖先节点
     */
    @Select("SELECT ancestor_id FROM sys_org_closure " +
            "WHERE descendant_id = #{descendantId} AND customer_id = #{customerId} AND is_deleted = 0")
    List<Long> getAncestorIds(@Param("customerId") Long customerId, @Param("descendantId") Long descendantId);

    /**
     * 查询组织的直接子节点
     */
    @Select("SELECT descendant_id FROM sys_org_closure " +
            "WHERE ancestor_id = #{ancestorId} AND depth = 1 AND customer_id = #{customerId} AND is_deleted = 0")
    List<Long> getDirectChildIds(@Param("customerId") Long customerId, @Param("ancestorId") Long ancestorId);

    /**
     * 查询组织层级关系
     */
    @Select("SELECT * FROM sys_org_closure " +
            "WHERE ancestor_id = #{ancestorId} AND customer_id = #{customerId} AND is_deleted = 0 " +
            "ORDER BY depth ASC")
    List<SysOrgClosure> getOrgHierarchy(@Param("customerId") Long customerId, @Param("ancestorId") Long ancestorId);

    /**
     * 批量插入闭包关系
     */
    void batchInsertClosure(@Param("closures") List<SysOrgClosure> closures);

    /**
     * 删除组织的所有闭包关系
     */
    void deleteOrgClosure(@Param("customerId") Long customerId, @Param("orgId") Long orgId);
}