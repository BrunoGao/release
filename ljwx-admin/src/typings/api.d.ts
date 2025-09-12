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

  /**
   * namespace System
   *
   * backend api module: "system"
   */
  namespace System {
    /** 动态菜单扫描配置 */
    interface DynamicMenuScanDTO {
      /** 前端项目路径 */
      frontendPath: string;
      /** 扫描模式：auto(自动), manual(手动), incremental(增量) */
      scanMode?: string;
      /** 包含的路径模式列表 */
      includePatterns?: string[];
      /** 排除的路径模式列表 */
      excludePatterns?: string[];
      /** 是否扫描子目录 */
      recursive?: boolean;
      /** 是否自动创建菜单 */
      autoCreate?: boolean;
      /** 是否覆盖已存在的菜单 */
      overwriteExisting?: boolean;
      /** 默认父菜单ID */
      defaultParentId?: number;
      /** 租户ID */
      customerId?: number;
      /** 菜单名称生成规则：filename(文件名), path(路径), comment(注释) */
      nameGenerationRule?: string;
      /** 图标生成规则：auto(自动), default(默认), none(无) */
      iconGenerationRule?: string;
      /** 排序起始值 */
      sortStartValue?: number;
      /** 排序增量 */
      sortIncrement?: number;
      /** 最大扫描文件数 */
      maxFiles?: number;
      /** 是否启用缓存 */
      enableCache?: boolean;
      /** 扫描标签（用于标记本次扫描） */
      scanTag?: string;
    }

    /** 动态菜单配置DTO */
    interface DynamicMenuConfigDTO {
      /** 菜单ID（新增时为空） */
      id?: number;
      /** 父菜单ID */
      parentId?: number;
      /** 菜单类型：1-目录，2-菜单，3-按钮 */
      type: string;
      /** 菜单名称 */
      name: string;
      /** 菜单显示名称 */
      title?: string;
      /** 国际化键值 */
      i18nKey?: string;
      /** 路由名称 */
      routeName?: string;
      /** 路由路径 */
      routePath?: string;
      /** 组件路径 */
      component?: string;
      /** 菜单图标 */
      icon?: string;
      /** 图标类型：1-Iconify图标，2-本地图标 */
      iconType?: string;
      /** 菜单状态：1-启用，0-禁用 */
      status?: string;
      /** 是否隐藏菜单：Y-隐藏，N-显示 */
      hide?: string;
      /** 外链地址 */
      href?: string;
      /** iframe地址 */
      iframeUrl?: string;
      /** 排序值 */
      sort?: number;
      /** 菜单层级 */
      level?: number;
      /** 权限标识 */
      permission?: string;
      /** 租户ID */
      customerId?: number;
      /** 是否为系统菜单 */
      isSystem?: boolean;
      /** 是否可删除 */
      deletable?: boolean;
      /** 是否可编辑 */
      editable?: boolean;
      /** 菜单描述 */
      description?: string;
      /** 菜单标签 */
      tags?: string[];
      /** 扩展属性 */
      extra?: Record<string, any>;
      /** 子菜单 */
      children?: DynamicMenuConfigDTO[];
      /** 路由meta配置 */
      meta?: Record<string, any>;
      /** 是否需要认证 */
      requireAuth?: boolean;
      /** 是否缓存 */
      keepAlive?: boolean;
      /** 菜单布局 */
      layout?: string;
      /** 菜单主题 */
      theme?: string;
      /** 是否全屏显示 */
      fullscreen?: boolean;
      /** 页面加载动画 */
      transition?: string;
      /** 面包屑配置 */
      breadcrumb?: Record<string, any>;
      /** 是否固定在标签栏 */
      affix?: boolean;
      /** 标签页标题 */
      tabTitle?: string;
      /** 菜单激活规则 */
      activeMenu?: string;
      /** 创建来源：manual-手动，scan-扫描，import-导入 */
      source?: string;
      /** 源文件路径（扫描创建时记录） */
      sourceFile?: string;
      /** 最后扫描时间 */
      lastScanTime?: string;
      /** 菜单版本（用于同步） */
      version?: string;
    }

    /** 菜单批量更新DTO */
    interface MenuBatchUpdateDTO {
      /** 要更新的菜单ID列表 */
      menuIds: number[];
      /** 更新操作类型：update-更新属性，enable-启用，disable-禁用，delete-删除，move-移动 */
      operation?: string;
      /** 更新的属性字段 */
      updateFields?: Record<string, any>;
      /** 目标父菜单ID（移动操作时使用） */
      targetParentId?: number;
      /** 插入位置：before-之前，after-之后，first-最前，last-最后 */
      position?: string;
      /** 参考菜单ID（插入位置为before/after时使用） */
      referenceMenuId?: number;
      /** 是否递归操作子菜单 */
      recursive?: boolean;
      /** 操作原因/备注 */
      reason?: string;
      /** 租户ID */
      customerId?: number;
      /** 是否强制执行（忽略警告） */
      force?: boolean;
      /** 预览模式（不实际执行） */
      preview?: boolean;
      /** 操作标签（用于审计） */
      operationTag?: string;
    }

    /** 动态菜单VO */
    interface DynamicMenuVO {
      /** 菜单ID */
      id: number;
      /** 父菜单ID */
      parentId?: number;
      /** 菜单类型：1-目录，2-菜单，3-按钮 */
      type: string;
      /** 菜单名称 */
      name: string;
      /** 菜单显示名称 */
      title?: string;
      /** 国际化键值 */
      i18nKey?: string;
      /** 路由名称 */
      routeName?: string;
      /** 路由路径 */
      routePath?: string;
      /** 组件路径 */
      component?: string;
      /** 菜单图标 */
      icon?: string;
      /** 图标类型：1-Iconify图标，2-本地图标 */
      iconType?: string;
      /** 菜单状态：1-启用，0-禁用 */
      status: string;
      /** 是否隐藏菜单：Y-隐藏，N-显示 */
      hide?: string;
      /** 外链地址 */
      href?: string;
      /** iframe地址 */
      iframeUrl?: string;
      /** 排序值 */
      sort: number;
      /** 菜单层级 */
      level: number;
      /** 权限标识 */
      permission?: string;
      /** 租户ID */
      customerId?: number;
      /** 是否为系统菜单 */
      isSystem: boolean;
      /** 是否可删除 */
      deletable: boolean;
      /** 是否可编辑 */
      editable: boolean;
      /** 菜单描述 */
      description?: string;
      /** 菜单标签 */
      tags?: string[];
      /** 扩展属性 */
      extra?: Record<string, any>;
      /** 子菜单 */
      children?: DynamicMenuVO[];
      /** 路由meta配置 */
      meta?: Record<string, any>;
      /** 是否需要认证 */
      requireAuth?: boolean;
      /** 是否缓存 */
      keepAlive?: boolean;
      /** 菜单布局 */
      layout?: string;
      /** 菜单主题 */
      theme?: string;
      /** 是否全屏显示 */
      fullscreen?: boolean;
      /** 页面加载动画 */
      transition?: string;
      /** 面包屑配置 */
      breadcrumb?: Record<string, any>;
      /** 是否固定在标签栏 */
      affix?: boolean;
      /** 标签页标题 */
      tabTitle?: string;
      /** 菜单激活规则 */
      activeMenu?: string;
      /** 创建来源：manual-手动，scan-扫描，import-导入 */
      source?: string;
      /** 源文件路径（扫描创建时记录） */
      sourceFile?: string;
      /** 最后扫描时间 */
      lastScanTime?: string;
      /** 菜单版本（用于同步） */
      version?: string;
      /** 创建时间 */
      createTime?: string;
      /** 更新时间 */
      updateTime?: string;
      /** 使用统计 */
      usageStats?: Record<string, any>;
    }

    /** 菜单扫描结果VO */
    interface MenuScanResultVO {
      /** 扫描时间 */
      scanTime: string;
      /** 发现的文件列表 */
      foundFiles: string[];
      /** 变更的文件列表 */
      changedFiles: string[];
      /** 新发现的路由 */
      newRoutes: RouteInfo[];
      /** 扫描统计 */
      scanStats?: ScanStats;
      /** 扫描标签 */
      scanTag?: string;
      /** 扫描消息 */
      messages?: string[];
      /** 扫描警告 */
      warnings?: string[];
      /** 扫描错误 */
      errors?: string[];
    }

    /** 路由信息 */
    interface RouteInfo {
      /** 路由路径 */
      path: string;
      /** 路由名称 */
      name?: string;
      /** 页面标题 */
      title?: string;
      /** 组件路径 */
      component?: string;
      /** 文件路径 */
      filePath: string;
      /** 文件修改时间 */
      lastModified?: string;
      /** 文件大小 */
      fileSize?: number;
      /** 路由类型：page-页面，component-组件 */
      routeType?: string;
      /** 是否为新路由 */
      isNew?: boolean;
      /** 菜单层级 */
      level?: number;
      /** 建议的父菜单 */
      suggestedParent?: string;
      /** 建议的图标 */
      suggestedIcon?: string;
      /** 建议的排序值 */
      suggestedSort?: number;
      /** 解析的元数据 */
      metadata?: any;
    }

    /** 扫描统计信息 */
    interface ScanStats {
      /** 总文件数 */
      totalFiles: number;
      /** Vue文件数 */
      vueFiles?: number;
      /** TypeScript文件数 */
      tsFiles?: number;
      /** JavaScript文件数 */
      jsFiles?: number;
      /** 变更文件数 */
      changedFiles: number;
      /** 新路由数 */
      newRoutes: number;
      /** 已存在路由数 */
      existingRoutes?: number;
      /** 扫描耗时（毫秒） */
      scanDuration?: number;
      /** 处理的目录数 */
      processedDirectories?: number;
      /** 跳过的文件数 */
      skippedFiles?: number;
      /** 错误文件数 */
      errorFiles?: number;
    }
  }
}
