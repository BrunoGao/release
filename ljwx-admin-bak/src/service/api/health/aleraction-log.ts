import { request } from '@/service/request';

// =============== Health Begin ===============

/** get aleractionLog list */
export function fetchGetAleractionLogList(params?: Api.Health.AleractionLogSearchParams) {
  return request<Api.Health.AleractionLogList>({
    url: '/t_alert_action_log/page',
    method: 'GET',
    params
  });
}

/** add aleractionLog info */
export function fetchAddAleractionLog(data: Api.Health.AleractionLogEdit) {
  return request<boolean>({
    url: '/t_alert_action_log/',
    method: 'POST',
    data
  });
}

/** update aleractionLog info */
export function fetchUpdateAleractionLogInfo(data: Api.Health.AleractionLogEdit) {
  return request<boolean>({
    url: '/t_alert_action_log/',
    method: 'PUT',
    data
  });
}

/** edit delete aleractionLog */
export function fetchDeleteAleractionLog(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_alert_action_log/',
    method: 'DELETE',
    data
  });
}

// =============== Health End  ===============
