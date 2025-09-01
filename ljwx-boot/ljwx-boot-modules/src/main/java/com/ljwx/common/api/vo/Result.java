package com.ljwx.common.api.vo;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;

import java.io.Serializable;

/**
 * 通用API响应结果类
 */
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Result<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    private static final int SUCCESS_CODE = 200;
    private static final int ERROR_CODE = 500;
    private static final String SUCCESS_MSG = "操作成功";
    private static final String ERROR_MSG = "操作失败";

    private int code;
    private String message;
    private T result;
    private Long timestamp;

    public Result() {
        this.timestamp = System.currentTimeMillis();
    }

    public Result(int code, String message) {
        this();
        this.code = code;
        this.message = message;
    }

    public Result(int code, String message, T result) {
        this();
        this.code = code;
        this.message = message;
        this.result = result;
    }

    public static <T> Result<T> ok() {
        return new Result<>(SUCCESS_CODE, SUCCESS_MSG);
    }

    public static <T> Result<T> ok(String message) {
        return new Result<>(SUCCESS_CODE, message);
    }

    public static <T> Result<T> ok(T result) {
        return new Result<>(SUCCESS_CODE, SUCCESS_MSG, result);
    }

    public static <T> Result<T> ok(String message, T result) {
        return new Result<>(SUCCESS_CODE, message, result);
    }

    public static <T> Result<T> error() {
        return new Result<>(ERROR_CODE, ERROR_MSG);
    }

    public static <T> Result<T> error(String message) {
        return new Result<>(ERROR_CODE, message);
    }

    public static <T> Result<T> error(int code, String message) {
        return new Result<>(code, message);
    }

    public static <T> Result<T> error(int code, String message, T result) {
        return new Result<>(code, message, result);
    }

    public boolean isSuccess() {
        return SUCCESS_CODE == this.code;
    }

    public boolean isError() {
        return SUCCESS_CODE != this.code;
    }
}