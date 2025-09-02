/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
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

package com.ljwx.modules.health.facade;

import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.dto.device.config.TDeviceConfigAddDTO;
import com.ljwx.modules.health.domain.dto.device.config.TDeviceConfigDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.config.TDeviceConfigSearchDTO;
import com.ljwx.modules.health.domain.dto.device.config.TDeviceConfigUpdateDTO;
import com.ljwx.modules.health.domain.vo.TDeviceConfigVO;

/**
 *  门面接口层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.ITDeviceConfigFacade
 * @CreateTime 2024-10-21 - 19:44:31
 */

public interface ITDeviceConfigFacade {

    /**
     *  - 分页查询
     *
     * @param pageQuery        分页对象
     * @param tDeviceConfigSearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2024-10-21 - 19:44:31
     */
    RPage<TDeviceConfigVO> listTDeviceConfigPage(PageQuery pageQuery, TDeviceConfigSearchDTO tDeviceConfigSearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id ID
     * @return {@link TDeviceConfigVO}  VO 对象
     * @author payne.zhuang
     * @CreateTime 2024-10-21 - 19:44:31
     */
    TDeviceConfigVO get(Long id);

    /**
     * 新增
     *
     * @param tDeviceConfigAddDTO 新增 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-10-21 - 19:44:31
     */
    boolean add(TDeviceConfigAddDTO tDeviceConfigAddDTO);

    /**
     * 编辑更新信息
     *
     * @param tDeviceConfigUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-10-21 - 19:44:31
     */
    boolean update(TDeviceConfigUpdateDTO tDeviceConfigUpdateDTO);

    /**
     * 批量删除信息
     *
     * @param tDeviceConfigDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2024-10-21 - 19:44:31
     */
    boolean batchDelete(TDeviceConfigDeleteDTO tDeviceConfigDeleteDTO);

}