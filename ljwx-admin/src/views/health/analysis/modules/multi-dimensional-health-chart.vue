<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

interface HealthDimension {
  name: string;
  current: number;
  baseline: number;
  target: number;
  weight: number;
  status: 'excellent' | 'good' | 'average' | 'poor';
  trend: 'up' | 'down' | 'stable';
}

interface Props {
  data: HealthDimension[];
  title?: string;
  showComparison?: boolean;
  chartType?: 'radar' | 'polar' | 'multi';
}

const props = withDefaults(defineProps<Props>(), {
  title: '多维度健康分析',
  showComparison: true,
  chartType: 'multi'
});

const chartRef = ref<HTMLElement>();
const { domRef, updateOptions } = useEcharts(chartRef, {
  darkMode: false,
  size: { width: '100%', height: '100%' }
});

const healthColors = {
  excellent: '#52c41a',
  good: '#1890ff',
  average: '#faad14',
  poor: '#ff4d4f',
  current: '#667eea',
  baseline: '#52c41a',
  target: '#fa8c16',
  background: '#f5f7fa'
};

const processedData = computed(() => {
  if (!props.data || props.data.length === 0) return null;

  const indicators = props.data.map(item => ({
    name: item.name,
    max: 100,
    min: 0
  }));

  const currentData = props.data.map(item => item.current);
  const baselineData = props.data.map(item => item.baseline);
  const targetData = props.data.map(item => item.target);

  // 计算综合评分
  const weightedScore = props.data.reduce((sum, item) => sum + item.current * item.weight, 0);
  const averageScore = Math.round(currentData.reduce((sum, score) => sum + score, 0) / currentData.length);

  return {
    indicators,
    currentData,
    baselineData,
    targetData,
    weightedScore: Math.round(weightedScore),
    averageScore,
    categories: props.data.map(item => item.name)
  };
});

watch(
  () => props.data,
  newData => {
    if (newData && newData.length > 0) {
      updateChart();
    }
  },
  { immediate: true }
);

