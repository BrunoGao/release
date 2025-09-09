package com.ljwx.modules.system.domain.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.io.Serial;

/**
 * 组织机构 Entity 实体类
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.entity.SysOrg
 */

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("sys_org")
public class SysOrg extends BaseEntity {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 组织名称
     */
    @TableField("org_name")
    private String orgName;

    /**
     * 父级组织ID
     */
    @TableField("parent_id")
    private Long parentId;

    /**
     * 组织编码
     */
    @TableField("org_code")
    private String orgCode;

    /**
     * 排序
     */
    @TableField("sort_order")
    private Integer sortOrder;

    /**
     * 状态(0:禁用,1:启用)
     */
    @TableField("status")
    private String status;

    /**
     * 是否删除(0:否,1:是)
     */
    @TableField("is_deleted")
    private Integer isDeleted;
}