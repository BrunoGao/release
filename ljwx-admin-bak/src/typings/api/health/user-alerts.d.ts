declare namespace Api {
  namespace Health {
    type UserAlerts = Common.CommonRecord<{
      alertType: string;
      deviceSn: string;
      timestamp: string;
      alertDesc: string;
    }>;

    /** UserAlerts search params */
    type UserAlertsSearchParams = CommonType.RecordNullable<Pick<Api.Health.UserAlerts, 'alertType' | 'deviceSn'> & Api.Common.CommonSearchParams>;

    /** UserAlerts edit model */
    type UserAlertsEdit = Pick<Api.Health.UserAlerts, 'alertType' | 'deviceSn' | 'timestamp' | 'alertDesc'>;
    /** UserAlerts list */
    type UserAlertsList = Common.PaginatingQueryRecord<UserAlerts>;
  }
}
