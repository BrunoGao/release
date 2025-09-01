package com.ljwx.common.core.result;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;

import java.io.Serializable;

/**
 * 通用API响应结果类
 */
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class R<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    private static final int SUCCESS_CODE = 200;
    private static final int ERROR_CODE = 500;
    private static final String SUCCESS_MSG = "操作成功";
    private static final String ERROR_MSG = "操作失败";

    private int code;
    private String message;
    private T data;
    private Long timestamp;

    public R() {
        this.timestamp = System.currentTimeMillis();
    }

    public R(int code, String message) {
        this();
        this.code = code;
        this.message = message;
    }

    public R(int code, String message, T data) {
        this();
        this.code = code;
        this.message = message;
        this.data = data;
    }

    public static <T> R<T> success() {
        return new R<>(SUCCESS_CODE, SUCCESS_MSG);
    }

    public static <T> R<T> success(String message) {
        return new R<>(SUCCESS_CODE, message);
    }

    public static <T> R<T> success(T data) {
        return new R<>(SUCCESS_CODE, SUCCESS_MSG, data);
    }

    public static <T> R<T> success(String message, T data) {
        return new R<>(SUCCESS_CODE, message, data);
    }

    public static <T> R<T> error() {
        return new R<>(ERROR_CODE, ERROR_MSG);
    }

    public static <T> R<T> error(String message) {
        return new R<>(ERROR_CODE, message);
    }

    public static <T> R<T> error(int code, String message) {
        return new R<>(code, message);
    }

    public static <T> R<T> error(int code, String message, T data) {
        return new R<>(code, message, data);
    }

    public boolean isSuccess() {
        return SUCCESS_CODE == this.code;
    }

    public boolean isError() {
        return SUCCESS_CODE != this.code;
    }
}