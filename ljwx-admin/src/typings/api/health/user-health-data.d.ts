declare namespace Api {
  namespace Health {
    type UserHealthData = Common.CommonRecord<{
      departmentInfo: string;
      userId: string;
      phoneNumber: string;
      heartRate: number;
      pressureHigh: number;
      pressureLow: number;
      bloodOxygen: number;
      temperature: number;
      step: number;
      timestamp: string;
      latitude: number;
      longitude: number;
      altitude: number;
      deviceSn: string;
      distance: number;
      calorie: number;
      sleepData: string;
      exerciseDailyData: string;
      exerciseDailyWeekData: string;
      scientificSleepData: string;
      startDate: number;
      endDate: number;
      customerId: string;
    }>;

    /** UserHealthData search params */
    type UserHealthDataSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.UserHealthData, 'phoneNumber' | 'deviceSn' | 'userId' | 'departmentInfo' | 'startDate' | 'endDate' | 'customerId'> &
        Api.Common.CommonSearchParams
    >;

    /** UserHealthData edit model */
    type UserHealthDataEdit = Pick<
      Api.Health.UserHealthData,
      | 'phoneNumber'
      | 'heartRate'
      | 'pressureHigh'
      | 'pressureLow'
      | 'bloodOxygen'
      | 'temperature'
      | 'step'
      | 'timestamp'
      | 'userId'
      | 'latitude'
      | 'longitude'
      | 'altitude'
      | 'deviceSn'
      | 'distance'
      | 'calorie'
      | 'sleepData'
      | 'exerciseDailyData'
      | 'exerciseDailyWeekData'
      | 'scientificSleepData'
      | 'startDate'
      | 'endDate'
    >;
    /** UserHealthData list */
    type UserHealthDataList = Common.PaginatingQueryRecord<UserHealthData>;

    type HealthChart = Common.CommonRecord<{
      departmentInfo: string;
      userId: string;
      deviceSn: string;
      startDate: number;
      endDate: number;
      timeType: string;
      customerId: number;
      dataType: string;
    }>;
    type HealthChartSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.HealthChart, 'departmentInfo' | 'userId' | 'deviceSn' | 'startDate' | 'endDate' | 'timeType' | 'customerId' | 'dataType'> &
        Api.Common.CommonSearchParams
    >;
    type HealthChartList = Common.PaginatingQueryRecord<HealthChart>;

    export type TotalDeviceInfo = Common.CommonRecord<{
      totalDevices: number;
      deviceStatusCounts: { ACTIVE: number; INACTIVE: number };
      deviceWearableCounts: { WORN: number };
      deviceOsCounts: { 'ARC-AL00CN 4.0.0.900(SP41C700E104R412P100)': number };
      deviceChargingCounts: { CHARGING: number; UNCHARGING: number };
    }>;
    export type TotalUserInfo = Common.CommonRecord<{
      totalUsers: number;
      userStatusCounts: { '1': number; '0': number };
      deviceBindCounts: { BOUND: number; UNBOUND: number };
    }>;
    export type TotalMessageInfo = Common.CommonRecord<{
      totalMessages: number;
      messageTypeCounts: { announcement: number; notification: number; job: number; task: number };
    }>;
    export type TotalAlertInfo = Common.CommonRecord<{
      alertStatusCounts: {
        pending: number;
      };
      alertTypeCounts: {
        [key: string]: number; // 动态键名
      };
      alerts: Array<any>; // 如果需要可以定义具体的 Alert 类型
      severityLevelCounts: {
        high: number;
        critical: number;
        medium: number;
      };
      totalAlerts: number;
      uniqueAlertTypes: number;
    }>;
  }
}
