#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信公众号天气通知机器人
功能：每日天气推送 + 农历节日倒计时
"""

import json
import os
import sys
from datetime import datetime, date
from requests import get, post

try:
    from zhdate import ZhDate
    ZH_DATE_AVAILABLE = True
except ImportError:
    ZH_DATE_AVAILABLE = False
    print("警告: 未找到zhdate库，农历功能将不可用")

class WeatherNotifier:
    def __init__(self, config_path="config.json"):
        self.config = self.load_config(config_path)
        self.access_token = None
        
    def load_config(self, config_path):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误: 配置文件 {config_path} 不存在")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"错误: 配置文件格式不正确 - {e}")
            sys.exit(1)
    
    def get_access_token(self):
        """获取微信访问令牌"""
        if self.access_token:
            return self.access_token
            
        app_id = self.config.get("app_id")
        app_secret = self.config.get("app_secret")
        
        if not app_id or not app_secret:
            print("错误: 缺少 app_id 或 app_secret")
            sys.exit(1)
            
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
        
        try:
            response = get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'access_token' in data:
                self.access_token = data['access_token']
                return self.access_token
            else:
                print(f"获取access_token失败: {data}")
                sys.exit(1)
                
        except Exception as e:
            print(f"获取access_token时发生错误: {e}")
            sys.exit(1)
    
    def get_weather_data(self, region):
        """获取天气数据"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        key = self.config.get("weather_key")
        if not key:
            print("错误: 缺少和风天气key")
            sys.exit(1)
        
        # 获取位置ID
        region_url = f"https://geoapi.qweather.com/v2/city/lookup?location={region}&key={key}"
        
        try:
            response = get(region_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == "404":
                raise ValueError("地区名称错误，请检查配置")
            elif data.get("code") == "401":
                raise ValueError("和风天气key错误")
                
            location_id = data["location"][0]["id"]
            
        except Exception as e:
            print(f"获取位置信息失败: {e}")
            sys.exit(1)
        
        # 获取天气信息
        weather_url = f"https://devapi.qweather.com/v7/weather/3d?location={location_id}&key={key}"
        
        try:
            response = get(weather_url, headers=headers, timeout=10)
            response.raise_for_status()
            weather_data = response.json()
            daily_data = weather_data["daily"][0]
            
            # 简化的天气信息
            return {
                "temp_range": f"{daily_data['tempMin']}~{daily_data['tempMax']}°C",
                "weather_change": f"{daily_data['textDay']}转{daily_data['textNight']}"
            }
            
        except Exception as e:
            print(f"获取天气信息失败: {e}")
            sys.exit(1)
    
    def get_lunar_info(self):
        """获取农历信息"""
        if not ZH_DATE_AVAILABLE:
            return "农历功能未启用", []
        
        try:
            today = datetime.now()
            lunar_date = ZhDate.from_datetime(today)
            
            # 农历日期
            lunar_str = f"{lunar_date.chinese()} {lunar_date.chinese_day()}"
            
            # 生肖
            zodiacs = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
            zodiac = zodiacs[(lunar_date.lunar_year - 4) % 12]
            
            # 节气
            solar_term = lunar_date.get_solar_term()
            if solar_term:
                lunar_str += f" {solar_term}"
                
            lunar_str += f" {zodiac}年"
            
            # 未来节日倒计时
            holidays = self.get_future_holidays()
            
            return lunar_str, holidays
            
        except Exception as e:
            print(f"获取农历信息失败: {e}")
            return "农历信息获取失败", []
    
    def get_future_holidays(self):
        """获取未来农历节日倒计时"""
        holidays_config = {
            "春节": "1-1",
            "元宵节": "1-15", 
            "端午节": "5-5",
            "七夕节": "7-7",
            "中秋节": "8-15",
            "重阳节": "9-9",
            "腊八节": "12-8",
            "小年": "12-23",
            "除夕": "12-30"
        }
        
        future_holidays = []
        today = date.today()
        
        for name, lunar_date in holidays_config.items():
            try:
                days_diff = self.calculate_lunar_days_diff(lunar_date)
                if days_diff >= 0:  # 只显示未来和今天的节日
                    if days_diff == 0:
                        future_holidays.append(f"🎉 今天是{name}")
                    else:
                        future_holidays.append(f"⏰ 距离{name}还有{days_diff}天")
            except:
                continue
                
        return future_holidays[:3]  # 最多显示3个节日
    
    def calculate_lunar_days_diff(self, lunar_date_str):
        """计算农历日期距离今天的天数"""
        if not ZH_DATE_AVAILABLE:
            return 999
            
        today = date.today()
        lunar_month = int(lunar_date_str.split("-")[0])
        lunar_day = int(lunar_date_str.split("-")[1])
        
        # 今年农历日期
        lunar_this_year = ZhDate(today.year, lunar_month, lunar_day)
        solar_this_year = lunar_this_year.to_datetime().date()
        
        # 明年农历日期  
        lunar_next_year = ZhDate(today.year + 1, lunar_month, lunar_day)
        solar_next_year = lunar_next_year.to_datetime().date()
        
        if today > solar_this_year:
            return (solar_next_year - today).days
        else:
            return (solar_this_year - today).days
    
    def get_daily_quote(self):
        """获取每日一句"""
        url = "http://open.iciba.com/dsapi/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "en": data.get("content", "Have a nice day!"),
                "cn": data.get("note", "祝你今天愉快!")
            }
            
        except Exception:
            # 默认名言
            return {
                "en": "The best preparation for tomorrow is doing your best today.",
                "cn": "对明天最好的准备就是今天做到最好"
            }
    
    def send_wechat_message(self, weather_info, lunar_info, holidays, quote):
        """发送微信消息"""
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={self.access_token}"
        
        today = datetime.now()
        week_days = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        week_day = week_days[today.weekday()]
        
        # 准备消息数据
        template_data = {
            "touser": self.config["user"][0],
            "template_id": self.config["template_id"],
            "url": "https://github.com",
            "data": {
                "date": {"value": f"{today.strftime('%Y年%m月%d日')} {week_day}"},
                "region": {"value": self.config["region"]},
                "weather": {"value": weather_info["weather_change"]},
                "temperature": {"value": weather_info["temp_range"]},
                "lunar_date": {"value": lunar_info},
                "holiday1": {"value": holidays[0] if len(holidays) > 0 else "近期无节日"},
                "holiday2": {"value": holidays[1] if len(holidays) > 1 else ""},
                "holiday3": {"value": holidays[2] if len(holidays) > 2 else ""},
                "quote_cn": {"value": quote["cn"]},
                "quote_en": {"value": quote["en"]}
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = post(url, headers=headers, json=template_data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                print("✅ 消息推送成功")
                return True
            else:
                print(f"❌ 消息推送失败: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 发送消息时发生错误: {e}")
            return False
    
    def run(self):
        """运行主程序"""
        print("🚀 开始执行微信天气通知任务...")
        
        # 获取访问令牌
        print("🔑 获取微信访问令牌...")
        self.get_access_token()
        
        # 获取天气数据
        print("🌤️ 获取天气信息...")
        weather_info = self.get_weather_data(self.config["region"])
        
        # 获取农历信息
        print("📅 获取农历信息...")
        lunar_info, holidays = self.get_lunar_info()
        
        # 获取每日一句
        print("💬 获取每日名言...")
        quote = self.get_daily_quote()
        
        # 发送消息
        print("📤 发送微信消息...")
        success = self.send_wechat_message(weather_info, lunar_info, holidays, quote)
        
        if success:
            print("🎉 任务执行完成！")
        else:
            print("❌ 任务执行失败！")
            sys.exit(1)

def main():
    """主函数"""
    # 检查是否在GitHub Actions中运行
    is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    
    if is_github_actions:
        print("运行环境: GitHub Actions")
    
    # 创建通知器实例并运行
    notifier = WeatherNotifier()
    notifier.run()

if __name__ == "__main__":
    main()
