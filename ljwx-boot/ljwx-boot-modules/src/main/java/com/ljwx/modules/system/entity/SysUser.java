package com.ljwx.modules.system.entity;

import com.baomidou.mybatisplus.annotation.*;
import com.ljwx.common.core.entity.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 系统用户实体类
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("sys_user")
public class SysUser extends BaseEntity {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long customerId;
    
    private String userName;
    
    private String nickName;
    
    private String realName;
    
    private String email;
    
    private String phone;
    
    private String password;
    
    private String avatar;
    
    private String gender;
    
    private Integer age;
    
    private LocalDateTime birthday;
    
    private String address;
    
    private String description;
    
    private Integer status;
    
    private String loginIp;
    
    private LocalDateTime lastLoginTime;
    
    private Integer loginCount;
    
    @TableField(exist = false)
    private List<Long> roleIds;
    
    @TableField(exist = false)
    private List<String> roleNames;
    
    @TableField(exist = false)
    private List<Long> orgIds;
    
    @TableField(exist = false)
    private List<String> orgNames;
}