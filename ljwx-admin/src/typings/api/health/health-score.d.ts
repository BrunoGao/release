declare namespace Api {
    namespace Health {
        type HealthScore = Common.CommonRecord<{
            /** 设备序列号 */
            deviceSn: string;
            /** 用户ID */
            userId: number;
            /** 组织ID */
            orgId: string;
            /** 客户ID(租户ID) */
            customerId: number;
            /** 特征名称 */
            featureName: string;
            /** 当日平均值 */
            avgValue: number;
            /** Z分数 */
            zScore: number;
            /** 基础健康评分(0-100) */
            healthScore: number;
            /** 应用体征权重后评分 */
            weightedScore: number;
            /** 最终评分(体征权重×岗位权重) */
            finalScore: number;
            /** 健康体征权重 */
            featureWeight: number;
            /** 岗位权重 */
            positionWeight: number;
            /** 基线均值 */
            baselineMean: number;
            /** 基线标准差 */
            baselineStd: number;
            /** 当前值 */
            currentValue: number;
            /** 评分值(0-100) */
            scoreValue: number;
            /** 惩罚分值 */
            penaltyValue: number;
            /** 基线时间 */
            baselineTime: string;
            /** 评分日期 */
            scoreDate: string;
            /** 创建时间 */
            createTime: string;
        }>;

        /** HealthScore search params */
        type HealthScoreSearchParams = CommonType.RecordNullable<Pick<Api.Health.HealthScore,
            > & Api.Common.CommonSearchParams
        >;

        /** HealthScore edit model */
        type HealthScoreEdit = Pick<Api.Health.HealthScore, 'id' |
            >;


        /** HealthScore list */
        type HealthScoreList = Common.PaginatingQueryRecord<HealthScore>;

    }
}
