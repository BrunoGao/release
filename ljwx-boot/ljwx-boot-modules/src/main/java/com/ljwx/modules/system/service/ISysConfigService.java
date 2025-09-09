package com.ljwx.modules.system.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.modules.system.domain.entity.SysConfig;

/**
 * 系统配置 Service 接口层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.ISysConfigService
 * @CreateTime 2025/9/9 - 20:55
 */
public interface ISysConfigService extends IService<SysConfig> {

    /**
     * 根据配置键获取配置值
     * 
     * @param configKey 配置键
     * @return 配置值
     */
    String getConfigValue(String configKey);

    /**
     * 根据配置键获取配置值，如果不存在则返回默认值
     * 
     * @param configKey 配置键
     * @param defaultValue 默认值
     * @return 配置值
     */
    String getConfigValue(String configKey, String defaultValue);

    /**
     * 根据配置键获取布尔类型配置值
     * 
     * @param configKey 配置键
     * @return 布尔值
     */
    Boolean getBooleanConfig(String configKey);

    /**
     * 根据配置键获取布尔类型配置值，如果不存在则返回默认值
     * 
     * @param configKey 配置键
     * @param defaultValue 默认值
     * @return 布尔值
     */
    Boolean getBooleanConfig(String configKey, Boolean defaultValue);

    /**
     * 根据配置键获取整数类型配置值
     * 
     * @param configKey 配置键
     * @return 整数值
     */
    Integer getIntegerConfig(String configKey);

    /**
     * 根据配置键获取整数类型配置值，如果不存在则返回默认值
     * 
     * @param configKey 配置键
     * @param defaultValue 默认值
     * @return 整数值
     */
    Integer getIntegerConfig(String configKey, Integer defaultValue);

    /**
     * 设置配置值
     * 
     * @param configKey 配置键
     * @param configValue 配置值
     * @return 是否设置成功
     */
    Boolean setConfigValue(String configKey, String configValue);

    /**
     * 检查许可证功能是否启用
     * 
     * @return 是否启用许可证验证
     */
    Boolean isLicenseSupportEnabled();
}