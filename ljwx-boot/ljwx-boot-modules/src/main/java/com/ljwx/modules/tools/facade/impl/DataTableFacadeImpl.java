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

package com.ljwx.modules.tools.facade.impl;

import com.ljwx.common.pool.StringPools;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.modules.tools.domain.entity.DataTable;
import com.ljwx.modules.tools.domain.vo.DataTableVO;
import com.ljwx.modules.tools.facade.IDataTableFacade;
import com.ljwx.modules.tools.service.IDataTableService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 数据库表管理 门面接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.tools.facade.impl.DataTableFacadeImpl
 * @CreateTime 2024/8/22 - 16:48
 */

@Service
@RequiredArgsConstructor
public class DataTableFacadeImpl implements IDataTableFacade {

    @NonNull
    private IDataTableService dataTableService;

    @Override
    public List<DataTableVO> queryAllDataTables() {
        return queryAllDataTables(StringPools.EMPTY);
    }

    @Override
    public List<DataTableVO> queryAllDataTables(String tableName) {
        List<DataTable> dataTables = dataTableService.queryAllDataTables(tableName);
        return CglibUtil.convertList(dataTables, DataTableVO::new);
    }

}
