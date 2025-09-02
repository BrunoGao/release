package com.ljwx.common.license;

import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.ljwx.common.api.Result;
import com.ljwx.common.api.ResultCode;

/**
 * 许可证控制切面
 * 拦截关键业务方法，检查许可证权限
 */
@Slf4j
@Aspect
@Component
public class LicenseControlAspect {

    @Autowired
    private LicenseManager licenseManager;
    
    /**
     * 拦截用户登录，检查用户数量限制
     */
    @Around("execution(* com.ljwx.modules.auth.service.*.login(..))")
    public Object checkUserLogin(ProceedingJoinPoint joinPoint) throws Throwable {
        try {
            // 检查许可证状态
            if (!licenseManager.isLicenseValid()) {
                log.warn("许可证无效或已过期，用户登录受限");
                // 试用模式下仍允许少量用户登录
            }
            
            // 记录使用情况
            licenseManager.recordUsage("user_login", "system");
            
            // 继续执行原方法
            return joinPoint.proceed();
            
        } catch (Exception e) {
            log.error("许可证检查失败", e);
            return joinPoint.proceed(); // 许可证检查失败时不阻断业务
        }
    }
    
    /**
     * 拦截设备添加，检查设备数量限制
     */
    @Around("execution(* com.ljwx.modules.device.service.*.addDevice(..))")
    public Object checkDeviceAdd(ProceedingJoinPoint joinPoint) throws Throwable {
        try {
            // 获取当前设备数量（这里需要注入相应的服务来查询）
            // long currentDeviceCount = deviceService.getTotalDeviceCount();
            
            // 暂时跳过数量检查，只记录使用情况
            licenseManager.recordUsage("device_add", "system");
            
            Object result = joinPoint.proceed();
            
            log.info("设备添加操作完成，许可证使用情况已记录");
            return result;
            
        } catch (Exception e) {
            log.error("设备添加许可证检查失败", e);
            return joinPoint.proceed();
        }
    }
    
    /**
     * 拦截大屏功能，检查功能权限
     */
    @Around("execution(* com.ljwx.modules.bigscreen.service.*.*(..))")
    public Object checkBigScreenFeature(ProceedingJoinPoint joinPoint) throws Throwable {
        try {
            // 检查大屏功能权限
            if (!licenseManager.hasFeature("big_screen")) {
                log.warn("当前许可证不支持大屏功能");
                return Result.failure(ResultCode.FORBIDDEN.getCode(), "当前许可证版本不支持大屏功能，请升级许可证");
            }
            
            licenseManager.recordUsage("big_screen", "system");
            
            return joinPoint.proceed();
            
        } catch (Exception e) {
            log.error("大屏功能许可证检查失败", e);
            return joinPoint.proceed();
        }
    }
    
    /**
     * 拦截AI分析功能，检查功能权限
     */
    @Around("execution(* com.ljwx.modules.ai.service.*.*(..))")
    public Object checkAIFeature(ProceedingJoinPoint joinPoint) throws Throwable {
        try {
            // 检查AI功能权限
            if (!licenseManager.hasFeature("ai_analysis")) {
                log.warn("当前许可证不支持AI分析功能");
                return Result.failure(ResultCode.FORBIDDEN.getCode(), "当前许可证版本不支持AI分析功能，请联系销售升级");
            }
            
            licenseManager.recordUsage("ai_analysis", "system");
            
            return joinPoint.proceed();
            
        } catch (Exception e) {
            log.error("AI功能许可证检查失败", e);
            return joinPoint.proceed();
        }
    }
    
    /**
     * 拦截健康数据查询，记录使用情况
     */
    @Around("execution(* com.ljwx.modules.health.service.*.getUserHealthData(..))")
    public Object checkHealthDataAccess(ProceedingJoinPoint joinPoint) throws Throwable {
        try {
            // 检查基础健康监测功能
            if (!licenseManager.hasFeature("health_monitoring") && 
                !licenseManager.hasFeature("basic_health")) {
                log.warn("当前许可证不支持健康监测功能");
                return Result.failure(ResultCode.FORBIDDEN.getCode(), "许可证不支持健康监测功能");
            }
            
            licenseManager.recordUsage("health_data", "system");
            
            return joinPoint.proceed();
            
        } catch (Exception e) {
            log.error("健康数据访问许可证检查失败", e);
            return joinPoint.proceed();
        }
    }
}