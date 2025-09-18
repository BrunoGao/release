<template>
  <div class="mini-trend-chart" ref="chartContainer">
    <canvas 
      ref="canvasRef" 
      :width="canvasWidth" 
      :height="canvasHeight"
      @mousemove="handleMouseMove"
      @mouseleave="handleMouseLeave"
    />
    
    <!-- 数据点提示 -->
    <div 
      v-if="tooltip.show" 
      class="chart-tooltip"
      :style="tooltipStyle"
    >
      <div class="tooltip-time">{{ tooltip.time }}</div>
      <div class="tooltip-value" v-if="!isDual">
        {{ tooltip.value }}
      </div>
      <div class="tooltip-values" v-else>
        <div class="tooltip-value primary">{{ tooltip.primaryValue }}</div>
        <div class="tooltip-value secondary">{{ tooltip.secondaryValue }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface DataPoint {
  timestamp: Date
  value: number
  secondaryValue?: number
}

interface Props {
  data: DataPoint[]
  color?: string
  secondaryColor?: string
  height?: number
  isDual?: boolean
  showGrid?: boolean
  animated?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  color: '#00ff9d',
  secondaryColor: '#00e4ff',
  height: 60,
  isDual: false,
  showGrid: true,
  animated: true
})

// 模板引用
const chartContainer = ref<HTMLElement>()
const canvasRef = ref<HTMLCanvasElement>()

// 响应式数据
const canvasWidth = ref(300)
const canvasHeight = ref(props.height)
const tooltip = reactive({
  show: false,
  x: 0,
  y: 0,
  time: '',
  value: '',
  primaryValue: '',
  secondaryValue: ''
})

// 计算属性
const tooltipStyle = computed(() => ({
  left: `${tooltip.x}px`,
  top: `${tooltip.y}px`,
  transform: 'translate(-50%, -100%)'
}))

// 绘制图表
const drawChart = () => {
  const canvas = canvasRef.value
  if (!canvas || !props.data.length) return
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const { width, height } = canvas
  const padding = 10
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2
  
  // 清除画布
  ctx.clearRect(0, 0, width, height)
  
  // 计算数据范围
  const values = props.data.flatMap(d => [d.value, d.secondaryValue].filter(v => v !== undefined))
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const valueRange = maxValue - minValue || 1
  
  // 绘制网格（可选）
  if (props.showGrid) {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
    ctx.lineWidth = 0.5
    
    // 水平网格线
    for (let i = 0; i <= 4; i++) {
      const y = padding + (chartHeight / 4) * i
      ctx.beginPath()
      ctx.moveTo(padding, y)
      ctx.lineTo(width - padding, y)
      ctx.stroke()
    }
    
    // 垂直网格线
    const timeStep = Math.ceil(props.data.length / 6)
    for (let i = 0; i < props.data.length; i += timeStep) {
      const x = padding + (chartWidth / (props.data.length - 1)) * i
      ctx.beginPath()
      ctx.moveTo(x, padding)
      ctx.lineTo(x, height - padding)
      ctx.stroke()
    }
  }
  
  // 绘制主要数据线
  drawLine(ctx, props.data.map(d => d.value), props.color, padding, chartWidth, chartHeight, minValue, valueRange)
  
  // 绘制次要数据线（双线模式）
  if (props.isDual && props.data.some(d => d.secondaryValue !== undefined)) {
    const secondaryValues = props.data.map(d => d.secondaryValue || d.value)
    drawLine(ctx, secondaryValues, props.secondaryColor, padding, chartWidth, chartHeight, minValue, valueRange)
  }
  
  // 绘制数据点
  drawDataPoints(ctx, props.data.map(d => d.value), props.color, padding, chartWidth, chartHeight, minValue, valueRange)
  
  if (props.isDual) {
    const secondaryValues = props.data.map(d => d.secondaryValue || d.value)
    drawDataPoints(ctx, secondaryValues, props.secondaryColor, padding, chartWidth, chartHeight, minValue, valueRange)
  }
}

