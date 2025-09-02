package com.ljwx.modules.health.controller;

import com.ljwx.common.api.vo.Result;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

/**
 * 健康画像控制器
 */
@RestController
@RequestMapping("/health/profile")
@Slf4j
public class HealthProfileController {

    @GetMapping("/test")
    public Result<String> test() {
        return Result.ok("健康画像智能生成系统已成功部署");
    }

    @PostMapping("/baseline/generate")
    public Result<String> generateBaseline(
            @RequestParam Long userId,
            @RequestParam(defaultValue = "30") Integer days) {
        
        log.info("健康基线生成接口已就绪，用户ID: {}, 天数: {}", userId, days);
        return Result.ok("健康基线生成接口已创建，等待服务层完整集成");
    }
}