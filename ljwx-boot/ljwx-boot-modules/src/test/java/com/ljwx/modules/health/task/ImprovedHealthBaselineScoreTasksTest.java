package com.ljwx.modules.health.task;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * 改进版健康基线和评分任务测试类
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.task.ImprovedHealthBaselineScoreTasksTest
 * @CreateTime 2025-09-08
 */
@ExtendWith(MockitoExtension.class)
class ImprovedHealthBaselineScoreTasksTest {

    @Mock
    private JdbcTemplate jdbcTemplate;
    
    @Mock
    private com.ljwx.modules.health.service.WeightCalculationService weightCalculationService;
    
    @Mock
    private com.ljwx.modules.health.service.HealthRecommendationService healthRecommendationService;

    @InjectMocks
    private ImprovedHealthBaselineScoreTasks improvedHealthBaselineScoreTasks;

    private ExecutorService testExecutorService;

    @BeforeEach
    void setUp() {
        testExecutorService = Executors.newFixedThreadPool(2);
        ReflectionTestUtils.setField(improvedHealthBaselineScoreTasks, "executorService", testExecutorService);
    }

    @Test
    void testGenerateUserHealthBaseline_WithValidData() {
        // 准备测试数据
        String testDate = LocalDate.now().minusDays(1).toString();
        
        // 模拟表存在检查
        when(jdbcTemplate.queryForObject(
            contains("information_schema.tables"), 
            eq(Integer.class), 
            anyString()))
            .thenReturn(1);
            
        // 模拟数据计数查询
        when(jdbcTemplate.queryForObject(
            contains("SELECT COUNT(*) FROM"), 
            eq(Long.class), 
            anyString()))
            .thenReturn(100L);
            
        // 模拟基线删除操作
        when(jdbcTemplate.update(
            contains("DELETE FROM t_health_baseline"), 
            anyString(), 
            anyString()))
            .thenReturn(5);
            
        // 模拟基线插入操作
        when(jdbcTemplate.update(anyString()))
            .thenReturn(10);

        // 执行测试
        assertDoesNotThrow(() -> {
            improvedHealthBaselineScoreTasks.generateUserHealthBaseline();
        });

        // 验证关键方法被调用
        verify(jdbcTemplate, atLeastOnce()).queryForObject(
            contains("COUNT(*) FROM"), eq(Long.class), anyString());
        verify(jdbcTemplate, atLeastOnce()).update(
            contains("DELETE FROM t_health_baseline"), anyString(), anyString());
    }

    @Test
    void testGenerateUserHealthBaseline_WithNoData() {
        // 模拟无数据情况
        when(jdbcTemplate.queryForObject(
            contains("SELECT COUNT(*) FROM"), 
            eq(Long.class), 
            anyString()))
            .thenReturn(0L);

        // 执行测试
        assertDoesNotThrow(() -> {
            improvedHealthBaselineScoreTasks.generateUserHealthBaseline();
        });

        // 验证没有执行删除和插入操作
        verify(jdbcTemplate, never()).update(
            contains("DELETE FROM t_health_baseline"), anyString(), anyString());
    }

    @Test
    void testGenerateDepartmentHealthBaseline_Success() {
        // 准备测试数据
        String testDate = LocalDate.now().minusDays(1).toString();
        
        // 模拟删除操作
        when(jdbcTemplate.update(
            contains("DELETE FROM t_org_health_baseline"), 
            anyString()))
            .thenReturn(3);
            
        // 模拟部门聚合插入操作
        when(jdbcTemplate.update(
            contains("INSERT INTO t_org_health_baseline"), 
            anyString(), anyString(), any(Double.class), anyString(), anyString()))
            .thenReturn(5);

        // 执行测试
        assertDoesNotThrow(() -> {
            improvedHealthBaselineScoreTasks.generateDepartmentHealthBaseline();
        });

        // 验证关键操作
        verify(jdbcTemplate, atLeastOnce()).update(
            contains("DELETE FROM t_org_health_baseline"), anyString());
        verify(jdbcTemplate, atLeastOnce()).update(
            contains("INSERT INTO t_org_health_baseline"), 
            anyString(), anyString(), any(Double.class), anyString(), anyString());
    }

