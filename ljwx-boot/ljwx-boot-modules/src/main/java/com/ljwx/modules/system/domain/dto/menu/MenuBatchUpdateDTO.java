package com.ljwx.modules.system.domain.dto.menu;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * 菜单批量更新DTO
 * 
 * @author bruno.gao
 */
@Data
@Schema(description = "菜单批量更新配置")
public class MenuBatchUpdateDTO implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    @Schema(description = "要更新的菜单ID列表")
    @NotEmpty(message = "菜单ID列表不能为空")
    private List<Long> menuIds;

    @Schema(description = "更新操作类型：update-更新属性，enable-启用，disable-禁用，delete-删除，move-移动")
    private String operation = "update";

    @Schema(description = "更新的属性字段")
    private Map<String, Object> updateFields;

    @Schema(description = "目标父菜单ID（移动操作时使用）")
    private Long targetParentId;

    @Schema(description = "插入位置：before-之前，after-之后，first-最前，last-最后")
    private String position = "last";

    @Schema(description = "参考菜单ID（插入位置为before/after时使用）")
    private Long referenceMenuId;

    @Schema(description = "是否递归操作子菜单")
    private Boolean recursive = false;

    @Schema(description = "操作原因/备注")
    private String reason;

    @Schema(description = "租户ID")
    private Long customerId;

    @Schema(description = "是否强制执行（忽略警告）")
    private Boolean force = false;

    @Schema(description = "预览模式（不实际执行）")
    private Boolean preview = false;

    @Schema(description = "操作标签（用于审计）")
    private String operationTag;

    /**
     * 批量更新项
     */
    @Data
    @Schema(description = "批量更新项")
    public static class BatchUpdateItem implements Serializable {
        @Serial
        private static final long serialVersionUID = 1L;

        @Schema(description = "菜单ID")
        private Long menuId;

        @Schema(description = "更新的字段")
        private Map<String, Object> fields;

        @Schema(description = "条件（可选）")
        private Map<String, Object> conditions;
    }

    @Schema(description = "详细更新项列表（优先级高于updateFields）")
    private List<BatchUpdateItem> updateItems;

    @Schema(description = "排序规则")
    private Map<String, Object> sortRules;

    @Schema(description = "验证规则")
    private Map<String, Object> validationRules;
}