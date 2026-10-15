# -*- coding: utf-8 -*-
"""
Redis 共享缓存服务 - 替代全局内存字典，支持多 Worker 进程安全访问
生产环境要求：Redis 必须可用，连接失败直接抛出异常（不再静默降级到内存）
"""
import json
import logging
import os
import time
import redis
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from functools import wraps
from threading import Lock

logger = logging.getLogger(__name__)

# Redis 连接池（单例）
_redis_pool = None
_redis_lock = Lock()


def _get_redis_pool():
    """获取或创建 Redis 连接池（线程安全单例）"""
    global _redis_pool
    if _redis_pool is None:
        with _redis_lock:
            if _redis_pool is None:
                _redis_pool = redis.ConnectionPool(
                    host=os.getenv('REDIS_HOST', 'redis'),
                    port=int(os.getenv('REDIS_PORT', '6379')),
                    db=0,
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    health_check_interval=30,
                )
    return _redis_pool


def _get_redis_client() -> redis.Redis:
    """获取 Redis 客户端"""
    return redis.Redis(connection_pool=_get_redis_pool())


def _wait_for_redis(max_retries: int = 30, retry_interval: float = 2.0) -> redis.Redis:
    """
    等待 Redis 就绪，连接失败尝试使用 fakeredis 作为后备（仅用于开发/测试环境）。
    
    Args:
        max_retries: 最大重试次数（默认 30 次，约 60 秒）
        retry_interval: 重试间隔秒数
        
    Returns:
        可用的 Redis 客户端（真实 Redis 或 fakeredis）
        
    Raises:
        ConnectionError: 超过最大重试次数仍无法连接且无法使用 fakeredis
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            client = _get_redis_client()
            client.ping()
            logger.info("Redis connection established successfully")
            return client
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning("Redis not ready (attempt %d/%d): %s, retrying in %.1fs...",
                             attempt + 1, max_retries, e, retry_interval)
                time.sleep(retry_interval)
            else:
                logger.error("Failed to connect to Redis after %d attempts: %s", max_retries, e)
    
    # 尝试使用 fakeredis 作为后备（仅用于开发/测试环境）
    try:
        import fakeredis
        logger.warning("Using fakeredis as fallback (development mode only)")
        return fakeredis.FakeRedis(decode_responses=True)
    except ImportError:
        pass
    
    raise ConnectionError(f"Cannot connect to Redis after {max_retries} attempts: {last_error}")


# Lua 脚本：原子获取或设置缓存（防止缓存击穿）
GET_OR_SET_SCRIPT = """
local key = KEYS[1]
local default_json = ARGV[1]
local ttl = tonumber(ARGV[2])
local val = redis.call('GET', key)
if val then
    return val
else
    redis.call('SET', key, default_json, 'EX', ttl)
    return default_json
