package com.ljwx.modules.monitor.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.monitor.domain.bo.MonLogsSchedulerBO;
import com.ljwx.modules.monitor.domain.dto.logs.scheduler.MonLogsSchedulerAddDTO;
import com.ljwx.modules.monitor.domain.dto.logs.scheduler.MonLogsSchedulerDeleteDTO;
import com.ljwx.modules.monitor.domain.dto.logs.scheduler.MonLogsSchedulerSearchDTO;
import com.ljwx.modules.monitor.domain.dto.logs.scheduler.MonLogsSchedulerUpdateDTO;
import com.ljwx.modules.monitor.domain.entity.MonLogsScheduler;
import com.ljwx.modules.monitor.domain.vo.MonLogsSchedulerVO;
import com.ljwx.modules.monitor.facade.IMonLogsSchedulerFacade;
import com.ljwx.modules.monitor.service.IMonLogsSchedulerService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

/**
 * 调度日志 门面接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName MonLogsSchedulerFacadeImpl
 * @CreateTime 2024-05-30
 */

@Service
@RequiredArgsConstructor
public class MonLogsSchedulerFacadeImpl implements IMonLogsSchedulerFacade {

    @NonNull
    private IMonLogsSchedulerService monLogsSchedulerService;

    @Override
    public RPage<MonLogsSchedulerVO> listMonLogsSchedulerPage(PageQuery pageQuery, MonLogsSchedulerSearchDTO monLogsSchedulerSearchDTO) {
        MonLogsSchedulerBO monLogsSchedulerBO = CglibUtil.convertObj(monLogsSchedulerSearchDTO, MonLogsSchedulerBO::new);
        IPage<MonLogsScheduler> monLogsSchedulerIPage = monLogsSchedulerService.listMonLogsSchedulerPage(pageQuery, monLogsSchedulerBO);
        return RPage.build(monLogsSchedulerIPage, MonLogsSchedulerVO::new);
    }

    @Override
    public MonLogsSchedulerVO get(Long id) {
        MonLogsScheduler byId = monLogsSchedulerService.getById(id);
        return CglibUtil.convertObj(byId, MonLogsSchedulerVO::new);
    }

    @Override
    public boolean add(MonLogsSchedulerAddDTO monLogsSchedulerAddDTO) {
        MonLogsSchedulerBO monLogsSchedulerBO = CglibUtil.convertObj(monLogsSchedulerAddDTO, MonLogsSchedulerBO::new);
        return monLogsSchedulerService.save(monLogsSchedulerBO);
    }

    @Override
    public boolean update(MonLogsSchedulerUpdateDTO monLogsSchedulerUpdateDTO) {
        MonLogsSchedulerBO monLogsSchedulerBO = CglibUtil.convertObj(monLogsSchedulerUpdateDTO, MonLogsSchedulerBO::new);
        return monLogsSchedulerService.updateById(monLogsSchedulerBO);
    }

    @Override
    public boolean batchDelete(MonLogsSchedulerDeleteDTO monLogsSchedulerDeleteDTO) {
        MonLogsSchedulerBO monLogsSchedulerBO = CglibUtil.convertObj(monLogsSchedulerDeleteDTO, MonLogsSchedulerBO::new);
        return monLogsSchedulerService.removeBatchByIds(monLogsSchedulerBO.getIds(), true);
    }

}