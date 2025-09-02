package com.ljwx.modules.system.domain.vo;

import lombok.Data;

import java.io.Serial;
import java.util.Map;

/**
 * 用户Map VO 对象
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.vo.SysUserMapVO
 * @CreateTime 2024-03-21 - 10:00:00
 */
@Data
public class SysUserMapVO {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 用户ID和用户名的映射
     */
    private Map<String, String> userMap;
} 