import type { App } from 'vue'
import * as echarts from 'echarts/core'

// 按需引入 ECharts 组件
import {
  BarChart,
  LineChart,
  PieChart,
  ScatterChart,
  RadarChart,
  MapChart,
  TreeChart,
  TreemapChart,
  GraphChart,
  GaugeChart,
  FunnelChart,
  ParallelChart,
  SankeyChart,
  BoxplotChart,
  CandlestickChart,
  EffectScatterChart,
  LinesChart,
  HeatmapChart,
  PictorialBarChart,
  ThemeRiverChart,
  SunburstChart,
  CustomChart
} from 'echarts/charts'

// 引入提示框，标题，直角坐标系，数据集，内置数据转换器组件
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  PolarComponent,
  AriaComponent,
  ParallelComponent,
  LegendComponent,
  RadarComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent,
  TimelineComponent,
  CalendarComponent,
  GraphicComponent,
  MarkPointComponent,
  MarkLineComponent,
  MarkAreaComponent,
  DatasetComponent,
  TransformComponent
} from 'echarts/components'

// 标签自动布局、全局过渡动画等特性
import { LabelLayout, UniversalTransition } from 'echarts/features'

// 引入 Canvas 渲染器
import { CanvasRenderer } from 'echarts/renderers'

// 注册必须的组件
echarts.use([
  // 图表类型
  BarChart,
  LineChart,
  PieChart,
  ScatterChart,
  RadarChart,
  MapChart,
  TreeChart,
  TreemapChart,
  GraphChart,
  GaugeChart,
  FunnelChart,
  ParallelChart,
  SankeyChart,
  BoxplotChart,
  CandlestickChart,
  EffectScatterChart,
  LinesChart,
  HeatmapChart,
  PictorialBarChart,
  ThemeRiverChart,
  SunburstChart,
  CustomChart,
  
  // 组件
  TitleComponent,
  TooltipComponent,
  GridComponent,
  PolarComponent,
  AriaComponent,
  ParallelComponent,
  LegendComponent,
  RadarComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent,
  TimelineComponent,
  CalendarComponent,
  GraphicComponent,
  MarkPointComponent,
  MarkLineComponent,
  MarkAreaComponent,
  DatasetComponent,
  TransformComponent,
  
  // 特性
  LabelLayout,
  UniversalTransition,
  
  // 渲染器
  CanvasRenderer
])

