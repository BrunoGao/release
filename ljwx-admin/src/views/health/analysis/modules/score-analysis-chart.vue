<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

interface ScoreData {
  category: string;
  score: number;
  weight: number;
  maxScore: number;
  trend: 'up' | 'down' | 'stable';
  level: 'excellent' | 'good' | 'average' | 'poor';
}

interface Props {
  data: ScoreData[];
  overallScore?: number;
  title?: string;
  chartType?: 'radar' | 'gauge' | 'combined';
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康评分分析',
  chartType: 'combined',
  overallScore: 75
});

const chartRef = ref<HTMLElement>();
const { domRef, updateOptions } = useEcharts(chartRef, {
  darkMode: false,
  size: { width: '100%', height: '100%' }
});

const scoreColors = {
  excellent: '#52c41a',
  good: '#1890ff',
  average: '#faad14',
  poor: '#ff4d4f',
  background: '#f0f2f5'
};

const processedData = computed(() => {
  if (!props.data || props.data.length === 0) return null;

  return {
    categories: props.data.map(item => item.category),
    scores: props.data.map(item => item.score),
    weights: props.data.map(item => item.weight),
    levels: props.data.map(item => item.level),
    radarIndicators: props.data.map(item => ({
      name: item.category,
      max: item.maxScore || 100
    })),
    radarData: props.data.map(item => item.score)
  };
});

watch(
  () => [props.data, props.overallScore],
  () => {
    updateChart();
  },
  { immediate: true, deep: true }
);

function updateChart() {
  if (!processedData.value) return;

  const { categories, scores, weights, levels, radarIndicators, radarData } = processedData.value;

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
        if (params.componentType === 'series') {
          const dataItem = props.data[params.dataIndex];
          if (dataItem) {
            return `
              <div style="padding: 8px;">
                <div style="font-weight: 600; margin-bottom: 8px;">${dataItem.category}</div>
                <div style="margin-bottom: 4px;">评分: ${dataItem.score}/${dataItem.maxScore}</div>
                <div style="margin-bottom: 4px;">权重: ${(dataItem.weight * 100).toFixed(1)}%</div>
                <div style="margin-bottom: 4px;">等级: ${getLevelText(dataItem.level)}</div>
                <div style="color: ${getTrendColor(dataItem.trend)};">
                  趋势: ${getTrendText(dataItem.trend)}
                </div>
              </div>
            `;
          }
        }
        return '';
      }
    },
    legend: {
      show: false
    },
    polar: {},
    angleAxis: {
      type: 'category',
      data: categories,
      clockwise: true,
      axisLabel: {
        fontSize: 11,
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
        data: Array(categories.length).fill(100),
        itemStyle: {
          color: scoreColors.background,
          opacity: 0.3
        },
        barWidth: '80%',
        silent: true
      },
      // 评分柱状图
      {
        type: 'bar',
        coordinateSystem: 'polar',
        data: scores.map((score, index) => ({
          value: score,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: getLevelColor(levels[index]) },
                { offset: 1, color: `${getLevelColor(levels[index])}60` }
              ]
            },
            borderRadius: [0, 0, 4, 4]
          }
        })),
        barWidth: '60%',
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.2)'
          }
        }
      },
      // 中心总分显示
      {
        type: 'gauge',
        center: ['50%', '60%'],
        radius: '25%',
        min: 0,
        max: 100,
        startAngle: 210,
        endAngle: -30,
        splitNumber: 4,
        axisLine: {
          lineStyle: {
            width: 8,
            color: [
              [0.2, '#ff4d4f'],
              [0.4, '#faad14'],
              [0.6, '#1890ff'],
              [1, '#52c41a']
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
              fontSize: 24,
              fontWeight: 'bold',
              color: getScoreColor(props.overallScore || 75)
            },
            unit: {
              fontSize: 14,
              color: '#6b7280',
              padding: [0, 0, 0, 4]
            }
          },
          offsetCenter: [0, '10%']
        },
        data: [
          {
            value: props.overallScore || 75,
            name: '综合评分'
          }
        ]
      }
    ],
    animation: true,
    animationDuration: 2000,
    animationEasing: 'elasticOut'
  };

  updateOptions(option);
}

function getLevelColor(level: string) {
  return scoreColors[level as keyof typeof scoreColors] || scoreColors.average;
}

function getLevelText(level: string) {
  const levelMap = {
    excellent: '优秀',
    good: '良好',
    average: '一般',
    poor: '较差'
  };
  return levelMap[level as keyof typeof levelMap] || '未知';
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
  if (score >= 80) return scoreColors.excellent;
  if (score >= 60) return scoreColors.good;
  if (score >= 40) return scoreColors.average;
  return scoreColors.poor;
}

onMounted(() => {
  if (props.data && props.data.length > 0) {
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
