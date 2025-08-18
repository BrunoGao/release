import { request } from '@/service/request';

// =============== Wechaalerconfig Begin ===============

/** get wechaalerconfig list */
export function fetchGetAlertConfigWechatList(params?: Api.Health.AlertConfigWechatSearchParams) {
  return request<Api.Health.AlertConfigWechatList>({
    url: '/t_wechat_alarm_config/page',
    method: 'GET',
    params
  });
}

/** add wechaalerconfig info */
export function fetchAddAlertConfigWechat(data: Api.Health.AlertConfigWechatEdit) {
  return request<boolean>({
    url: '/t_wechat_alarm_config/',
    method: 'POST',
    data
  });
}

/** update wechaalerconfig info */
export function fetchUpdateAlertConfigWechatInfo(data: Api.Health.AlertConfigWechatEdit) {
  return request<boolean>({
    url: '/t_wechat_alarm_config/',
    method: 'PUT',
    data
  });
}

/** edit delete wechaalerconfig */
export function fetchDeleteAlertConfigWechat(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_wechat_alarm_config/',
    method: 'DELETE',
    data
  });
}

// =============== Wechaalerconfig End  ===============
