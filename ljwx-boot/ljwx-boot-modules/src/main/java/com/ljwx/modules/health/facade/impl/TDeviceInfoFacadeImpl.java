/*
 * All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.modules.health.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.bo.TDeviceInfoBO;
import com.ljwx.modules.health.domain.dto.device.info.TDeviceInfoAddDTO;
import com.ljwx.modules.health.domain.dto.device.info.TDeviceInfoDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.info.TDeviceInfoSearchDTO;
import com.ljwx.modules.health.domain.dto.device.info.TDeviceInfoUpdateDTO;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.ljwx.modules.health.domain.vo.TDeviceInfoVO;
import com.ljwx.modules.health.facade.ITDeviceInfoFacade;
import com.ljwx.modules.health.service.ITDeviceInfoService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TDeviceInfoFacadeImpl
 * @CreateTime 2024-12-14 - 21:31:16
 */

@Service
@RequiredArgsConstructor
public class TDeviceInfoFacadeImpl implements ITDeviceInfoFacade {

    @NonNull
    private ITDeviceInfoService tDeviceInfoService;

    @Override
    public RPage<TDeviceInfoVO> listTDeviceInfoPage(PageQuery pageQuery, TDeviceInfoSearchDTO tDeviceInfoSearchDTO) {
       TDeviceInfoBO tDeviceInfoBO = CglibUtil.convertObj(tDeviceInfoSearchDTO, TDeviceInfoBO::new);
       // #确保userId正确转换为userIdStr字段
       tDeviceInfoBO.setUserIdStr(tDeviceInfoSearchDTO.getUserId());
       
       // #处理前端参数映射: orgId -> departmentInfo
       String departmentInfo = tDeviceInfoSearchDTO.getDepartmentInfo();
       if (departmentInfo == null && tDeviceInfoSearchDTO.getOrgId() != null) {
           departmentInfo = tDeviceInfoSearchDTO.getOrgId();
       }
       tDeviceInfoBO.setDepartmentInfo(departmentInfo);
       
       System.out.println("🔄 参数转换 - userId: " + tDeviceInfoSearchDTO.getUserId() + " -> userIdStr: " + tDeviceInfoBO.getUserIdStr());
       System.out.println("🔄 参数转换 - orgId: " + tDeviceInfoSearchDTO.getOrgId() + ", departmentInfo: " + tDeviceInfoSearchDTO.getDepartmentInfo() + " -> " + departmentInfo);
        IPage<TDeviceInfo> tDeviceInfoIPage = tDeviceInfoService.listTDeviceInfoPage(pageQuery, tDeviceInfoBO);
        return RPage.build(tDeviceInfoIPage, TDeviceInfoVO::new);
    }

    @Override
    public TDeviceInfoVO get(Long id) {
        TDeviceInfo byId = tDeviceInfoService.getById(id);
        return CglibUtil.convertObj(byId, TDeviceInfoVO::new);
    }

    @Override
    @Transactional
    public boolean add(TDeviceInfoAddDTO tDeviceInfoAddDTO) {
        TDeviceInfoBO tDeviceInfoBO = CglibUtil.convertObj(tDeviceInfoAddDTO, TDeviceInfoBO::new);
        return tDeviceInfoService.save(tDeviceInfoBO);
    }

    @Override
    @Transactional
    public boolean update(TDeviceInfoUpdateDTO tDeviceInfoUpdateDTO) {
        TDeviceInfoBO tDeviceInfoBO = CglibUtil.convertObj(tDeviceInfoUpdateDTO, TDeviceInfoBO::new);
        return tDeviceInfoService.updateById(tDeviceInfoBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TDeviceInfoDeleteDTO tDeviceInfoDeleteDTO) {
        TDeviceInfoBO tDeviceInfoBO = CglibUtil.convertObj(tDeviceInfoDeleteDTO, TDeviceInfoBO::new);
        return tDeviceInfoService.removeBatchByIds(tDeviceInfoBO.getIds(), true);
    }

}