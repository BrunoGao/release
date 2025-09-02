package com.ljwx.modules.ai.service;

import com.ljwx.modules.ai.vo.ChatRequest;
import com.ljwx.modules.ai.vo.ChatResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.HttpEntity;
import org.springframework.web.client.RestTemplate;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

@SpringBootTest
class DeepSeekR1ServiceTest {

    @Autowired
    private DeepSeekR1Service deepSeekR1Service;

    @MockBean
    private RestTemplate restTemplate;

    private ChatRequest chatRequest;
    private ChatResponse mockResponse;

    @BeforeEach
    void setUp() {
        // 准备测试数据
        chatRequest = ChatRequest.builder()
                .message("Hello, AI!")
                .userId(1L)
                .build();

        mockResponse = new ChatResponse();
        mockResponse.setContent("Hello, Human!");
    }

    @Test
    void generateResponse_ShouldReturnValidResponse() {
        // 设置模拟行为
        when(restTemplate.postForObject(
                eq("http://localhost:11434/api/chat/completions"),
                any(HttpEntity.class),
                eq(ChatResponse.class)
        )).thenReturn(mockResponse);

        // 执行测试
        ChatResponse response = deepSeekR1Service.generateResponse(chatRequest);

        // 验证结果
        assertNotNull(response);
        assertEquals("Hello, Human!", response.getContent());
    }

    @Test
    void generateResponse_ShouldHandleNullResponse() {
        // 设置模拟行为返回null
        when(restTemplate.postForObject(
                any(String.class),
                any(HttpEntity.class),
                eq(ChatResponse.class)
        )).thenReturn(null);

        // 执行测试并验证结果
        ChatResponse response = deepSeekR1Service.generateResponse(chatRequest);
        assertNull(response);
    }
} 