declare namespace Api {
  namespace Geofence {
    type Geofence = Common.CommonRecord<{
      /** 电子围栏名称 */
      name: string;
      /** 围栏区域 */
      area: any;
      /** 围栏描述 */
      description: string;
      /** 围栏状态 */
      status: any;
      /** 创建用户 */
      createUser: string;
      /** 创建时间 */
      createTime: string;
      /** 围栏类型 */
      fenceType?: 'CIRCLE' | 'RECTANGLE' | 'POLYGON';
      /** 中心点经度 */
      centerLng?: number;
      /** 中心点纬度 */
      centerLat?: number;
      /** 半径(米) */
      radius?: number;
      /** 进入告警 */
      alertOnEnter?: boolean;
      /** 离开告警 */
      alertOnExit?: boolean;
      /** 停留告警 */
      alertOnStay?: boolean;
      /** 停留时长阈值(分钟) */
      stayDurationMinutes?: number;
      /** 告警级别 */
      alertLevel?: 'LOW' | 'MEDIUM' | 'HIGH';
      /** 租户ID */
      customerId?: number;
      /** 是否启用 */
      isActive?: boolean;
    }>;

    /** Geofence Alert */
    type GeofenceAlert = Common.CommonRecord<{
      /** 告警ID */
      alertId: string;
      /** 围栏ID */
      fenceId: number;
      /** 围栏名称 */
      fenceName: string;
      /** 用户ID */
      userId: number;
      /** 设备序列号 */
      deviceSn: string;
      /** 事件类型 */
      eventType: 'ENTER' | 'EXIT' | 'STAY_TIMEOUT';
      /** 事件时间 */
      eventTime: string;
      /** 位置经度 */
      locationLng: number;
      /** 位置纬度 */
      locationLat: number;
      /** 告警级别 */
      alertLevel: 'LOW' | 'MEDIUM' | 'HIGH';
      /** 告警状态 */
      alertStatus: 'PENDING' | 'PROCESSING' | 'PROCESSED' | 'IGNORED';
      /** 处理时间 */
      processTime?: string;
      /** 处理人 */
      processedBy?: string;
      /** 处理备注 */
      processNote?: string;
      /** 通知状态 */
      notificationStatus?: any;
      /** 租户ID */
      customerId?: number;
      /** 组织ID */
      orgId?: number;
    }>;

    /** Geofence Event */
    type GeofenceEvent = {
      /** 事件ID */
      eventId: string;
      /** 围栏ID */
      fenceId: number;
      /** 围栏名称 */
      fenceName: string;
      /** 用户ID */
      userId: number;
      /** 事件类型 */
      eventType: 'ENTER' | 'EXIT' | 'STAY_TIMEOUT';
      /** 事件时间 */
      eventTime: string;
      /** 位置经度 */
      locationLng: number;
      /** 位置纬度 */
      locationLat: number;
      /** 告警级别 */
      alertLevel: 'LOW' | 'MEDIUM' | 'HIGH';
      /** 设备ID */
      deviceId?: string;
    };

    /** Geofence search params */
    type GeofenceSearchParams = CommonType.RecordNullable<Pick<Api.Geofence.Geofence, 'name' | 'status'> & Api.Common.CommonSearchParams>;

    /** Geofence Alert search params */
    type GeofenceAlertSearchParams = CommonType.RecordNullable<{
      /** 用户ID */
      userId?: number;
      /** 围栏ID */
      fenceId?: number;
      /** 事件类型 */
      eventType?: 'ENTER' | 'EXIT' | 'STAY_TIMEOUT';
      /** 告警状态 */
      alertStatus?: 'PENDING' | 'PROCESSING' | 'PROCESSED' | 'IGNORED';
      /** 告警级别 */
      alertLevel?: 'LOW' | 'MEDIUM' | 'HIGH';
      /** 开始时间 */
      startTime?: string;
      /** 结束时间 */
      endTime?: string;
      /** 数量限制 */
      limit?: number;
    } & Api.Common.CommonSearchParams>;

    /** Geofence Alert Process */
    type GeofenceAlertProcess = {
      /** 告警ID */
      alertId: string;
      /** 新状态 */
      newStatus: 'PROCESSING' | 'PROCESSED' | 'IGNORED';
      /** 处理备注 */
      processNote?: string;
    };

    /** Geofence Alert Stats */
    type GeofenceAlertStats = {
      /** 总数 */
      total: number;
      /** 待处理 */
      pending: number;
      /** 处理中 */
      processing: number;
      /** 已处理 */
      processed: number;
      /** 已忽略 */
      ignored: number;
      /** 各级别统计 */
      levelStats: {
        low: number;
        medium: number;
        high: number;
      };
      /** 各类型统计 */
      typeStats: {
        enter: number;
        exit: number;
        stayTimeout: number;
      };
    };

    /** Geofence edit model */
    type GeofenceEdit = Pick<Api.Geofence.Geofence, 'id' | 'name' | 'area' | 'description' | 'status'>;

    /** Geofence list */
    type GeofenceList = Common.PaginatingQueryRecord<Geofence>;

    /** Geofence Alert list */
    type GeofenceAlertList = Common.PaginatingQueryRecord<GeofenceAlert>;
  }
}
