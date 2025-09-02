#!/usr/bin/env python3
import sys
sys.path.append('.')
from bigScreen.bigScreen import db, WeChatAlarmConfig
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ljwx:ljwx123@localhost:3308/ljwx'
db.init_app(app)

with app.app_context():
    configs = WeChatAlarmConfig.query.all()
    print("📋 微信配置列表:")
    for c in configs:
        print(f"ID={c.id} type={c.type} enabled={c.enabled} corp_id={c.corp_id or 'None'} appid={c.appid or 'None'}") 