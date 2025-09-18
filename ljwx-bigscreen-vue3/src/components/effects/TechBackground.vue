<template>
  <div class="tech-background">
    <!-- 粒子效果层 -->
    <canvas 
      ref="particlesCanvas" 
      class="particles-layer"
      :width="canvasSize.width"
      :height="canvasSize.height"
    />
    
    <!-- 网格效果层 -->
    <div class="grid-layer">
      <div 
        v-for="i in gridLines.horizontal" 
        :key="`h-${i}`"
        class="grid-line horizontal"
        :style="{ top: `${(i * 100) / gridLines.horizontal}%` }"
      />
      <div 
        v-for="i in gridLines.vertical" 
        :key="`v-${i}`"
        class="grid-line vertical"
        :style="{ left: `${(i * 100) / gridLines.vertical}%` }"
      />
    </div>
    
    <!-- 脉冲波纹层 -->
    <div class="pulse-layer">
      <div 
        v-for="(pulse, index) in pulses" 
        :key="index"
        class="pulse-ring"
        :style="{
          left: pulse.x + 'px',
          top: pulse.y + 'px',
          '--delay': pulse.delay + 's'
        }"
      />
    </div>
    
    <!-- 数据流动层 -->
    <div class="data-flow-layer">
      <div 
        v-for="(flow, index) in dataFlows" 
        :key="index"
        class="data-flow"
        :style="{
          left: flow.x + 'px',
          top: flow.y + 'px',
          transform: `rotate(${flow.angle}deg)`,
          '--duration': flow.duration + 's'
        }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
  size: number
  color: string
}

interface Pulse {
  x: number
  y: number
  delay: number
}

interface DataFlow {
  x: number
  y: number
  angle: number
  duration: number
}

// 组件属性
interface Props {
  intensity?: number
  particleCount?: number
  enableGrid?: boolean
  enablePulse?: boolean
  enableDataFlow?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  intensity: 1,
  particleCount: 100,
  enableGrid: true,
  enablePulse: true,
  enableDataFlow: true
})

// 响应式数据
const particlesCanvas = ref<HTMLCanvasElement>()
const canvasSize = reactive({ width: 0, height: 0 })
const particles = ref<Particle[]>([])
const animationId = ref<number>()

// 网格配置
const gridLines = computed(() => ({
  horizontal: Math.floor(canvasSize.height / 50),
  vertical: Math.floor(canvasSize.width / 50)
}))

// 脉冲点配置
const pulses = computed<Pulse[]>(() => {
  if (!props.enablePulse) return []
  
  return Array.from({ length: 5 }, (_, i) => ({
    x: (canvasSize.width / 6) * (i + 1),
    y: canvasSize.height * (0.2 + Math.random() * 0.6),
    delay: i * 0.5
  }))
})

// 数据流配置
const dataFlows = computed<DataFlow[]>(() => {
  if (!props.enableDataFlow) return []
  
  return Array.from({ length: 8 }, (_, i) => ({
    x: Math.random() * canvasSize.width,
    y: Math.random() * canvasSize.height,
    angle: Math.random() * 360,
    duration: 2 + Math.random() * 3
  }))
})

// 初始化粒子
const initParticles = () => {
  particles.value = Array.from({ length: props.particleCount }, () => createParticle())
}

const createParticle = (): Particle => {
  return {
    x: Math.random() * canvasSize.width,
    y: Math.random() * canvasSize.height,
    vx: (Math.random() - 0.5) * 0.5,
    vy: (Math.random() - 0.5) * 0.5,
    life: Math.random() * 100,
    maxLife: 100 + Math.random() * 100,
    size: 1 + Math.random() * 2,
    color: Math.random() > 0.5 ? '#00ff9d' : '#00e4ff'
  }
}

// 更新粒子
const updateParticles = () => {
  particles.value.forEach(particle => {
    // 更新位置
    particle.x += particle.vx * props.intensity
    particle.y += particle.vy * props.intensity
    
    // 边界检测
    if (particle.x < 0 || particle.x > canvasSize.width) {
      particle.vx *= -1
    }
    if (particle.y < 0 || particle.y > canvasSize.height) {
      particle.vy *= -1
    }
    
    // 生命周期
    particle.life += 1
    if (particle.life >= particle.maxLife) {
      Object.assign(particle, createParticle())
    }
  })
}

