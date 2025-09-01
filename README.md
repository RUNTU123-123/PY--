# 微信公众号天气通知机器人

一个自动推送天气信息和农历节日的微信公众号机器人。

## 功能特点

- 🌤️ 每日天气推送（温度范围 + 天气变化）
- 📅 农历日期和生肖显示
- 🎉 农历节日倒计时（只显示未来节日）
- 💬 中英文每日一句
- ⚡ 支持GitHub Actions自动部署

## 部署说明

### 1. 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置config.json
cp config.example.json config.json
# 编辑config.json填写你的配置信息

# 运行程序
python main.py
