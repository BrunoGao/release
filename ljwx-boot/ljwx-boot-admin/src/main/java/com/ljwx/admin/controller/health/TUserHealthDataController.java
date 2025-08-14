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

package com.ljwx.admin.controller.health;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataAddDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataDeleteDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataSearchDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataUpdateDTO;
import com.ljwx.modules.health.domain.vo.TUserHealthDataVO;
import com.ljwx.modules.health.domain.vo.HealthDataPageVO;
import com.ljwx.modules.health.facade.ITUserHealthDataFacade;
import com.ljwx.modules.health.service.ITUserHealthDataService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.format.DateTimeParseException;
import java.util.Map;
import java.util.HashMap;
/**
 *  Controller 控制层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName health.controller.com.ljwx.admin.TUserHealthDataController
 * @CreateTime 2024-12-15 - 22:04:51
 */
@Slf4j
@RestController
@Tag(name = "")
@RequiredArgsConstructor
@RequestMapping("t_user_health_data")
public class TUserHealthDataController {

    @NonNull
    private ITUserHealthDataFacade tUserHealthDataFacade;

    @NonNull
    private ITUserHealthDataService tUserHealthDataService;

    

    @Operation(summary = "获取用户健康信息")
    @GetMapping(value = "/getUserHealthData")
    public HttpEntity<Object> getUserHealthData(@RequestParam("departmentInfo") String departmentInfo,
                                                @RequestParam("userName") String userName,
                                                @RequestParam("startDate") Long startDateStr,
                                                @RequestParam("endDate") Long endDateStr,
                                                @RequestParam("timeType") String timeType) {
        try {
           LocalDateTime startDateTime = Instant.ofEpochMilli(startDateStr)
                                              .atZone(ZoneId.systemDefault())
                                              .toLocalDateTime();
        LocalDateTime endDateTime = Instant.ofEpochMilli(endDateStr)
                                            .atZone(ZoneId.systemDefault())
                                            .toLocalDateTime();

        // Step 2: Adjust startDateTime to start of day and endDateTime to end of day
        LocalDateTime adjustedStartDateTime = startDateTime.toLocalDate().atStartOfDay();
        LocalDateTime adjustedEndDateTime = endDateTime.toLocalDate().atTime(LocalTime.MAX);

        // Step 3: Log or verify conversion (optional)
        System.out.println("Adjusted Start DateTime: " + adjustedStartDateTime);
        System.out.println("Adjusted End DateTime: " + adjustedEndDateTime);

            // Pass the new parameters to the service method
            return tUserHealthDataService.getUserHealthData(departmentInfo, userName, adjustedStartDateTime, adjustedEndDateTime, timeType);

        } catch (DateTimeParseException e) {
            log.error("Error parsing dates: startDate={}, endDate={}, exception={}", startDateStr, endDateStr, e.getMessage(), e);
            return new ResponseEntity<>("Invalid date format", HttpStatus.BAD_REQUEST);
        } catch (Exception e) {
            log.error("Unexpected error: startDate={}, endDate={}, exception={}", startDateStr, endDateStr, e);
            return new ResponseEntity<>("An error occurred", HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping("/page")
    @SaCheckPermission("t:user:health:data:page")
    @Operation(operationId = "1", summary = "获取列表")
    public Result<Map<String,Object>> page(PageQuery pageQuery, TUserHealthDataSearchDTO dto) {
        HealthDataPageVO<Map<String,Object>> vo = tUserHealthDataFacade.listTUserHealthDataPage(pageQuery, dto);
        Map<String,Object> data = new HashMap<>();
        data.put("page", vo.getCurrent());
        data.put("pageSize", vo.getSize());
        data.put("pages", vo.getTotal() == 0 ? 0 : (int)Math.ceil((double)vo.getTotal()/vo.getSize()));
        data.put("total", vo.getTotal());
        data.put("records", vo.getRecords());
        data.put("columns", vo.getColumns());
        return Result.data(data);
    }

    @GetMapping("/{id}")
    //@SaCheckPermission("t:user:health:data:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<TUserHealthDataVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tUserHealthDataFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:user:health:data:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TUserHealthDataAddDTO tUserHealthDataAddDTO) {
        return Result.status(tUserHealthDataFacade.add(tUserHealthDataAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:user:health:data:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TUserHealthDataUpdateDTO tUserHealthDataUpdateDTO) {
        return Result.status(tUserHealthDataFacade.update(tUserHealthDataUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:user:health:data:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TUserHealthDataDeleteDTO tUserHealthDataDeleteDTO) {
        return Result.status(tUserHealthDataFacade.batchDelete(tUserHealthDataDeleteDTO));
    }

}