declare namespace Api {
  namespace Health {
    type DeviceConfig = Common.CommonRecord<{
      spo2measureperiod: number;
      stressmeasureperiod: number;
      bodytemperaturemeasureperiod: number;
      heartratewarninghigh: number;
      heartratewarninglow: number;
      spo2warning: number;
      stresswarning: number;
      bodytemperaturehighwarning: number;
      bodytemperaturelowwarning: number;
      httpurl: string;
      logo: string;
      uitype: string;
      bodytemperaturewarningcnt: number;
      heartwarningcnt: number;
      heartratemeasureperiod: number;
      spo2warningcnt: number;
      stressmonitoringenabled: number;
      stepsmonitoringenabled: number;
      distancemonitoringenabled: number;
      caloriemonitoringenabled: number;
      sleepmonitoringenabled: number;
      ecgmonitoringenabled: number;
      locationmonitoringenabled: number;
      soseventlistenerenabled: number;
      doubleclickeventlistenerenabled: number;
      temperatureabnormallistenerenabled: number;
      heartrateabnormallistenerenabled: number;
      stressabnormallistenerenabled: number;
      falleventlistenerenabled: number;
      spo2abnormallistenerenabled: number;
      oneclickalarmlistenerenabled: number;
      wearingstatuslistenerenabled: number;
      createUser: string;
      createTime: string;
    }>;

    /** DeviceConfig search params */
    type DeviceConfigSearchParams = CommonType.RecordNullable<Pick<Api.Health.DeviceConfig, 'logo'> & Api.Common.CommonSearchParams>;

    /** DeviceConfig edit model */
    type DeviceConfigEdit = Pick<
      Api.Health.DeviceConfig,
      | 'spo2measureperiod'
      | 'stressmeasureperiod'
      | 'bodytemperaturemeasureperiod'
      | 'heartratewarninghigh'
      | 'heartratewarninglow'
      | 'spo2warning'
      | 'stresswarning'
      | 'bodytemperaturehighwarning'
      | 'bodytemperaturelowwarning'
      | 'httpurl'
      | 'logo'
      | 'uitype'
      | 'bodytemperaturewarningcnt'
      | 'heartwarningcnt'
      | 'heartratemeasureperiod'
      | 'spo2warningcnt'
      | 'stressmonitoringenabled'
      | 'stepsmonitoringenabled'
      | 'distancemonitoringenabled'
      | 'caloriemonitoringenabled'
      | 'sleepmonitoringenabled'
      | 'ecgmonitoringenabled'
      | 'locationmonitoringenabled'
      | 'soseventlistenerenabled'
      | 'doubleclickeventlistenerenabled'
      | 'temperatureabnormallistenerenabled'
      | 'heartrateabnormallistenerenabled'
      | 'stressabnormallistenerenabled'
      | 'falleventlistenerenabled'
      | 'spo2abnormallistenerenabled'
      | 'oneclickalarmlistenerenabled'
      | 'wearingstatuslistenerenabled'
      | 'createUser'
      | 'createTime'
    >;

    /** DeviceConfig list */
    type DeviceConfigList = Common.PaginatingQueryRecord<DeviceConfig>;
  }
}
