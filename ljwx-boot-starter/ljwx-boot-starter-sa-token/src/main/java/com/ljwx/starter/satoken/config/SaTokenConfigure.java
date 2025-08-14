package com.ljwx.starter.satoken.config;

import cn.dev33.satoken.config.SaTokenConfig;
import cn.dev33.satoken.jwt.StpLogicJwtForSimple;
import cn.dev33.satoken.stp.StpLogic;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

/**
 * Sa Token 全局配置 - 优化登录稳定性
 *
 * @Author payne.zhuang <paynezhuang@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.starter.satoken.config.SaTokenConfigure
 * @CreateTime 2024/4/19 - 10:14
 */

@Configuration
public class SaTokenConfigure {

    /**
     * Sa-Token 参数配置，参考文档：<a href="https://sa-token.cc">https://sa-token.cc</a> <br/>
     * 此配置会覆盖 application.yml 中的配置
     */
    @Bean
    @Primary
    public SaTokenConfig getSaTokenConfigPrimary() {
        return new SaTokenConfig()
                // jwt秘钥
                .setJwtSecretKey("GtztRxC5JUpd5bfAibJuTKGJDVZaRfBR")
                // token 前缀
                .setTokenPrefix("Bearer")
                // token 名称（同时也是 cookie 名称）
                .setTokenName("Authorization")
                // token 风格 https://sa-token.cc/doc.html#/up/token-style
                .setTokenStyle("random-32")
                // token 有效期（单位：秒），延长到7天避免频繁过期 #延长token有效期
                .setTimeout(604800)
                // token 最低活跃频率（单位：秒），延长到24小时避免频繁冻结 #延长活跃频率
                .setActiveTimeout(86400)
                // 是否允许同一账号多地同时登录（为 true 时允许一起登录，为 false 时新登录挤掉旧登录）
                .setIsConcurrent(true)
                // 在多人登录同一账号时，是否共用一个 token （为 true 时所有登录共用一个 token，为 false 时每次登录新建一个 token）
                // Simple 模式，此项无效
                .setIsShare(true)
                // 是否尝试从 cookie 里读取 Token，此值为 false 后，StpUtil.login(id) 登录时也不会再往前端注入Cookie
                .setIsReadCookie(false)
                // 是否在初始化配置时打印版本字符画
                .setIsPrint(false)
                // 是否输出操作日志
                .setIsLog(true)
                // 自动续签配置 #自动续签
                .setAutoRenew(true)
                // 是否开启自动刷新 #自动刷新
                .setTokenSessionCheckLogin(true);
    }

    /**
     * Sa-Token 整合 jwt (Simple 简单模式) <br/>
     * <a href="https://sa-token.cc/doc.html#/plugin/jwt-extend">https://sa-token.cc/doc.html#/plugin/jwt-extend</a>
     */
    @Bean
    public StpLogic getStpLogicJwt() {
        return new StpLogicJwtForSimple();
    }
}
