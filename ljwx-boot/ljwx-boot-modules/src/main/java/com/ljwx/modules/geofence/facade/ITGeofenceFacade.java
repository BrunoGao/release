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

package com.ljwx.modules.geofence.facade;

import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceAddDTO;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceDeleteDTO;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceSearchDTO;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceUpdateDTO;
import com.ljwx.modules.geofence.domain.vo.TGeofenceVO;

/**
 *  门面接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.geofence.facade.ITGeofenceFacade
 * @CreateTime 2025-01-07 - 19:44:06
 */

public interface ITGeofenceFacade {

    /**
     *  - 分页查询
     *
     * @param pageQuery        分页对象
     * @param tGeofenceSearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2025-01-07 - 19:44:06
     */
    RPage<TGeofenceVO> listTGeofencePage(PageQuery pageQuery, TGeofenceSearchDTO tGeofenceSearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id ID
     * @return {@link TGeofenceVO}  VO 对象
     * @author payne.zhuang
     * @CreateTime 2025-01-07 - 19:44:06
     */
    TGeofenceVO get(Long id);

    /**
     * 新增
     *
     * @param tGeofenceAddDTO 新增 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-01-07 - 19:44:06
     */
    boolean add(TGeofenceAddDTO tGeofenceAddDTO);

    /**
     * 编辑更新信息
     *
     * @param tGeofenceUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-01-07 - 19:44:06
     */
    boolean update(TGeofenceUpdateDTO tGeofenceUpdateDTO);

    /**
     * 批量删除信息
     *
     * @param tGeofenceDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-01-07 - 19:44:06
     */
    boolean batchDelete(TGeofenceDeleteDTO tGeofenceDeleteDTO);

}