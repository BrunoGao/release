package com.ljwx.modules.monitor.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.monitor.domain.bo.MonLogsOperationBO;
import com.ljwx.modules.monitor.domain.dto.logs.operation.MonLogsOperationAddDTO;
import com.ljwx.modules.monitor.domain.dto.logs.operation.MonLogsOperationDeleteDTO;
import com.ljwx.modules.monitor.domain.dto.logs.operation.MonLogsOperationSearchDTO;
import com.ljwx.modules.monitor.domain.dto.logs.operation.MonLogsOperationUpdateDTO;
import com.ljwx.modules.monitor.domain.entity.MonLogsOperation;
import com.ljwx.modules.monitor.domain.vo.MonLogsOperationVO;
import com.ljwx.modules.monitor.facade.IMonLogsOperationFacade;
import com.ljwx.modules.monitor.service.IMonLogsOperationService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

/**
 * 操作日志 门面接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName MonLogsOperationFacadeImpl
 * @CreateTime 2024-05-07
 */

@Service
@RequiredArgsConstructor
public class MonLogsOperationFacadeImpl implements IMonLogsOperationFacade {

    @NonNull
    private IMonLogsOperationService monLogsOperationService;

    @Override
    public RPage<MonLogsOperationVO> listMonLogsOperationPage(PageQuery pageQuery, MonLogsOperationSearchDTO monLogsOperationSearchDTO) {
        MonLogsOperationBO monLogsOperationBO = CglibUtil.convertObj(monLogsOperationSearchDTO, MonLogsOperationBO::new);
        IPage<MonLogsOperation> monLogsOperationIPage = monLogsOperationService.listMonLogsOperationPage(pageQuery, monLogsOperationBO);
        return RPage.build(monLogsOperationIPage, MonLogsOperationVO::new);
    }

    @Override
    public MonLogsOperationVO get(Long id) {
        MonLogsOperation byId = monLogsOperationService.getById(id);
        return CglibUtil.convertObj(byId, MonLogsOperationVO::new);
    }

    @Override
    public boolean add(MonLogsOperationAddDTO monLogsOperationAddDTO) {
        MonLogsOperationBO monLogsOperationBO = CglibUtil.convertObj(monLogsOperationAddDTO, MonLogsOperationBO::new);
        return monLogsOperationService.save(monLogsOperationBO);
    }

    @Override
    public boolean update(MonLogsOperationUpdateDTO monLogsOperationUpdateDTO) {
        MonLogsOperationBO monLogsOperationBO = CglibUtil.convertObj(monLogsOperationUpdateDTO, MonLogsOperationBO::new);
        return monLogsOperationService.updateById(monLogsOperationBO);
    }

    @Override
    public boolean batchDelete(MonLogsOperationDeleteDTO monLogsOperationDeleteDTO) {
        MonLogsOperationBO monLogsOperationBO = CglibUtil.convertObj(monLogsOperationDeleteDTO, MonLogsOperationBO::new);
        return monLogsOperationService.removeBatchByIds(monLogsOperationBO.getIds(), true);
    }

}