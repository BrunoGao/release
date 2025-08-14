import requests
import json
import time
import subprocess
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.dnspod.v20210323 import dnspod_client, models

# 替换成你的SecretId和SecretKey
SECRET_ID = 'AKIDxoYAmmlaKwWB4pPlzAA8yhLuV0b8X9dy'
SECRET_KEY = 'GOPQMF1mMhspePAwfQ6iBY1PqFnDoOsB'
DOMAIN = 'lingjingwanxiang.com'  # 例如 'example.com'
SUB_DOMAIN = 'www'  # 例如 'www'
RECORD_TYPE = 'A'  # 动态IP一般是IPv4，所以用A记录

# 获取当前公网IP地址
def get_public_ip():
    try:
        # Use curl to get public IP from ipinfo.io
        result = subprocess.run(['curl', '-s', 'ipinfo.io'], capture_output=True, text=True)
        ip_info = json.loads(result.stdout)
        ip = ip_info['ip']
        print(f"当前公网IP: {ip}")
        return ip
    except Exception as e:
        print(f"获取IP失败: {e}")
        return None

# 更新DNS记录
def update_dns_record(ip):
    try:
        cred = credential.Credential(SECRET_ID, SECRET_KEY)
        httpProfile = HttpProfile()
        httpProfile.endpoint = "dnspod.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = dnspod_client.DnspodClient(cred, "", clientProfile)

        req = models.DescribeRecordListRequest()
        params = {
            "Domain": DOMAIN,
            "Subdomain": SUB_DOMAIN,
            "RecordType": RECORD_TYPE
        }
        req.from_json_string(json.dumps(params))

        # 获取记录ID
        resp = client.DescribeRecordList(req)
        record_id = None
        for record in resp.RecordList:
            print(f"Record: {record}")  # Print each record
            if record.Name == SUB_DOMAIN and record.Type == RECORD_TYPE:
                record_id = record.RecordId
                break

        if record_id is None:
            print("未找到指定的DNS记录")
            return

        # 更新记录
        req = models.ModifyRecordRequest()
        params = {
            "Domain": DOMAIN,
            "RecordId": record_id,
            "SubDomain": SUB_DOMAIN,
            "RecordType": RECORD_TYPE,
            "RecordLine": "默认",
            "Value": ip
        }
        req.from_json_string(json.dumps(params))
        resp = client.ModifyRecord(req)
        print(f"DNS记录已更新为: {ip}")
    except Exception as e:
        print(f"更新DNS记录失败: {e}")

# 主循环：每隔5分钟检查IP变化并更新DNS记录
def main():
    current_ip = None
    while True:
        ip = get_public_ip()
        if ip and ip != current_ip:
            update_dns_record(ip)
            current_ip = ip
        time.sleep(300)  # 每隔5分钟检查一次

if __name__ == '__main__':
    main()
