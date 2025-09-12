package com.ljwx.modules.system.domain.dto.menu;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.List;

/**
 * 动态菜单扫描DTO
 * 
 * @author bruno.gao
 */
@Data
@Schema(description = "动态菜单扫描配置")
public class DynamicMenuScanDTO implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    @Schema(description = "前端项目路径")
    @NotBlank(message = "前端项目路径不能为空")
    private String frontendPath;

    @Schema(description = "扫描模式：auto(自动), manual(手动), incremental(增量)")
    private String scanMode = "auto";

    @Schema(description = "包含的路径模式列表")
    private List<String> includePatterns;

    @Schema(description = "排除的路径模式列表")
    private List<String> excludePatterns;

    @Schema(description = "是否扫描子目录")
    private Boolean recursive = true;

    @Schema(description = "是否自动创建菜单")
    private Boolean autoCreate = false;

    @Schema(description = "是否覆盖已存在的菜单")
    private Boolean overwriteExisting = false;

    @Schema(description = "默认父菜单ID")
    private Long defaultParentId;

    @Schema(description = "租户ID")
    private Long customerId;

    @Schema(description = "菜单名称生成规则：filename(文件名), path(路径), comment(注释)")
    private String nameGenerationRule = "filename";

    @Schema(description = "图标生成规则：auto(自动), default(默认), none(无)")
    private String iconGenerationRule = "auto";

    @Schema(description = "排序起始值")
    private Integer sortStartValue = 1000;

    @Schema(description = "排序增量")
    private Integer sortIncrement = 10;

    @Schema(description = "最大扫描文件数")
    private Integer maxFiles = 1000;

    @Schema(description = "是否启用缓存")
    private Boolean enableCache = true;

    @Schema(description = "扫描标签（用于标记本次扫描）")
    private String scanTag;
}