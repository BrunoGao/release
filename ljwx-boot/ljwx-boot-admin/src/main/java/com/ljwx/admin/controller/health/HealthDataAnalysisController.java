package com.ljwx.admin.controller.health;

import com.ljwx.common.api.Result;
import com.ljwx.modules.health.domain.dto.user.health.data.HealthDataAnalysisDTO;
import com.ljwx.modules.health.domain.vo.HealthDataAnalysisVO;
import com.ljwx.modules.health.service.IHealthDataAnalysisService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@Tag(name = "健康数据分析接口")
@RequestMapping("/health/analysis")
public class HealthDataAnalysisController {

    private final IHealthDataAnalysisService healthDataAnalysisService;

    @Operation(summary = "分析健康数据")
    @PostMapping("/analyze")
    public Result<HealthDataAnalysisVO> analyzeHealthData(@RequestBody HealthDataAnalysisDTO analysisDTO) {
        HealthDataAnalysisVO result = healthDataAnalysisService.analyzeHealthData(analysisDTO);
        return Result.data(result);
    }
} 