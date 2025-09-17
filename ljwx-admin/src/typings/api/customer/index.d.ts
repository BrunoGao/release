declare namespace Api {
  /**
   * namespace Customer
   *
   * backend api module: "Customer"
   */
  namespace Customer {
    /** 客户信息 */
    interface CustomerInfo {
      id: number;
      name: string;
      code?: string;
      logo?: string;
      status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
      description?: string;
      contactPerson?: string;
      contactPhone?: string;
      contactEmail?: string;
      address?: string;
      createTime?: string;
      updateTime?: string;
    }

    /** 客户搜索参数 */
    interface CustomerSearchParams extends Api.Common.CommonSearchParams {
      name?: string;
      code?: string;
      status?: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
      contactPerson?: string;
    }

    /** 客户列表响应 */
    interface CustomerList {
      records: CustomerInfo[];
      page: number;
      pageSize: number;
      total: number;
    }

    /** 客户统计信息 */
    interface CustomerStatistics {
      totalUsers: number;
      activeUsers: number;
      totalDevices: number;
      activeDevices: number;
      totalOrgs: number;
      totalMessages: number;
      totalAlerts: number;
      healthDataCount: number;
      lastActivityTime?: string;
    }

    /** 客户切换历史记录 */
    interface CustomerSwitchHistory {
      id: number;
      userId: number;
      userName: string;
      fromCustomerId?: number;
      fromCustomerName?: string;
      toCustomerId: number;
      toCustomerName: string;
      reason?: string;
      ipAddress: string;
      userAgent: string;
      switchTime: string;
    }

    /** 客户切换历史列表 */
    interface CustomerSwitchHistoryList {
      records: CustomerSwitchHistory[];
      page: number;
      pageSize: number;
      total: number;
    }

    /** 客户访问权限 */
    interface CustomerAccess {
      customerId: number;
      permissions: string[];
      roles: string[];
      hasFullAccess: boolean;
      restrictions?: {
        modules?: string[];
        operations?: string[];
        dataScope?: string;
      };
    }
  }
}
