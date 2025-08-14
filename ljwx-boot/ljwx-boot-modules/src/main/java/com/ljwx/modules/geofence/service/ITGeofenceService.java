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

package com.ljwx.modules.geofence.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.geofence.domain.bo.TGeofenceBO;
import com.ljwx.modules.geofence.domain.entity.TGeofence;

/**
 *  Service 服务接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.geofence.service.ITGeofenceService
 * @CreateTime 2025-01-07 - 19:44:06
 */

public interface ITGeofenceService extends IService<TGeofence> {

    /**
     *  - 分页查询
     *
     * @param pageQuery 分页对象
     * @param tGeofenceBO BO 查询对象
     * @return {@link IPage} 分页结果
     * @author payne.zhuang
     * @CreateTime 2025-01-07 - 19:44:06
     */
    IPage<TGeofence> listTGeofencePage(PageQuery pageQuery, TGeofenceBO tGeofenceBO);
}
