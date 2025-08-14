import re

# 定义需要添加的字段
additional_fields = """
    create_user    varchar(40)   not null comment '创建用户',
    create_user_id bigint        not null comment '创建用户ID',
    create_time    datetime      not null comment '创建时间',
    update_user    varchar(40)   null comment '修改用户',
    update_user_id bigint        null comment '修改用户ID',
    update_time    datetime      null comment '修改时间',
    is_deleted     int default 0 null comment '是否删除(0:否,1:是)'
"""

# 定义正则匹配 CREATE TABLE 语句
table_regex = re.compile(r"(CREATE\s+TABLE\s+.*?\(.*?)(\);)", re.S | re.I)

def add_fields_to_sql(sql_content):
    """
    在 SQL 文件中每个 CREATE TABLE 中添加附加字段
    """
    def replacer(match):
        create_table_statement = match.group(1)  # 原始 CREATE TABLE 部分
        closing = match.group(2)  # 结尾 ");"
        
        # 在字段定义中添加额外字段
        updated_table = f"{create_table_statement},\n{additional_fields}{closing}"
        return updated_table

    # 替换 SQL 文件中所有 CREATE TABLE 语句
    updated_sql = table_regex.sub(replacer, sql_content)
    return updated_sql

# 读取 SQL 文件
input_file = "input.sql"
output_file = "output.sql"

with open(input_file, "r", encoding="utf-8") as file:
    sql_content = file.read()

# 更新 SQL 内容
updated_sql_content = add_fields_to_sql(sql_content)

# 写入新的 SQL 文件
with open(output_file, "w", encoding="utf-8") as file:
    file.write(updated_sql_content)

print(f"处理完成！已生成新的 SQL 文件：{output_file}")