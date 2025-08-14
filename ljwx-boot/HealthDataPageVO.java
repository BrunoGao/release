import lombok.Data;
import java.util.List;

@Data
public class HealthDataPageVO<T> {
    private List<T> records;
    private long total, size, current;
    private List<?> columns;

    public HealthDataPageVO(List<T> records, long total, long size, long current, List<?> columns) {
        this.records = records;
        this.total = total;
        this.size = size;
        this.current = current;
        this.columns = columns;
    }
}