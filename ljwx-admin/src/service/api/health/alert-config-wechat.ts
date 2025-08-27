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

// =============== MessageConfig Begin ===============

/** get message config list */
export function fetchGetMessageConfigList(params?: Api.Health.MessageConfigSearchParams) {
  return request<Api.Health.MessageConfigList>({
    url: '/t_message_config/page',
    method: 'GET',
    params
  });
}

/** add message config */
export function createMessageConfig(data: Api.Health.MessageConfigEdit) {
  return request<boolean>({
    url: '/t_message_config/',
    method: 'POST',
    data
  });
}

/** update message config */
export function updateMessageConfig(data: Api.Health.MessageConfigEdit) {
  return request<boolean>({
    url: '/t_message_config/',
    method: 'PUT',
    data
  });
}

/** delete message config */
export function fetchDeleteMessageConfig(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_message_config/',
    method: 'DELETE',
    data
  });
}

// =============== MessageConfig End  ===============
