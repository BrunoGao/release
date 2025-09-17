<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

interface HealthDimension {
  name: string;
  score: number;
  status: 'excellent' | 'good' | 'average' | 'poor';
  trend: 'up' | 'down' | 'stable';
  weight: number;
}

interface ProfileInsight {
  type: 'positive' | 'warning' | 'suggestion';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
}

interface Props {
  healthDimensions: HealthDimension[];
  insights?: ProfileInsight[];
  completeness?: number;
  title?: string;
  chartType?: 'radar' | 'sunburst' | 'combined';
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康画像分析',
  chartType: 'combined',
  completeness: 85,
  insights: () => []
});

const chartRef = ref<HTMLElement>();
const { domRef, updateOptions } = useEcharts(chartRef, {
  darkMode: false,
  size: { width: '100%', height: '100%' }
});

const profileColors = {
  excellent: '#52c41a',
  good: '#1890ff',
  average: '#faad14',
  poor: '#ff4d4f',
  positive: '#52c41a',
  warning: '#faad14',
  suggestion: '#1890ff',
  background: '#f5f5f5'
};

const processedData = computed(() => {
  if (!props.healthDimensions || props.healthDimensions.length === 0) return null;

  const radarIndicators = props.healthDimensions.map(item => ({
    name: item.name,
    max: 100
  }));

  const radarData = props.healthDimensions.map(item => item.score);

  // 创建旭日图数据
  const sunburstData = [
    {
      name: '健康画像',
      children: props.healthDimensions.map(item => ({
        name: item.name,
        value: item.score,
        itemStyle: {
          color: getStatusColor(item.status)
        },
        children: [
          {
            name: `${item.name}-评分`,
            value: item.score,
            itemStyle: {
              color: getStatusColor(item.status, 0.8)
            }
          },
          {
            name: `${item.name}-权重`,
            value: item.weight * 100,
            itemStyle: {
              color: getStatusColor(item.status, 0.5)
            }
          }
        ]
      }))
    }
  ];

  return {
    radarIndicators,
    radarData,
    sunburstData,
    averageScore: Math.round(radarData.reduce((sum, score) => sum + score, 0) / radarData.length)
  };
});

watch(
  () => [props.healthDimensions, props.completeness],
  () => {
    updateChart();
  },
  { immediate: true, deep: true }
);

