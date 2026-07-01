"""WPS 积分签到脚本 — GitHub Actions 定时运行"""
import os
import sys
import time
import random
import json
import requests

WPS_SID = os.environ.get("WPS_SID", "").strip()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "")

HEADERS = {
    "Cookie": f"wps_sid={WPS_SID}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
}

SIGN_URL = "https://vip.wps.cn/sign/v2"
CHECK_URL = "https://vip.wps.cn/sign/mobile/v3/get_data"
CAPTCHA_URL = "https://vip.wps.cn/checkcode/signin/captcha.png?platform=8&encode=0&img_witdh=275.164&img_height=69.184"


def create_issue(title, body):
    """通过 GitHub API 创建 Issue 提醒"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print(f"[提醒] {title}: {body}")
        return
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        r = requests.post(url, headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }, json={"title": title, "body": body, "labels": ["cookie-expired"]}, timeout=10)
        if r.status_code == 201:
            print(f"Issue 已创建: {r.json().get('html_url')}")
        else:
            print(f"创建 Issue 失败: {r.status_code}")
    except Exception as e:
        print(f"创建 Issue 异常: {e}")


def check_already_signed():
    """检查今日是否已签到"""
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
    """执行签到，返回 (success, message)"""
    # 不带验证码签到
    try:
        r = requests.post(SIGN_URL, headers=HEADERS, data={"platform": "8"}, timeout=15)
    except Exception as e:
        return False, f"签到请求失败: {e}"

    if "msg" not in r.text:
        return False, "Cookie 失效，wps_sid 已过期，请重新获取"

    result = r.json().get("result")
    if result == "ok":
        return True, f"签到成功 (免验证) — 返回: {r.text}"

    # 需要验证码，固定坐标反复重试
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
                return True, f"签到成功 (第 {attempt} 次验证通过) — 返回: {r.text}"
        except Exception:
            continue

    return False, f"签到失败: 50 次验证码重试均未通过"


COOKIE_EXPIRED_MSG = "Cookie 失效，wps_sid 已过期，请重新获取"


def main():
    if not WPS_SID:
        print("未设置 WPS_SID")
        sys.exit(1)

    already, err = check_already_signed()
    if err:
        print(f"失败: {err}")
        if COOKIE_EXPIRED_MSG in err:
            create_issue("WPS 签到失败：Cookie 已过期",
                         "wps_sid 已失效，请重新获取并更新仓库的 Actions Secret `WPS_SID`。\n\n"
                         "获取方法：浏览器打开 vip.wps.cn 登录后，F12 → Application → Cookies → 找到 wps_sid 复制值。")
        sys.exit(1)

    if already:
        print("今日已签到")
        return

    success, msg = do_sign()
    print(msg)
    if success:
        return

    # 签到失败，判断是否为 cookie 过期
    if COOKIE_EXPIRED_MSG in msg:
        create_issue("WPS 签到失败：Cookie 已过期",
                     "wps_sid 已失效，请重新获取并更新仓库的 Actions Secret `WPS_SID`。\n\n"
                     "获取方法：浏览器打开 vip.wps.cn 登录后，F12 → Application → Cookies → 找到 wps_sid 复制值。")
    else:
        create_issue("WPS 签到失败",
                     f"签到异常，错误信息：{msg}\n\n请检查 Actions 日志了解详情。")
    sys.exit(1)


if __name__ == "__main__":
    main()
