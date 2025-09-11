/**
 * Namespace Api
 *
 * All backend api type
 */
declare namespace Api {
  namespace Common {
    /** common params of paginating */
    interface PaginatingCommonParams {
      /** current page number */
      page: number;
      /** page size */
      pageSize: number;
      /** total count */
      total: number;
    }

    /** common params of paginating query list data */
    interface PaginatingQueryRecord<T = any> extends PaginatingCommonParams {
      records: T[];
    }

    /**
     * enable status
     *
     * - "0": disabled
     * - "1": enabled
     */
    type EnableStatus = '0' | '1';

    /** common record */
    type CommonRecord<T = any> = {
      /** record id */
      id: string;
      /** record creator */
      createUser: string;
      /** record create time */
      createTime: string;
      /** record updater */
      updateUser: string;
      /** record update time */
      updateTime: string;
    } & T;

    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'page' | 'pageSize'>;

    /** common delete params */
    type DeleteParams = {
      ids: string[];
    };
  }

  /**
   * Namespace Health
   *
   * Backend api types for health module
   */
  namespace Health {
    /** 告警自动处理规则 */
    type AlertAutoProcess = Common.CommonRecord<{
      /** 生理指标 */
      physicalSign: string;
      /** 告警类型 */
      alertType?: string;
      /** 事件类型 */
      eventType: string;
      /** 严重程度 */
      level: string;
      /** 阈值最小值 */
      thresholdMin: number | null;
      /** 阈值最大值 */
      thresholdMax: number | null;
      /** 告警描述 */
      alertDesc?: string;
      /** 是否启用 */
      isEnabled: boolean;
      /** 自动处理是否启用 */
      autoProcessEnabled: boolean;
      /** 自动处理动作 */
      autoProcessAction?: string;
      /** 自动处理延迟秒数 */
      autoProcessDelaySeconds?: number;
      /** 自动解决阈值计数 */
      autoResolveThresholdCount?: number;
      /** 抑制持续时间(分钟) */
      suppressDurationMinutes?: number;
      /** 时间窗口(秒) */
      timeWindowSeconds?: number;
      /** 客户ID */
      customerId?: string;
      /** 组织ID */
      orgId?: string;
      /** 备注 */
      remark?: string;
    }>;

    /** 告警自动处理规则搜索参数 */
    type AlertAutoProcessSearchParams = CommonSearchParams & {
      /** 规则名称 */
      ruleName?: string;
      /** 告警类型 */
      alertType?: string;
      /** 生理指标 */
      physicalSign?: string;
      /** 严重程度 */
      severityLevel?: string;
      /** 是否启用 */
      isEnabled?: boolean;
      /** 自动处理是否启用 */
      autoProcessEnabled?: boolean;
      /** 自动处理动作 */
      autoProcessAction?: string;
      /** 客户ID */
      customerId?: string;
      /** 组织ID */
      orgId?: string;
      /** 创建时间开始 */
      createTimeStart?: string;
      /** 创建时间结束 */
      createTimeEnd?: string;
      /** 更新时间开始 */
      updateTimeStart?: string;
      /** 更新时间结束 */
      updateTimeEnd?: string;
      /** 排序字段 */
      orderBy?: string;
      /** 排序方向 */
      sortDirection?: string;
    };

    /** 告警自动处理规则列表 */
    type AlertAutoProcessList = Common.PaginatingQueryRecord<AlertAutoProcess>;

    /** 告警自动处理规则编辑 */
    type AlertAutoProcessEdit = {
      /** ID (编辑时需要) */
      id?: string;
      /** 生理指标 */
      physicalSign: string;
      /** 事件类型 */
      eventType: string;
      /** 严重程度 */
      level: string;
      /** 阈值最小值 */
      thresholdMin: number | null;
      /** 阈值最大值 */
      thresholdMax: number | null;
      /** 告警描述 */
      alertDesc?: string;
      /** 是否启用 */
      isEnabled: boolean;
      /** 自动处理是否启用 */
      autoProcessEnabled: boolean;
      /** 自动处理动作 */
      autoProcessAction?: string;
      /** 自动处理延迟秒数 */
      autoProcessDelaySeconds?: number;
      /** 自动解决阈值计数 */
      autoResolveThresholdCount?: number;
      /** 抑制持续时间(分钟) */
      suppressDurationMinutes?: number;
      /** 时间窗口(秒) */
      timeWindowSeconds?: number;
      /** 备注 */
      remark?: string;
    };

    /** 告警自动处理规则统计 */
    type AlertAutoProcessStats = {
      /** 总规则数 */
      totalRules: number;
      /** 启用规则数 */
      enabledRules: number;
      /** 自动处理启用规则数 */
      autoProcessEnabledRules: number;
      /** 禁用规则数 */
      disabledRules?: number;
      /** 自动处理覆盖率(%) */
      autoProcessCoverageRate?: number;
      /** 按动作类型统计 */
      actionStats?: Record<string, number>;
      /** 按严重程度统计 */
      severityStats?: Record<string, number>;
      /** 按告警类型统计 */
      alertTypeStats?: Record<string, number>;
      /** 按生理指标统计 */
      physicalSignStats?: Record<string, number>;
      /** 最近24小时自动处理次数 */
      recentAutoProcessCount?: number;
      /** 最近24小时自动处理成功率(%) */
      recentAutoProcessSuccessRate?: number;
      /** 平均处理延迟时间(秒) */
      averageProcessDelaySeconds?: number;
      /** 统计时间 */
      statsTime?: string;
      /** 数据更新时间 */
      lastUpdateTime?: string;
    };

