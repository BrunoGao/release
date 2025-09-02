package com.ljwx.modules.system.entity;

import com.baomidou.mybatisplus.annotation.*;
import com.ljwx.common.core.entity.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 用户组织关系实体类
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("sys_user_org")
public class SysUserOrg extends BaseEntity {

    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long userId;
    
    private Long orgId;
    
    private Integer isPrimary;
    
    @TableField(exist = false)
    private String userName;
    
    @TableField(exist = false)
    private String orgName;
}