function updateChart() {
  if (!processedData.value) return;

  const { indicators, currentData, baselineData, targetData, weightedScore, averageScore, categories } = processedData.value;

  const option = {
    title: {
      text: props.title,
      left: 'center',
      top: '2%',
      textStyle: {
        color: '#1f2937',
        fontSize: 16,
        fontWeight: '600'
      }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151'
      },
      formatter(params: any) {
        if (params.componentType === 'radar') {
          const dimension = props.data[params.dataIndex];
          return `
            <div style="padding: 12px;">
              <div style="font-weight: 600; margin-bottom: 8px; color: #1f2937;">${dimension.name}</div>
              <div style="margin-bottom: 6px;">
                <span style="color: ${healthColors.current};">●</span> 
                <span style="margin-left: 6px;">当前值: ${dimension.current}</span>
              </div>
              <div style="margin-bottom: 6px;">
                <span style="color: ${healthColors.baseline};">●</span> 
                <span style="margin-left: 6px;">基线值: ${dimension.baseline}</span>
              </div>
              <div style="margin-bottom: 6px;">
                <span style="color: ${healthColors.target};">●</span> 
                <span style="margin-left: 6px;">目标值: ${dimension.target}</span>
              </div>
              <div style="margin-bottom: 6px;">
                <span style="color: #6b7280;">权重: ${(dimension.weight * 100).toFixed(1)}%</span>
              </div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 12px; padding: 2px 6px; border-radius: 4px; background: ${getStatusBgColor(dimension.status)}; color: ${getStatusColor(dimension.status)};">
                  ${getStatusText(dimension.status)}
                </span>
                <span style="color: ${getTrendColor(dimension.trend)};">
                  ${getTrendText(dimension.trend)}
                </span>
              </div>
            </div>
          `;
        }
        return '';
      }
    },
    legend: {
      data: ['当前状态', '基线水平', '目标值'],
      top: '8%',
      left: 'center',
      textStyle: {
        color: '#6b7280',
        fontSize: 12
      }
    },
    radar: {
      indicator: indicators,
      center: ['50%', '55%'],
      radius: '65%',
      startAngle: 90,
      splitNumber: 4,
      shape: 'polygon',
      name: {
        formatter(name: string) {
          return name;
        },
        textStyle: {
          color: '#374151',
          fontSize: 11,
          fontWeight: '500'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#e5e7eb',
          width: 1
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(103, 126, 234, 0.05)', 'rgba(103, 126, 234, 0.02)']
        }
      },
      axisLine: {
        lineStyle: {
          color: '#d1d5db'
        }
      }
    },
    series: [
      // 背景网格
      {
        type: 'radar',
        emphasis: {
          disabled: true
        },
        data: [
          {
            value: Array(indicators.length).fill(100),
            name: '满分参考',
            itemStyle: {
              color: 'transparent'
            },
            lineStyle: {
              color: 'transparent'
            },
            areaStyle: {
              color: healthColors.background,
              opacity: 0.3
            },
            symbol: 'none'
          }
        ]
      },
      // 目标值
      {
        type: 'radar',
        data: [
          {
            value: targetData,
            name: '目标值',
            itemStyle: {
              color: healthColors.target,
              borderColor: '#ffffff',
              borderWidth: 2
            },
            lineStyle: {
              color: healthColors.target,
              width: 2,
              type: 'dashed'
            },
            areaStyle: {
              color: healthColors.target,
              opacity: 0.1
            },
            symbol: 'diamond',
            symbolSize: 6
          }
        ]
      },
      // 基线水平
      {
        type: 'radar',
        data: [
          {
            value: baselineData,
            name: '基线水平',
            itemStyle: {
              color: healthColors.baseline,
              borderColor: '#ffffff',
              borderWidth: 2
            },
            lineStyle: {
              color: healthColors.baseline,
              width: 2,
              type: 'dotted'
            },
            areaStyle: {
              color: healthColors.baseline,
              opacity: 0.1
            },
            symbol: 'triangle',
            symbolSize: 6
          }
        ]
      },
      // 当前状态
      {
        type: 'radar',
        data: [
          {
            value: currentData,
            name: '当前状态',
            itemStyle: {
              color: healthColors.current,
              borderColor: '#ffffff',
              borderWidth: 3,
              shadowBlur: 8,
              shadowColor: `${healthColors.current}40`
            },
            lineStyle: {
              color: healthColors.current,
              width: 3
            },
            areaStyle: {
              color: {
                type: 'radial',
                x: 0.5,
                y: 0.5,
                r: 0.5,
                colorStops: [
                  { offset: 0, color: `${healthColors.current}40` },
                  { offset: 1, color: `${healthColors.current}10` }
                ]
              }
            },
            symbol: 'circle',
            symbolSize: 8
          }
        ]
      },
      // 中心综合评分展示
      {
        type: 'gauge',
        center: ['50%', '85%'],
        radius: '15%',
        min: 0,
        max: 100,
        startAngle: 210,
        endAngle: -30,
        splitNumber: 4,
        axisLine: {
          lineStyle: {
            width: 6,
            color: [
              [0.2, healthColors.poor],
              [0.4, healthColors.average],
              [0.6, healthColors.good],
              [1, healthColors.excellent]
            ]
          }
        },
        axisLabel: {
          show: false
        },
        axisTick: {
          show: false
        },
        splitLine: {
          show: false
        },
        pointer: {
          show: false
        },
        detail: {
          valueAnimation: true,
          formatter(value: number) {
            return `{value|${Math.round(value)}}{unit|分}`;
          },
          rich: {
            value: {
              fontSize: 18,
              fontWeight: 'bold',
              color: getScoreColor(weightedScore)
            },
            unit: {
              fontSize: 12,
              color: '#6b7280',
              padding: [0, 0, 0, 4]
            }
          },
          offsetCenter: [0, '20%']
        },
        data: [
          {
            value: weightedScore,
            name: '综合评分'
          }
        ]
      }
    ],
    graphic: [
      // 评分标签
      {
        type: 'text',
        left: '50%',
        top: '92%',
        style: {
          text: `综合评分: ${weightedScore} (权重) | 平均分: ${averageScore}`,
          fontSize: 12,
          fill: '#6b7280',
          textAlign: 'center'
        }
      }
    ],
    animation: true,
    animationDuration: 2000,
    animationEasing: 'elasticOut'
  };

  updateOptions(option);
}

function getStatusColor(status: string) {
  return healthColors[status as keyof typeof healthColors] || healthColors.average;
}

function getStatusBgColor(status: string) {
  const color = getStatusColor(status);
  return `${color}20`;
}

function getStatusText(status: string) {
  const statusMap = {
    excellent: '优秀',
    good: '良好',
    average: '一般',
    poor: '较差'
  };
  return statusMap[status as keyof typeof statusMap] || '未知';
}

function getTrendColor(trend: string) {
  switch (trend) {
    case 'up':
      return '#52c41a';
    case 'down':
      return '#ff4d4f';
    case 'stable':
      return '#6b7280';
    default:
      return '#6b7280';
  }
}

function getTrendText(trend: string) {
  switch (trend) {
    case 'up':
      return '↗ 上升';
    case 'down':
      return '↘ 下降';
    case 'stable':
      return '→ 稳定';
    default:
      return '- 未知';
  }
}

function getScoreColor(score: number) {
  if (score >= 80) return healthColors.excellent;
  if (score >= 60) return healthColors.good;
  if (score >= 40) return healthColors.average;
  return healthColors.poor;
}

onMounted(() => {
  if (props.data && props.data.length > 0) {
    updateChart();
  }
});
</script>

<template>
  <div ref="chartRef" class="h-full min-h-80 w-full" />
</template>

<style scoped>
/* Chart container styling */
</style>
