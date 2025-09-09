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
 * 系统配置 Entity 实体类
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.entity.SysConfig
 * @CreateTime 2025/9/9 - 20:45
 */

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("sys_config")
public class SysConfig extends BaseEntity {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 配置键
     */
    @TableField("config_key")
    private String configKey;

    /**
     * 配置值
     */
    @TableField("config_value")
    private String configValue;

    /**
     * 配置类型(string,number,boolean,json)
     */
    @TableField("config_type")
    private String configType;

    /**
     * 配置描述
     */
    @TableField("description")
    private String description;

    /**
     * 配置分类
     */
    @TableField("category")
    private String category;

    /**
     * 是否只读
     */
    @TableField("is_readonly")
    private Boolean readonly;

    /**
     * 获取布尔类型配置值
     */
    public Boolean getBooleanValue() {
        if (configValue == null) {
            return false;
        }
        return Boolean.parseBoolean(configValue.trim());
    }

    /**
     * 获取整数类型配置值
     */
    public Integer getIntegerValue() {
        if (configValue == null) {
            return null;
        }
        try {
            return Integer.parseInt(configValue.trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /**
     * 获取长整数类型配置值
     */
    public Long getLongValue() {
        if (configValue == null) {
            return null;
        }
        try {
            return Long.parseLong(configValue.trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }
}