// 健康科技主题配置
const healthTechTheme = {
  color: [
    '#00ff9d', // 主色 - 健康绿
    '#00e4ff', // 科技蓝
    '#ff6b6b', // 警告红
    '#ffa726', // 警告橙
    '#66bb6a', // 成功绿
    '#42a5f5', // 信息蓝
    '#ab47bc', // 紫色
    '#26c6da', // 青色
    '#ffee58', // 黄色
    '#ff8a65'  // 深橙
  ],
  
  backgroundColor: 'transparent',
  
  textStyle: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif',
    color: '#ffffff',
    fontSize: 12
  },
  
  title: {
    textStyle: {
      fontWeight: '600',
      color: '#ffffff',
      fontSize: 16
    },
    subtextStyle: {
      color: 'rgba(255, 255, 255, 0.8)',
      fontSize: 12
    }
  },
  
  line: {
    itemStyle: {
      borderWidth: 2
    },
    lineStyle: {
      width: 2
    },
    symbolSize: 6,
    symbol: 'circle',
    smooth: true
  },
  
  radar: {
    itemStyle: {
      borderWidth: 2
    },
    lineStyle: {
      width: 2
    },
    symbolSize: 6,
    symbol: 'circle',
    smooth: true
  },
  
  bar: {
    itemStyle: {
      barBorderWidth: 0,
      barBorderColor: 'transparent'
    }
  },
  
  pie: {
    itemStyle: {
      borderWidth: 0,
      borderColor: 'transparent'
    }
  },
  
  scatter: {
    itemStyle: {
      borderWidth: 0,
      borderColor: 'transparent'
    }
  },
  
  boxplot: {
    itemStyle: {
      borderWidth: 0,
      borderColor: 'transparent'
    }
  },
  
  parallel: {
    itemStyle: {
      borderWidth: 0,
      borderColor: 'transparent'
    }
  },
  
  sankey: {
    itemStyle: {
      borderWidth: 0,
      borderColor: 'transparent'
    }
  },
  
  funnel: {
    itemStyle: {
      borderWidth: 0,
      borderColor: 'transparent'
    }
  },
  
  gauge: {
    itemStyle: {
      borderWidth: 0,
      borderColor: 'transparent'
    },
    axisLine: {
      lineStyle: {
        color: [
          [0.2, '#ff6b6b'],
          [0.4, '#ffa726'],
          [0.6, '#66bb6a'],
          [0.8, '#42a5f5'],
          [1, '#00ff9d']
        ],
        width: 8
      }
    },
    axisTick: {
      lineStyle: {
        color: '#ffffff',
        width: 1
      }
    },
    axisLabel: {
      color: '#ffffff',
      fontSize: 10
    },
    splitLine: {
      lineStyle: {
        color: '#ffffff',
        width: 2
      }
    },
    pointer: {
      itemStyle: {
        color: '#00e4ff'
      }
    },
    detail: {
      color: '#00e4ff',
      fontWeight: 'bold'
    }
  },
  
  candlestick: {
    itemStyle: {
      color: '#00ff9d',
      color0: '#ff6b6b',
      borderColor: '#00ff9d',
      borderColor0: '#ff6b6b'
    }
  },
  
  graph: {
    itemStyle: {
      borderWidth: 0,
      borderColor: 'transparent'
    },
    lineStyle: {
      width: 1,
      color: 'rgba(255, 255, 255, 0.3)'
    },
    symbolSize: 6,
    symbol: 'circle',
    smooth: true,
    color: [
      '#00ff9d',
      '#00e4ff',
      '#ff6b6b',
      '#ffa726',
      '#66bb6a'
    ],
    label: {
      color: '#ffffff'
    }
  },
  
  categoryAxis: {
    axisLine: {
      show: true,
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.2)'
      }
    },
    axisTick: {
      show: false,
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.2)'
      }
    },
    axisLabel: {
      show: true,
      color: 'rgba(255, 255, 255, 0.8)',
      fontSize: 11
    },
    splitLine: {
      show: false,
      lineStyle: {
        color: ['rgba(255, 255, 255, 0.1)']
      }
    },
    splitArea: {
      show: false,
      areaStyle: {
        color: ['rgba(255, 255, 255, 0.02)', 'rgba(255, 255, 255, 0.05)']
      }
    }
  },
  
  valueAxis: {
    axisLine: {
      show: false,
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.2)'
      }
    },
    axisTick: {
      show: false,
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.2)'
      }
    },
    axisLabel: {
      show: true,
      color: 'rgba(255, 255, 255, 0.8)',
      fontSize: 11
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: ['rgba(255, 255, 255, 0.1)']
      }
    },
    splitArea: {
      show: false,
      areaStyle: {
        color: ['rgba(255, 255, 255, 0.02)', 'rgba(255, 255, 255, 0.05)']
      }
    }
  },
  
  logAxis: {
    axisLine: {
      show: false,
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.2)'
      }
    },
    axisTick: {
      show: false,
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.2)'
      }
    },
    axisLabel: {
      show: true,
      color: 'rgba(255, 255, 255, 0.8)',
      fontSize: 11
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: ['rgba(255, 255, 255, 0.1)']
      }
    },
    splitArea: {
      show: false,
      areaStyle: {
        color: ['rgba(255, 255, 255, 0.02)', 'rgba(255, 255, 255, 0.05)']
      }
    }
  },
  
  timeAxis: {
    axisLine: {
      show: true,
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.2)'
      }
    },
    axisTick: {
      show: false,
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.2)'
      }
    },
    axisLabel: {
      show: true,
      color: 'rgba(255, 255, 255, 0.8)',
      fontSize: 11
    },
    splitLine: {
      show: false,
      lineStyle: {
        color: ['rgba(255, 255, 255, 0.1)']
      }
    },
    splitArea: {
      show: false,
      areaStyle: {
        color: ['rgba(255, 255, 255, 0.02)', 'rgba(255, 255, 255, 0.05)']
      }
    }
  },
  
  toolbox: {
    iconStyle: {
      borderColor: 'rgba(255, 255, 255, 0.8)'
    },
    emphasis: {
      iconStyle: {
        borderColor: '#00ff9d'
      }
    }
  },
  
  legend: {
    textStyle: {
      color: 'rgba(255, 255, 255, 0.8)',
      fontSize: 12
    }
  },
  
  tooltip: {
    axisPointer: {
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.6)',
        width: 1
      },
      crossStyle: {
        color: 'rgba(255, 255, 255, 0.6)',
        width: 1
      }
    },
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    borderColor: 'rgba(0, 255, 157, 0.3)',
    borderWidth: 1,
    textStyle: {
      color: '#ffffff',
      fontSize: 12
    }
  },
  
  timeline: {
    lineStyle: {
      color: 'rgba(255, 255, 255, 0.3)',
      width: 1
    },
    itemStyle: {
      color: '#00ff9d',
      borderWidth: 1
    },
    controlStyle: {
      color: '#00ff9d',
      borderColor: '#00ff9d',
      borderWidth: 1
    },
    checkpointStyle: {
      color: '#00e4ff',
      borderColor: '#00e4ff'
    },
    label: {
      color: 'rgba(255, 255, 255, 0.8)',
      fontSize: 11
    },
    emphasis: {
      itemStyle: {
        color: '#00e4ff'
      },
      controlStyle: {
        color: '#00e4ff',
        borderColor: '#00e4ff',
        borderWidth: 2
      },
      label: {
        color: '#ffffff'
      }
    }
  },
  
  visualMap: {
    color: ['#00ff9d', '#00e4ff', '#ff6b6b'],
    textStyle: {
      color: 'rgba(255, 255, 255, 0.8)',
      fontSize: 11
    }
  },
  
  dataZoom: {
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    dataBackgroundColor: 'rgba(255, 255, 255, 0.1)',
    fillerColor: 'rgba(0, 255, 157, 0.2)',
    handleColor: '#00ff9d',
    handleSize: '100%',
    textStyle: {
      color: 'rgba(255, 255, 255, 0.8)',
      fontSize: 11
    }
  },
  
  markPoint: {
    label: {
      color: '#ffffff'
    },
    emphasis: {
      label: {
        color: '#ffffff'
      }
    }
  }
}

