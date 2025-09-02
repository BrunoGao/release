/**
 * 智能健康数据分析平台 - 全局变量
 */

// 全局图表变量
let globalCharts = null;

// 当前选择状态
let currentDept = '';
let currentUser = '';

// 图表实例集合
let charts = {
  healthScore: null,
  stats: null,
  trend: null,
  alert: null,
  messageStats: null
};

// 导出全局变量到window对象
window.currentDept = currentDept;
window.currentUser = currentUser;
window.charts = charts;

console.log('✅ globals.js 加载完成'); 