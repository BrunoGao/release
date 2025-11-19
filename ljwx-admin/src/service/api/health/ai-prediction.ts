import { request } from '@/service/request';

export namespace AiPrediction {
  // 健康预测结果
  export interface HealthPredictionResult {
    userId: number;
    generatedAt: string;
    modelVersion: string;
    healthTrend: string;
    riskFactors: string[];
    keyIndicators: string[];
    confidence: number;
    recommendations: string[];
    rawResponse: string;
  }

  // 健康建议结果
  export interface HealthAdviceResult {
    userId: number;
    generatedAt: string;
    modelVersion: string;
    lifestyleAdvice: {
      diet: string[];
      exercise: string[];
      sleep: string[];
    };
    riskPrevention: string[];
    shortTermPlan: {
      duration: string;
      goals: string[];
      actions: string[];
    };
    longTermGoals: string[];
    priority: string;
    rawResponse: string;
  }

  // AI服务健康状态
  export interface AiHealthStatus {
    healthy: boolean;
    availableModels: string[];
    checkTime: string;
  }

  // 批量预测结果
  export type BatchPredictionResult = Record<number, HealthPredictionResult>;
}

/**
 * AI健康预测服务
 */
export const aiPredictionApi = {
  /**
   * AI健康预测
   */
  predict: (userId: number, days: number = 7) => {
    return request.post<AiPrediction.HealthPredictionResult>('/t_health_prediction/ai/predict', null, {
      params: { userId, days }
    });
  },

  /**
   * AI健康建议
   */
  advice: (userId: number, healthIssues?: string[]) => {
    return request.post<AiPrediction.HealthAdviceResult>('/t_health_prediction/ai/advice', null, {
      params: { userId, healthIssues }
    });
  },

  /**
   * 获取可用AI模型列表
   */
  getAvailableModels: () => {
    return request.get<string[]>('/t_health_prediction/ai/models');
  },

  /**
   * 检查AI服务健康状态
   */
  checkHealth: () => {
    return request.get<AiPrediction.AiHealthStatus>('/t_health_prediction/ai/health');
  },

  /**
   * 批量AI健康预测
   */
  batchPredict: (userIds: number[], days: number = 7) => {
    return request.post<AiPrediction.BatchPredictionResult>('/t_health_prediction/ai/batch-predict', userIds, {
      params: { days }
    });
  }
};
