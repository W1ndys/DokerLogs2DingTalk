import docker
import time
import hmac
import hashlib
import urllib.parse
import base64
import requests
import logging
import json


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


def get_logs(container_name, num_lines):
    client = docker.from_env()
    container = client.containers.get(container_name)
    logs = container.logs(tail=num_lines).decode("utf-8").splitlines()
    return logs


def extract_log_blocks(logs):
    blocks = []
    current_block = []
    in_block = False

    for i in range(1, len(logs) - 1):
        if (
            "[info]" in logs[i - 1]
            and "[info]" in logs[i + 1]
            and "[info]" not in logs[i]
        ):
            if not in_block:
                current_block = []
                in_block = True
            current_block.append(logs[i])
        else:
            if in_block:
                blocks.append(current_block)
                in_block = False

    # Add the last block if it was not added
    if in_block:
        blocks.append(current_block)

    return blocks


def print_log_blocks(blocks):
    if not blocks:
        print("没有找到符合条件的日志块。")
    else:
        for block in blocks:
            print("----- 分割线 -----")
            for line in block:
                print(line)


if __name__ == "__main__":
    container_name = "napcat"  # 替换为你的容器名称
    num_lines = 100  # 读取的日志行数
    logs = get_logs(container_name, num_lines)
    log_blocks = extract_log_blocks(logs)
    print_log_blocks(log_blocks)

    # 只有在找到符合条件的日志块时才推送钉钉消息
    if log_blocks:
        dingtalk_token = (
            "0c0ad4540eed1d1eab06d7229a573146430e6a8b5429eb4e3ada81e039987f6c"
        )
        dingtalk_secret = (
            "SEC1000ac85e635258597301a211cde38a94644e10f473b110af6f2463e6008e441"
        )
        message = f"容器 '{container_name}' 的错误日志"
        description = "\n".join(["\n".join(block) for block in log_blocks])
        send_dingtalk_message(message, description, dingtalk_token, dingtalk_secret)
