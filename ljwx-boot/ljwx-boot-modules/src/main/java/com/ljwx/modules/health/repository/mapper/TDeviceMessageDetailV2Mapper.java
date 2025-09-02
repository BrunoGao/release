package com.ljwx.modules.health.repository.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetailV2;
import org.apache.ibatis.annotations.Mapper;

/**
 * 设备消息详情表V2 Mapper接口 - 基于userId直接关联
 *
 * @author ljwx-system
 * @since 2025-08-31
 */
@Mapper
public interface TDeviceMessageDetailV2Mapper extends BaseMapper<TDeviceMessageDetailV2> {

}