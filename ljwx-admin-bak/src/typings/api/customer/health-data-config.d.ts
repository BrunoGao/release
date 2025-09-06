declare namespace Api {
  namespace Customer {
    type HealthDataConfig = Common.CommonRecord<{
      customerId: number;
      dataType: string;
      frequencyInterval: number;
      isRealtime: number;
      isEnabled: number;
      isDefault: number;
      weight: number;
    }>;

    /** HealthDataConfig search params */
    type HealthDataConfigSearchParams = CommonType.RecordNullable<Pick<Api.Customer.HealthDataConfig, 'customerId'> & Api.Common.CommonSearchParams>;

    /** HealthDataConfig edit model */
    type HealthDataConfigEdit = Pick<
      Api.Customer.HealthDataConfig,
      'id' | 'customerId' | 'dataType' | 'frequencyInterval' | 'isRealtime' | 'isEnabled' | 'isDefault' | 'weight'
    >;

    /** HealthDataConfig list */
    type HealthDataConfigList = Common.PaginatingQueryRecord<HealthDataConfig>;
  }
}
