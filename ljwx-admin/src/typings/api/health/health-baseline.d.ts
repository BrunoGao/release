declare namespace Api {
    namespace Health {
        type HealthBaseline = Common.CommonRecord<{
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
            /** 基线日期 */
            baselineDate: string;
            /** 平均值 */
            meanValue: number;
            /** 标准差 */
            stdValue: number;
            /** 最小值 */
            minValue: number;
            /** 最大值 */
            maxValue: number;
            /** 样本数量 */
            sampleCount: number;
            /** 是否当前有效 */
            current: number;
            /** 基线生成时间 */
            baselineTime: string;
            /** 创建时间 */
            createTime: string;
        }>;

        /** HealthBaseline search params */
        type HealthBaselineSearchParams = CommonType.RecordNullable<Pick<Api.Health.HealthBaseline,
            'id' | 'customerId'
            > & Api.Common.CommonSearchParams
        >;

        /** HealthBaseline edit model */
        type HealthBaselineEdit = Pick<Api.Health.HealthBaseline, 'id' |
            'customerId'
            >;


        /** HealthBaseline list */
        type HealthBaselineList = Common.PaginatingQueryRecord<HealthBaseline>;

    }
}
