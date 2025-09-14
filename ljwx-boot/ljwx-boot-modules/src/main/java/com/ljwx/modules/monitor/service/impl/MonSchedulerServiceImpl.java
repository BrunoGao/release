package com.ljwx.modules.monitor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.common.exception.BizException;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.holder.GlobalUserHolder;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.util.GsonUtil;
import com.ljwx.common.domain.KVPairs;
import com.ljwx.modules.monitor.domain.bo.MonSchedulerBO;
import com.ljwx.modules.monitor.domain.entity.MonScheduler;
import com.ljwx.modules.monitor.repository.mapper.MonSchedulerMapper;
import com.ljwx.modules.monitor.scheduler.util.SchedulerSetupUtil;
import com.ljwx.modules.monitor.service.IMonSchedulerService;
import com.ljwx.quartz.domain.SchedulerSetup;
import com.ljwx.quartz.service.ISchedulerService;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import jakarta.annotation.Resource;
import org.apache.commons.lang3.ObjectUtils;
import org.quartz.JobKey;
import org.quartz.Trigger;
import org.quartz.TriggerKey;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import lombok.extern.slf4j.Slf4j;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 调度任务 Service 服务实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.monitor.service.impl.MonSchedulerServiceImpl
 * @CreateTime 2024/5/18 - 18:21
 */

@Slf4j
@Service
public class MonSchedulerServiceImpl extends ServiceImpl<MonSchedulerMapper, MonScheduler> implements IMonSchedulerService {

    @Resource
    private MonSchedulerMapper monSchedulerMapper;

    @Resource
    @Qualifier("schedulerService")
    private ISchedulerService schedulerService;

    @Override
    public IPage<MonSchedulerBO> listMonSchedulerBOPage(PageQuery pageQuery, MonSchedulerBO monSchedulerBO) {
        IPage<MonSchedulerBO> iPage = pageQuery.buildPage();
        List<MonSchedulerBO> monSchedulerBOS = monSchedulerMapper.listMonSchedulerPage(iPage, monSchedulerBO);
        return iPage.setRecords(monSchedulerBOS);
    }

    @Override
    public MonSchedulerBO queryById(Long id) {
        return monSchedulerMapper.queryById(id);
    }

    @Override
    public boolean addMonScheduler(MonSchedulerBO monSchedulerBO) {
        // 查询任务
        LambdaQueryWrapper<MonScheduler> jobEq = new LambdaQueryWrapper<MonScheduler>()
                .eq(MonScheduler::getJobName, monSchedulerBO.getJobName())
                .eq(MonScheduler::getJobGroup, monSchedulerBO.getJobGroup());
        MonScheduler job = super.getOne(jobEq);
        // 查询触发器
        LambdaQueryWrapper<MonScheduler> triggerEq = new LambdaQueryWrapper<MonScheduler>()
                .eq(MonScheduler::getTriggerName, monSchedulerBO.getTriggerName())
                .eq(MonScheduler::getTriggerGroup, monSchedulerBO.getTriggerGroup());
        MonScheduler trigger = super.getOne(triggerEq);
        if (ObjectUtils.anyNotNull(job, trigger)) {
            throw new BizException("已存在相同名称的任务或触发器，请核实。");
        }
        SchedulerSetup schedulerSetup = SchedulerSetupUtil.convert(monSchedulerBO);
        boolean added = schedulerService.add(schedulerSetup);
        if (added) {
            // 添加到自建表中进行ID管理
            MonScheduler scheduler = CglibUtil.convertObj(monSchedulerBO, MonScheduler::new);
            super.save(scheduler);
        }
        return added;
    }

    @Override
    public boolean updateMonScheduler(MonSchedulerBO monSchedulerBO) {
        SchedulerSetup schedulerSetup = SchedulerSetupUtil.convert(monSchedulerBO);
        boolean updated = schedulerService.update(schedulerSetup);
        if (updated) {
            LambdaUpdateWrapper<MonScheduler> updateWrapper = new LambdaUpdateWrapper<MonScheduler>()
                    .set(MonScheduler::getUpdateUserId, GlobalUserHolder.getUserId())
                    .set(MonScheduler::getUpdateUser, GlobalUserHolder.getUserName())
                    .set(MonScheduler::getUpdateTime, LocalDateTime.now())
                    .set(MonScheduler::getJobData, GsonUtil.toJson(monSchedulerBO.getJobData()))
                    .set(MonScheduler::getTriggerData, GsonUtil.toJson(monSchedulerBO.getTriggerData()))
                    .eq(MonScheduler::getId, monSchedulerBO.getId());
            super.update(updateWrapper);
        }
        return updated;
    }

