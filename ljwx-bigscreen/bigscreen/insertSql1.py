import random
from datetime import datetime

# Possible phone numbers and alert types
phone_numbers = [
    '18911111111', '18922222222', '18933333333'
]
alert_types = ['心率异常', '体温异常', '跌倒', '血氧异常', '血压异常']

# Function to generate random latitude and longitude
def random_coordinate():
    return round(random.uniform(-90, 90), 6), round(random.uniform(-180, 180), 6)

# Generate 50 SQL insert statements
sql_statements = []
for _ in range(50):
    phone_number = random.choice(phone_numbers)
    alert_type = random.choice(alert_types)
    latitude, longitude = random_coordinate()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql = f"INSERT INTO t_user_alerts (userName, phoneNumber, alertType, latitude, longitude, timestamp) VALUES ('User_{random.randint(1, 100)}', '{phone_number}', '{alert_type}', {latitude}, {longitude}, '{timestamp}');"
    sql_statements.append(sql)

# Print all SQL statements
for statement in sql_statements:
    print(statement)