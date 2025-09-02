package com.ljwx.modules.monitor.domain.bo;

import com.ljwx.modules.monitor.domain.entity.MonLogsLogin;
import lombok.Data;

import java.io.Serial;
import java.util.List;

/**
 * 登录日志 BO 业务处理对象
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.monitor.domain.entity.MonLogsLogin
 * @CreateTime 2024-05-05
 */

@Data
public class MonLogsLoginBO extends MonLogsLogin {

    @Serial
    private static final long serialVersionUID = 7129959475004671045L;

    /**
     * Ids
     */
    private List<Long> ids;

}