    /** 告警处理统计数据 */
    type AlertProcessingStats = {
      /** 总告警数 */
      totalAlerts: number;
      /** 自动处理告警数 */
      autoProcessedAlerts: number;
      /** 人工处理告警数 */
      manualProcessedAlerts: number;
      /** 平均处理时间(秒) */
      avgProcessingTime: number;
      /** 处理成功率(%) */
      successRate: number;
      /** 自动处理成功率(%) */
      autoProcessSuccessRate: number;
      /** 按严重程度分布 */
      severityDistribution?: Record<string, number>;
      /** 按处理动作分布 */
      actionDistribution?: Record<string, number>;
    };

    /** 告警处理日志 */
    type AlertProcessingLog = Common.CommonRecord<{
      /** 告警ID */
      alertId: string;
      /** 设备序列号 */
      deviceSn: string;
      /** 告警类型 */
      alertType: string;
      /** 严重程度 */
      severityLevel: string;
      /** 是否自动处理 */
      autoProcessed: boolean;
      /** 自动处理动作 */
      autoProcessAction?: string;
      /** 处理状态 */
      processStatus: string;
      /** 处理时间 */
      processTime: string;
      /** 处理耗时(毫秒) */
      processDuration: number;
      /** 处理结果 */
      processResult?: string;
      /** 错误信息 */
      errorMessage?: string;
      /** 规则ID */
      ruleId?: string;
      /** 客户ID */
      customerId?: string;
    }>;

    /** 告警处理日志搜索参数 */
    type AlertProcessingLogSearchParams = Common.CommonSearchParams & {
      /** 告警ID */
      alertId?: string;
      /** 设备序列号 */
      deviceSn?: string;
      /** 告警类型 */
      alertType?: string;
      /** 严重程度 */
      severityLevel?: string;
      /** 是否自动处理 */
      autoProcessed?: boolean;
      /** 处理状态 */
      processStatus?: string;
      /** 开始时间 */
      startTime?: string;
      /** 结束时间 */
      endTime?: string;
      /** 客户ID */
      customerId?: string;
    };

    /** 告警处理日志列表 */
    type AlertProcessingLogList = Common.PaginatingQueryRecord<AlertProcessingLog>;

    /** 告警处理趋势数据 */
    type AlertProcessingTrend = {
      /** 时间点 */
      timestamp: string;
      /** 总告警数 */
      totalAlerts: number;
      /** 自动处理数 */
      autoProcessed: number;
      /** 人工处理数 */
      manualProcessed: number;
      /** 处理成功数 */
      successCount: number;
      /** 处理失败数 */
      failureCount: number;
      /** 平均处理时间 */
      avgProcessingTime: number;
    };

    /** 告警处理汇总数据 */
    type AlertProcessingSummary = {
      /** 今日告警总数 */
      todayTotal: number;
      /** 今日自动处理数 */
      todayAutoProcessed: number;
      /** 今日人工处理数 */
      todayManualProcessed: number;
      /** 今日待处理数 */
      todayPending: number;
      /** 自动处理平均时间(秒) */
      autoAvgTime: number;
      /** 人工处理平均时间(秒) */
      manualAvgTime: number;
      /** 与昨日对比增长率(%) */
      todayGrowthRate: number;
      /** 自动处理覆盖率(%) */
      autoProcessCoverageRate: number;
    };

    /** 告警处理详情 */
    type AlertProcessingDetail = Common.CommonRecord<{
      /** 告警基本信息 */
      alertInfo: {
        alertId: string;
        deviceSn: string;
        alertType: string;
        severityLevel: string;
        alertDesc: string;
        alertTimestamp: string;
      };
      /** 处理信息 */
      processInfo: {
        autoProcessed: boolean;
        processAction?: string;
        processStatus: string;
        processTime: string;
        processDuration: number;
        processResult?: string;
        errorMessage?: string;
      };
      /** 规则信息 */
      ruleInfo?: {
        ruleId: string;
        ruleName: string;
        autoProcessAction: string;
        delaySeconds: number;
      };
      /** 处理步骤 */
      processSteps: Array<{
        step: string;
        status: string;
        timestamp: string;
        message?: string;
      }>;
    }>;

    /** 告警处理性能分析 */
    type AlertProcessingPerformance = {
      /** 效率分析 */
      efficiency: {
        /** 自动处理平均时间 */
        autoAvgTime: number;
        /** 人工处理平均时间 */
        manualAvgTime: number;
        /** 效率提升百分比 */
        improvementRate: number;
        /** 时间节省(秒) */
        timeSaved: number;
      };
      /** 准确性分析 */
      accuracy: {
        /** 自动处理成功率 */
        autoSuccessRate: number;
        /** 误判率 */
        falsePositiveRate: number;
        /** 漏判率 */
        falseNegativeRate: number;
      };
      /** 覆盖率分析 */
      coverage: {
        /** 总覆盖率 */
        totalCoverageRate: number;
        /** 按严重程度覆盖率 */
        severityCoverageRates: Record<string, number>;
        /** 按告警类型覆盖率 */
        typeCoverageRates: Record<string, number>;
      };
    };
  }
}