    @Test
    void testGenerateTenantHealthBaseline_Success() {
        // 模拟租户聚合操作
        when(jdbcTemplate.update(
            contains("DELETE FROM t_org_health_baseline"), 
            anyString(), anyString(), anyString(), anyString()))
            .thenReturn(2);
            
        when(jdbcTemplate.update(
            contains("INSERT INTO t_org_health_baseline"), 
            anyString(), anyString(), any(Double.class), anyString(), anyString()))
            .thenReturn(3);

        // 执行测试
        assertDoesNotThrow(() -> {
            improvedHealthBaselineScoreTasks.generateTenantHealthBaseline();
        });

        // 验证租户级别聚合执行
        verify(jdbcTemplate, atLeastOnce()).update(
            contains("INSERT INTO t_org_health_baseline"), 
            anyString(), anyString(), any(Double.class), anyString(), anyString());
    }

    @Test
    void testGenerateUserHealthScore_WithBaselines() {
        String testDate = LocalDate.now().minusDays(1).toString();
        
        // 模拟权重服务调用
        doNothing().when(weightCalculationService).updateDailyWeights();
        
        // 模拟基线数据存在
        when(jdbcTemplate.queryForObject(
            contains("SELECT COUNT(*) FROM t_health_baseline"), 
            eq(Long.class), 
            anyString()))
            .thenReturn(50L);
            
        // 模拟表存在检查
        when(jdbcTemplate.queryForObject(
            contains("information_schema.tables"), 
            eq(Integer.class), 
            anyString()))
            .thenReturn(1);
            
        // 模拟评分删除和插入操作
        when(jdbcTemplate.update(
            contains("DELETE FROM t_health_score"), 
            anyString()))
            .thenReturn(10);
            
        when(jdbcTemplate.update(anyString()))
            .thenReturn(15);

        // 执行测试
        assertDoesNotThrow(() -> {
            improvedHealthBaselineScoreTasks.generateUserHealthScore();
        });

        // 验证权重服务被调用
        verify(weightCalculationService, times(1)).updateDailyWeights();
        
        // 验证基线数据检查
        verify(jdbcTemplate, atLeastOnce()).queryForObject(
            contains("SELECT COUNT(*) FROM t_health_baseline"), eq(Long.class), anyString());
    }

    @Test
    void testGenerateUserHealthScore_WithoutBaselines() {
        // 模拟权重服务调用
        doNothing().when(weightCalculationService).updateDailyWeights();
        
        // 模拟无基线数据
        when(jdbcTemplate.queryForObject(
            contains("SELECT COUNT(*) FROM t_health_baseline"), 
            eq(Long.class), 
            anyString()))
            .thenReturn(0L);

        // 执行测试
        assertDoesNotThrow(() -> {
            improvedHealthBaselineScoreTasks.generateUserHealthScore();
        });

        // 验证权重服务被调用
        verify(weightCalculationService, times(1)).updateDailyWeights();
        
        // 验证没有执行删除操作（因为没有基线数据）
        verify(jdbcTemplate, never()).update(
            contains("DELETE FROM t_health_score"), anyString());
    }

    @Test
    void testGenerateDepartmentHealthScore_Success() {
        String testDate = LocalDate.now().minusDays(1).toString();
        
        // 模拟删除和插入操作
        when(jdbcTemplate.update(
            contains("DELETE FROM t_org_health_score"), 
            anyString()))
            .thenReturn(5);
            
        when(jdbcTemplate.update(
            contains("INSERT INTO t_org_health_score"), 
            anyString()))
            .thenReturn(8);

        // 执行测试
        assertDoesNotThrow(() -> {
            improvedHealthBaselineScoreTasks.generateDepartmentHealthScore();
        });

        // 验证部门评分生成
        verify(jdbcTemplate, times(1)).update(
            contains("DELETE FROM t_org_health_score"), anyString());
        verify(jdbcTemplate, times(1)).update(
            contains("INSERT INTO t_org_health_score"), anyString());
    }

