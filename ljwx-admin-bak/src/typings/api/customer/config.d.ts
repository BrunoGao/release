declare namespace Api {
  namespace Customer {
    type CustomerConfig = Common.CommonRecord<{
      customerName: string;
      description: string;
      uploadMethod: any;
      licenseKey: number;
      supportLicense: boolean;
      id: number;
      enableResume: boolean;
      uploadRetryCount: number;
      cacheMaxCount: number;
    }>;

    /** CustomerConfig search params */
    type CustomerConfigSearchParams = CommonType.RecordNullable<Pick<Api.Customer.CustomerConfig, 'id'> & Api.Common.CommonSearchParams>;

    /** CustomerConfig edit model */
    type CustomerConfigEdit = Pick<
      Api.Customer.CustomerConfig,
      'customerName' | 'description' | 'uploadMethod' | 'licenseKey' | 'supportLicense' | 'enableResume' | 'uploadRetryCount' | 'cacheMaxCount'
    >;
    /** CustomerConfig list */
    type CustomerConfigList = Common.PaginatingQueryRecord<CustomerConfig>;
  }
}
