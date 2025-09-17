import { request } from '@/service/request';

/** License管理API接口 */

/** License状态信息 */
export interface LicenseStatus {
  licenseEnabled: boolean;
  licenseValid: boolean;
  globalEnabled: boolean;
  licenseInfo?: LicenseInfo;
  remainingDays: number;
  totalTenants: number;
  enabledTenants: number;
  warnings?: string[];
}

/** License详细信息 */
export interface LicenseInfo {
  licenseId: string;
  customerName: string;
  customerId: string;
  licenseType: string;
  startDate: string;
  endDate: string;
  hardwareFingerprint: string;
  maxUsers: number;
  maxDevices: number;
  maxOrganizations: number;
  features: string[];
  signature: string;
  version: string;
  createTime: string;
  remarks?: string;
}

/** License使用统计 */
export interface LicenseStatistics {
  maxDevices: number;
  maxUsers: number;
  remainingDays: number;
  currentDevices: number;
  deviceUsageRate: number;
  totalTenants: number;
  enabledTenants: number;
  featureUsage: Record<string, number>;
}

/** 租户License状态 */
export interface TenantLicenseInfo {
  customerId: number;
  customerName: string;
  supportLicense: boolean;
  licenseStatus: {
    customerId: number;
    customerSupportLicense: boolean;
    systemLicenseEnabled: boolean;
    systemLicenseValid: boolean;
    effectiveLicenseEnabled: boolean;
    licenseInfo?: LicenseInfo;
    remainingDays?: number;
    message?: string;
    error?: string;
  };
  currentDevices: number;
}

/** License使用历史记录 */
export interface LicenseUsageHistory {
  operation: string;
  description: string;
  userId: number;
  timestamp: string;
}

/** 获取系统License状态 */
export function getLicenseStatus() {
  return request<LicenseStatus>({
    url: '/license/management/status',
    method: 'get'
  });
}

/** 获取License详细信息 */
export function getLicenseInfo() {
  return request<LicenseInfo>({
    url: '/license/management/info',
    method: 'get'
  });
}

/** 导入License文件 */
export function importLicense(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  return request({
    url: '/license/management/import',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}

/** 全局启用/禁用License功能 */
export function toggleLicenseGlobally(enabled: boolean) {
  return request({
    url: `/license/management/toggle/${enabled}`,
    method: 'post'
  });
}

/** 获取租户License配置列表 */
export function getTenantLicenseList(params: { pageNum?: number; pageSize?: number; customerName?: string; supportLicense?: boolean }) {
  return request<{
    rows: TenantLicenseInfo[];
    total: number;
  }>({
    url: '/license/management/tenant/list',
    method: 'get',
    params
  });
}

/** 为租户启用/禁用License */
export function toggleTenantLicense(customerId: number, enabled: boolean) {
  return request({
    url: `/license/management/tenant/${customerId}/toggle/${enabled}`,
    method: 'post'
  });
}

/** 获取租户License状态 */
export function getTenantLicenseStatus(customerId: number) {
  return request<TenantLicenseInfo>({
    url: `/license/management/tenant/${customerId}/status`,
    method: 'get'
  });
}

/** 租户导入License（当前租户） */
export function importTenantLicense(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  return request({
    url: '/license/management/tenant/import',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}

/** 获取License使用统计 */
export function getLicenseStatistics() {
  return request<LicenseStatistics>({
    url: '/license/management/statistics',
    method: 'get'
  });
}

/** 获取License使用历史 */
export function getLicenseUsageHistory(params: { pageNum?: number; pageSize?: number; startDate?: string; endDate?: string }) {
  return request<{
    rows: LicenseUsageHistory[];
    total: number;
  }>({
    url: '/license/management/usage/history',
    method: 'get',
    params
  });
}

/** 强制重新验证License */
export function revalidateLicense() {
  return request({
    url: '/license/management/revalidate',
    method: 'post'
  });
}

/** 获取BigScreen License状态（内部API） */
export function getBigScreenLicenseStatus() {
  return request({
    url: '/license/management/bigscreen/status',
    method: 'get'
  });
}

/** 注册BigScreen设备（内部API） */
export function registerBigScreenDevice(deviceInfo: { device_sn: string; customer_id?: number }) {
  return request({
    url: '/license/management/bigscreen/device/register',
    method: 'post',
    data: deviceInfo
  });
}
