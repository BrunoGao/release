package com.ljwx.modules.monitor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.monitor.domain.bo.MonLogsLoginBO;
import com.ljwx.modules.monitor.domain.entity.MonLogsLogin;
import com.ljwx.modules.monitor.repository.mapper.MonLogsLoginMapper;
import com.ljwx.modules.monitor.service.IMonLogsLoginService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.stereotype.Service;

/**
 * 登录日志 Service 服务接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.monitor.domain.entity.MonLogsLogin
 * @CreateTime 2024-05-05
 */

@Service
public class MonLogsLoginServiceImpl extends ServiceImpl<MonLogsLoginMapper, MonLogsLogin> implements IMonLogsLoginService {
    @Override
    public IPage<MonLogsLogin> listMonLogsLoginPage(PageQuery pageQuery, MonLogsLoginBO loginBO) {
        LambdaQueryWrapper<MonLogsLogin> queryWrapper = new LambdaQueryWrapper<MonLogsLogin>()
                .eq(ObjectUtils.isNotEmpty(loginBO.getUserName()), MonLogsLogin::getUserName, loginBO.getUserName())
                .eq(ObjectUtils.isNotEmpty(loginBO.getUserRealName()), MonLogsLogin::getUserRealName, loginBO.getUserRealName())
                .orderByDesc(MonLogsLogin::getCreateTime);
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

}
