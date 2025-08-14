import requests

def get_access_token(app_id, app_secret):
    # 微信公众号的 access_token 获取 URL
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"

    # 发送请求
    response = requests.get(url)

    # 将响应结果解析为 JSON
    data = response.json()

    # 检查是否成功获取 access_token
    if "access_token" in data:
        access_token = data['access_token']
        expires_in = data['expires_in']
        print(f"Access Token: {access_token}")
        print(f"Expires in: {expires_in} seconds")
        return access_token
    else:
        # 如果请求失败，打印错误信息
        print(f"Failed to get access_token: {data}")
        return None

# 替换为你的 AppID 和 AppSecret
app_id = 'wx10dcc9f0235e1d77'
app_secret = 'b7e9088f3f5fe18a9cfb990c641138b3'

# 获取 access_token
get_access_token(app_id, app_secret)