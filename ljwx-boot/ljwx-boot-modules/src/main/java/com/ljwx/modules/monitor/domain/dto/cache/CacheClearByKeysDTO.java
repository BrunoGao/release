package com.ljwx.modules.monitor.domain.dto.cache;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.NotEmpty;
import java.util.List;

/**
 * 按键列表清理缓存请求DTO
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName CacheClearByKeysDTO
 * @CreateTime 2025-08-30 14:43
 */
@Data
@Schema(description = "按键列表清理缓存请求")
public class CacheClearByKeysDTO {

    @NotEmpty(message = "缓存键列表不能为空")
    @Schema(description = "缓存键列表", example = "[\"user:1\", \"user:2\"]")
    private List<String> keys;
}