    @Override
    public boolean batchDeleteMonScheduler(List<Long> ids) {
        List<MonScheduler> monSchedulers = baseMapper.selectBatchIds(ids);
        // 进行安全删除
        boolean allDeleted = monSchedulers.stream()
                .allMatch(item -> schedulerService.delete(new JobKey(item.getJobName(), item.getJobGroup()),
                        new TriggerKey(item.getTriggerName(), item.getTriggerGroup())));
        // 删除数据库数据
        if (allDeleted) {
            super.removeBatchByIds(ids, true);
        }
        return allDeleted;
    }

    @Override
    public boolean immediateMonScheduler(Long id) {
        // 使用Mapper直接查询以确保TypeHandler正确工作
        MonScheduler monScheduler = monSchedulerMapper.selectById(id);
        
        // 如果TypeHandler没有正确工作，手动从数据库查询JSON数据
        if (monScheduler.getJobData() == null || monScheduler.getTriggerData() == null) {
            log.warn("TypeHandler未正确工作，尝试手动查询JSON数据");
            monScheduler = loadSchedulerWithManualJson(id);
        }
        
        try {
            // 直接尝试执行Job
            schedulerService.immediate(monScheduler.getJobName(), monScheduler.getJobGroup());
        } catch (com.ljwx.quartz.exception.SchedulerServiceException sse) {
            // 专门处理 SchedulerServiceException
            log.warn("调度服务异常: {}", sse.getMessage());
            log.debug("SchedulerServiceException详细信息: ", sse);
            
            // 检查是否是Job不存在的问题
            boolean isJobNotExist = sse.getMessage() != null && 
                (sse.getMessage().contains("does not exist") || 
                 sse.getMessage().contains("referenced by the trigger does not exist"));
            
            // 也检查根本原因
            if (!isJobNotExist && sse.getCause() != null && sse.getCause().getMessage() != null) {
                isJobNotExist = sse.getCause().getMessage().contains("does not exist") || 
                              sse.getCause().getMessage().contains("referenced by the trigger does not exist");
            }
            
            if (isJobNotExist) {
                log.info("检测到Job不存在，正在尝试动态注册: {}.{}", monScheduler.getJobGroup(), monScheduler.getJobName());
                handleJobNotExistException(monScheduler);
            } else {
                // 其他类型的调度异常，根据具体情况提供友好的错误信息
                String friendlyMessage = buildFriendlyErrorMessage(sse);
                throw new BizException(friendlyMessage);
            }
        } catch (Exception e) {
            // 处理其他类型的异常
            log.error("Job执行失败，异常详情: {}", e.getMessage(), e);
            log.error("异常类型: {}", e.getClass().getSimpleName());
            if (e.getCause() != null) {
                log.error("根本原因: {}, 类型: {}", e.getCause().getMessage(), e.getCause().getClass().getSimpleName());
            }
            
            // 对于其他异常，也检查是否为Job不存在的问题
            boolean shouldRegisterJob = e.getMessage() != null && 
                (e.getMessage().contains("does not exist") || 
                 e.getMessage().contains("referenced by the trigger does not exist"));
            
            // 也检查根本原因
            if (!shouldRegisterJob && e.getCause() != null && e.getCause().getMessage() != null) {
                shouldRegisterJob = e.getCause().getMessage().contains("does not exist") || 
                                  e.getCause().getMessage().contains("referenced by the trigger does not exist");
            }
            
            if (shouldRegisterJob) {
                log.info("检测到Job不存在，正在尝试动态注册: {}.{}", monScheduler.getJobGroup(), monScheduler.getJobName());
                handleJobNotExistException(monScheduler);
            } else {
                log.error("Job执行失败: {}", e.getMessage(), e);
                throw new BizException("Job执行失败: " + e.getMessage());
            }
        }
        
        return true;
    }
    
