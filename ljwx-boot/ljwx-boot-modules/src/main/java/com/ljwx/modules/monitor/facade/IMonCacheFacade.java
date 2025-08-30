package com.ljwx.modules.monitor.facade;

import com.ljwx.modules.monitor.domain.vo.MonCacheRedisVO;

import java.util.List;

/**
 * 缓存服务监控 门面接口层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.monitor.facade.IMonCacheFacade
 * @CreateTime 2024/5/4 - 16:01
 */
public interface IMonCacheFacade {

    /**
     * 获取 Redis 信息
     *
     * @return {@link MonCacheRedisVO} Redis 信息
     * @author payne.zhuang
     * @CreateTime 2024-05-04 17:15
     */
    MonCacheRedisVO redisInfo();

    /**
     * 清理全部缓存
     *
     * @return {@code Long} 删除的键数量
     * @author bruno.gao
     * @CreateTime 2025-08-30 14:38
     */
    Long clearAllCache();

    /**
     * 按模式清理缓存
     *
     * @param pattern 缓存键模式，如：user:*
     * @return {@code Long} 删除的键数量
     * @author bruno.gao
     * @CreateTime 2025-08-30 14:38
     */
    Long clearCacheByPattern(String pattern);

    /**
     * 按键列表清理缓存
     *
     * @param keys 缓存键列表
     * @return {@code Long} 删除的键数量
     * @author bruno.gao
     * @CreateTime 2025-08-30 14:38
     */
    Long clearCacheByKeys(List<String> keys);
}
