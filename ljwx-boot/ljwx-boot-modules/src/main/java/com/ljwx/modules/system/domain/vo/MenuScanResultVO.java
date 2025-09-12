package com.ljwx.modules.system.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.List;

/**
 * 菜单扫描结果VO
 * 
 * @author bruno.gao
 */
@Data
@Schema(description = "菜单扫描结果")
public class MenuScanResultVO implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    @Schema(description = "扫描时间")
    private String scanTime;

    @Schema(description = "发现的文件列表")
    private List<String> foundFiles;

    @Schema(description = "变更的文件列表")
    private List<String> changedFiles;

    @Schema(description = "新发现的路由")
    private List<RouteInfo> newRoutes;

    @Schema(description = "扫描统计")
    private ScanStats scanStats;

    @Schema(description = "扫描标签")
    private String scanTag;

    @Schema(description = "扫描消息")
    private List<String> messages;

    @Schema(description = "扫描警告")
    private List<String> warnings;

    @Schema(description = "扫描错误")
    private List<String> errors;

    /**
     * 路由信息
     */
    @Data
    @Schema(description = "路由信息")
    public static class RouteInfo implements Serializable {
        @Serial
        private static final long serialVersionUID = 1L;

        @Schema(description = "路由路径")
        private String path;

        @Schema(description = "路由名称")
        private String name;

        @Schema(description = "页面标题")
        private String title;

        @Schema(description = "组件路径")
        private String component;

        @Schema(description = "文件路径")
        private String filePath;

        @Schema(description = "文件修改时间")
        private String lastModified;

        @Schema(description = "文件大小")
        private Long fileSize;

        @Schema(description = "路由类型：page-页面，component-组件")
        private String routeType = "page";

        @Schema(description = "是否为新路由")
        private Boolean isNew = true;

        @Schema(description = "菜单层级")
        private Integer level;

        @Schema(description = "建议的父菜单")
        private String suggestedParent;

        @Schema(description = "建议的图标")
        private String suggestedIcon;

        @Schema(description = "建议的排序值")
        private Integer suggestedSort;

        @Schema(description = "解析的元数据")
        private Object metadata;
    }

    /**
     * 扫描统计信息
     */
    @Data
    @Schema(description = "扫描统计信息")
    public static class ScanStats implements Serializable {
        @Serial
        private static final long serialVersionUID = 1L;

        @Schema(description = "总文件数")
        private Integer totalFiles = 0;

        @Schema(description = "Vue文件数")
        private Integer vueFiles = 0;

        @Schema(description = "TypeScript文件数")
        private Integer tsFiles = 0;

        @Schema(description = "JavaScript文件数")
        private Integer jsFiles = 0;

        @Schema(description = "变更文件数")
        private Integer changedFiles = 0;

        @Schema(description = "新路由数")
        private Integer newRoutes = 0;

        @Schema(description = "已存在路由数")
        private Integer existingRoutes = 0;

        @Schema(description = "扫描耗时（毫秒）")
        private Long scanDuration = 0L;

        @Schema(description = "处理的目录数")
        private Integer processedDirectories = 0;

        @Schema(description = "跳过的文件数")
        private Integer skippedFiles = 0;

        @Schema(description = "错误文件数")
        private Integer errorFiles = 0;
    }
}