    /**
     * 处理Job不存在的异常，尝试动态注册并执行Job
     */
    private void handleJobNotExistException(MonScheduler monScheduler) {
        try {
            log.info("步骤1: 准备创建MonSchedulerBO");
            // 从MonScheduler创建MonSchedulerBO并注册Job
            MonSchedulerBO schedulerBO = createMonSchedulerBO(monScheduler);
            log.info("步骤2: MonSchedulerBO创建成功");
            SchedulerSetup schedulerSetup = SchedulerSetupUtil.convert(schedulerBO);
            
            // 添加Job到Quartz调度器
            schedulerService.add(schedulerSetup);
            log.info("步骤3: Job成功注册到调度器");
            
            // 重新尝试执行
            schedulerService.immediate(monScheduler.getJobName(), monScheduler.getJobGroup());
            log.info("步骤4: Job执行成功");
        } catch (com.ljwx.quartz.exception.SchedulerServiceException sse) {
            log.error("Job注册或执行失败 (SchedulerServiceException): {}", sse.getMessage(), sse);
            throw new BizException("调度任务注册或执行失败: " + sse.getMessage());
        } catch (Exception registerException) {
            log.error("Job注册和执行失败: {}", registerException.getMessage(), registerException);
            throw new BizException("Job注册和执行失败: " + registerException.getMessage());
        }
    }
    
    /**
     * 构建用户友好的错误信息
     */
    private String buildFriendlyErrorMessage(com.ljwx.quartz.exception.SchedulerServiceException sse) {
        String originalMessage = sse.getMessage();
        
        // 根据常见的错误类型提供友好的错误信息
        if (originalMessage != null) {
            if (originalMessage.contains("Failed to immediate job") && originalMessage.contains("does not exist")) {
                return "调度任务不存在，请检查任务配置是否正确";
            } else if (originalMessage.contains("Failed to pause")) {
                return "暂停调度任务失败，任务可能不存在或已处于暂停状态";
            } else if (originalMessage.contains("Failed to resume")) {
                return "恢复调度任务失败，任务可能不存在或已处于运行状态";
            } else if (originalMessage.contains("Failed to delete")) {
                return "删除调度任务失败，任务可能不存在";
            } else if (originalMessage.contains("Failed to add")) {
                return "添加调度任务失败，任务配置可能有误";
            } else if (originalMessage.contains("Failed to update")) {
                return "更新调度任务失败，请检查任务配置";
            }
        }
        
        // 如果没有匹配的模式，返回通用的友好信息
        return "调度任务执行失败: " + (originalMessage != null ? originalMessage : "未知错误");
    }
    
    /**
     * 从MonScheduler创建MonSchedulerBO
     */
    private MonSchedulerBO createMonSchedulerBO(MonScheduler monScheduler) {
        log.info("开始创建MonSchedulerBO, 调度任务: id={}, jobName={}, jobGroup={}", 
            monScheduler.getId(), monScheduler.getJobName(), monScheduler.getJobGroup());
        
        // 详细调试jobData和triggerData
        log.info("jobData类型: {}, 值: {}", 
            monScheduler.getJobData() == null ? "null" : monScheduler.getJobData().getClass().getSimpleName(),
            monScheduler.getJobData());
        log.info("triggerData类型: {}, 值: {}", 
            monScheduler.getTriggerData() == null ? "null" : monScheduler.getTriggerData().getClass().getSimpleName(),
            monScheduler.getTriggerData());
            
        // 检查jobData和triggerData是否为null
        if (monScheduler.getJobData() == null || monScheduler.getTriggerData() == null) {
            log.error("MonScheduler配置数据不完整: jobData={}, triggerData={}", 
                monScheduler.getJobData(), monScheduler.getTriggerData());
            throw new BizException("调度任务配置数据不完整，请检查数据库中的job_data和trigger_data字段");
        }
        
        // 从jobData中提取jobClass
        String jobClassName = monScheduler.getJobData().stream()
                .filter(kv -> "jobClass".equals(kv.getKey()))
                .map(KVPairs::getValue)
                .findFirst()
                .orElseThrow(() -> new BizException("Job配置中缺少jobClass参数"));
        
        // 从jobData中提取description
        String description = monScheduler.getJobData().stream()
                .filter(kv -> "description".equals(kv.getKey()))
                .map(KVPairs::getValue)
                .findFirst()
                .orElse("");
        
        // 从triggerData中提取cronExpression
        String cronExpression = monScheduler.getTriggerData().stream()
                .filter(kv -> "cronExpression".equals(kv.getKey()))
                .map(KVPairs::getValue)
                .findFirst()
                .orElseThrow(() -> new BizException("触发器配置中缺少cronExpression参数"));
        
        // 从triggerData中提取triggerDescription
        String triggerDescription = monScheduler.getTriggerData().stream()
                .filter(kv -> "description".equals(kv.getKey()))
                .map(KVPairs::getValue)
                .findFirst()
                .orElse("");
        
        return MonSchedulerBO.builder()
                .id(monScheduler.getId())
                .jobName(monScheduler.getJobName())
                .jobGroup(monScheduler.getJobGroup())
                .jobClassName(jobClassName)
                .description(description)
                .jobData(monScheduler.getJobData())
                .triggerName(monScheduler.getTriggerName())
                .triggerGroup(monScheduler.getTriggerGroup())
                .triggerDescription(triggerDescription)
                .triggerData(monScheduler.getTriggerData())
                .cronExpression(cronExpression)
                .build();
    }
    
