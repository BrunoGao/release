import { request } from '@/service/request';

// =============== Health Begin ===============

/** get alert info list */
export function fetchGetAlertInfoList(params?: Api.Health.AlertInfoSearchParams) {
  return request<Api.Health.AlertInfoList>({
    url: '/t_alert_info/page',
    method: 'GET',
    params
  });
}

/** add alert info */
export function fetchAddAlertInfo(data: Api.Health.AlertInfoEdit) {
  return request<boolean>({
    url: '/t_alert_info/',
    method: 'POST',
    data
  });
}

/** update alert info */
export function fetchUpdateAlertInfo(data: Api.Health.AlertInfoEdit) {
  return request<boolean>({
    url: '/t_alert_info/',
    method: 'PUT',
    data
  });
}

/** edit delete alert info */
export function fetchDeleteAlertInfo(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_alert_info/',
    method: 'DELETE',
    data
  });
}

// =============== Health End  ===============
