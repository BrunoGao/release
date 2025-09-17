/** License管理相关类型定义 */

declare namespace Api {
  namespace License {
    /** License基本信息 */
    interface LicenseInfo {
      /** 许可证ID */
      licenseId: string;
      /** 客户名称 */
      customerName: string;
      /** 客户ID */
      customerId: string;
      /** 许可证类型 */
      licenseType: string;
      /** 生效日期 */
      startDate: string;
      /** 过期日期 */
      endDate: string;
      /** 硬件指纹 */
      hardwareFingerprint: string;
      /** 最大用户数 */
      maxUsers: number;
      /** 最大设备数 */
      maxDevices: number;
      /** 最大组织数 */
      maxOrganizations: number;
      /** 允许的功能列表 */
      features: string[];
      /** 数字签名 */
      signature: string;
      /** 版本号 */
      version: string;
      /** 创建时间 */
      createTime: string;
      /** 备注信息 */
      remarks?: string;
    }

    /** 系统License状态 */
    interface SystemStatus {
      /** License功能是否启用 */
      licenseEnabled: boolean;
      /** License是否有效 */
      licenseValid: boolean;
      /** 全局是否启用 */
      globalEnabled: boolean;
      /** License详细信息 */
      licenseInfo?: LicenseInfo;
      /** 剩余天数 */
      remainingDays: number;
      /** 总租户数 */
      totalTenants: number;
      /** 已启用租户数 */
      enabledTenants: number;
      /** 警告信息 */
      warnings?: string[];
    }

    /** License使用统计 */
    interface Statistics {
      /** 最大设备数 */
      maxDevices: number;
      /** 最大用户数 */
      maxUsers: number;
      /** 剩余天数 */
      remainingDays: number;
      /** 当前设备数 */
      currentDevices: number;
      /** 设备使用率 */
      deviceUsageRate: number;
      /** 总租户数 */
      totalTenants: number;
      /** 已启用租户数 */
      enabledTenants: number;
      /** 功能使用统计 */
      featureUsage: Record<string, number>;
    }

    /** 租户License状态 */
    interface TenantLicenseStatus {
      /** 租户ID */
      customerId: number;
      /** 客户配置是否支持License */
      customerSupportLicense: boolean;
      /** 系统License功能是否启用 */
      systemLicenseEnabled: boolean;
      /** 系统License是否有效 */
      systemLicenseValid: boolean;
      /** 有效的License状态（综合判断结果） */
      effectiveLicenseEnabled: boolean;
      /** License详细信息 */
      licenseInfo?: LicenseInfo;
      /** 剩余天数 */
      remainingDays?: number;
      /** 状态信息 */
      message?: string;
      /** 错误信息 */
      error?: string;
    }

    /** 租户License信息 */
    interface TenantInfo {
      /** 租户ID */
      customerId: number;
      /** 租户名称 */
      customerName: string;
      /** 是否支持License */
      supportLicense: boolean;
      /** License状态 */
      licenseStatus: TenantLicenseStatus;
      /** 当前设备数 */
      currentDevices: number;
    }

    /** License使用历史记录 */
    interface UsageHistory {
      /** 操作类型 */
      operation: string;
      /** 操作描述 */
      description: string;
      /** 操作用户ID */
      userId: number;
      /** 操作时间 */
      timestamp: string;
    }

    /** License导入请求 */
    interface ImportRequest {
      /** License文件 */
      file: File;
    }

    /** License切换请求 */
    interface ToggleRequest {
      /** 是否启用 */
      enabled: boolean;
    }

    /** 租户License查询参数 */
    interface TenantQueryParams {
      /** 页码 */
      pageNum?: number;
      /** 页面大小 */
      pageSize?: number;
      /** 客户名称（模糊查询） */
      customerName?: string;
      /** 是否支持License */
      supportLicense?: boolean;
    }

    /** License使用历史查询参数 */
    interface HistoryQueryParams {
      /** 页码 */
      pageNum?: number;
      /** 页面大小 */
      pageSize?: number;
      /** 开始日期 */
      startDate?: string;
      /** 结束日期 */
      endDate?: string;
    }

    /** BigScreen设备信息 */
    interface BigScreenDeviceInfo {
      /** 设备序列号 */
      device_sn: string;
      /** 客户ID */
      customer_id?: number;
    }

    /** BigScreen License状态 */
    interface BigScreenStatus {
      /** 是否成功 */
      success: boolean;
      /** License是否有效 */
      licenseValid: boolean;
      /** 状态消息 */
      message?: string;
      /** License数据 */
      data?: {
        licenseInfo: LicenseInfo;
        remainingDays: number;
        maxDevices: number;
        features: string[];
      };
    }
  }
}
