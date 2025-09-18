import { defineStore } from 'pinia'
import type { DeviceInfo, DeviceData } from '@/types/health'

interface DeviceLocation {
  deviceId: string
  name: string
  type: string
  status: 'online' | 'offline' | 'error'
  location: {
    x: number
    y: number
    floor?: string
    building?: string
  }
  lastSeen: Date
  batteryLevel?: number
  signalStrength?: number
}

interface DeviceState {
  devices: DeviceInfo[]
  deviceLocations: DeviceLocation[]
  selectedDevice: string | null
  isLoading: boolean
  lastSyncTime: number
  connectionStatus: 'connected' | 'disconnected' | 'syncing'
}

export const useDeviceStore = defineStore('device', {
  state: (): DeviceState => ({
    devices: [],
    deviceLocations: [
      {
        deviceId: 'device_001',
        name: '温度传感器-01',
        type: 'temperature',
        status: 'online',
        location: { x: 100, y: 150, floor: '1F', building: 'A栋' },
        lastSeen: new Date(),
        batteryLevel: 85,
        signalStrength: 92
      },
      {
        deviceId: 'device_002',
        name: '血氧监测器-02',
        type: 'oxygen',
        status: 'online',
        location: { x: 250, y: 200, floor: '1F', building: 'A栋' },
        lastSeen: new Date(),
        batteryLevel: 78,
        signalStrength: 88
      },
      {
        deviceId: 'device_003',
        name: '心率监护仪-03',
        type: 'heartrate',
        status: 'offline',
        location: { x: 180, y: 320, floor: '2F', building: 'A栋' },
        lastSeen: new Date(Date.now() - 300000), // 5分钟前
        batteryLevel: 12,
        signalStrength: 0
      },
      {
        deviceId: 'device_004',
        name: '智能手环-04',
        type: 'wearable',
        status: 'online',
        location: { x: 320, y: 180, floor: '2F', building: 'B栋' },
        lastSeen: new Date(),
        batteryLevel: 95,
        signalStrength: 95
      }
    ],
    selectedDevice: null,
    isLoading: false,
    lastSyncTime: Date.now(),
    connectionStatus: 'connected'
  }),

  getters: {
    onlineDevices: (state) => state.deviceLocations.filter(d => d.status === 'online'),
    offlineDevices: (state) => state.deviceLocations.filter(d => d.status === 'offline'),
    errorDevices: (state) => state.deviceLocations.filter(d => d.status === 'error'),
    
    deviceStats: (state) => {
      const total = state.deviceLocations.length
      const online = state.deviceLocations.filter(d => d.status === 'online').length
      const offline = state.deviceLocations.filter(d => d.status === 'offline').length
      const error = state.deviceLocations.filter(d => d.status === 'error').length
      
      return {
        total,
        online,
        offline,
        error,
        onlinePercentage: total > 0 ? (online / total) * 100 : 0
      }
    },
    
    lowBatteryDevices: (state) => state.deviceLocations.filter(d => 
      d.batteryLevel !== undefined && d.batteryLevel < 20
    ),
    
    devicesByType: (state) => {
      const grouped = state.deviceLocations.reduce((acc, device) => {
        if (!acc[device.type]) {
          acc[device.type] = []
        }
        acc[device.type].push(device)
        return acc
      }, {} as Record<string, DeviceLocation[]>)
      
      return grouped
    },
    
    getDeviceById: (state) => (deviceId: string) => {
      return state.deviceLocations.find(d => d.deviceId === deviceId)
    }
  },

  actions: {
    async fetchDeviceStatus() {
      this.isLoading = true
      try {
        const response = await fetch('/api/devices/status')
        const data = await response.json()
        
        this.devices = data.devices || []
        this.deviceLocations = data.locations || this.deviceLocations
        this.lastSyncTime = Date.now()
        this.connectionStatus = 'connected'
      } catch (error) {
        console.error('Failed to fetch device status:', error)
        this.connectionStatus = 'disconnected'
        throw error
      } finally {
        this.isLoading = false
      }
    },
    
    async syncData() {
      this.connectionStatus = 'syncing'
      try {
        await this.fetchDeviceStatus()
        await this.fetchDeviceLocations()
      } finally {
        this.connectionStatus = 'connected'
      }
    },
    
    async fetchDeviceLocations() {
      try {
        const response = await fetch('/api/devices/locations')
        const data = await response.json()
        
        this.deviceLocations = data.map((location: any) => ({
          ...location,
          lastSeen: new Date(location.lastSeen)
        }))
      } catch (error) {
        console.error('Failed to fetch device locations:', error)
        throw error
      }
    },
    
    async updateDeviceLocation(deviceId: string, location: { x: number, y: number, floor?: string, building?: string }) {
      try {
        const response = await fetch(`/api/devices/${deviceId}/location`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(location)
        })
        
        if (response.ok) {
          const deviceIndex = this.deviceLocations.findIndex(d => d.deviceId === deviceId)
          if (deviceIndex !== -1) {
            this.deviceLocations[deviceIndex].location = location
          }
        }
      } catch (error) {
        console.error('Failed to update device location:', error)
        throw error
      }
    },
    
    async restartDevice(deviceId: string) {
      try {
        const response = await fetch(`/api/devices/${deviceId}/restart`, {
          method: 'POST'
        })
        
        if (response.ok) {
          // 更新设备状态
          const device = this.deviceLocations.find(d => d.deviceId === deviceId)
          if (device) {
            device.status = 'online'
            device.lastSeen = new Date()
          }
        }
      } catch (error) {
        console.error('Failed to restart device:', error)
        throw error
      }
    },
    
    async calibrateDevice(deviceId: string) {
      try {
        const response = await fetch(`/api/devices/${deviceId}/calibrate`, {
          method: 'POST'
        })
        
        return response.ok
      } catch (error) {
        console.error('Failed to calibrate device:', error)
        throw error
      }
    },
    
    selectDevice(deviceId: string) {
      this.selectedDevice = deviceId
    },
    
    clearSelection() {
      this.selectedDevice = null
    },
    
    // 模拟实时数据更新
    simulateRealtimeUpdates() {
      setInterval(() => {
        this.deviceLocations.forEach(device => {
          if (device.status === 'online') {
            // 模拟电池电量变化
            if (device.batteryLevel !== undefined) {
              device.batteryLevel = Math.max(0, device.batteryLevel - Math.random() * 0.1)
            }
            
            // 模拟信号强度变化
            if (device.signalStrength !== undefined) {
              device.signalStrength = Math.max(0, Math.min(100, 
                device.signalStrength + (Math.random() - 0.5) * 5
              ))
            }
            
            // 更新最后见到时间
            device.lastSeen = new Date()
          }
        })
      }, 5000) // 每5秒更新一次
    },
    
    // 获取设备历史数据
    async getDeviceHistory(deviceId: string, timeRange: string) {
      try {
        const response = await fetch(`/api/devices/${deviceId}/history?range=${timeRange}`)
        const data = await response.json()
        
        return data.map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp)
        }))
      } catch (error) {
        console.error('Failed to fetch device history:', error)
        throw error
      }
    },
    
    // 导出设备报告
    async exportDeviceReport(options: any = {}) {
      try {
        const response = await fetch('/api/devices/report/export', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(options)
        })
        
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `device-report-${new Date().toISOString().split('T')[0]}.pdf`
        a.click()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Failed to export device report:', error)
        throw error
      }
    }
  }
})