import docker
import requests
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import logging
import re
from datetime import datetime

def get_container_logs(container_name, num_lines):
    client = docker.from_env()
    try:
        container = client.containers.get(container_name)
        logs = container.logs(tail=num_lines)
        simplified_logs = "\n".join(
            "【隐藏的info日志】" if re.search(r"\[32minfo.*\[39m\]", line) else line
            for line in logs.decode("utf-8").splitlines()
        )
        return simplified_logs
    except docker.errors.NotFound:
        return f"容器 '{container_name}' 不存在."
    except Exception as e:
        return str(e)


def send_dingtalk_message(text, desp, dingtalk_token, dingtalk_secret):
    url = f"https://oapi.dingtalk.com/robot/send?access_token={dingtalk_token}"
    headers = {"Content-Type": "application/json"}
    payload = {"msgtype": "text", "text": {"content": f"{text}\n{desp}"}}

    if dingtalk_token and dingtalk_secret:
        timestamp = str(round(time.time() * 1000))
        secret_enc = dingtalk_secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{dingtalk_secret}"
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(
            base64.b64encode(hmac_code).decode("utf-8").strip()
        )
        url = f"{url}&timestamp={timestamp}&sign={sign}"

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    try:
        data = response.json()
        if response.status_code == 200 and data.get("errcode") == 0:
            logging.info("钉钉发送通知消息成功🎉")
        else:
            logging.error(f"钉钉发送通知消息失败😞\n{data.get('errmsg')}")
    except Exception as e:
        logging.error(f"钉钉发送通知消息失败😞\n{e}")

    return response.json()


# 获取容器日志
container_name = "napcat"
num_lines = 5
logs = get_container_logs(container_name, num_lines)
print(logs)

# 钉钉推送
dingtalk_token = "0c0ad4540eed1d1eab06d7229a573146430e6a8b5429eb4e3ada81e039987f6c"
dingtalk_secret = "SEC1000ac85e635258597301a211cde38a94644e10f473b110af6f2463e6008e441"
message = f"容器 '{container_name}' 的日志"
description = logs

# 当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"当前时间：{current_time}")
description = f"{current_time}\n{description}"
send_dingtalk_message(message, description, dingtalk_token, dingtalk_secret)
