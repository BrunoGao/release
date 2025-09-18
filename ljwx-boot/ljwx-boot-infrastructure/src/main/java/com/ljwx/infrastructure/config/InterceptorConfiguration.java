package com.ljwx.infrastructure.config;

import cn.dev33.satoken.interceptor.SaInterceptor;
import cn.dev33.satoken.stp.StpUtil;
import com.ljwx.infrastructure.interceptor.GlobalRequestInterceptor;
import jakarta.annotation.Resource;
import lombok.NonNull;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.Ordered;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 拦截器配置
 *
 * @Author payne.zhuang <paynezhuang@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.infrastructure.config.InterceptorConfiguration
 * @CreateTime 2024/4/24 - 22:12
 */

@Configuration
public class InterceptorConfiguration implements WebMvcConfigurer
{

    @Resource
    private GlobalRequestInterceptor globalRequestInterceptor;

    // 对 swagger 的请求不进行拦截
    public final String[] swaggerExcludePatterns = new String[]{
            "/v3/**",
            "/webjars/**",
            "/swagger-ui/**",
            "/swagger-resources/**",
            "/favicon.ico",
            "/api",
            "/api-docs",
            "/api-docs/**",
            "/doc.html/**"};

    // 对 Druid 的请求不进行拦截
    public final String[] druidExcludePatterns = new String[]{
            "/druid/**"
    };

    // 业务放行接口
    public final String[] businessExcludePatterns = new String[]{
            "/auth/user_name"
    };

    // 设备端API放行接口（Python ljwx-bigscreen 迁移，设备端无需认证）
    public final String[] deviceApiExcludePatterns = new String[]{
            // ========== 配置管理接口（设备端） ==========
            "/config/health-data",           // 获取健康数据配置
            "/config/get_health_data_config", // Python兼容路径
            "/config/health",                 // 配置服务健康检查
            
            // ========== 批量上传接口（设备端） ==========
            "/batch/upload-health-data",      // 健康数据批量上传
            "/batch/upload_health_data",      // Python兼容路径
            "/batch/upload-device-info",      // 设备信息批量上传
            "/batch/upload_device_info",      // Python兼容路径
            "/batch/upload-common-event",     // 通用事件上传
            "/batch/upload_common_event",     // Python兼容路径
            "/batch/stats",                   // 批处理统计信息
            "/batch/performance-test",        // 性能测试（调试用）
            "/batch/health",                  // 批处理服务健康检查
            
            // ========== 其他设备相关接口 ==========
            "/device/api/**",                 // 设备相关API
            "/health/device/**",              // 设备健康数据API
            "/monitor/device/**"              // 设备监控API
    };

    // 监控端点放行接口
    public final String[] monitoringExcludePatterns = new String[]{
            "/monitoring/**",
            "/actuator/**"
    };

    // 静态资源放行接口
    public final String[] staticResourceExcludePatterns = new String[]{
            "/uploads/**",
            "/logos/**"
    };

    @Override
    public void addInterceptors(@NonNull InterceptorRegistry registry) {

        // 全局请求拦截器，优先级最高
        registry.addInterceptor(globalRequestInterceptor)
                .addPathPatterns("/**")
                .order(Ordered.HIGHEST_PRECEDENCE);

        // sa token 路由拦截器，优先级次之
        registry.addInterceptor(new SaInterceptor(handle -> StpUtil.checkLogin()))
                .addPathPatterns("/**")
                .excludePathPatterns(swaggerExcludePatterns)
                .excludePathPatterns(druidExcludePatterns)
                .excludePathPatterns(businessExcludePatterns)
                .excludePathPatterns(deviceApiExcludePatterns)  // 设备API免认证
                .excludePathPatterns(monitoringExcludePatterns)
                .excludePathPatterns(staticResourceExcludePatterns)
                .order(Ordered.HIGHEST_PRECEDENCE + 1);
    }
}
