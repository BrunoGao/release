/*
* All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
* Open Source Agreement: Apache License, Version 2.0
*/

package com.ljwx.modules.health.repository.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.domain.entity.TDeviceBindRequest;
import org.apache.ibatis.annotations.Mapper;

/**
* 设备绑定申请表 Mapper 数据访问类
*
* @Author Claude Code
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.repository.mapper.TDeviceBindRequestMapper
* @CreateTime 2025-08-23
*/

@Mapper
public interface TDeviceBindRequestMapper extends BaseMapper<TDeviceBindRequest> {

}