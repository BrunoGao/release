package com.ljwx.watch.scheduler.tasks;

import com.ljwx.watch.HttpService;
import com.ljwx.watch.scheduler.ScheduledTask;
import com.ljwx.watch.scheduler.TaskExecutionInfo;
import com.ljwx.watch.utils.DataManager;
import com.ljwx.watch.utils.DataManagerAdapter;
import ohos.app.Context;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 消息获取任务
 * 负责从服务器获取待处理消息
 */
public class MessageFetchTask extends ScheduledTask {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    private DataManagerAdapter dataManager = DataManagerAdapter.getInstance();

    public MessageFetchTask() {
        // 消息获取为低优先级任务，间隔1分钟
        super("MessageFetch", Priority.LOW, 60, "从服务器获取消息");
    }

    @Override
    protected boolean shouldExecute(Context context, TaskExecutionInfo executionInfo) {
        // 检查基本条件
        if (!super.shouldExecute(context, executionInfo)) {
            return false;
        }

        // 检查WiFi模式
        if (!"wifi".equals(dataManager.getUploadMethod())) {
            HiLog.debug(LABEL_LOG, "MessageFetchTask::shouldExecute 非WiFi模式，跳过消息获取");
            return false;
        }

        // 检查license状态
        if (dataManager.isLicenseExceeded()) {
            HiLog.debug(LABEL_LOG, "MessageFetchTask::shouldExecute License已超出，跳过消息获取");
            return false;
        }

        // 检查消息获取URL配置
        String fetchUrl = dataManager.getFetchMessageUrl();
        if (fetchUrl == null || fetchUrl.isEmpty()) {
            HiLog.debug(LABEL_LOG, "MessageFetchTask::shouldExecute 消息获取URL未配置");
            return false;
        }

        return true;
    }

    @Override
    protected void executeTask(Context context, TaskExecutionInfo executionInfo) {
        try {
            HiLog.info(LABEL_LOG, "MessageFetchTask::executeTask 开始获取服务器消息");

            // 检查context是否为HttpService实例
            if (context instanceof HttpService) {
                HttpService httpService = (HttpService) context;
                
                // 调用HttpService的消息获取方法
                httpService.fetchMessageFromServer();
                
                // 更新执行统计
                executionInfo.recordSuccess();
                HiLog.info(LABEL_LOG, "MessageFetchTask::executeTask 消息获取任务执行成功");
            } else {
                HiLog.error(LABEL_LOG, "MessageFetchTask::executeTask Context不是HttpService实例");
                executionInfo.recordFailure("Context类型错误");
            }

        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "MessageFetchTask::executeTask 执行失败: " + e.getMessage());
            executionInfo.recordFailure("消息获取异常: " + e.getMessage());
        }
    }

    @Override
    protected void onTaskSkipped(String reason) {
        HiLog.debug(LABEL_LOG, "MessageFetchTask::onTaskSkipped 任务跳过: " + reason);
    }

    @Override
    protected void onTaskFailed(String reason) {
        HiLog.warn(LABEL_LOG, "MessageFetchTask::onTaskFailed 任务失败: " + reason);
    }

    @Override
    protected boolean requiresNetwork() {
        return true; // 消息获取需要网络连接
    }

    @Override
    protected boolean requiresWiFi() {
        return true; // 消息获取仅在WiFi模式下执行
    }
}