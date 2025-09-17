import { request } from '@/service/request';

// =============== Health Begin ===============

/** get alertrules list */
export function fetchGetAlertRulesList(params?: Api.Health.AlertRulesSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.AlertRulesList>({
    url: '/t_alert_rules/page',
    method: 'GET',
    params: filteredParams
  });
}

/** add alertrules info */
export function fetchAddAlertRules(data: Api.Health.AlertRulesEdit) {
  return request<boolean>({
    url: '/t_alert_rules/',
    method: 'POST',
    data
  });
}

/** update alertrules info */
export function fetchUpdateAlertRulesInfo(data: Api.Health.AlertRulesEdit) {
  return request<boolean>({
    url: '/t_alert_rules/',
    method: 'PUT',
    data
  });
}

/** edit delete alertrules */
export function fetchDeleteAlertRules(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_alert_rules/',
    method: 'DELETE',
    data
  });
}

// =============== Health End  ===============
