# WPS 会员积分自动签到

基于 GitHub Actions 的纯云端定时签到方案，无需本地开机，每天自动完成 WPS 会员积分签到。

## 项目结构

```
wps-sign/
├── wps_sign.py              # 签到脚本
├── .github/
│   └── workflows/
│       └── wps-sign.yml     # GitHub Actions 定时触发配置
└── README.md                # 项目文档（本文件）
```

## 工作原理

```
GitHub Actions (每天 16:00 触发)
  └→ 拉取仓库代码
      └→ 安装 Python + requests
          └→ 运行 wps_sign.py
              ├→ 检查今日是否已签到
              ├→ 未签到 → POST vip.wps.cn/sign/v2
              │   ├→ 免验证：直接签到成功
              │   └→ 需验证码：固定坐标重试（最多 50 次）
              └→ 失败时自动创建 Issue 提醒
```

## 部署清单

### 前置条件

| 序号 | 步骤 | 备注 |
|------|------|------|
| 1 | GitHub 仓库 | 创建空仓库，不勾选 Add README |
| 2 | 获取 wps_sid | 见下方「获取 wps_sid」 |
| 3 | GitHub Token | Fine-grained token，见下方「Token 权限」 |
| 4 | 推送文件 | 将本目录文件推送到仓库 |
| 5 | 配置 Secret | 在仓库 Settings → Secrets → Actions 添加 `WPS_SID` |

### Token 权限要求

创建 Fine-grained personal access token 时需要以下权限：

| 权限 | 用途 |
|------|------|
| Contents (Read and write) | 推送代码文件 |
| Workflows (Read and write) | 推送 workflow 配置 |
| Metadata (Read-only) | 自动附带 |

> 创建路径：GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens

## ⚠️ 常见问题与避坑

### 1. wps_sid 获取（最容易出错）

**正确步骤**：
1. 浏览器打开 https://vip.wps.cn/ 并**登录**
2. 按 `F12` → **Application**（应用程序）→ 左侧 **Cookies** → 点击 `https://vip.wps.cn`
3. 在右侧表格中找到 `wps_sid` 行
4. **只复制 Value 列的值**（一串以 `V02` 开头的字符串）

**常见错误**：
- ❌ 未登录就打开 F12 → Cookie 列表为空
- ❌ 把 Value 复制后二次粘贴导致拼接重复（如 `xxxV02xxxV02`）
- ❌ 复制了整行而非仅 Value 列
- ❌ 用错了 Cookie 域名（必须是 `vip.wps.cn`，不是 `wps.cn`）

> sid 值格式参考：`V02SNWNi_LhaW0hCguX_Aeiko52UNwg00ae5ff010008994a77`

### 2. Token 权限不足

症状：推送 `.github/workflows/` 下文件时报 403 错误。

解决：确保 Token 有 **Workflows (Read and write)** 权限，不只是 Contents。

### 3. wps_sid 有效期

wps_sid 通常有效期约 **7-30 天**，过期后签到会失败，脚本会自动创建 Issue 提醒你更新。收到提醒后：
1. 重新登录 vip.wps.cn 获取新的 wps_sid
2. 在仓库 Settings → Secrets → Actions → 编辑 `WPS_SID`
3. 手动触发一次 workflow 验证

### 4. 修改签到时间

编辑 `.github/workflows/wps-sign.yml`，修改 `cron` 表达式：

```yaml
schedule:
  - cron: "0 8 * * *"   # UTC 8:00 = 北京时间 16:00
```

| cron | 北京时间 | 说明 |
|------|----------|------|
| `0 0 * * *` | 08:00 | 每天早上 8 点 |
| `0 2 * * *` | 10:00 | 每天早上 10 点 |
| `0 8 * * *` | 16:00 | 每天下午 4 点（默认） |
| `30 0 * * *` | 08:30 | 每天早上 8:30 |

> cron 格式：`分 时 日 月 星期`（UTC 时间，需自行 +8 换算）

### 5. 修改签到时间

编辑 `.github/workflows/wps-sign.yml` 中的 `cron` 字段，注意 cron 时间使用 **UTC**（北京时间 -8 小时）。

## 手动触发验证

部署后建议手动触发一次确认配置正确：
1. 打开仓库 → **Actions** → 左侧 **WPS 每日签到**
2. 点击 **Run workflow** → **Run workflow**
3. 等待执行完成，查看日志确认签到成功

## 结果通知

| 情况 | 通知方式 |
|------|----------|
| 签到成功 | Actions 日志（绿色 ✓） |
| Cookie 过期 | 自动创建 Issue「WPS 签到失败：Cookie 已过期」 |
| 其他异常 | 自动创建 Issue 并附带错误信息 |

GitHub 默认会向账户注册邮箱发送 Issue 和 Workflow 失败通知邮件。
