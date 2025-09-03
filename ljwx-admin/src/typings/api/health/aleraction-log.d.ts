declare namespace Api {
  namespace Health {
    type AleractionLog = Common.CommonRecord<{
      logId: number;
      alertId: number;
      action: string;
      actionTimestamp: string;
      actionUser: string;
      actionUserId: number;
      details: string;
      result: string;
      orgId: number;
    }>;

    /** AleractionLog search params */
    type AleractionLogSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.AleractionLog, 'alertId' | 'actionUser' | 'result' | 'logId' | 'orgId'> & Api.Common.CommonSearchParams
    >;

    /** AleractionLog edit model */
    type AleractionLogEdit = Pick<
      Api.Health.AleractionLog,
      'logId' | 'alertId' | 'action' | 'actionTimestamp' | 'actionUser' | 'actionUserId' | 'details' | 'result'
    >;
    /** AleractionLog list */
    type AleractionLogList = Common.PaginatingQueryRecord<AleractionLog>;
  }
}
