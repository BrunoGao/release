package com.ljwx.admin.controller.monitor;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.modules.monitor.domain.dto.cache.CacheClearByKeysDTO;
import com.ljwx.modules.monitor.domain.dto.cache.CacheClearByPatternDTO;
import com.ljwx.modules.monitor.domain.vo.MonCacheRedisVO;
import com.ljwx.modules.monitor.facade.IMonCacheFacade;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;

/**
 * 系统服务监控
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName monitor.controller.com.ljwx.admin.MonCacheController
 * @CreateTime 2024/5/4 - 15:49
 */
@RestController
@Tag(name = "缓存服务监控")
@RequiredArgsConstructor
@RequestMapping("/mon_cache")
public class MonCacheController {

    @NonNull
    private IMonCacheFacade monCacheFacade;

    @GetMapping("/redis")
    @SaCheckPermission("mon:cache:redis")
    @Operation(operationId = "1", summary = "获取 Redis 信息")
    public Result<MonCacheRedisVO> getRedisInfo() {
        return Result.data(monCacheFacade.redisInfo());
    }

    @PostMapping("/clear-all")
    @SaCheckPermission("mon:cache:clear")
    @Operation(operationId = "2", summary = "清理全部缓存")
    public Result<Long> clearAllCache() {
        Long deletedCount = monCacheFacade.clearAllCache();
        return Result.data(deletedCount);
    }

    @PostMapping("/clear-pattern")
    @SaCheckPermission("mon:cache:clear")
    @Operation(operationId = "3", summary = "按模式清理缓存")
    public Result<Long> clearCacheByPattern(@Valid @RequestBody CacheClearByPatternDTO dto) {
        Long deletedCount = monCacheFacade.clearCacheByPattern(dto.getPattern());
        return Result.data(deletedCount);
    }

    @PostMapping("/clear-keys")
    @SaCheckPermission("mon:cache:clear")
    @Operation(operationId = "4", summary = "按键列表清理缓存")
    public Result<Long> clearCacheByKeys(@Valid @RequestBody CacheClearByKeysDTO dto) {
        Long deletedCount = monCacheFacade.clearCacheByKeys(dto.getKeys());
        return Result.data(deletedCount);
    }
}
