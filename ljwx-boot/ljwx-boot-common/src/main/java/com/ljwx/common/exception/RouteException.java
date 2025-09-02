package com.ljwx.common.exception;

import lombok.Getter;
import lombok.Setter;

import java.io.Serial;

/**
 * 用户路由异常
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName exception.com.ljwx.common.RouteException
 * @CreateTime 2024/4/20 - 22:25
 */

@Getter
@Setter
public class RouteException extends RuntimeException {

    @Serial
    private static final long serialVersionUID = -4901070393720426967L;

    /**
     * 错误码
     */
    private final int code;

    /**
     * 错误信息
     */
    private final String msg;

    public RouteException(int code, String msg) {
        super(msg);
        this.code = code;
        this.msg = msg;
    }

}
