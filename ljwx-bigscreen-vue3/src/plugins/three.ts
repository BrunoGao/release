// Three.js 相关工具和配置
// Three.js utilities and configuration

// 注意: 这个文件提供 Three.js 的基础配置和工具函数
// 由于 Three.js 是一个大型库，我们使用轻量级的替代方案或按需导入

// 基础的 3D 数学工具函数
export class Vector3 {
  x: number
  y: number
  z: number

  constructor(x = 0, y = 0, z = 0) {
    this.x = x
    this.y = y
    this.z = z
  }

  set(x: number, y: number, z: number) {
    this.x = x
    this.y = y
    this.z = z
    return this
  }

  add(v: Vector3) {
    this.x += v.x
    this.y += v.y
    this.z += v.z
    return this
  }

  subtract(v: Vector3) {
    this.x -= v.x
    this.y -= v.y
    this.z -= v.z
    return this
  }

  multiply(scalar: number) {
    this.x *= scalar
    this.y *= scalar
    this.z *= scalar
    return this
  }

  length() {
    return Math.sqrt(this.x * this.x + this.y * this.y + this.z * this.z)
  }

  normalize() {
    const length = this.length()
    if (length > 0) {
      this.x /= length
      this.y /= length
      this.z /= length
    }
    return this
  }

  clone() {
    return new Vector3(this.x, this.y, this.z)
  }
}

// 简化的颜色类
export class Color {
  r: number
  g: number
  b: number

  constructor(r = 1, g = 1, b = 1) {
    this.r = r
    this.g = g
    this.b = b
  }

  setHex(hex: number) {
    this.r = ((hex >> 16) & 255) / 255
    this.g = ((hex >> 8) & 255) / 255
    this.b = (hex & 255) / 255
    return this
  }

  setHSL(h: number, s: number, l: number) {
    h = h - Math.floor(h)
    s = Math.max(0, Math.min(1, s))
    l = Math.max(0, Math.min(1, l))

    if (s === 0) {
      this.r = this.g = this.b = l
    } else {
      const hue2rgb = (p: number, q: number, t: number) => {
        if (t < 0) t += 1
        if (t > 1) t -= 1
        if (t < 1/6) return p + (q - p) * 6 * t
        if (t < 1/2) return q
        if (t < 2/3) return p + (q - p) * (2/3 - t) * 6
        return p
      }

      const q = l < 0.5 ? l * (1 + s) : l + s - l * s
      const p = 2 * l - q

      this.r = hue2rgb(p, q, h + 1/3)
      this.g = hue2rgb(p, q, h)
      this.b = hue2rgb(p, q, h - 1/3)
    }

    return this
  }

  toHex() {
    const r = Math.round(this.r * 255)
    const g = Math.round(this.g * 255)
    const b = Math.round(this.b * 255)
    return (r << 16) | (g << 8) | b
  }

  toString() {
    return `rgb(${Math.round(this.r * 255)}, ${Math.round(this.g * 255)}, ${Math.round(this.b * 255)})`
  }

  clone() {
    return new Color(this.r, this.g, this.b)
  }
}

// 数学工具函数
export const MathUtils = {
  // 度数转弧度
  degToRad: (degrees: number) => degrees * (Math.PI / 180),
  
  // 弧度转度数
  radToDeg: (radians: number) => radians * (180 / Math.PI),
  
  // 线性插值
  lerp: (a: number, b: number, t: number) => a + (b - a) * t,
  
  // 将值限制在范围内
  clamp: (value: number, min: number, max: number) => Math.max(min, Math.min(max, value)),
  
  // 映射值从一个范围到另一个范围
  mapRange: (value: number, inMin: number, inMax: number, outMin: number, outMax: number) => {
    return outMin + (value - inMin) * (outMax - outMin) / (inMax - inMin)
  },
  
  // 随机数生成
  randFloat: (min: number, max: number) => min + Math.random() * (max - min),
  randInt: (min: number, max: number) => Math.floor(min + Math.random() * (max - min + 1)),
  
  // 噪声函数（简化版）
  noise: (x: number, y = 0, z = 0) => {
    const hash = (n: number) => {
      n = Math.sin(n) * 43758.5453123
      return n - Math.floor(n)
    }
    return hash(x + y * 57 + z * 113)
  }
}

// 粒子系统基类
export class ParticleSystem {
  particles: Array<{
    position: Vector3
    velocity: Vector3
    life: number
    maxLife: number
    size: number
    color: Color
  }> = []

  constructor(public count: number = 100) {
    this.init()
  }

  init() {
    for (let i = 0; i < this.count; i++) {
      this.particles.push({
        position: new Vector3(
          MathUtils.randFloat(-10, 10),
          MathUtils.randFloat(-10, 10),
          MathUtils.randFloat(-10, 10)
        ),
        velocity: new Vector3(
          MathUtils.randFloat(-1, 1),
          MathUtils.randFloat(-1, 1),
          MathUtils.randFloat(-1, 1)
        ),
        life: MathUtils.randFloat(0.5, 2),
        maxLife: 2,
        size: MathUtils.randFloat(1, 3),
        color: new Color().setHSL(MathUtils.randFloat(0.4, 0.7), 0.8, 0.6)
      })
    }
  }

  update(deltaTime: number) {
    this.particles.forEach(particle => {
      // 更新位置
      particle.position.add(
        particle.velocity.clone().multiply(deltaTime)
      )
      
      // 更新生命值
      particle.life -= deltaTime
      
      // 重生粒子
      if (particle.life <= 0) {
        particle.position.set(
          MathUtils.randFloat(-10, 10),
          MathUtils.randFloat(-10, 10),
          MathUtils.randFloat(-10, 10)
        )
        particle.life = particle.maxLife
        particle.color.setHSL(MathUtils.randFloat(0.4, 0.7), 0.8, 0.6)
      }
    })
  }
}