// 绘制线条
const drawLine = (
  ctx: CanvasRenderingContext2D,
  values: number[],
  color: string,
  padding: number,
  chartWidth: number,
  chartHeight: number,
  minValue: number,
  valueRange: number
) => {
  if (values.length < 2) return
  
  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  
  // 创建渐变填充
  const gradient = ctx.createLinearGradient(0, padding, 0, padding + chartHeight)
  gradient.addColorStop(0, color + '40')
  gradient.addColorStop(1, color + '10')
  
  ctx.beginPath()
  
  values.forEach((value, index) => {
    const x = padding + (chartWidth / (values.length - 1)) * index
    const y = padding + chartHeight - ((value - minValue) / valueRange) * chartHeight
    
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  
  ctx.stroke()
  
  // 填充区域
  if (values.length > 1) {
    ctx.lineTo(padding + chartWidth, padding + chartHeight)
    ctx.lineTo(padding, padding + chartHeight)
    ctx.closePath()
    ctx.fillStyle = gradient
    ctx.fill()
  }
}

// 绘制数据点
const drawDataPoints = (
  ctx: CanvasRenderingContext2D,
  values: number[],
  color: string,
  padding: number,
  chartWidth: number,
  chartHeight: number,
  minValue: number,
  valueRange: number
) => {
  ctx.fillStyle = color
  
  values.forEach((value, index) => {
    const x = padding + (chartWidth / (values.length - 1)) * index
    const y = padding + chartHeight - ((value - minValue) / valueRange) * chartHeight
    
    // 绘制数据点
    ctx.beginPath()
    ctx.arc(x, y, 2, 0, Math.PI * 2)
    ctx.fill()
    
    // 添加发光效果
    ctx.shadowBlur = 6
    ctx.shadowColor = color
    ctx.fill()
    ctx.shadowBlur = 0
  })
}

// 处理鼠标移动
const handleMouseMove = (event: MouseEvent) => {
  const canvas = canvasRef.value
  if (!canvas || !props.data.length) return
  
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const padding = 10
  const chartWidth = canvas.width - padding * 2
  
  // 计算最近的数据点
  const dataIndex = Math.round(((x - padding) / chartWidth) * (props.data.length - 1))
  const clampedIndex = Math.max(0, Math.min(dataIndex, props.data.length - 1))
  
  if (clampedIndex >= 0 && clampedIndex < props.data.length) {
    const dataPoint = props.data[clampedIndex]
    
    tooltip.show = true
    tooltip.x = x
    tooltip.y = 0
    tooltip.time = dataPoint.timestamp.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
    
    if (props.isDual) {
      tooltip.primaryValue = dataPoint.value.toFixed(1)
      tooltip.secondaryValue = (dataPoint.secondaryValue || dataPoint.value).toFixed(1)
    } else {
      tooltip.value = dataPoint.value.toFixed(1)
    }
  }
}

// 处理鼠标离开
const handleMouseLeave = () => {
  tooltip.show = false
}

// 调整画布大小
const resizeCanvas = () => {
  if (!chartContainer.value || !canvasRef.value) return
  
  const containerRect = chartContainer.value.getBoundingClientRect()
  canvasWidth.value = containerRect.width
  canvasHeight.value = props.height
  
  // 设置高DPI支持
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  const devicePixelRatio = window.devicePixelRatio || 1
  
  canvas.width = canvasWidth.value * devicePixelRatio
  canvas.height = canvasHeight.value * devicePixelRatio
  canvas.style.width = canvasWidth.value + 'px'
  canvas.style.height = canvasHeight.value + 'px'
  
  if (ctx) {
    ctx.scale(devicePixelRatio, devicePixelRatio)
  }
  
  nextTick(() => {
    drawChart()
  })
}

// 动画绘制
const animateChart = () => {
  if (!props.animated) {
    drawChart()
    return
  }
  
  let animationFrame = 0
  const totalFrames = 30
  
  const animate = () => {
    animationFrame++
    const progress = animationFrame / totalFrames
    
    // 这里可以添加动画逻辑
    // 目前简化为直接绘制
    drawChart()
    
    if (animationFrame < totalFrames) {
      requestAnimationFrame(animate)
    }
  }
  
  requestAnimationFrame(animate)
}

// 监听数据变化
watch(() => props.data, () => {
  nextTick(() => {
    animateChart()
  })
}, { deep: true })

watch(() => props.height, () => {
  resizeCanvas()
})

// 生命周期
onMounted(() => {
  resizeCanvas()
  
  // 监听窗口大小变化
  const resizeObserver = new ResizeObserver(() => {
    resizeCanvas()
  })
  
  if (chartContainer.value) {
    resizeObserver.observe(chartContainer.value)
  }
  
  onUnmounted(() => {
    resizeObserver.disconnect()
  })
})
</script>

<style lang="scss" scoped>
.mini-trend-chart {
  width: 100%;
  height: 100%;
  position: relative;
  cursor: crosshair;
  
  canvas {
    width: 100%;
    height: 100%;
    display: block;
  }
}

.chart-tooltip {
  position: absolute;
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  padding: var(--spacing-xs);
  font-size: var(--font-xs);
  color: var(--text-primary);
  pointer-events: none;
  z-index: 1000;
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(10px);
  
  .tooltip-time {
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
  }
  
  .tooltip-value {
    font-family: var(--font-tech);
    font-weight: 600;
    
    &.primary {
      color: var(--primary-500);
    }
    
    &.secondary {
      color: var(--tech-500);
    }
  }
  
  .tooltip-values {
    display: flex;
    gap: var(--spacing-sm);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .chart-tooltip {
    font-size: var(--font-xs);
    padding: var(--spacing-xs);
  }
}

// 可访问性
@media (prefers-reduced-motion: reduce) {
  .mini-trend-chart {
    canvas {
      transition: none;
    }
  }
}
</style>