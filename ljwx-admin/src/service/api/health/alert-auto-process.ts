import { request } from '@/service/request';

/** 获取告警自动处理规则列表 */
export function fetchGetAlertAutoProcessList(params?: Api.Health.AlertAutoProcessSearchParams) {
  return request<Api.Health.AlertAutoProcessList>({
    url: '/admin/health/alert-auto-process/list',
    method: 'GET',
    params
  });
}

/** 获取告警自动处理规则详情 */
export function fetchGetAlertAutoProcess(id: string) {
  return request<Api.Health.AlertAutoProcess>({
    url: `/admin/health/alert-auto-process/${id}`,
    method: 'GET'
  });
}

/** 新增告警自动处理规则 */
export function fetchAddAlertAutoProcess(data: Api.Health.AlertAutoProcessEdit) {
  return request<boolean>({
    url: '/admin/health/alert-auto-process',
    method: 'POST',
    data
  });
}

/** 更新告警自动处理规则 */
export function fetchUpdateAlertAutoProcess(data: Api.Health.AlertAutoProcessEdit) {
  return request<boolean>({
    url: '/admin/health/alert-auto-process',
    method: 'PUT',
    data
  });
}

/** 删除告警自动处理规则 */
export function fetchDeleteAlertAutoProcess(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/admin/health/alert-auto-process',
    method: 'DELETE',
    data
  });
}

/** 批量启用/禁用自动处理 */
export function fetchToggleAutoProcess(data: { ids: string[]; enabled: boolean }) {
  return request<boolean>({
    url: '/admin/health/alert-auto-process/toggle-auto-process',
    method: 'PUT',
    data
  });
}

/** 获取自动处理规则统计 */
export function fetchGetAlertAutoProcessStats(params?: { customerId?: string }) {
  return request<Api.Health.AlertAutoProcessStats>({
    url: '/admin/health/alert-auto-process/stats',
    method: 'GET',
    params
  });
}

/** 导出自动处理规则 */
export function fetchExportAlertAutoProcess(params?: Api.Health.AlertAutoProcessSearchParams) {
  return request<Blob>({
    url: '/admin/health/alert-auto-process/export',
    method: 'POST',
    data: params,
    responseType: 'blob'
  });
}

/** 获取自动处理动作选项 */
export function fetchGetActionOptions() {
  return request<Record<string, string>>({
    url: '/admin/health/alert-auto-process/action-options',
    method: 'GET'
  });
}

/** 获取严重程度选项 */
export function fetchGetSeverityOptions() {
  return request<Record<string, string>>({
    url: '/admin/health/alert-auto-process/severity-options',
    method: 'GET'
  });
}
