# 🔌 YLAI-AUTO-PLATFORM API 规范与文档

## 📋 目录
1. [API 规范](#api-规范)
2. [响应格式](#响应格式)
3. [错误处理](#错误处理)
4. [认证授权](#认证授权)
5. [速率限制](#速率限制)
6. [API 端点清单](#api-端点清单)

---

## API 规范

### RESTful 设计原则

所有 API 端点遵循 REST 规范：

| 方法 | 用途 | 示例 |
|------|------|------|
| `GET` | 获取资源 | `GET /api/tasks/{id}` |
| `POST` | 创建资源 | `POST /api/tasks` |
| `PUT` | 完全更新 | `PUT /api/tasks/{id}` |
| `PATCH` | 部分更新 | `PATCH /api/tasks/{id}` |
| `DELETE` | 删除资源 | `DELETE /api/tasks/{id}` |

### 版本管理

```
# API 版本在路径中
GET /api/v1/tasks
GET /api/v2/tasks

# 当前版本：v1 (默认)
# 兼容期：6 个月
# 弃用通知：在响应头中标注
X-API-Warn: Version 1 will be deprecated on 2026-07-07
```

### URL 规范

```
# 基础 URL
https://api.ylai.local/api/v1

# 资源访问
GET    /api/v1/tasks              # 列表
GET    /api/v1/tasks/{id}         # 单个
POST   /api/v1/tasks              # 创建
PUT    /api/v1/tasks/{id}         # 更新
DELETE /api/v1/tasks/{id}         # 删除

# 查询参数
GET /api/v1/tasks?page=1&size=10&sort=-created_at&filter=status:pending

# 参数说明
# - page: 页码（从 1 开始）
# - size: 每页数量（最大 100）
# - sort: 排序字段（前缀 - 为降序）
# - filter: 过滤条件（支持 key:value 格式）
```

---

## 响应格式

### 成功响应 (2xx)

```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "id": "task-001",
    "name": "Web Scraping",
    "status": "running",
    "created_at": "2026-01-07T12:00:00Z",
    "updated_at": "2026-01-07T12:30:00Z"
  },
  "meta": {
    "timestamp": "2026-01-07T12:30:45Z",
    "request_id": "req-uuid-12345",
    "version": "1.0.0"
  }
}
```

### 列表响应 (分页)

```json
{
  "code": 0,
  "message": "Success",
  "data": [
    { "id": "task-001", "name": "Task 1" },
    { "id": "task-002", "name": "Task 2" }
  ],
  "pagination": {
    "page": 1,
    "size": 10,
    "total": 250,
    "pages": 25
  },
  "meta": {
    "timestamp": "2026-01-07T12:30:45Z",
    "request_id": "req-uuid-12345"
  }
}
```

### 响应头

```
Content-Type: application/json; charset=utf-8
X-Request-ID: req-uuid-12345
X-Response-Time: 125ms
X-API-Version: 1.0.0
Cache-Control: no-cache, no-store, must-revalidate
```

---

## 错误处理

### 错误响应格式

```json
{
  "code": 4001,
  "message": "Resource not found",
  "error": {
    "type": "ResourceNotFoundError",
    "detail": "Task with id 'invalid-id' does not exist",
    "field": "id"
  },
  "meta": {
    "timestamp": "2026-01-07T12:30:45Z",
    "request_id": "req-uuid-12345",
    "documentation_url": "https://docs.ylai.local/errors/4001"
  }
}
```

### HTTP 状态码与错误码映射

| HTTP | 错误码 | 说明 |
|------|--------|------|
| 200 | 0 | 成功 |
| 201 | 0 | 创建成功 |
| 400 | 4000 | 请求参数无效 |
| 401 | 4001 | 未认证 |
| 403 | 4003 | 无权限 |
| 404 | 4004 | 资源不存在 |
| 409 | 4009 | 资源冲突 |
| 422 | 4022 | 数据验证失败 |
| 429 | 4029 | 请求过于频繁 |
| 500 | 5000 | 服务器内部错误 |
| 503 | 5003 | 服务不可用 |

### 错误代码清单

```
# 4xxx - 客户端错误
4000: ValidationError          # 验证错误
4001: AuthenticationError      # 认证失败
4003: PermissionError          # 权限不足
4004: ResourceNotFoundError    # 资源不存在
4009: ConflictError            # 资源冲突
4011: RateLimitError           # 请求过于频繁
4029: TooManyRequestsError     # 并发请求过多

# 5xxx - 服务器错误
5000: InternalServerError      # 内部错误
5001: DatabaseError            # 数据库错误
5002: ExternalServiceError     # 外部服务错误
5003: ServiceUnavailableError  # 服务不可用
```

---

## 认证授权

### JWT 令牌认证

```bash
# 1. 获取令牌
curl -X POST http://api.ylai.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"secret"}'

# 响应
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 3600,
  "token_type": "Bearer"
}

# 2. 使用令牌
curl -H "Authorization: Bearer {access_token}" \
  http://api.ylai.local/api/v1/tasks

# 3. 刷新令牌
curl -X POST http://api.ylai.local/api/v1/auth/refresh \
  -H "Authorization: Bearer {refresh_token}"
```

### 权限模型 (RBAC)

```
角色（Role）→ 权限（Permission）
┌─────────────────────────────────────┐
├─ Admin        → 所有权限            │
├─ User         → 查看、创建任务      │
├─ Guest        → 仅查看公开内容      │
└─ Manager      → 管理团队任务        │

权限（Permission）示例：
├─ task:read      # 读取任务
├─ task:create    # 创建任务
├─ task:update    # 更新任务
├─ task:delete    # 删除任务
├─ user:manage    # 管理用户
└─ system:admin   # 系统管理
```

---

## 速率限制

### 限制规则

```
# 全局限制
- 10,000 请求 / 小时 (所有用户)
- 1,000 请求 / 分钟 (单个用户)
- 100 请求 / 秒 (单个 IP)

# 响应头
X-RateLimit-Limit: 1000           # 限制数
X-RateLimit-Remaining: 999        # 剩余数
X-RateLimit-Reset: 1673088000    # 重置时间 (Unix 时间戳)
```

### 重试策略

```bash
# 当收到 429 (Too Many Requests) 响应时
# 1. 等待 X-RateLimit-Reset 时间
# 2. 或指数退避重试：2s, 4s, 8s, 16s ...

# 指数退避示例
for i in {1..5}; do
  sleep $((2 ** i))
  curl -H "Authorization: Bearer $TOKEN" \
    http://api.ylai.local/api/v1/tasks && break
done
```

---

## API 端点清单

### 认证相关

```
POST   /api/v1/auth/register      # 用户注册
POST   /api/v1/auth/login         # 用户登录
POST   /api/v1/auth/logout        # 用户登出
POST   /api/v1/auth/refresh       # 刷新令牌
POST   /api/v1/auth/password-reset # 重置密码
```

### 任务管理

```
GET    /api/v1/tasks              # 任务列表
POST   /api/v1/tasks              # 创建任务
GET    /api/v1/tasks/{id}         # 获取任务详情
PUT    /api/v1/tasks/{id}         # 更新任务
PATCH  /api/v1/tasks/{id}         # 部分更新任务
DELETE /api/v1/tasks/{id}         # 删除任务
GET    /api/v1/tasks/{id}/logs    # 获取任务日志
```

### 监控数据

```
GET    /api/v1/monitor/health     # 系统健康状态
GET    /api/v1/monitor/metrics    # 性能指标
GET    /api/v1/monitor/logs       # 系统日志
```

### WebSocket 端点

```
WS     /ws/tasks/{id}             # 实时任务进度
WS     /ws/monitor                # 实时监控数据
```

---

## 📚 使用示例

### Python 客户端

```python
import requests

class YLAIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def get_tasks(self, page=1, size=10):
        response = requests.get(
            f"{self.base_url}/api/v1/tasks",
            params={"page": page, "size": size},
            headers=self.headers
        )
        return response.json()
    
    def create_task(self, name, description):
        response = requests.post(
            f"{self.base_url}/api/v1/tasks",
            json={"name": name, "description": description},
            headers=self.headers
        )
        return response.json()

# 使用
client = YLAIClient("https://api.ylai.local", "your-token")
tasks = client.get_tasks()
```

### JavaScript 客户端

```javascript
class YLAIClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async getTasks(page = 1, size = 10) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/tasks?page=${page}&size=${size}`,
      { headers: { "Authorization": `Bearer ${this.apiKey}` } }
    );
    return response.json();
  }

  async createTask(name, description) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/tasks`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${this.apiKey}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ name, description })
      }
    );
    return response.json();
  }
}

// 使用
const client = new YLAIClient("https://api.ylai.local", "your-token");
const tasks = await client.getTasks();
```

---

**最后更新**: 2026-01-07  
**API 版本**: v1.0.0  
**状态**: ✅ 生产就绪
