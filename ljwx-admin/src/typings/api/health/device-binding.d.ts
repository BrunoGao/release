declare namespace Api {
  namespace DeviceBinding {
    /** 设备绑定申请记录 */
    interface DeviceBindRequest {
      /** 申请ID */
      id: string;
      /** 设备序列号 */
      deviceSn: string;
      /** 申请用户ID */
      userId: string;
      /** 申请用户姓名 */
      userName?: string;
      /** 手机号码 */
      phoneNumber: string;
      /** 组织ID */
      orgId?: string;
      /** 申请时间 */
      applyTime: string;
      /** 审批时间 */
      approveTime?: string;
      /** 审批人ID */
      approverId?: string;
      /** 审批人姓名 */
      approverName?: string;
      /** 申请状态 */
      status: 'PENDING' | 'APPROVED' | 'REJECTED';
      /** 审批备注 */
      comment?: string;
      /** 创建时间 */
      createTime?: string;
      /** 更新时间 */
      updateTime?: string;
    }

    /** 检查设备绑定状态参数 */
    interface CheckBindingParams {
      /** 设备序列号 */
      serialNumber: string;
      /** 手机号码 */
      phoneNumber: string;
    }

    /** 检查设备绑定状态结果 */
    interface CheckBindingResult {
      /** 操作是否成功 */
      success: boolean;
      /** 绑定关系是否存在 */
      exists?: boolean;
      /** 是否已绑定 */
      bound?: boolean;
      /** 是否有待审批申请 */
      pending?: boolean;
      /** 绑定的用户ID */
      user_id?: string;
      /** 错误信息 */
      error?: string;
    }

    /** 提交绑定申请参数 */
    interface SubmitApplicationParams {
      /** 设备序列号 */
      device_sn: string;
      /** 手机号码 */
      phone_number: string;
      /** 申请用户ID */
      user_id: string;
      /** 申请时间戳 */
      timestamp?: string;
    }

    /** 提交绑定申请结果 */
    interface SubmitApplicationResult {
      /** 操作是否成功 */
      success: boolean;
      /** 成功消息 */
      message?: string;
      /** 申请ID */
      request_id?: string;
      /** 错误信息 */
      error?: string;
    }

    /** 申请列表搜索参数 */
    interface ApplicationSearchParams {
      /** 申请状态 */
      status?: 'PENDING' | 'APPROVED' | 'REJECTED';
      /** 当前页码 */
      current?: number;
      /** 每页数量 */
      size?: number;
    }

    /** 申请列表结果 */
    interface ApplicationListResult {
      /** 操作是否成功 */
      success: boolean;
      /** 数据 */
      data?: {
        /** 申请记录列表 */
        items: DeviceBindRequest[];
        /** 总数量 */
        total: number;
        /** 当前页 */
        page: number;
        /** 每页大小 */
        size: number;
        /** 总页数 */
        pages: number;
      };
      /** 错误信息 */
      error?: string;
    }

    /** 批量审批参数 */
    interface BatchApproveParams {
      /** 申请ID列表 */
      ids: string[];
      /** 审批操作 */
      action: 'APPROVED' | 'REJECTED';
      /** 审批人ID */
      approverId: string;
      /** 审批备注 */
      comment?: string;
    }

    /** 批量审批结果 */
    interface BatchApproveResult {
      /** 操作是否成功 */
      success: boolean;
      /** 成功消息 */
      message?: string;
      /** 成功处理的ID列表 */
      success_ids?: string[];
      /** 失败处理的ID列表 */
      failed_ids?: string[];
      /** 错误信息 */
      error?: string;
    }

    /** 用户绑定设备记录 */
    interface UserDeviceBinding {
      /** 绑定ID */
      id: string;
      /** 设备序列号 */
      deviceSn: string;
      /** 用户ID */
      userId: string;
      /** 用户姓名 */
      userName?: string;
      /** 绑定时间 */
      operateTime: string;
      /** 绑定状态 */
      status: 'BIND' | 'UNBIND';
    }

    /** 用户绑定列表结果 */
    interface UserBindingListResult {
      /** 操作是否成功 */
      success: boolean;
      /** 绑定设备列表 */
      data?: UserDeviceBinding[];
      /** 错误信息 */
      error?: string;
    }
  }
}
