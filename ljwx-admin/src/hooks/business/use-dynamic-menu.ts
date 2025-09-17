import { request } from '@/service/request';

export function useDynamicMenu() {
  /** 获取动态菜单配置 */
  function getDynamicMenus(customerId?: number) {
    return request<Api.System.DynamicMenuVO[]>({
      url: '/sys_menu/dynamic/config',
      method: 'get',
      params: { customerId }
    });
  }

  /** 扫描前端路由文件 */
  function scanRoutes(params: Api.System.DynamicMenuScanDTO) {
    return request<Api.System.MenuScanResultVO>({
      url: '/sys_menu/dynamic/scan',
      method: 'post',
      data: params
    });
  }

  /** 自动同步菜单配置 */
  function autoSyncMenus(params: Api.System.DynamicMenuScanDTO) {
    return request<string>({
      url: '/sys_menu/dynamic/auto-sync',
      method: 'post',
      data: params
    });
  }

  /** 更新动态菜单配置 */
  function updateMenuConfig(config: Api.System.DynamicMenuConfigDTO) {
    return request<string>({
      url: '/sys_menu/dynamic/config',
      method: 'put',
      data: config
    });
  }

  /** 批量更新菜单 */
  function batchUpdateMenus(params: Api.System.MenuBatchUpdateDTO) {
    return request<string>({
      url: '/sys_menu/dynamic/batch',
      method: 'put',
      data: params
    });
  }

  /** 重新排序菜单 */
  function reorderMenus(menuIds: number[]) {
    return request<string>({
      url: '/sys_menu/dynamic/reorder',
      method: 'put',
      data: menuIds
    });
  }

  /** 应用预设菜单模板 */
  function applyPresetTemplate(templateName: string, customerId?: number) {
    return request<string>({
      url: '/sys_menu/dynamic/preset',
      method: 'post',
      params: { templateName, customerId }
    });
  }

  /** 清除菜单缓存 */
  function clearMenuCache(customerId?: number) {
    return request<string>({
      url: '/sys_menu/dynamic/cache',
      method: 'delete',
      params: { customerId }
    });
  }

  /** 预览菜单配置 */
  function previewMenuConfig(customerId?: number, roleId?: number) {
    return request<Api.System.DynamicMenuVO[]>({
      url: '/sys_menu/dynamic/preview',
      method: 'get',
      params: { customerId, roleId }
    });
  }

  /** 导入菜单配置 */
  function importMenuConfig(configList: Api.System.DynamicMenuConfigDTO[]) {
    return request<string>({
      url: '/sys_menu/dynamic/import',
      method: 'post',
      data: configList
    });
  }

  /** 导出菜单配置 */
  function exportMenuConfig(customerId?: number) {
    return request<Api.System.DynamicMenuConfigDTO[]>({
      url: '/sys_menu/dynamic/export',
      method: 'get',
      params: { customerId }
    });
  }

  /** 获取菜单使用统计 */
  function getMenuUsageStats(customerId?: number) {
    return request<any>({
      url: '/sys_menu/dynamic/stats',
      method: 'get',
      params: { customerId }
    });
  }

  return {
    getDynamicMenus,
    scanRoutes,
    autoSyncMenus,
    updateMenuConfig,
    batchUpdateMenus,
    reorderMenus,
    applyPresetTemplate,
    clearMenuCache,
    previewMenuConfig,
    importMenuConfig,
    exportMenuConfig,
    getMenuUsageStats
  };
}

export default useDynamicMenu;
