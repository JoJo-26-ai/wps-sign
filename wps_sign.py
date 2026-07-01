"""WPS 积分签到脚本 — GitHub Actions 定时运行"""
import os
import sys
import time
import random
import json
import requests

WPS_SID = os.environ.get("WPS_SID", "").strip()

HEADERS = {
    "Cookie": f"wps_sid={WPS_SID}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
}

SIGN_URL = "https://vip.wps.cn/sign/v2"
CHECK_URL = "https://vip.wps.cn/sign/mobile/v3/get_data"
CAPTCHA_URL = "https://vip.wps.cn/checkcode/signin/captcha.png?platform=8&encode=0&img_witdh=275.164&img_height=69.184"


def check_already_signed():
    try:
        r = requests.get(CHECK_URL, headers=HEADERS, timeout=15)
        if "会员登录" in r.text:
            return None, "Cookie 失效，wps_sid 已过期，请重新获取"
        data = r.json()
        is_sign = data.get("data", {}).get("is_sign", False)
        return is_sign, None
    except Exception as e:
        return None, f"查询签到状态失败: {e}"


def do_sign():
    try:
        r = requests.post(SIGN_URL, headers=HEADERS, data={"platform": "8"}, timeout=15)
    except Exception as e:
        return False, f"签到请求失败: {e}"

    if "msg" not in r.text:
        return False, "Cookie 失效，wps_sid 已过期，请重新获取"

    result = r.json().get("result")
    if result == "ok":
        return True, f"签到成功 (免验证)"

    captcha_data = {
        "platform": "8",
        "captcha_pos": "137.00431974731889, 36.00431593261568",
        "img_witdh": "275.164",
        "img_height": "69.184",
    }

    for attempt in range(1, 51):
        try:
            requests.get(CAPTCHA_URL, headers=HEADERS, timeout=10)
            r = requests.post(SIGN_URL, headers=HEADERS, data=captcha_data, timeout=15)
            result = r.json().get("result")
            time.sleep(random.randint(0, 5) / 10)
            if result == "ok":
                return True, f"签到成功 (第 {attempt} 次验证通过)"
        except Exception:
            continue

    return False, "签到失败: 50 次验证码重试均未通过"


def main():
    if not WPS_SID:
        print("未设置 WPS_SID")
        sys.exit(1)

    already, err = check_already_signed()
    if err:
        print(f"失败: {err}")
        sys.exit(1)
    if already:
        print("今日已签到")
        return

    success, msg = do_sign()
    print(msg)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