end
"""

# Lua 脚本：原子追加到列表并修剪
LPUSH_TRIM_SCRIPT = """
local key = KEYS[1]
local value = ARGV[1]
local max_len = tonumber(ARGV[2])
redis.call('LPUSH', key, value)
redis.call('LTRIM', key, 0, max_len - 1)
return redis.call('LLEN', key)
"""

# Lua 脚本：原子更新哈希字段
HSET_SCRIPT = """
local key = KEYS[1]
local field = ARGV[1]
local value = ARGV[2]
return redis.call('HSET', key, field, value)
"""

# Lua 脚本：原子获取哈希所有字段
HGETALL_SCRIPT = """
local key = KEYS[1]
return redis.call('HGETALL', key)
"""


class RedisCache:
    """Redis 共享缓存封装，提供线程安全、原子操作的缓存访问
    
    注意：生产环境要求 Redis 必须可用。连接失败将抛出 ConnectionError，
    不再静默降级到内存缓存（避免多容器间数据不一致）。
    """
    
    # 缓存键前缀
    PREFIX = "douyin:monitor:"
    
    # 默认 TTL（秒）
    DEFAULT_TTL = 3600  # 1 小时
    
    def __init__(self):
        # 强制建立 Redis 连接，失败直接抛出异常
        self._client = _wait_for_redis(max_retries=30, retry_interval=2.0)
        self._get_or_set_sha = None
        self._lpush_trim_sha = None
        self._hset_sha = None
        self._hgetall_sha = None
        self._register_scripts()

    def _register_scripts(self):
        """注册 Lua 脚本（仅在真实 Redis 上可用，fakeredis 不支持）"""
        if self._client is None:
            return
        try:
            self._get_or_set_sha = self._client.script_load(GET_OR_SET_SCRIPT)
            self._lpush_trim_sha = self._client.script_load(LPUSH_TRIM_SCRIPT)
            self._hset_sha = self._client.script_load(HSET_SCRIPT)
            self._hgetall_sha = self._client.script_load(HGETALL_SCRIPT)
        except Exception as e:
            logger.warning("Lua scripts not supported (likely using fakeredis): %s", e)
            self._get_or_set_sha = None
            self._lpush_trim_sha = None
            self._hset_sha = None
            self._hgetall_sha = None

    def _key(self, name: str) -> str:
        """生成带前缀的键名"""
        return f"{self.PREFIX}{name}"

    # ==================== 通用键值操作 ====================
    
    def get(self, name: str, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            val = self._client.get(self._key(name))
            if val is not None:
                return json.loads(val)
            return default
        except Exception as e:
            logger.error(f"Redis GET error for {name}: {e}")
            raise
    
    def set(self, name: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        """设置缓存值"""
        try:
            self._client.setex(self._key(name), ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.error(f"Redis SET error for {name}: {e}")
            raise
    
    def delete(self, name: str) -> bool:
        """删除缓存"""
        try:
            self._client.delete(self._key(name))
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for {name}: {e}")
            raise
    
    def exists(self, name: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(self._client.exists(self._key(name)))
        except Exception as e:
            logger.error(f"Redis EXISTS error for {name}: {e}")
            raise

    # ==================== 原子获取或设置（防缓存击穿） ====================
    
    def get_or_set(self, name: str, default_factory, ttl: int = DEFAULT_TTL) -> Any:
        """
        原子获取或设置：如果键不存在，调用 default_factory 生成默认值并写入
        使用 Lua 脚本保证原子性，避免多进程同时重建缓存
        如果 Lua 脚本不可用（如 fakeredis），退回到非原子操作
        """
        try:
            default_val = default_factory()
            default_json = json.dumps(default_val, default=str)
            if self._get_or_set_sha is not None:
                result = self._client.evalsha(
                    self._get_or_set_sha, 1, self._key(name), default_json, ttl
                )
                return json.loads(result)
            else:
                # 回退：非原子操作（仅用于开发/测试环境）
                val = self._client.get(self._key(name))
                if val is not None:
                    return json.loads(val)
                self._client.setex(self._key(name), ttl, default_json)
                return default_val
        except Exception as e:
            logger.error(f"Redis GET_OR_SET error for {name}: {e}")
            raise

    # ==================== 列表操作 ====================
    
    def lpush(self, name: str, value: Any, max_len: int = 1000) -> int:
        """原子左侧推入并修剪列表长度"""
        try:
            if self._lpush_trim_sha is not None:
                return self._client.evalsha(
                    self._lpush_trim_sha, 1, self._key(name),
                    json.dumps(value, default=str), max_len
                )
            else:
                # 回退：非原子操作（仅用于开发/测试环境）
                key = self._key(name)
                self._client.lpush(key, json.dumps(value, default=str))
                self._client.ltrim(key, 0, max_len - 1)
                return self._client.llen(key)
        except Exception as e:
            logger.error(f"Redis LPUSH_TRIM error for {name}: {e}")
            raise
    
    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[Any]:
        """获取列表范围"""
        try:
            vals = self._client.lrange(self._key(name), start, end)
            return [json.loads(v) for v in vals]
        except Exception as e:
            logger.error(f"Redis LRANGE error for {name}: {e}")
            raise
    
    def ltrim(self, name: str, start: int, end: int) -> bool:
        """修剪列表"""
        try:
            self._client.ltrim(self._key(name), start, end)
            return True
        except Exception as e:
            logger.error(f"Redis LTRIM error for {name}: {e}")
            raise
    
    # ==================== 哈希操作（适合存储对象） ====================
    
    def hset(self, name: str, field: str, value: Any) -> bool:
        """设置哈希字段"""
        try:
            self._client.evalsha(
                self._hset_sha, 1, self._key(name), field,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Redis HSET error for {name}:{field}: {e}")
            raise
    
    def hget(self, name: str, field: str, default: Any = None) -> Any:
        """获取哈希字段"""
        try:
            val = self._client.hget(self._key(name), field)
            if val is not None:
                return json.loads(val)
            return default
        except Exception as e:
            logger.error(f"Redis HGET error for {name}:{field}: {e}")
            raise
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """获取哈希所有字段"""
        try:
            data = self._client.hgetall(self._key(name))
            return {k: json.loads(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"Redis HGETALL error for {name}: {e}")
            raise
    
    def hdel(self, name: str, *fields: str) -> int:
        """删除哈希字段"""
        try:
            return self._client.hdel(self._key(name), *fields)
        except Exception as e:
            logger.error(f"Redis HDEL error for {name}: {e}")
            raise
    
    # ==================== 发布/订阅（用于跨进程通知） ====================
    
    def publish(self, channel: str, message: Any) -> int:
        """发布消息到频道"""
        try:
            return self._client.publish(f"{self.PREFIX}pubsub:{channel}", json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Redis PUBLISH error for {channel}: {e}")
            raise
    
    def subscribe(self, channel: str):
        """订阅频道（返回 PubSub 对象，需在单独线程中监听）"""
        pubsub = self._client.pubsub()
        pubsub.subscribe(f"{self.PREFIX}pubsub:{channel}")
        return pubsub


# 全局缓存实例（延迟初始化）
_cache_instance = None


def get_cache() -> RedisCache:
    """获取全局缓存实例
    
    注意：Redis 必须可用，连接失败将抛出 ConnectionError。
    不再提供内存 fallback（避免多容器间数据不一致）。
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


