package com.ljwx.modules.monitor.domain.dto.cache;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.NotBlank;

/**
 * 按模式清理缓存请求DTO
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName CacheClearByPatternDTO
 * @CreateTime 2025-08-30 14:42
 */
@Data
@Schema(description = "按模式清理缓存请求")
public class CacheClearByPatternDTO {

    @NotBlank(message = "缓存键模式不能为空")
    @Schema(description = "缓存键模式，如：user:*", example = "user:*")
    private String pattern;
}