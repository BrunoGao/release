package com.ljwx.api.v1.controller;

import com.ljwx.api.v1.dto.*;
import com.ljwx.api.v1.service.MessageService;
import com.ljwx.common.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 消息管理API控制器 v1
 * 
 * @author LJWX Team
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/v1/messages")
@RequiredArgsConstructor
@Tag(name = "Message API", description = "消息管理相关接口")
public class MessageController {

    private final MessageService messageService;

    /**
     * 获取用户消息
     */
    @GetMapping("/user")
    @Operation(summary = "获取用户消息", description = "获取用户的消息列表")
    public ApiResponse<List<UserMessageDTO>> getUserMessages(
            @Parameter(description = "用户ID", required = true) @RequestParam String userId) {
        
        List<UserMessageDTO> result = messageService.getUserMessages(userId);
        return ApiResponse.success(result);
    }
}