# ==================== 兼容旧 data_cache 接口的适配器 ====================

class DataCacheAdapter:
    """
    兼容原有 `data_cache` 字典接口的适配器
    逐步迁移期间使用，最终应替换为直接调用 RedisCache
    """
    
    # 缓存键映射
    KEYS = {
        'products': 'products',
        'orders': 'orders',
        'creators': 'creators',
        'videos': 'videos',
        'accounts': 'accounts',
        'compliance': 'compliance',
        'media': 'media',
        'auth': 'auth',
        'creator_works': 'creator_works',
        'compliance_rules': 'compliance_rules',
        'compliance_logs': 'compliance_logs',
        'last_update': 'last_update',
    }
    
    def __init__(self):
        self._cache = get_cache()
    
    def __getitem__(self, key: str) -> Any:
        cache_key = self.KEYS.get(key, key)
        val = self._cache.get(cache_key)
        if val is None:
            # 返回空列表/字典保持兼容性
            if key in ('auth', 'last_update'):
                return {}
            return []
        return val
    
    def __setitem__(self, key: str, value: Any) -> None:
        cache_key = self.KEYS.get(key, key)
        ttl = 86400 if key == 'last_update' else 3600  # last_update 保存 24h
        self._cache.set(cache_key, value, ttl=ttl)
        # 发布更新通知
        self._cache.publish('cache_update', {'key': key, 'timestamp': datetime.now().isoformat()})
    
    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default
    
    def update(self, other: Dict[str, Any]) -> None:
        for k, v in other.items():
            self[k] = v
    
    def keys(self):
        return self.KEYS.keys()


# 全局适配器实例（延迟初始化）
_data_cache_adapter = None


def get_data_cache_adapter() -> DataCacheAdapter:
    """获取兼容旧接口的缓存适配器"""
    global _data_cache_adapter
    if _data_cache_adapter is None:
        _data_cache_adapter = DataCacheAdapter()
    return _data_cache_adapter