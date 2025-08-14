/*
 * All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
 */

package com.ljwx.modules.system.test;

import com.ljwx.modules.system.service.ISysUserOrgService;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import javax.annotation.Resource;
import java.util.Arrays;
import java.util.Collections;
import static org.junit.jupiter.api.Assertions.*;

/**
 * 用户组织主管标记更新测试
 * 修复orgUnitsPrincipalIds为空时的NullPointerException问题
 */
@SpringBootTest
@ActiveProfiles("test")
public class SysUserOrgPrincipalUpdateTest {

    @Resource
    private ISysUserOrgService sysUserOrgService;

    @Test
    public void testUpdateUserOrgWithEmptyPrincipalIds() {
        // 测试数据
        Long userId = 1935226491089788929L;
        var orgIds = Arrays.asList(1L); // 有组织
        var principalIds = Collections.<Long>emptyList(); // 空主管ID列表
        
        // 执行更新 - 不应该抛出NullPointerException
        assertDoesNotThrow(() -> {
            boolean result = sysUserOrgService.updateUserOrg(userId, orgIds, principalIds);
            System.out.println("更新结果: " + result);
        }, "当principalIds为空时不应该抛出异常");
    }

    @Test 
    public void testUpdateUserOrgWithValidPrincipalIds() {
        // 测试数据  
        Long userId = 1935226491089788929L;
        var orgIds = Arrays.asList(1L);
        var principalIds = Arrays.asList(1L); // 有效主管ID
        
        // 执行更新
        assertDoesNotThrow(() -> {
            boolean result = sysUserOrgService.updateUserOrg(userId, orgIds, principalIds);
            System.out.println("更新结果: " + result);
        }, "正常情况下不应该抛出异常");
    }

    @Test
    public void testUpdateUserOrgWithNullPrincipalIds() {
        // 测试数据
        Long userId = 1935226491089788929L; 
        var orgIds = Arrays.asList(1L);
        
        // 执行更新 - principalIds为null
        assertDoesNotThrow(() -> {
            boolean result = sysUserOrgService.updateUserOrg(userId, orgIds, null);
            System.out.println("更新结果: " + result);
        }, "当principalIds为null时不应该抛出异常");
    }
} 