package com.ljwx.modules.geofence.util;

/**
 * @author brunoGao
 * @version $ v 0.1 2025/1/7 20:14 Exp $$
 */

import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;

import java.sql.*;

public class GeoJsonTypeHandler extends BaseTypeHandler<String> {

    public GeoJsonTypeHandler() {
    }

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, String parameter, JdbcType jdbcType) throws SQLException {
        ps.setString(i, parameter); // 如果需要插入数据，传递 GeoJSON 字符串
    }

    @Override
    public String getNullableResult(ResultSet rs, String columnName) throws SQLException {
        String result = rs.getString(columnName);
        return result; // 从数据库读取 GeoJSON 数据
    }

    @Override
    public String getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        String result = rs.getString(columnIndex);
        return result; // 从数据库读取 GeoJSON 数据
    }

    @Override
    public String getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        String result = cs.getString(columnIndex);
        return result; // 从数据库读取 GeoJSON 数据
    }
}