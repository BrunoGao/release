declare namespace Api {
  namespace Track {
    /** Track Point */
    type TrackPoint = {
      /** 用户ID */
      userId: number;
      /** 设备序列号 */
      deviceSn: string;
      /** 时间戳 */
      timestamp: string;
      /** 经度 */
      longitude: number;
      /** 纬度 */
      latitude: number;
      /** 海拔 */
      altitude?: number;
      /** 速度(km/h) */
      speed?: number;
      /** 方向角(度，0-360) */
      bearing?: number;
      /** 定位精度(米) */
      accuracy?: number;
      /** 定位类型 1-GPS 2-网络 3-被动 */
      locationType?: number;
      /** 步数 */
      step?: number;
      /** 距离(米) */
      distance?: number;
      /** 卡路里 */
      calorie?: number;
      /** 租户ID */
      customerId?: number;
      /** 组织ID */
      orgId?: number;
    };

    /** Track Query Parameters */
    type TrackQueryParams = {
      /** 用户ID */
      userId?: number;
      /** 设备序列号 */
      deviceSn?: string;
      /** 开始时间 */
      startTime?: string;
      /** 结束时间 */
      endTime?: string;
      /** 页码 */
      pageNum?: number;
      /** 每页大小 */
      pageSize?: number;
      /** 简化容差(米) */
      simplifyTolerance?: number;
      /** 排序字段 */
      orderBy?: string;
      /** 排序方向 ASC/DESC */
      sortDirection?: string;
      /** 租户ID */
      customerId?: number;
      /** 组织ID */
      orgId?: number;
    };

    /** Track Statistics Query Parameters */
    type TrackStatsQueryParams = {
      /** 用户ID */
      userId?: number;
      /** 设备序列号 */
      deviceSn?: string;
      /** 开始时间 */
      startTime?: string;
      /** 结束时间 */
      endTime?: string;
      /** 租户ID */
      customerId?: number;
      /** 组织ID */
      orgId?: number;
    };

    /** Track Statistics */
    type TrackStats = {
      /** 用户ID */
      userId: number;
      /** 设备序列号 */
      deviceSn: string;
      /** 统计开始时间 */
      startTime: string;
      /** 统计结束时间 */
      endTime: string;
      /** 总距离(米) */
      totalDistance: number;
      /** 总时长(分钟) */
      totalDuration: number;
      /** 最大速度(km/h) */
      maxSpeed: number;
      /** 平均速度(km/h) */
      avgSpeed: number;
      /** 轨迹点数量 */
      pointCount: number;
      /** 总步数 */
      totalSteps?: number;
      /** 总卡路里 */
      totalCalories?: number;
    };

    /** Track Point List */
    type TrackPointList = TrackPoint[];

    /** Batch Track Result */
    type BatchTrackResult = Record<number, TrackPoint[]>;
  }
}