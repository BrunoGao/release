# redis_helper.py
from redis import Redis
import json

class RedisHelper:
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self.client = Redis(host=host, port=port, db=db, password=password, decode_responses=True)

    def set_data(self, key, data, expire=None):
        self.client.set(key, json.dumps(data), ex=expire)

    def get_data(self, key):
        data = self.client.get(key)
        return json.loads(data) if data else None

    def hset_data(self, key, mapping):
        self.client.hset(key, mapping=mapping)

    def hgetall_data(self, key):
        data = self.client.hgetall(key)
        return {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}

    def publish(self, channel, message):
        self.client.publish(channel, message)
        
        
    def pubsub(self):
        return self.client.pubsub()
    
    def exists(self, key):
        return self.client.exists(key)
    
    def delete(self, key):
        return self.client.delete(key)
    
    def type(self, key):
        return self.client.type(key)
    
    def hgetall(self, key):
        return self.client.hgetall(key)
    
    def publish(self, channel, message):
        return self.client.publish(channel, message)
    
    def pubsub(self):
        return self.client.pubsub()
    
    def set(self, key, value, ex=None):
        """
        Set key to hold the string value with optional expiry
        :param key: key
        :param value: value
        :param ex: expiry time in seconds
        """
        try:
            self.client.set(key, value, ex=ex)
            return True
        except Exception as e:
            print(f"Error in set: {str(e)}")
            return False
    
    def get(self, key):
        return self.client.get(key)
    
    def hset(self, key, mapping):
        return self.client.hset(key, mapping=mapping)

    def setex(self, key, time, value):
        """
        Set key to hold the string value and set key to timeout after a given number of seconds
        :param key: key
        :param time: expiry time in seconds
        :param value: value to store
        """
        try:
            self.client.setex(key, time, value)
            return True
        except Exception as e:
            print(f"Error in setex: {str(e)}")
            return False

    def subscribe(self, channel, callback=None):
        """
        Subscribe to a channel
        :param channel: channel name
        :param callback: callback function to handle messages
        """
        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            print(f"Error in subscribe: {str(e)}")
            return None