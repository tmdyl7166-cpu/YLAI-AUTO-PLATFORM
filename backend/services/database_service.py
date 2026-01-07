"""
数据库服务模块
提供SQLite/PostgreSQL/MySQL数据库集成
"""
import sqlite3
import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import yaml
from contextlib import contextmanager


class DatabaseService:
    """数据库服务类"""

    def __init__(self):
        self.config = self._load_config()
        self.connection = None
        self.db_type = self.config.get('database', {}).get('type', 'sqlite')

    async def initialize(self):
        """初始化数据库服务"""
        try:
            # 测试连接
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
            # 初始化表结构
            self.init_tables()
            return True
        except Exception as e:
            print(f"Database initialization failed: {e}")
            return False

    def _load_config(self) -> dict:
        """加载数据库配置"""
        config_path = Path(__file__).parent.parent / "config" / "performance.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            return {
                'database': {
                    'type': 'sqlite',
                    'sqlite': {
                        'path': 'data/ylai.db'
                    }
                }
            }

    def _get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        db_config = self.config.get('database', {})

        if self.db_type == 'sqlite':
            sqlite_config = db_config.get('sqlite', {})
            db_path = sqlite_config.get('path', 'data/ylai.db')
            # 确保目录存在
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{db_path}"

        elif self.db_type == 'postgresql':
            pg_config = db_config.get('postgresql', {})
            return f"postgresql://{pg_config.get('user')}:{pg_config.get('password')}@{pg_config.get('host')}:{pg_config.get('port')}/{pg_config.get('database')}"

        elif self.db_type == 'mysql':
            mysql_config = db_config.get('mysql', {})
            return f"mysql://{mysql_config.get('user')}:{mysql_config.get('password')}@{mysql_config.get('host')}:{mysql_config.get('port')}/{mysql_config.get('database')}"

        return "sqlite:///data/ylai.db"

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        if self.db_type == 'sqlite':
            conn = sqlite3.connect(self._get_connection_string().replace('sqlite:///', ''))
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
        else:
            # 对于其他数据库类型，需要安装相应的驱动
            raise NotImplementedError(f"Database type {self.db_type} not implemented yet")

    def init_tables(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 用户操作日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    details TEXT
                )
            ''')

            # API调用统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER,
                    response_time REAL,
                    user_id TEXT,
                    ip_address TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 脚本执行记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS script_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_name TEXT NOT NULL,
                    user_id TEXT,
                    parameters TEXT,
                    result TEXT,
                    execution_time REAL,
                    status TEXT,
                    error_message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 号码分析缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS phone_cache (
                    phone TEXT PRIMARY KEY,
                    carrier TEXT,
                    province TEXT,
                    city TEXT,
                    area_code TEXT,
                    post_code TEXT,
                    analysis_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    def log_user_action(self, user_id: str, action: str, resource: str = None,
                       ip_address: str = None, user_agent: str = None, details: dict = None):
        """记录用户操作"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_logs (user_id, action, resource, ip_address, user_agent, details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id, action, resource, ip_address, user_agent,
                json.dumps(details) if details else None
            ))
            conn.commit()

    def log_api_call(self, endpoint: str, method: str, status_code: int,
                    response_time: float, user_id: str = None, ip_address: str = None):
        """记录API调用"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO api_stats (endpoint, method, status_code, response_time, user_id, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (endpoint, method, status_code, response_time, user_id, ip_address))
            conn.commit()

    def log_script_run(self, script_name: str, user_id: str = None, parameters: dict = None,
                      result: Any = None, execution_time: float = None, status: str = "success",
                      error_message: str = None):
        """记录脚本执行"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO script_runs (script_name, user_id, parameters, result, execution_time, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                script_name, user_id,
                json.dumps(parameters) if parameters else None,
                json.dumps(result) if result else None,
                execution_time, status, error_message
            ))
            conn.commit()

    def get_phone_cache(self, phone: str) -> Optional[Dict]:
        """获取号码分析缓存"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT carrier, province, city, area_code, post_code, analysis_time
                FROM phone_cache
                WHERE phone = ?
            ''', (phone,))

            row = cursor.fetchone()
            if row:
                return {
                    'carrier': row[0],
                    'province': row[1],
                    'city': row[2],
                    'area_code': row[3],
                    'post_code': row[4],
                    'analysis_time': row[5]
                }
        return None

    def set_phone_cache(self, phone: str, data: Dict):
        """设置号码分析缓存"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO phone_cache
                (phone, carrier, province, city, area_code, post_code, analysis_time, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                phone,
                data.get('carrier'),
                data.get('province'),
                data.get('city'),
                data.get('area_code'),
                data.get('post_code'),
                data.get('analysis_time')
            ))
            conn.commit()

    def get_api_stats(self, limit: int = 100) -> List[Dict]:
        """获取API统计数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT endpoint, method, status_code, response_time, user_id, timestamp
                FROM api_stats
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 删除旧的用户日志
            cursor.execute('''
                DELETE FROM user_logs
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))

            # 删除旧的API统计
            cursor.execute('''
                DELETE FROM api_stats
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))

            # 删除旧的脚本执行记录
            cursor.execute('''
                DELETE FROM script_runs
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))

            conn.commit()

    def close(self):
        """关闭数据库连接"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
        except Exception:
            pass


# 全局数据库服务实例
db_service = DatabaseService()