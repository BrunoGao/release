package com.ljwx.modules.system.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serial;
import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * 动态菜单VO
 * 
 * @author bruno.gao
 */
@Data
@Schema(description = "动态菜单信息")
public class DynamicMenuVO implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    @Schema(description = "菜单ID")
    private Long id;

    @Schema(description = "父菜单ID")
    private Long parentId;

    @Schema(description = "菜单类型：1-目录，2-菜单，3-按钮")
    private String type;

    @Schema(description = "菜单名称")
    private String name;

    @Schema(description = "菜单显示名称")
    private String title;

    @Schema(description = "国际化键值")
    private String i18nKey;

    @Schema(description = "路由名称")
    private String routeName;

    @Schema(description = "路由路径")
    private String routePath;

    @Schema(description = "组件路径")
    private String component;

    @Schema(description = "菜单图标")
    private String icon;

    @Schema(description = "图标类型：1-Iconify图标，2-本地图标")
    private String iconType;

    @Schema(description = "菜单状态：1-启用，0-禁用")
    private String status;

    @Schema(description = "是否隐藏菜单：Y-隐藏，N-显示")
    private String hide;

    @Schema(description = "外链地址")
    private String href;

    @Schema(description = "iframe地址")
    private String iframeUrl;

    @Schema(description = "排序值")
    private Integer sort;

    @Schema(description = "菜单层级")
    private Integer level;

    @Schema(description = "权限标识")
    private String permission;

    @Schema(description = "租户ID")
    private Long customerId;

    @Schema(description = "是否为系统菜单")
    private Boolean isSystem;

    @Schema(description = "是否可删除")
    private Boolean deletable;

    @Schema(description = "是否可编辑")
    private Boolean editable;

    @Schema(description = "菜单描述")
    private String description;

    @Schema(description = "菜单标签")
    private List<String> tags;

    @Schema(description = "扩展属性")
    private Map<String, Object> extra;

    @Schema(description = "子菜单")
    private List<DynamicMenuVO> children;

    @Schema(description = "路由meta配置")
    private Map<String, Object> meta;

    @Schema(description = "是否需要认证")
    private Boolean requireAuth;

    @Schema(description = "是否缓存")
    private Boolean keepAlive;

    @Schema(description = "菜单布局")
    private String layout;

    @Schema(description = "菜单主题")
    private String theme;

    @Schema(description = "是否全屏显示")
    private Boolean fullscreen;

    @Schema(description = "页面加载动画")
    private String transition;

    @Schema(description = "面包屑配置")
    private Map<String, Object> breadcrumb;

    @Schema(description = "是否固定在标签栏")
    private Boolean affix;

    @Schema(description = "标签页标题")
    private String tabTitle;

    @Schema(description = "菜单激活规则")
    private String activeMenu;

    @Schema(description = "创建来源：manual-手动，scan-扫描，import-导入")
    private String source;

    @Schema(description = "源文件路径（扫描创建时记录）")
    private String sourceFile;

    @Schema(description = "最后扫描时间")
    private String lastScanTime;

    @Schema(description = "菜单版本（用于同步）")
    private String version;

    @Schema(description = "创建时间")
    private String createTime;

    @Schema(description = "更新时间")
    private String updateTime;

    @Schema(description = "使用统计")
    private Map<String, Object> usageStats;
}