// Canvas 基础渲染器
export class BasicRenderer {
  canvas: HTMLCanvasElement
  ctx: CanvasRenderingContext2D
  width: number
  height: number
  devicePixelRatio: number

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas
    this.ctx = canvas.getContext('2d')!
    this.devicePixelRatio = window.devicePixelRatio || 1
    this.resize()
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect()
    this.width = rect.width * this.devicePixelRatio
    this.height = rect.height * this.devicePixelRatio
    
    this.canvas.width = this.width
    this.canvas.height = this.height
    this.canvas.style.width = rect.width + 'px'
    this.canvas.style.height = rect.height + 'px'
    
    this.ctx.scale(this.devicePixelRatio, this.devicePixelRatio)
  }

  clear() {
    this.ctx.clearRect(0, 0, this.width, this.height)
  }

  drawParticle(position: Vector3, size: number, color: Color) {
    const x = (position.x + 10) * (this.width / this.devicePixelRatio) / 20
    const y = (position.y + 10) * (this.height / this.devicePixelRatio) / 20
    
    this.ctx.save()
    this.ctx.globalAlpha = 0.8
    this.ctx.fillStyle = color.toString()
    this.ctx.beginPath()
    this.ctx.arc(x, y, size, 0, Math.PI * 2)
    this.ctx.fill()
    this.ctx.restore()
  }

  drawLine(start: Vector3, end: Vector3, color: Color, width = 1) {
    const x1 = (start.x + 10) * (this.width / this.devicePixelRatio) / 20
    const y1 = (start.y + 10) * (this.height / this.devicePixelRatio) / 20
    const x2 = (end.x + 10) * (this.width / this.devicePixelRatio) / 20
    const y2 = (end.y + 10) * (this.height / this.devicePixelRatio) / 20
    
    this.ctx.save()
    this.ctx.strokeStyle = color.toString()
    this.ctx.lineWidth = width
    this.ctx.beginPath()
    this.ctx.moveTo(x1, y1)
    this.ctx.lineTo(x2, y2)
    this.ctx.stroke()
    this.ctx.restore()
  }
}

// 动画循环管理
export class AnimationLoop {
  private running = false
  private lastTime = 0
  private callbacks: Array<(deltaTime: number) => void> = []

  add(callback: (deltaTime: number) => void) {
    this.callbacks.push(callback)
  }

  remove(callback: (deltaTime: number) => void) {
    const index = this.callbacks.indexOf(callback)
    if (index > -1) {
      this.callbacks.splice(index, 1)
    }
  }

  start() {
    if (!this.running) {
      this.running = true
      this.lastTime = performance.now()
      this.loop()
    }
  }

  stop() {
    this.running = false
  }

  private loop = () => {
    if (!this.running) return
    
    const currentTime = performance.now()
    const deltaTime = (currentTime - this.lastTime) / 1000
    this.lastTime = currentTime
    
    this.callbacks.forEach(callback => callback(deltaTime))
    
    requestAnimationFrame(this.loop)
  }
}

// 预设的效果函数
export const Effects = {
  // 创建星空背景
  createStarField: (count = 200) => {
    return Array.from({ length: count }, () => ({
      x: MathUtils.randFloat(0, 1),
      y: MathUtils.randFloat(0, 1),
      size: MathUtils.randFloat(0.5, 2),
      brightness: MathUtils.randFloat(0.3, 1),
      twinkle: MathUtils.randFloat(0, Math.PI * 2)
    }))
  },

  // 创建数据流效果
  createDataStream: (canvas: HTMLCanvasElement) => {
    const ctx = canvas.getContext('2d')!
    const streams: Array<{
      x: number
      y: number
      speed: number
      length: number
      color: string
    }> = []

    for (let i = 0; i < 10; i++) {
      streams.push({
        x: MathUtils.randFloat(0, canvas.width),
        y: MathUtils.randFloat(-100, -20),
        speed: MathUtils.randFloat(2, 8),
        length: MathUtils.randFloat(20, 60),
        color: `hsl(${MathUtils.randFloat(180, 220)}, 80%, 60%)`
      })
    }

    return (deltaTime: number) => {
      ctx.save()
      ctx.globalCompositeOperation = 'screen'
      
      streams.forEach(stream => {
        stream.y += stream.speed
        
        if (stream.y > canvas.height + stream.length) {
          stream.y = -stream.length
          stream.x = MathUtils.randFloat(0, canvas.width)
        }
        
        const gradient = ctx.createLinearGradient(0, stream.y - stream.length, 0, stream.y)
        gradient.addColorStop(0, 'transparent')
        gradient.addColorStop(0.8, stream.color)
        gradient.addColorStop(1, 'transparent')
        
        ctx.fillStyle = gradient
        ctx.fillRect(stream.x, stream.y - stream.length, 2, stream.length)
      })
      
      ctx.restore()
    }
  },

  // 创建网格效果
  createGrid: (canvas: HTMLCanvasElement, gridSize = 50) => {
    const ctx = canvas.getContext('2d')!
    
    return () => {
      ctx.save()
      ctx.strokeStyle = 'rgba(0, 255, 157, 0.1)'
      ctx.lineWidth = 1
      ctx.beginPath()
      
      // 垂直线
      for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.moveTo(x, 0)
        ctx.lineTo(x, canvas.height)
      }
      
      // 水平线
      for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.moveTo(0, y)
        ctx.lineTo(canvas.width, y)
      }
      
      ctx.stroke()
      ctx.restore()
    }
  }
}

// 导出主要类和工具
export {
  Vector3 as THREE_Vector3,
  Color as THREE_Color,
  MathUtils as THREE_MathUtils
}