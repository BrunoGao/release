declare namespace Api {
  namespace Health {
    type AlertRules = Common.CommonRecord<{
      ruleType: string;
      physicalSign: string;
      thresholdMin: number;
      thresholdMax: number;
      deviationPercentage: number;
      trendDuration: number;
      parameters: any;
      triggerCondition: string;
      alertMessage: string;
      severityLevel: string;
      notificationType: string;
      customerId: number;
    }>;

    /** AlertRules search params */
    type AlertRulesSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.AlertRules, 'ruleType' | 'physicalSign' | 'severityLevel' | 'customerId'> & Api.Common.CommonSearchParams
    >;

    /** AlertRules edit model */
    type AlertRulesEdit = Pick<
      Api.Health.AlertRules,
      | 'ruleType'
      | 'physicalSign'
      | 'thresholdMin'
      | 'thresholdMax'
      | 'deviationPercentage'
      | 'trendDuration'
      | 'parameters'
      | 'triggerCondition'
      | 'alertMessage'
      | 'severityLevel'
      | 'notificationType'
      | 'customerId'
    >;
    /** AlertRules list */
    type AlertRulesList = Common.PaginatingQueryRecord<AlertRules>;
  }
}
