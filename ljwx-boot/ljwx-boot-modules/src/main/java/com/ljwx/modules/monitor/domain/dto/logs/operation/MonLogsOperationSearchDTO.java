package com.ljwx.modules.monitor.domain.dto.logs.operation;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

import java.io.Serial;
import java.io.Serializable;

/**
 * 操作日志 查询 DTO 对象
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName MonLogsOperationSearchDTO
 * @CreateTime 2024-05-07
 */

@Getter
@Setter
@Schema(name = "MonLogsOperationSearchDTO", description = "操作日志 查询 DTO 对象")
public class MonLogsOperationSearchDTO implements Serializable {

    @Serial
    private static final long serialVersionUID = -4381792986609980335L;
}