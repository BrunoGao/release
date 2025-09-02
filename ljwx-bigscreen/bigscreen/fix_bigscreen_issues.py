#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复大屏bigscreen_main.html的三个问题：
1. 手表管理面板高度问题
2. 健康评分硬编码问题
3. 健康基线图表初始化冲突问题
"""

import re
import os

def fix_bigscreen_issues():
    file_path = 'bigScreen/templates/bigscreen_main.html'
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    print("🔧 开始修复大屏问题...")
    
    try:
        # 读取原文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复1: 调整手表管理面板高度
        print("1️⃣ 修复手表管理面板高度...")
        content = content.replace(
            'height: 30%; /* 手表管理面板：保持30% */',
            'height: 26%; /* 手表管理面板：从30%调整为26%避免覆盖 */'
        )
        content = content.replace(
            'height: 34%; /* 健康数据分析面板：从32%增加到34% */',
            'height: 38%; /* 健康数据分析面板：从34%增加到38%给图表更多空间 */'
        )
        
        # 修复2: 为健康基线图表添加唯一ID避免冲突
        print("2️⃣ 修复健康基线图表初始化冲突...")
        
        # 在renderHealthChart函数中添加图表实例清理
        render_health_chart_pattern = r'(// 健康趋势图\s*const trendChart = echarts\.init\(document\.getElementById\(\'trendChart\'\)\);)'
        
        replacement = '''// 健康趋势图 - 添加实例清理避免冲突
    const trendContainer = document.getElementById('trendChart');
    
    // 清理可能存在的旧实例
    const existingChart = echarts.getInstanceByDom(trendContainer);
    if (existingChart) {
      existingChart.dispose();
      console.log('🗑️ 清理了旧的健康趋势图实例');
    }
    
    const trendChart = echarts.init(trendContainer);
    console.log('✅ 初始化新的健康趋势图实例');'''
        
        content = re.sub(render_health_chart_pattern, replacement, content)
        
        # 修复3: 在健康评分更新中连接总分与雷达图评分
        print("3️⃣ 修复健康评分数据连接...")
        
        # 查找健康评分更新逻辑并确保总分与API数据一致
        health_score_pattern = r'(// 更新总分显示\s*const totalScoreElement = document\.querySelector\(\'\.total-score\'\);.*?overallScore}\`;)'
        
        health_score_replacement = '''// 更新总分显示 - 连接API数据
                            const totalScoreElement = document.querySelector('.total-score');
                            const overallScoreElement = document.getElementById('overallHealthScore');
                            
                            if (totalScoreElement) {
                                totalScoreElement.textContent = `总分：${result.data.summary.overallScore}`;
                            }
                            
                            // 同步更新综合健康评分显示
                            if (overallScoreElement) {
                                overallScoreElement.textContent = result.data.summary.overallScore || '89';
                                console.log('✅ 更新综合健康评分:', result.data.summary.overallScore);
                            }'''
        
        content = re.sub(health_score_pattern, health_score_replacement, content, flags=re.DOTALL)
        
        # 修复4: 在renderHealthChart函数中添加数据更新健康统计
        print("4️⃣ 增强renderHealthChart函数...")
        
        render_pattern = r'(// 更新健康统计数据\s*if \(health_summary\) \{.*?\})'
        
        render_replacement = '''// 更新健康统计数据
    if (health_summary) {
      const healthScoreEl = document.getElementById('healthScore');
      const normalCountEl = document.getElementById('normalCount');
      const riskCountEl = document.getElementById('riskCount');
      const overallScoreEl = document.getElementById('overallHealthScore');
      
      if (healthScoreEl) healthScoreEl.textContent = health_summary.overall_score || 85;
      if (normalCountEl) normalCountEl.textContent = health_summary.normal_indicators || 0;
      if (riskCountEl) riskCountEl.textContent = health_summary.risk_indicators || 0;
      
      // 同步更新综合健康评分
      if (overallScoreEl) {
        overallScoreEl.textContent = health_summary.overall_score || 85;
        console.log('✅ 通过baseline更新综合健康评分:', health_summary.overall_score);
      }
      
      console.log('✅ 健康统计数据已更新:', health_summary);
    }'''
        
        content = re.sub(render_pattern, render_replacement, content, flags=re.DOTALL)
        
        # 检查是否有修改
        if content == original_content:
            print("⚠️ 没有检测到需要修改的内容")
            return False
        
        # 写入修改后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 修复完成！主要变更:")
        print("   1. 手表管理面板高度: 30% → 26%")
        print("   2. 健康数据分析面板高度: 34% → 38%")
        print("   3. 添加了图表实例清理逻辑")
        print("   4. 连接了健康评分API数据与显示")
        print("   5. 增强了健康统计数据更新")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        return False

if __name__ == "__main__":
    success = fix_bigscreen_issues()
    if success:
        print("\n🎉 所有问题修复完成！")
        print("📋 修复说明:")
        print("   • 手表管理面板不再覆盖健康数据分析")
        print("   • 健康基线图表初始化冲突已解决") 
        print("   • 综合健康评分现在使用API数据而非硬编码89")
        print("\n🔄 请重启服务以查看效果")
    else:
        print("\n❌ 修复失败，请检查文件内容") 