// 渲染粒子
const renderParticles = () => {
  const canvas = particlesCanvas.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  // 清空画布
  ctx.clearRect(0, 0, canvasSize.width, canvasSize.height)
  
  // 绘制粒子
  particles.value.forEach(particle => {
    const alpha = 1 - (particle.life / particle.maxLife)
    
    ctx.beginPath()
    ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
    ctx.fillStyle = particle.color + Math.floor(alpha * 255).toString(16).padStart(2, '0')
    ctx.fill()
    
    // 添加发光效果
    ctx.shadowBlur = 10
    ctx.shadowColor = particle.color
    ctx.fill()
    ctx.shadowBlur = 0
  })
  
  // 绘制粒子连线
  drawConnections(ctx)
}

// 绘制粒子连接线
const drawConnections = (ctx: CanvasRenderingContext2D) => {
  const maxDistance = 100
  
  for (let i = 0; i < particles.value.length; i++) {
    for (let j = i + 1; j < particles.value.length; j++) {
      const p1 = particles.value[i]
      const p2 = particles.value[j]
      
      const distance = Math.sqrt(
        Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2)
      )
      
      if (distance < maxDistance) {
        const alpha = (1 - distance / maxDistance) * 0.3
        
        ctx.beginPath()
        ctx.moveTo(p1.x, p1.y)
        ctx.lineTo(p2.x, p2.y)
        ctx.strokeStyle = `rgba(0, 255, 157, ${alpha})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    }
  }
}

// 动画循环
const animate = () => {
  updateParticles()
  renderParticles()
  animationId.value = requestAnimationFrame(animate)
}

// 调整画布大小
const resizeCanvas = () => {
  canvasSize.width = window.innerWidth
  canvasSize.height = window.innerHeight
}

// 监听窗口大小变化
const { width, height } = useWindowSize()
watch([width, height], resizeCanvas, { immediate: true })

// 页面可见性控制
const { isVisible } = useDocumentVisibility()
watch(isVisible, (visible) => {
  if (visible) {
    animate()
  } else if (animationId.value) {
    cancelAnimationFrame(animationId.value)
  }
})

// 生命周期
onMounted(() => {
  initParticles()
  animate()
})

onUnmounted(() => {
  if (animationId.value) {
    cancelAnimationFrame(animationId.value)
  }
})
</script>

<style lang="scss" scoped>
.tech-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: -1;
  overflow: hidden;
}

.particles-layer {
  position: absolute;
  top: 0;
  left: 0;
  opacity: 0.6;
}

.grid-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.1;
  
  .grid-line {
    position: absolute;
    background: linear-gradient(90deg, 
      transparent 0%, 
      var(--primary-500) 50%, 
      transparent 100%
    );
    
    &.horizontal {
      width: 100%;
      height: 1px;
      animation: gridPulseH 4s ease-in-out infinite;
    }
    
    &.vertical {
      width: 1px;
      height: 100%;
      background: linear-gradient(0deg, 
        transparent 0%, 
        var(--tech-500) 50%, 
        transparent 100%
      );
      animation: gridPulseV 4s ease-in-out infinite;
    }
  }
}

.pulse-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  
  .pulse-ring {
    position: absolute;
    width: 4px;
    height: 4px;
    transform: translate(-50%, -50%);
    
    &::before,
    &::after {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      border: 2px solid var(--primary-500);
      border-radius: 50%;
      animation: pulseRing 3s ease-out infinite;
      animation-delay: var(--delay);
    }
    
    &::after {
      animation-delay: calc(var(--delay) + 1s);
    }
  }
}

.data-flow-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  
  .data-flow {
    position: absolute;
    width: 100px;
    height: 2px;
    background: linear-gradient(90deg,
      transparent 0%,
      var(--tech-500) 30%,
      var(--primary-500) 70%,
      transparent 100%
    );
    opacity: 0.7;
    animation: dataFlow var(--duration) ease-in-out infinite;
  }
}

// 动画定义
@keyframes gridPulseH {
  0%, 100% { opacity: 0.1; }
  50% { opacity: 0.3; }
}

@keyframes gridPulseV {
  0%, 100% { opacity: 0.1; }
  50% { opacity: 0.2; }
}

@keyframes pulseRing {
  0% {
    width: 4px;
    height: 4px;
    opacity: 1;
  }
  100% {
    width: 60px;
    height: 60px;
    opacity: 0;
  }
}

@keyframes dataFlow {
  0% {
    transform: translateX(-50px) rotate(var(--angle));
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateX(50px) rotate(var(--angle));
    opacity: 0;
  }
}

// 性能优化：在低端设备上减少效果
@media (max-width: 768px) {
  .grid-layer {
    display: none;
  }
  
  .data-flow-layer {
    .data-flow:nth-child(n+4) {
      display: none;
    }
  }
}

@media (prefers-reduced-motion: reduce) {
  .grid-layer,
  .pulse-layer,
  .data-flow-layer {
    display: none;
  }
}
</style>