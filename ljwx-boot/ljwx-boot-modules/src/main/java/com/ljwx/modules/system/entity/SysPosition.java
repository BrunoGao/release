package com.ljwx.modules.system.entity;

import com.baomidou.mybatisplus.annotation.*;
import com.ljwx.common.core.entity.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 系统职位实体类
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("sys_position")
public class SysPosition extends BaseEntity {

    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long customerId;
    
    private String name;
    
    private String code;
    
    private String riskLevel;
    
    private Double weight;
    
    private String description;
    
    private Integer status;
    
    private Integer sortOrder;
    
    @TableField(exist = false)
    private Integer userCount;
}