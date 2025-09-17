import { request } from '@/service/request';

// =============== Customer Management APIs ===============

/** 获取客户列表 */
export function fetchGetCustomerList(params?: Api.Customer.CustomerSearchParams) {
  return request<Api.Customer.CustomerList>({
    url: '/sys/customer/page',
    method: 'GET',
    params
  });
}

/** 获取客户详情 */
export function fetchGetCustomerById(customerId: number) {
  return request<Api.Customer.CustomerInfo>({
    url: `/sys/customer/${customerId}`,
    method: 'GET'
  });
}

/** 根据组织ID获取客户ID */
export function fetchCustomerIdByOrgId(orgId: number) {
  return request<{ customerId: number }>({
    url: `/sys/org-units/${orgId}/customer`,
    method: 'GET'
  });
}

/** 获取当前用户可访问的客户列表 */
export function fetchGetAccessibleCustomers() {
  return request<Api.Customer.CustomerInfo[]>({
    url: '/sys/customer/accessible',
    method: 'GET'
  });
}

/** 验证用户对客户的访问权限 */
export function fetchVerifyCustomerAccess(customerId: number) {
  return request<{ hasAccess: boolean; permissions: string[] }>({
    url: `/sys/customer/${customerId}/verify-access`,
    method: 'GET'
  });
}

/** 获取客户统计信息 */
export function fetchGetCustomerStatistics(customerId: number) {
  return request<Api.Customer.CustomerStatistics>({
    url: `/sys/customer/${customerId}/statistics`,
    method: 'GET'
  });
}

// =============== Customer Switch History ===============

/** 获取客户切换历史 */
export function fetchGetCustomerSwitchHistory(params?: {
  page?: number;
  pageSize?: number;
  startDate?: string;
  endDate?: string;
}) {
  return request<Api.Customer.CustomerSwitchHistoryList>({
    url: '/sys/customer/switch-history',
    method: 'GET',
    params
  });
}

/** 记录客户切换操作 */
export function fetchRecordCustomerSwitch(data: {
  fromCustomerId?: number;
  toCustomerId: number;
  reason?: string;
}) {
  return request<boolean>({
    url: '/sys/customer/switch-history',
    method: 'POST',
    data
  });
}

// =============== Customer Config APIs ===============

/** 获取所有可用的客户列表（用于客户选择器） */
export function fetchGetAllAvailableCustomers() {
  return request<Array<{ customerId: number; customerName: string }>>({
    url: '/t_customer_config/all-customers',
    method: 'GET'
  });
}