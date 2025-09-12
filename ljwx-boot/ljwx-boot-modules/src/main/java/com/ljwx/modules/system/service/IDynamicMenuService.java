package com.ljwx.modules.system.service;

import com.ljwx.modules.system.domain.dto.menu.DynamicMenuConfigDTO;
import com.ljwx.modules.system.domain.dto.menu.DynamicMenuScanDTO;
import com.ljwx.modules.system.domain.dto.menu.MenuBatchUpdateDTO;
import com.ljwx.modules.system.domain.vo.DynamicMenuVO;
import com.ljwx.modules.system.domain.vo.MenuScanResultVO;

import java.util.List;

/**
 * 动态菜单管理服务接口
 * 提供前端路由扫描、菜单自动同步、灵活配置等功能
 * 
 * @author bruno.gao
 */
public interface IDynamicMenuService {

    /**
     * 扫描前端路由文件，发现新的页面和路由
     * 
     * @param scanDTO 扫描配置
     * @return 扫描结果
     */
    MenuScanResultVO scanFrontendRoutes(DynamicMenuScanDTO scanDTO);

    /**
     * 自动同步菜单配置
     * 根据扫描结果自动创建或更新菜单项
     * 
     * @param scanDTO 同步配置
     * @return 同步结果描述
     */
    String autoSyncMenus(DynamicMenuScanDTO scanDTO);

    /**
     * 获取动态菜单配置
     * 
     * @param customerId 租户ID（null表示全局）
     * @return 菜单配置列表
     */
    List<DynamicMenuVO> getDynamicMenuConfig(Long customerId);

    /**
     * 更新动态菜单配置
     * 
     * @param configDTO 菜单配置
     * @return 更新结果
     */
    String updateDynamicMenuConfig(DynamicMenuConfigDTO configDTO);

    /**
     * 批量更新菜单
     * 支持批量修改名称、图标、排序等
     * 
     * @param batchDTO 批量更新数据
     * @return 更新结果
     */
    String batchUpdateMenus(MenuBatchUpdateDTO batchDTO);

    /**
     * 重新排序菜单
     * 
     * @param menuIds 菜单ID列表（按新顺序排列）
     * @return 排序结果
     */
    String reorderMenus(List<Long> menuIds);

    /**
     * 应用预设菜单模板
     * 
     * @param templateName 模板名称
     * @param customerId 租户ID
     * @return 应用结果
     */
    String applyPresetTemplate(String templateName, Long customerId);

    /**
     * 清除菜单缓存
     * 
     * @param customerId 租户ID（null表示清除所有）
     * @return 清除结果
     */
    String clearMenuCache(Long customerId);

    /**
     * 预览菜单配置
     * 根据角色权限预览实际显示的菜单
     * 
     * @param customerId 租户ID
     * @param roleId 角色ID
     * @return 预览菜单
     */
    List<DynamicMenuVO> previewMenuConfig(Long customerId, Long roleId);

    /**
     * 导入菜单配置
     * 
     * @param configList 菜单配置列表
     * @return 导入结果
     */
    String importMenuConfig(List<DynamicMenuConfigDTO> configList);

    /**
     * 导出菜单配置
     * 
     * @param customerId 租户ID
     * @return 菜单配置
     */
    List<DynamicMenuConfigDTO> exportMenuConfig(Long customerId);

    /**
     * 检测前端页面文件变化
     * 
     * @return 变化的文件列表
     */
    List<String> detectPageChanges();

    /**
     * 自动生成菜单项
     * 基于文件路径和命名规范自动生成菜单配置
     * 
     * @param routePath 路由路径
     * @param filePath 文件路径
     * @return 生成的菜单配置
     */
    DynamicMenuConfigDTO autoGenerateMenu(String routePath, String filePath);

    /**
     * 验证菜单配置
     * 
     * @param config 菜单配置
     * @return 验证结果
     */
    List<String> validateMenuConfig(DynamicMenuConfigDTO config);

    /**
     * 获取菜单使用统计
     * 
     * @param customerId 租户ID
     * @return 使用统计
     */
    Object getMenuUsageStats(Long customerId);
}