function updateChart() {
  if (!processedData.value) return;

  const { radarIndicators, radarData, sunburstData, averageScore } = processedData.value;

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
          const dimension = props.healthDimensions[params.dataIndex];
          return `
            <div style="padding: 8px;">
              <div style="font-weight: 600; margin-bottom: 8px;">${dimension.name}</div>
              <div style="margin-bottom: 4px;">评分: ${dimension.score}/100</div>
              <div style="margin-bottom: 4px;">状态: ${getStatusText(dimension.status)}</div>
              <div style="margin-bottom: 4px;">权重: ${(dimension.weight * 100).toFixed(1)}%</div>
              <div style="color: ${getTrendColor(dimension.trend)};">
                趋势: ${getTrendText(dimension.trend)}
              </div>
            </div>
          `;
        } else if (params.componentType === 'sunburst') {
          return `
            <div style="padding: 8px;">
              <div style="font-weight: 600; margin-bottom: 8px;">${params.name}</div>
              <div>数值: ${params.value}</div>
            </div>
          `;
        }
        return '';
      }
    },
    legend: {
      show: false
    },
    polar: {
      center: ['25%', '50%'],
      radius: '35%'
    },
    angleAxis: {
      type: 'category',
      data: radarIndicators.map(item => item.name),
      clockwise: true,
      axisLabel: {
        fontSize: 10,
        color: '#6b7280'
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: '#e5e7eb'
        }
      }
    },
    radiusAxis: {
      type: 'value',
      min: 0,
      max: 100,
      splitNumber: 4,
      axisLabel: {
        show: false
      },
      axisLine: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: '#f3f4f6',
          type: 'dashed'
        }
      }
    },
    series: [
      // 雷达图背景
      {
        type: 'bar',
        coordinateSystem: 'polar',
        data: Array(radarIndicators.length).fill(100),
        itemStyle: {
          color: profileColors.background,
          opacity: 0.3
        },
        barWidth: '90%',
        silent: true
      },
      // 健康维度评分
      {
        type: 'bar',
        coordinateSystem: 'polar',
        data: props.healthDimensions.map((item, index) => ({
          value: item.score,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: getStatusColor(item.status) },
                { offset: 1, color: getStatusColor(item.status, 0.6) }
              ]
            },
            borderRadius: [0, 0, 4, 4]
          }
        })),
        barWidth: '70%',
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        }
      },
      // 旭日图
      {
        type: 'sunburst',
        center: ['75%', '50%'],
        radius: ['15%', '35%'],
        data: sunburstData,
        itemStyle: {
          borderRadius: 4,
          borderWidth: 2,
          borderColor: '#ffffff'
        },
        emphasis: {
          focus: 'ancestor'
        },
        label: {
          fontSize: 10,
          fontWeight: 'bold'
        }
      },
      // 完整度环形图
      {
        type: 'pie',
        center: ['75%', '80%'],
        radius: ['8%', '12%'],
        startAngle: 90,
        data: [
          {
            value: props.completeness,
            name: '数据完整度',
            itemStyle: {
              color: getCompletenessColor(props.completeness)
            }
          },
          {
            value: 100 - props.completeness,
            name: '缺失',
            itemStyle: {
              color: '#f0f0f0'
            },
            label: {
              show: false
            }
          }
        ],
        label: {
          show: true,
          position: 'center',
          formatter: `${props.completeness}%`,
          fontSize: 12,
          fontWeight: 'bold',
          color: getCompletenessColor(props.completeness)
        }
      },
      // 中心综合评分
      {
        type: 'gauge',
        center: ['25%', '80%'],
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
              [0.2, profileColors.poor],
              [0.4, profileColors.average],
              [0.6, profileColors.good],
              [1, profileColors.excellent]
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
              fontSize: 16,
              fontWeight: 'bold',
              color: getScoreColor(averageScore)
            },
            unit: {
              fontSize: 10,
              color: '#6b7280',
              padding: [0, 0, 0, 2]
            }
          },
          offsetCenter: [0, '20%']
        },
        data: [
          {
            value: averageScore,
            name: '综合'
          }
        ]
      }
    ],
    graphic: [
      // 健康等级标签
      {
        type: 'text',
        left: '25%',
        top: '75%',
        style: {
          text: getHealthGrade(averageScore),
          fontSize: 12,
          fontWeight: 'bold',
          fill: getScoreColor(averageScore),
          textAlign: 'center'
        }
      },
      // 完整度标签
      {
        type: 'text',
        left: '75%',
        top: '92%',
        style: {
          text: '数据完整度',
          fontSize: 10,
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

function getStatusColor(status: string, opacity: number = 1) {
  const color = profileColors[status as keyof typeof profileColors] || profileColors.average;
  if (opacity < 1) {
    const hex = color.replace('#', '');
    const r = Number.parseInt(hex.substr(0, 2), 16);
    const g = Number.parseInt(hex.substr(2, 2), 16);
    const b = Number.parseInt(hex.substr(4, 2), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }
  return color;
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
  if (score >= 80) return profileColors.excellent;
  if (score >= 60) return profileColors.good;
  if (score >= 40) return profileColors.average;
  return profileColors.poor;
}

function getHealthGrade(score: number) {
  if (score >= 90) return 'A+';
  if (score >= 80) return 'A';
  if (score >= 70) return 'B';
  if (score >= 60) return 'C';
  return 'D';
}

function getCompletenessColor(completeness: number) {
  if (completeness >= 90) return '#52c41a';
  if (completeness >= 70) return '#1890ff';
  if (completeness >= 50) return '#faad14';
  return '#ff4d4f';
}

onMounted(() => {
  if (props.healthDimensions && props.healthDimensions.length > 0) {
    updateChart();
  }
});
</script>

<template>
  <div ref="chartRef" class="h-full min-h-96 w-full" />
</template>

<style scoped>
/* Chart container styling */
</style>