    @Test
    void testGenerateTenantHealthScore_Success() {
        // 模拟租户评分插入操作
        when(jdbcTemplate.update(
            contains("INSERT IGNORE INTO t_org_health_score"), 
            anyString()))
            .thenReturn(12);

        // 执行测试
        assertDoesNotThrow(() -> {
            improvedHealthBaselineScoreTasks.generateTenantHealthScore();
        });

        // 验证租户评分生成
        verify(jdbcTemplate, times(1)).update(
            contains("INSERT IGNORE INTO t_org_health_score"), anyString());
    }

    @Test
    void testManualGenerateImprovedBaselinesAndScores() {
        String startDate = "2025-09-01";
        String endDate = "2025-09-03";
        
        // 模拟表存在检查
        when(jdbcTemplate.queryForObject(
            contains("information_schema.tables"), 
            eq(Integer.class), 
            anyString()))
            .thenReturn(1);
            
        // 模拟各种数据库操作
        when(jdbcTemplate.update(anyString())).thenReturn(5);
        when(jdbcTemplate.update(anyString(), anyString())).thenReturn(3);
        when(jdbcTemplate.update(anyString(), anyString(), anyString())).thenReturn(2);
        when(jdbcTemplate.update(
            anyString(), anyString(), anyString(), any(Double.class), anyString(), anyString()))
            .thenReturn(4);

        // 执行测试
        assertDoesNotThrow(() -> {
            improvedHealthBaselineScoreTasks.manualGenerateImprovedBaselinesAndScores(startDate, endDate);
        });

        // 验证执行了多次数据库操作（3天 × 多个特征 × 多种操作类型）
        verify(jdbcTemplate, atLeast(30)).update(anyString());
    }

    @Test
    void testPerformDataQualityCheck() {
        String testDate = "2025-09-08";
        
        // 模拟数据质量查询结果
        Map<String, Object> qualityResult = new HashMap<>();
        qualityResult.put("total_baselines", 100);
        qualityResult.put("missing_user_id", 5);
        qualityResult.put("missing_device_sn", 3);
        qualityResult.put("low_sample_count", 8);
        qualityResult.put("zero_std", 2);
        
        when(jdbcTemplate.queryForMap(
            contains("SELECT"), anyString()))
            .thenReturn(qualityResult);
            
        // 模拟特征一致性查询
        Map<String, Object> consistencyResult = new HashMap<>();
        consistencyResult.put("user_baseline_count", 95);
        consistencyResult.put("dept_baseline_count", 12);
        consistencyResult.put("tenant_baseline_count", 3);
        
        when(jdbcTemplate.queryForMap(
            contains("COUNT(DISTINCT hb.user_id)"), 
            anyString(), anyString(), anyString(), anyString()))
            .thenReturn(consistencyResult);

        // 使用反射调用私有方法进行测试
        assertDoesNotThrow(() -> {
            ReflectionTestUtils.invokeMethod(
                improvedHealthBaselineScoreTasks, 
                "performDataQualityCheck", 
                testDate);
        });

        // 验证数据质量查询被调用
        verify(jdbcTemplate, atLeastOnce()).queryForMap(
            contains("SELECT"), anyString());
    }

