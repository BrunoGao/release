package com.ljwx.modules.monitor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.monitor.domain.bo.MonLogsErrorBO;
import com.ljwx.modules.monitor.domain.entity.MonLogsError;
import com.ljwx.modules.monitor.repository.mapper.MonLogsErrorMapper;
import com.ljwx.modules.monitor.service.IMonLogsErrorService;
import org.springframework.stereotype.Service;

/**
 * 错误异常日志 Service 服务接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.monitor.domain.entity.MonLogsError
 * @CreateTime 2024-05-07
 */

@Service
public class MonLogsErrorServiceImpl extends ServiceImpl<MonLogsErrorMapper, MonLogsError> implements IMonLogsErrorService {
    @Override
    public IPage<MonLogsError> listMonLogsErrorPage(PageQuery pageQuery, MonLogsErrorBO monLogsErrorBO) {
        LambdaQueryWrapper<MonLogsError> queryWrapper = new LambdaQueryWrapper<MonLogsError>()
                .orderByDesc(MonLogsError::getCreateTime);
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }
}
