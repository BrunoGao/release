import redis

# 连接 Redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# 查找所有以 device_info 开头的键
keys = r.keys("*")

# 删除这些键
if keys:
    r.delete(*keys)

print(f"Deleted {len(keys)} keys.")