from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# 不要在这里导入其他模块

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'ljwx-bigscreen-secret-key'
    
    # 配置CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # 配置数据库
    try:
        from .models import db
        import os
        from urllib.parse import quote_plus
        # 从环境变量读取数据库配置
        mysql_host = os.getenv('MYSQL_HOST', 'mysql')
        mysql_port = os.getenv('MYSQL_PORT', '3306') 
        mysql_user = os.getenv('MYSQL_USER', 'root')
        mysql_password = os.getenv('MYSQL_PASSWORD', '123456')
        mysql_database = os.getenv('MYSQL_DATABASE', 'lj-06')
        # 密码URL编码处理
        encoded_password = quote_plus(mysql_password)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'pool_timeout': 20,
            'pool_recycle': -1,
            'max_overflow': 0,
            'pool_pre_ping': True
        }
        
        # 初始化数据库
        db.init_app(app)
        
        # 创建应用上下文并初始化数据库
        with app.app_context():
            try:
                db.create_all()
                print("✅数据库初始化完成")
            except Exception as e:
                print(f"⚠️数据库初始化警告: {e}")
        
    except Exception as e:
        print(f"❌数据库配置失败: {e}")
    
    # 注册蓝图
    try:
        from .views import bp as views_bp
        app.register_blueprint(views_bp)
        print("✅视图蓝图注册完成")
    except Exception as e:
        print(f"❌蓝图注册失败: {e}")
    
    # 🔥关键修复：导入并注册bigScreen模块中的路由#
    try:
        from . import bigScreen  #导入bigScreen模块注册所有路由#
        # 将bigScreen模块中已注册的路由复制到当前app实例#
        for rule in bigScreen.app.url_map.iter_rules():
            if rule.endpoint not in app.view_functions:
                app.add_url_rule(rule.rule, rule.endpoint, 
                                bigScreen.app.view_functions[rule.endpoint],
                                methods=rule.methods) #复制所有路由规则#
        print(f"✅bigScreen路由模块注册完成 - 已复制{len(bigScreen.app.url_map._rules)}个路由")
    except Exception as e:
        print(f"❌bigScreen路由模块注册失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 🔥关键修复：应用启动时直接初始化系统事件处理器
    with app.app_context():
        try:
            from .system_event_alert import get_processor
            processor = get_processor()
            if not processor.is_running:
                processor.start(worker_count=3)
                print("✅系统事件处理器已启动")
            else:
                print("ℹ️系统事件处理器已在运行")
        except Exception as e:
            print(f"⚠️系统事件处理器启动失败: {e}")
            import traceback
            traceback.print_exc()

    return app