    @Test
    void testHierarchicalDataConsistencyCheck() {
        String testDate = "2025-09-08";
        
        // 模拟层级一致性检查查询
        Map<String, Object> consistencyData = new HashMap<>();
        consistencyData.put("user_baseline_count", 88);
        consistencyData.put("dept_baseline_count", 15);
        consistencyData.put("tenant_baseline_count", 4);
        
        when(jdbcTemplate.queryForMap(
            anyString(), anyString(), anyString(), anyString(), anyString()))
            .thenReturn(consistencyData);

        // 使用反射调用私有方法
        assertDoesNotThrow(() -> {
            ReflectionTestUtils.invokeMethod(
                improvedHealthBaselineScoreTasks, 
                "checkHierarchicalDataConsistency", 
                testDate);
        });

        // 验证一致性检查被执行（每个健康特征都会检查）
        verify(jdbcTemplate, times(10)).queryForMap(
            anyString(), anyString(), anyString(), anyString(), anyString());
    }

    @Test
    void testTableExistenceCheck() {
        String testTableName = "t_user_health_data_202509";
        
        // 模拟表存在
        when(jdbcTemplate.queryForObject(
            contains("information_schema.tables"), 
            eq(Integer.class), 
            eq(testTableName)))
            .thenReturn(1);

        // 使用反射调用私有方法
        Boolean exists = ReflectionTestUtils.invokeMethod(
            improvedHealthBaselineScoreTasks, 
            "tableExists", 
            testTableName);

        assertTrue(exists);
        
        // 验证查询被执行
        verify(jdbcTemplate, times(1)).queryForObject(
            contains("information_schema.tables"), eq(Integer.class), eq(testTableName));
    }

    @Test
    void testFeatureValueRanges() {
        // 测试心率范围
        Double minHeartRate = ReflectionTestUtils.invokeMethod(
            improvedHealthBaselineScoreTasks, "getFeatureMinValue", "heart_rate");
        Double maxHeartRate = ReflectionTestUtils.invokeMethod(
            improvedHealthBaselineScoreTasks, "getFeatureMaxValue", "heart_rate");
        
        assertEquals(30.0, minHeartRate);
        assertEquals(200.0, maxHeartRate);

        // 测试血氧范围
        Double minBloodOxygen = ReflectionTestUtils.invokeMethod(
            improvedHealthBaselineScoreTasks, "getFeatureMinValue", "blood_oxygen");
        Double maxBloodOxygen = ReflectionTestUtils.invokeMethod(
            improvedHealthBaselineScoreTasks, "getFeatureMaxValue", "blood_oxygen");
        
        assertEquals(70.0, minBloodOxygen);
        assertEquals(100.0, maxBloodOxygen);
    }

    @Test
    void testMinStandardDeviationValues() {
        // 测试不同特征的最小标准差
        Double heartRateStd = ReflectionTestUtils.invokeMethod(
            improvedHealthBaselineScoreTasks, "getMinStandardDeviation", "heart_rate");
        assertEquals(1.0, heartRateStd);

        Double temperatureStd = ReflectionTestUtils.invokeMethod(
            improvedHealthBaselineScoreTasks, "getMinStandardDeviation", "temperature");
        assertEquals(0.1, temperatureStd);

        Double stepStd = ReflectionTestUtils.invokeMethod(
            improvedHealthBaselineScoreTasks, "getMinStandardDeviation", "step");
        assertEquals(100.0, stepStd);
    }

    @Test
    void testErrorHandling_DatabaseException() {
        // 模拟数据库异常
        when(jdbcTemplate.queryForObject(
            contains("SELECT COUNT(*) FROM"), 
            eq(Long.class), 
            anyString()))
            .thenThrow(new RuntimeException("Database connection failed"));

        // 验证异常被正确处理
        assertThrows(RuntimeException.class, () -> {
            improvedHealthBaselineScoreTasks.generateUserHealthBaseline();
        });
    }

    @Test 
    void testThreadPoolShutdown() {
        // 验证线程池能够正确关闭
        assertDoesNotThrow(() -> {
            improvedHealthBaselineScoreTasks.destroy();
        });
    }
}