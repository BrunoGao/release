package com.ljwx.modules.system.entity;

import com.baomidou.mybatisplus.annotation.*;
import com.ljwx.common.core.entity.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.util.List;

/**
 * 系统组织单元实体类
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("sys_org_units")
public class SysOrgUnits extends BaseEntity {

    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long customerId;
    
    private String name;
    
    private String code;
    
    private String shortName;
    
    private Long parentId;
    
    private Integer level;
    
    private String path;
    
    private Integer sortOrder;
    
    private String orgType;
    
    private String description;
    
    private String address;
    
    private String phone;
    
    private String email;
    
    private String manager;
    
    private Integer status;
    
    @TableField(exist = false)
    private List<SysOrgUnits> children;
    
    @TableField(exist = false)
    private String parentName;
    
    @TableField(exist = false)
    private Integer userCount;
}