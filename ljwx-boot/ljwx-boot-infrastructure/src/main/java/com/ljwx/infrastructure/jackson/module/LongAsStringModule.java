package com.ljwx.infrastructure.jackson.module;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.type.WritableTypeId;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.fasterxml.jackson.databind.jsontype.TypeSerializer;
import com.fasterxml.jackson.databind.module.SimpleModule;
import lombok.extern.slf4j.Slf4j;

import java.io.IOException;
import java.io.Serial;

/**
 * Long 大精度类型序列化，避免超过js的精度，造成精度丢失
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName module.jackson.com.ljwx.infrastructure.LongAsStringModule
 * @CreateTime 2023/7/9 - 16:46
 */
@Slf4j
public class LongAsStringModule extends SimpleModule {

    @Serial
    private static final long serialVersionUID = -4168037594159276647L;

    public LongAsStringModule() {
        super();
        // 序列化时，当值为 Long 类型时，转换为字符串类型
        addSerializer(Long.class, new JsonSerializer<>() {
            @Override
            public void serialize(Long value, JsonGenerator gen, SerializerProvider serializers) throws IOException {
                // JavaScript Number.MAX_SAFE_INTEGER = 2^53 - 1 = 9007199254740991
                // 超过这个值就会有精度问题，所以转为字符串
                if (value > 9007199254740991L || value < -9007199254740991L) {
                    log.debug("Long value {} exceeds JavaScript safe integer range, converting to string", value);
                    gen.writeString(value.toString());
                } else {
                    gen.writeNumber(value);
                }
            }

            @Override
            public void serializeWithType(Long value, JsonGenerator gen, SerializerProvider serializers, TypeSerializer typeSer) throws IOException {
                WritableTypeId typeIdDef = typeSer.typeId(value, JsonToken.VALUE_STRING);
                typeSer.writeTypePrefix(gen, typeIdDef);
                serialize(value, gen, serializers);
                typeSer.writeTypeSuffix(gen, typeIdDef);
            }
        });

        // 反序列化时，当值为字符串类型或数值类型时，转换为 Long 类型
        addDeserializer(Long.class, new JsonDeserializer<>() {
            @Override
            public Long deserialize(JsonParser p, DeserializationContext deserializationContext) throws IOException {
                if (p.hasToken(JsonToken.VALUE_STRING)) {
                    // 字符串值，直接解析
                    String value = p.getValueAsString();
                    try {
                        return Long.parseLong(value);
                    } catch (NumberFormatException e) {
                        throw new InvalidFormatException(p, "Invalid numeric value: " + value, value, Long.class);
                    }
                } else if (p.hasToken(JsonToken.VALUE_NUMBER_INT)) {
                    // 整数值，可能有精度问题，优先使用文本形式
                    try {
                        return p.getLongValue();
                    } catch (IOException e) {
                        // 如果精度丢失，尝试从文本获取
                        String numStr = p.getValueAsString();
                        log.warn("Long value precision issue detected, using text representation: {}", numStr);
                        return Long.parseLong(numStr);
                    }
                } else {
                    throw new InvalidFormatException(p, "Cannot deserialize Long from " + p.getCurrentToken(), null, Long.class);
                }
            }
        });
    }
}
