package com.ljwx.modules.system.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.modules.system.domain.entity.SysConfig;
import com.ljwx.modules.system.repository.mapper.SysConfigMapper;
import com.ljwx.modules.system.service.ISysConfigService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * 系统配置 Service 实现类
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.SysConfigServiceImpl
 * @CreateTime 2025/9/9 - 20:55
 */
@Slf4j
@Service
public class SysConfigServiceImpl extends ServiceImpl<SysConfigMapper, SysConfig> implements ISysConfigService {

    @Autowired
    private SysConfigMapper sysConfigMapper;

    @Override
    public String getConfigValue(String configKey) {
        try {
            return sysConfigMapper.getConfigValue(configKey);
        } catch (Exception e) {
            log.warn("获取配置失败，配置键: {}, 错误: {}", configKey, e.getMessage());
            return null;
        }
    }

    @Override
    public String getConfigValue(String configKey, String defaultValue) {
        String value = getConfigValue(configKey);
        return value != null ? value : defaultValue;
    }

    @Override
    public Boolean getBooleanConfig(String configKey) {
        String value = getConfigValue(configKey);
        if (value == null) {
            return null;
        }
        return Boolean.parseBoolean(value.trim());
    }

    @Override
    public Boolean getBooleanConfig(String configKey, Boolean defaultValue) {
        Boolean value = getBooleanConfig(configKey);
        return value != null ? value : defaultValue;
    }

    @Override
    public Integer getIntegerConfig(String configKey) {
        String value = getConfigValue(configKey);
        if (value == null) {
            return null;
        }
        try {
            return Integer.parseInt(value.trim());
        } catch (NumberFormatException e) {
            log.warn("配置值格式错误，配置键: {}, 值: {}", configKey, value);
            return null;
        }
    }

    @Override
    public Integer getIntegerConfig(String configKey, Integer defaultValue) {
        Integer value = getIntegerConfig(configKey);
        return value != null ? value : defaultValue;
    }

    @Override
    public Boolean setConfigValue(String configKey, String configValue) {
        try {
            LambdaQueryWrapper<SysConfig> queryWrapper = new LambdaQueryWrapper<>();
            queryWrapper.eq(SysConfig::getConfigKey, configKey);
            
            SysConfig existingConfig = getOne(queryWrapper);
            
            if (existingConfig != null) {
                // 更新现有配置
                LambdaUpdateWrapper<SysConfig> updateWrapper = new LambdaUpdateWrapper<>();
                updateWrapper.eq(SysConfig::getConfigKey, configKey)
                           .set(SysConfig::getConfigValue, configValue);
                return update(updateWrapper);
            } else {
                // 创建新配置
                SysConfig newConfig = SysConfig.builder()
                    .configKey(configKey)
                    .configValue(configValue)
                    .configType("string")
                    .category("system")
                    .readonly(false)
                    .build();
                return save(newConfig);
            }
        } catch (Exception e) {
            log.error("设置配置失败，配置键: {}, 值: {}, 错误: {}", configKey, configValue, e.getMessage());
            return false;
        }
    }

    @Override
    public Boolean isLicenseSupportEnabled() {
        try {
            Boolean enabled = getBooleanConfig("is_support_license", false);
            log.debug("许可证支持状态: {}", enabled);
            return enabled;
        } catch (Exception e) {
            log.warn("检查许可证支持状态失败: {}", e.getMessage());
            return false; // 默认不启用许可证验证
        }
    }
}