    /**
     * 手动从数据库查询JSON数据并解析
     */
    private MonScheduler loadSchedulerWithManualJson(Long id) {
        try {
            // 先获取基本信息
            MonScheduler scheduler = baseMapper.selectById(id);
            
            // 直接从数据库查询JSON字符串
            List<Map<String, Object>> rawDataList = baseMapper.selectMaps(
                new LambdaQueryWrapper<MonScheduler>()
                    .eq(MonScheduler::getId, id)
            );
            
            if (rawDataList.isEmpty()) {
                throw new BizException("调度任务不存在: " + id);
            }
            
            Map<String, Object> rawData = rawDataList.get(0);
            String jobDataJson = (String) rawData.get("job_data");
            String triggerDataJson = (String) rawData.get("trigger_data");
            
            log.info("手动查询JSON: jobDataJson={}, triggerDataJson={}", jobDataJson, triggerDataJson);
            
            // 手动解析JSON
            Gson gson = new Gson();
            if (jobDataJson != null && !jobDataJson.isEmpty()) {
                List<KVPairs> jobData = gson.fromJson(jobDataJson, new TypeToken<List<KVPairs>>(){}.getType());
                scheduler.setJobData(jobData);
                log.info("jobData解析成功，包含{}个配置项", jobData.size());
            }
            if (triggerDataJson != null && !triggerDataJson.isEmpty()) {
                List<KVPairs> triggerData = gson.fromJson(triggerDataJson, new TypeToken<List<KVPairs>>(){}.getType());
                scheduler.setTriggerData(triggerData);
                log.info("triggerData解析成功，包含{}个配置项", triggerData.size());
            }
            
            return scheduler;
            
        } catch (Exception e) {
            log.error("手动解析JSON失败", e);
            throw new BizException("无法解析调度任务配置数据: " + e.getMessage());
        }
    }

    @Override
    public boolean pauseMonScheduler(Long id) {
        MonScheduler monScheduler = super.getById(id);
        // 暂停任务，实际上是暂停触发器
        schedulerService.pauseTrigger(monScheduler.getTriggerName(), monScheduler.getTriggerGroup());
        return schedulerService.checkState(monScheduler.getTriggerName(), monScheduler.getTriggerGroup(), Trigger.TriggerState.PAUSED);
    }

    @Override
    public boolean pauseMonSchedulerGroup(Long id) {
        MonScheduler monScheduler = super.getById(id);
        // 按组暂停任务，实际上是暂停触发器组
        schedulerService.pauseTriggerGroup(monScheduler.getTriggerGroup());
        return schedulerService.checkStateGroup(monScheduler.getTriggerGroup(), Trigger.TriggerState.PAUSED);
    }

    @Override
    public boolean resumeMonScheduler(Long id) {
        MonScheduler monScheduler = super.getById(id);
        // 恢复任务，实际上是恢复触发器
        schedulerService.resumeTrigger(monScheduler.getTriggerName(), monScheduler.getTriggerGroup());
        return schedulerService.checkState(monScheduler.getTriggerName(), monScheduler.getTriggerGroup());
    }

    @Override
    public boolean resumeMonSchedulerGroup(Long id) {
        MonScheduler monScheduler = super.getById(id);
        // 按组恢复任务，实际上是恢复触发器
        schedulerService.resumeTriggerGroup(monScheduler.getTriggerGroup());
        // 查看触发器组状态是不是属于正常状态
        return schedulerService.checkStateGroup(monScheduler.getTriggerGroup());
    }

    @Override
    public List<MonScheduler> getAllMonSchedulerJobName() {
        LambdaQueryWrapper<MonScheduler> queryWrapper = new LambdaQueryWrapper<MonScheduler>()
                .select(MonScheduler::getJobName)
                .orderByDesc(MonScheduler::getCreateTime);
        return baseMapper.selectList(queryWrapper);
    }
}
