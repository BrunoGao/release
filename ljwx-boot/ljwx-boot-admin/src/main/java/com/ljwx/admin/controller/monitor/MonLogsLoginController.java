package com.ljwx.admin.controller.monitor;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.monitor.domain.dto.logs.login.MonLogsLoginAddDTO;
import com.ljwx.modules.monitor.domain.dto.logs.login.MonLogsLoginDeleteDTO;
import com.ljwx.modules.monitor.domain.dto.logs.login.MonLogsLoginSearchDTO;
import com.ljwx.modules.monitor.domain.dto.logs.login.MonLogsLoginUpdateDTO;
import com.ljwx.modules.monitor.domain.vo.MonLogsLoginVO;
import com.ljwx.modules.monitor.facade.IMonLogsLoginFacade;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 登录日志 Controller 控制层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName monitor.controller.com.ljwx.admin.MonLogsLoginController
 * @CreateTime 2024-05-05
 */

@RestController
@Tag(name = "登录日志")
@RequiredArgsConstructor
@RequestMapping("/mon_logs_login")
public class MonLogsLoginController {

    @NonNull
    private IMonLogsLoginFacade monLogsLoginFacade;

    @GetMapping("/page")
    @SaCheckPermission("mon:logs:login:page")
    @Operation(operationId = "1", summary = "获取登录日志列表")
    public Result<RPage<MonLogsLoginVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                              @Parameter(description = "查询对象") MonLogsLoginSearchDTO monLogsLoginSearchDTO) {
        return Result.data(monLogsLoginFacade.listMonLogsLoginPage(pageQuery, monLogsLoginSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("mon:logs:login:get")
    @Operation(operationId = "2", summary = "根据ID获取登录日志详细信息")
    public Result<MonLogsLoginVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(monLogsLoginFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("mon:logs:login:add")
    @Operation(operationId = "3", summary = "新增登录日志")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody MonLogsLoginAddDTO monLogsLoginAddDTO) {
        return Result.status(monLogsLoginFacade.add(monLogsLoginAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("mon:logs:login:update")
    @Operation(operationId = "4", summary = "更新登录日志信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody MonLogsLoginUpdateDTO monLogsLoginUpdateDTO) {
        return Result.status(monLogsLoginFacade.update(monLogsLoginUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("mon:logs:login:delete")
    @Operation(operationId = "5", summary = "批量删除登录日志信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody MonLogsLoginDeleteDTO monLogsLoginDeleteDTO) {
        return Result.status(monLogsLoginFacade.batchDelete(monLogsLoginDeleteDTO));
    }

}
