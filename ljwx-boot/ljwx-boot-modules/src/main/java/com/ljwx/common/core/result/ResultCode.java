package com.ljwx.common.core.result;

/**
 * 响应状态码枚举
 */
public enum ResultCode {

    SUCCESS(200, "操作成功"),
    
    BAD_REQUEST(400, "请求参数错误"),
    UNAUTHORIZED(401, "未授权访问"),
    FORBIDDEN(403, "权限不足"),
    NOT_FOUND(404, "资源不存在"),
    METHOD_NOT_ALLOWED(405, "请求方法不允许"),
    
    INTERNAL_ERROR(500, "系统内部错误"),
    SERVICE_UNAVAILABLE(503, "服务暂时不可用"),
    
    BUSINESS_ERROR(600, "业务处理失败"),
    VALIDATION_ERROR(601, "数据验证失败"),
    DATA_NOT_FOUND(602, "数据不存在"),
    DATA_ALREADY_EXISTS(603, "数据已存在"),
    OPERATION_NOT_ALLOWED(604, "操作不被允许"),
    
    HEALTH_BASELINE_ERROR(700, "健康基线生成失败"),
    HEALTH_SCORE_ERROR(701, "健康评分计算失败"),
    HEALTH_RECOMMENDATION_ERROR(702, "健康建议生成失败"),
    HEALTH_PROFILE_ERROR(703, "健康画像生成失败"),
    
    ALERT_RULE_ERROR(800, "告警规则处理失败"),
    ALERT_PROCESS_ERROR(801, "告警处理失败"),
    NOTIFICATION_ERROR(802, "通知发送失败"),
    
    DEVICE_ERROR(900, "设备操作失败"),
    MESSAGE_ERROR(901, "消息处理失败");

    private final int code;
    private final String message;

    ResultCode(int code, String message) {
        this.code = code;
        this.message = message;
    }

    public int getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }
}