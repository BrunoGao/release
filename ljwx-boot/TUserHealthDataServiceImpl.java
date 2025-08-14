import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class TUserHealthDataServiceImpl {
    private static final ObjectMapper M = new ObjectMapper();

    private Map sleepMap(String s) {
        try {
            var l = org.springframework.util.StringUtils.hasText(s) ? M.readValue(s, List.class) : new ArrayList<>();
            double total = 0, light = 0, deep = 0;
            for (var o : (List<Map>) l) {
                double h = (o.get("endTimeStamp") == null || o.get("startTimeStamp") == null) ? 0 : (Long.valueOf(o.get("endTimeStamp").toString()) - Long.valueOf(o.get("startTimeStamp").toString())) / 3600000.0;
                total += h;
                if (o.get("type") != null && o.get("type").toString().equals("2")) deep += h; else light += h;
            }
            return Map.of("value", String.format("%.1f", total), "tooltip", "浅度睡眠：" + String.format("%.1f", light) + "小时；深度睡眠：" + String.format("%.1f", deep) + "小时");
        } catch (Exception e) {
            return Map.of("value", "0", "tooltip", "无数据");
        }
    }

    // 组装VO时
    vo.sleepData = sleepMap(data.sleep);
} 