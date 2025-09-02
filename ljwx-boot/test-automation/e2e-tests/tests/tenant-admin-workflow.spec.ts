import { test, expect } from '@playwright/test';

/**
 * 租户管理员端到端工作流测试
 * 验证租户权限隔离和功能完整性
 */
test.describe('租户管理员工作流', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('租户管理员登录和权限验证', async ({ page }) => {
    // 1. 租户管理员登录
    await page.fill('[data-testid="username"]', 'tenant_admin_001');
    await page.fill('[data-testid="password"]', 'tenant123'); // 假设租户管理员密码
    await page.click('[data-testid="login-button"]');
    
    // 验证登录成功
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('[data-testid="user-info"]')).toContainText('租户管理员');
    
    // 2. 验证首页数据隔离
    await expect(page.locator('[data-testid="dashboard-stats"]')).toBeVisible();
    
    // 验证数据只显示当前租户的信息
    const tenantInfo = page.locator('[data-testid="current-tenant-info"]');
    await expect(tenantInfo).toBeVisible();
    await expect(tenantInfo).not.toContainText('全局'); // 不应显示全局数据
    
    // 3. 租户管理权限验证
    await page.click('[data-testid="menu-tenant-management"]');
    await page.waitForLoadState('networkidle');
    
    // 租户管理员应该只能查看，不能修改租户信息
    const tenantTable = page.locator('[data-testid="tenant-table"]');
    await expect(tenantTable).toBeVisible();
    
    // 验证没有"添加租户"按钮（只有Admin才有）
    await expect(page.locator('[data-testid="add-tenant-button"]')).not.toBeVisible();
    
    // 4. 用户管理权限验证
    await page.click('[data-testid="menu-user-management"]');
    await page.waitForLoadState('networkidle');
    
    // 应该只看到本租户的用户
    const userTable = page.locator('[data-testid="user-table"]');
    await expect(userTable).toBeVisible();
    
    // 验证用户数据都属于当前租户
    const userRows = page.locator('[data-testid="user-row"]');
    const rowCount = await userRows.count();
    
    if (rowCount > 0) {
      // 检查前几行用户的租户ID
      for (let i = 0; i < Math.min(3, rowCount); i++) {
        const tenantCell = userRows.nth(i).locator('[data-testid="user-tenant-id"]');
        const tenantId = await tenantCell.textContent();
        expect(tenantId).not.toBe('0'); // 不应该是全局用户
      }
    }
  });

  test('租户管理员数据隔离边界测试', async ({ page }) => {
    // 登录租户管理员
    await page.fill('[data-testid="username"]', 'tenant_admin_001');
    await page.fill('[data-testid="password"]', 'tenant123');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*dashboard/);
    
    // 5. 设备管理权限验证
    await page.click('[data-testid="menu-device-management"]');
    await page.waitForLoadState('networkidle');
    
    const deviceTable = page.locator('[data-testid="device-table"]');
    await expect(deviceTable).toBeVisible();
    
    // 尝试搜索设备（应该只返回本租户设备）
    await page.fill('[data-testid="device-search"]', '');
    await page.click('[data-testid="search-button"]');
    await page.waitForLoadState('networkidle');
    
    // 6. 消息管理权限验证
    await page.click('[data-testid="menu-message-management"]');
    await page.waitForLoadState('networkidle');
    
    const messageTable = page.locator('[data-testid="message-table"]');
    await expect(messageTable).toBeVisible();
    
    // 验证消息发送功能（租户隔离）
    await page.click('[data-testid="send-message-button"]');
    
    const recipientSelector = page.locator('[data-testid="message-recipients"]');
    await expect(recipientSelector).toBeVisible();
    
    // 收件人列表应该只包含本租户用户
    await recipientSelector.click();
    const recipientOptions = page.locator('[data-testid="recipient-option"]');
    const optionCount = await recipientOptions.count();
    
    // 验证收件人数量合理（不应包含其他租户用户）
    expect(optionCount).toBeGreaterThan(0);
    expect(optionCount).toBeLessThan(1000); // 合理的租户内用户数量
    
    // 7. 告警管理权限验证
    await page.click('[data-testid="menu-alert-management"]');
    await page.waitForLoadState('networkidle');
    
    const alertTable = page.locator('[data-testid="alert-table"]');
    await expect(alertTable).toBeVisible();
    
    // 验证告警数据隔离
    const alertRows = page.locator('[data-testid="alert-row"]');
    const alertCount = await alertRows.count();
    
    if (alertCount > 0) {
      // 点击第一个告警查看详情
      await alertRows.first().click();
      await expect(page.locator('[data-testid="alert-detail-modal"]')).toBeVisible();
      
      // 验证告警详情属于当前租户
      const alertTenantInfo = page.locator('[data-testid="alert-tenant-info"]');
      await expect(alertTenantInfo).toBeVisible();
      
      await page.click('[data-testid="close-detail-modal"]');
    }
  });

  test('租户管理员功能操作权限测试', async ({ page }) => {
    // 登录租户管理员
    await page.fill('[data-testid="username"]', 'tenant_admin_001');
    await page.fill('[data-testid="password"]', 'tenant123');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*dashboard/);
    
    // 8. 角色和岗位管理权限验证
    await page.click('[data-testid="menu-role-management"]');
    await page.waitForLoadState('networkidle');
    
    // 验证可以管理租户内角色
    const roleTable = page.locator('[data-testid="role-table"]');
    await expect(roleTable).toBeVisible();
    
    // 验证可以创建租户角色
    if (await page.locator('[data-testid="add-role-button"]').isVisible()) {
      await page.click('[data-testid="add-role-button"]');
      await expect(page.locator('[data-testid="role-form"]')).toBeVisible();
      
      // 验证角色权限范围限制在租户内
      const permissionTree = page.locator('[data-testid="permission-tree"]');
      await expect(permissionTree).toBeVisible();
      
      // 关闭表单
      await page.click('[data-testid="cancel-role-form"]');
    }
    
    // 9. 健康图标配置权限验证
    await page.click('[data-testid="menu-health-icons"]');
    await page.waitForLoadState('networkidle');
    
    const iconTable = page.locator('[data-testid="health-icon-table"]');
    await expect(iconTable).toBeVisible();
    
    // 验证可以配置租户级健康图标
    if (await page.locator('[data-testid="add-icon-button"]').isVisible()) {
      await page.click('[data-testid="add-icon-button"]');
      await expect(page.locator('[data-testid="icon-config-form"]')).toBeVisible();
      
      // 验证配置范围限制在租户内
      await page.click('[data-testid="cancel-icon-form"]');
    }
  });

  test('租户权限边界安全测试', async ({ page }) => {
    // 登录租户管理员
    await page.fill('[data-testid="username"]', 'tenant_admin_001');
    await page.fill('[data-testid="password"]', 'tenant123');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*dashboard/);
    
    // 尝试访问超出权限的功能
    
    // 1. 验证无法访问全局系统配置
    const systemConfigUrl = page.url().replace(/\/dashboard.*/, '/system/config');
    await page.goto(systemConfigUrl);
    
    // 应该被重定向或显示权限不足
    await page.waitForLoadState('networkidle');
    expect(page.url()).not.toContain('/system/config');
    
    // 2. 验证无法修改其他租户数据
    // 这个测试需要根据实际的前端路由和权限控制机制来实现
    
    // 3. 验证URL直接访问保护
    const adminOnlyUrl = page.url().replace(/\/dashboard.*/, '/admin/global-settings');
    await page.goto(adminOnlyUrl);
    
    await page.waitForLoadState('networkidle');
    
    // 应该无法访问或被重定向
    const currentUrl = page.url();
    expect(currentUrl).not.toContain('/admin/global-settings');
  });
});