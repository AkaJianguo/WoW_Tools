
# @Version      : 1.0
# @Author       : Jianguo
# @File         : wcl_auth_test.py
# @Time         :2026/3/25 10:59
import os
import requests
from dotenv import load_dotenv

# 加载 .env 文件中的凭证
load_dotenv()

CLIENT_ID = os.getenv("WCL_CLIENT_ID")
CLIENT_SECRET = os.getenv("WCL_CLIENT_SECRET")


def get_wcl_token():
    print(">>> 正在尝试连接 WCL 中国区身份验证服务器...")
    url = "https://cn.warcraftlogs.com/oauth/token"
    data = {'grant_type': 'client_credentials'}

    try:
        response = requests.post(url, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
        response.raise_for_status()  # 如果 Secret 错误会抛出异常
        token = response.json().get('access_token')
        print(">>> [成功] 凭证验证通过！")
        print(f">>> 临时令牌 (Token): {token[:10]}...")
        return token
    except Exception as e:
        print(f">>> [失败] 无法获取令牌，请检查 Secret 是否完整: {e}")
        return None


if __name__ == "__main__":
    get_wcl_token()