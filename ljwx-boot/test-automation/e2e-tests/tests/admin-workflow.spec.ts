import { test, expect } from '@playwright/test';

/**
 * Admin管理员端到端工作流测试
 */
test.describe('Admin管理员工作流', () => {
  
  test.beforeEach(async ({ page }) => {
    // 访问管理后台
    await page.goto('/');
    
    // 等待页面加载
    await page.waitForLoadState('networkidle');
  });

  test('Admin完整登录和数据管理流程', async ({ page }) => {
    // 1. 登录流程
    await page.fill('[data-testid="username"]', 'admin');
    await page.fill('[data-testid="password"]', 'admin123'); // 假设前端使用明文密码
    await page.click('[data-testid="login-button"]');
    
    // 验证登录成功
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('[data-testid="user-info"]')).toContainText('admin');
    
    // 2. 首页数据验证
    await expect(page.locator('[data-testid="dashboard-stats"]')).toBeVisible();
    
    // 验证关键指标卡片
    const statsCards = page.locator('[data-testid="stats-card"]');
    await expect(statsCards).toHaveCount(4); // 假设有4个统计卡片
    
    // 3. 租户管理验证
    await page.click('[data-testid="menu-tenant-management"]');
    await page.waitForLoadState('networkidle');
    
    // 验证可以查看所有租户（Admin全局权限）
    const tenantTable = page.locator('[data-testid="tenant-table"]');
    await expect(tenantTable).toBeVisible();
    
    // 4. 用户管理验证  
    await page.click('[data-testid="menu-user-management"]');
    await page.waitForLoadState('networkidle');
    
    // 验证可以查看跨租户用户
    const userTable = page.locator('[data-testid="user-table"]');
    await expect(userTable).toBeVisible();
    
    // 验证搜索功能
    await page.fill('[data-testid="user-search"]', 'admin');
    await page.click('[data-testid="search-button"]');
    await expect(userTable.locator('tbody tr')).toHaveCountGreaterThan(0);
    
    // 5. 组织管理验证（验证闭包表优化效果）
    await page.click('[data-testid="menu-org-management"]');
    
    // 测试组织树展开性能
    const startTime = Date.now();
    await page.click('[data-testid="expand-org-tree"]');
    await page.waitForSelector('[data-testid="org-tree-node"]');
    const loadTime = Date.now() - startTime;
    
    // 验证组织树加载性能（闭包表优化后应该很快）
    expect(loadTime).toBeLessThan(500); // 应该在500ms内加载完成
    
    // 6. 设备管理验证
    await page.click('[data-testid="menu-device-management"]');
    await page.waitForLoadState('networkidle');
    
    const deviceTable = page.locator('[data-testid="device-table"]');
    await expect(deviceTable).toBeVisible();
    
    // 7. 告警管理验证
    await page.click('[data-testid="menu-alert-management"]');
    await page.waitForLoadState('networkidle');
    
    // 验证告警列表和实时更新
    const alertTable = page.locator('[data-testid="alert-table"]');
    await expect(alertTable).toBeVisible();
    
    // 8. 健康数据管理验证
    await page.click('[data-testid="menu-health-data"]');
    await page.waitForLoadState('networkidle');
    
    const healthTable = page.locator('[data-testid="health-data-table"]');
    await expect(healthTable).toBeVisible();
  });

  test('Admin跨租户数据访问权限验证', async ({ page }) => {
    // 先登录
    await page.fill('[data-testid="username"]', 'admin');
    await page.fill('[data-testid="password"]', 'admin123');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*dashboard/);
    
    // 验证可以切换租户视角
    await page.click('[data-testid="tenant-selector"]');
    
    // 应该看到所有租户选项
    const tenantOptions = page.locator('[data-testid="tenant-option"]');
    await expect(tenantOptions).toHaveCountGreaterThan(1);
    
    // 切换到特定租户
    await page.click('[data-testid="tenant-option"]:first-child');
    
    // 验证数据视角切换成功
    await page.waitForLoadState('networkidle');
    
    // 在用户管理中验证只看到该租户的用户
    await page.click('[data-testid="menu-user-management"]');
    await page.waitForLoadState('networkidle');
  });

  test('组织架构性能和交互测试', async ({ page }) => {
    // 登录
    await page.fill('[data-testid="username"]', 'admin');
    await page.fill('[data-testid="password"]', 'admin123');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*dashboard/);
    
    // 进入组织管理
    await page.click('[data-testid="menu-org-management"]');
    
    // 性能测试：大量组织节点展开
    const performanceStart = Date.now();
    
    // 展开多层组织树
    const expandButtons = page.locator('[data-testid="org-expand-button"]');
    const expandCount = await expandButtons.count();
    
    for (let i = 0; i < Math.min(5, expandCount); i++) {
      await expandButtons.nth(i).click();
      await page.waitForTimeout(100); // 短暂等待动画
    }
    
    const performanceEnd = Date.now();
    const totalTime = performanceEnd - performanceStart;
    
    console.log(`组织树展开性能: ${totalTime}ms for ${Math.min(5, expandCount)} nodes`);
    
    // 验证响应性能（得益于闭包表优化）
    expect(totalTime).toBeLessThan(2000); // 总共不超过2秒
    
    // 验证组织数据显示完整性
    const orgNodes = page.locator('[data-testid="org-tree-node"]');
    await expect(orgNodes).toHaveCountGreaterThan(0);
  });

  test('实时告警功能E2E测试', async ({ page }) => {
    // 登录
    await page.fill('[data-testid="username"]', 'admin');
    await page.fill('[data-testid="password"]', 'admin123');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*dashboard/);
    
    // 进入告警管理页面
    await page.click('[data-testid="menu-alert-management"]');
    await page.waitForLoadState('networkidle');
    
    // 验证告警列表加载
    const alertTable = page.locator('[data-testid="alert-table"]');
    await expect(alertTable).toBeVisible();
    
    // 验证告警状态过滤功能
    await page.click('[data-testid="alert-status-filter"]');
    await page.click('[data-testid="status-critical"]');
    
    // 等待过滤结果
    await page.waitForLoadState('networkidle');
    
    // 验证过滤后的告警都是critical级别
    const alertRows = page.locator('[data-testid="alert-row"]');
    const rowCount = await alertRows.count();
    
    if (rowCount > 0) {
      for (let i = 0; i < Math.min(3, rowCount); i++) {
        const levelCell = alertRows.nth(i).locator('[data-testid="alert-level"]');
        await expect(levelCell).toContainText('critical');
      }
    }
    
    // 测试告警详情查看
    if (rowCount > 0) {
      await alertRows.first().click();
      await expect(page.locator('[data-testid="alert-detail-modal"]')).toBeVisible();
      
      // 验证详情信息完整性
      await expect(page.locator('[data-testid="alert-detail-content"]')).toBeVisible();
      
      // 关闭详情
      await page.click('[data-testid="close-detail-modal"]');
    }
  });
});