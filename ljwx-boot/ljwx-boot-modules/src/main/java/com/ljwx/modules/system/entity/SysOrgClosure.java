package com.ljwx.modules.system.entity;

import com.baomidou.mybatisplus.annotation.*;
import com.ljwx.common.core.entity.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 组织闭包表实体类
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("sys_org_closure")
public class SysOrgClosure extends BaseEntity {

    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long customerId;
    
    private Long ancestorId;
    
    private Long descendantId;
    
    private Integer depth;
    
    @TableField(exist = false)
    private String ancestorName;
    
    @TableField(exist = false)
    private String descendantName;
}