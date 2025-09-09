package com.ljwx.modules.system.repository.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.system.domain.entity.SysConfig;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/**
 * 系统配置 Mapper 接口层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.repository.mapper.SysConfigMapper
 * @CreateTime 2025/9/9 - 20:50
 */
@Mapper
public interface SysConfigMapper extends BaseMapper<SysConfig> {

    /**
     * 根据配置键查询配置值
     * 
     * @param configKey 配置键
     * @return 配置值
     */
    @Select("SELECT config_value FROM sys_config WHERE config_key = #{configKey} LIMIT 1")
    String getConfigValue(@Param("configKey") String configKey);

    /**
     * 根据配置键查询配置对象
     * 
     * @param configKey 配置键
     * @return 配置对象
     */
    @Select("SELECT * FROM sys_config WHERE config_key = #{configKey} LIMIT 1")
    SysConfig getConfigByKey(@Param("configKey") String configKey);
}