// 注册主题
echarts.registerTheme('health-tech', healthTechTheme)

// 默认配置
const defaultOptions = {
  theme: 'health-tech',
  backgroundColor: 'transparent',
  animation: true,
  animationDuration: 1000,
  animationEasing: 'cubicOut',
  renderer: 'canvas' as const
}

// ECharts 插件安装函数
export function setupECharts(app: App) {
  // 全局配置
  app.config.globalProperties.$echarts = echarts
  
  // 提供全局实例
  app.provide('echarts', echarts)
  app.provide('echartsTheme', 'health-tech')
  app.provide('echartsDefaultOptions', defaultOptions)
  
  console.log('🎨 ECharts 插件初始化完成')
}

// 导出 ECharts 实例和配置
export { echarts, healthTechTheme, defaultOptions }

// 导出常用的图表配置生成器
export const chartConfigGenerators = {
  // 健康评分仪表盘
  healthGauge: (score: number, title = '健康评分') => ({
    title: {
      text: title,
      left: 'center',
      top: '20px',
      textStyle: {
        fontSize: 16,
        fontWeight: '600'
      }
    },
    series: [{
      type: 'gauge',
      min: 0,
      max: 100,
      radius: '80%',
      startAngle: 225,
      endAngle: -45,
      axisLine: {
        lineStyle: {
          width: 8,
          color: [
            [0.2, '#ff6b6b'],
            [0.4, '#ffa726'],
            [0.6, '#66bb6a'],
            [0.8, '#42a5f5'],
            [1, '#00ff9d']
          ]
        }
      },
      pointer: {
        itemStyle: {
          color: '#00e4ff'
        }
      },
      axisTick: {
        distance: -8,
        length: 4,
        lineStyle: {
          color: '#fff',
          width: 1
        }
      },
      splitLine: {
        distance: -15,
        length: 8,
        lineStyle: {
          color: '#fff',
          width: 2
        }
      },
      axisLabel: {
        color: '#fff',
        distance: 20,
        fontSize: 10
      },
      detail: {
        valueAnimation: true,
        formatter: '{value}%',
        color: '#00e4ff',
        fontSize: 24,
        fontWeight: 'bold',
        offsetCenter: [0, '70%']
      },
      data: [{
        value: score,
        name: '评分'
      }]
    }]
  }),
  
  // 趋势图
  trendLine: (data: any[], categories: string[], title = '趋势图') => ({
    title: {
      text: title,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    xAxis: {
      type: 'category',
      data: categories,
      boundaryGap: false
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      type: 'line',
      data: data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3
      },
      areaStyle: {
        opacity: 0.3
      }
    }]
  }),
  
  // 雷达图
  healthRadar: (data: any[], indicators: any[], title = '健康指标') => ({
    title: {
      text: title,
      left: 'center'
    },
    radar: {
      indicator: indicators,
      radius: '70%',
      axisName: {
        color: '#fff',
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.2)'
        }
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(0, 255, 157, 0.1)', 'rgba(0, 228, 255, 0.1)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.3)'
        }
      }
    },
    series: [{
      type: 'radar',
      data: data,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3
      },
      areaStyle: {
        opacity: 0.3
      }
    }]
  })
}

export default echarts