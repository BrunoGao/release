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

    // 监控端点放行接口
    public final String[] monitoringExcludePatterns = new String[]{
            "/monitoring/**",
            "/actuator/**"
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
                .excludePathPatterns(monitoringExcludePatterns)
                .order(Ordered.HIGHEST_PRECEDENCE + 1);
    }
}
