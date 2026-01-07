# 🚀 YLAI-AUTO-PLATFORM 生产部署指南

## 📋 目录
1. [部署前检查](#部署前检查)
2. [环境配置](#环境配置)
3. [Docker 部署](#docker-部署)
4. [Kubernetes 部署](#kubernetes-部署)
5. [监控与告警](#监控与告警)
6. [故障排查](#故障排查)
7. [灾难恢复](#灾难恢复)

---

## 部署前检查

### ✅ 检查清单

- [ ] 代码已提交到 git 仓库
- [ ] 所有依赖已在 requirements.txt 中声明且版本已锁定
- [ ] 环境变量配置已准备（.env.production）
- [ ] SSL/TLS 证书已获取
- [ ] 数据库备份策略已制定
- [ ] 监控告警规则已配置
- [ ] 日志存储容量已预留
- [ ] 容灾计划已制定

### 必要工具

```bash
# 验证工具可用性
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
kubectl version --client  # kubectl 1.27+（Kubernetes 部署时）
curl --version            # curl 7.0+
```

---

## 环境配置

### 1. 准备环境变量

```bash
# 从模板生成生产环境配置
cp backend/.env.example backend/.env.production

# 编辑敏感配置
nano backend/.env.production
```

### 2. 关键环境变量说明

| 变量 | 示例值 | 说明 |
|------|-------|------|
| `ENV` | production | 运行环境 |
| `SECRET_KEY` | `your-256-char-secret` | JWT 签名密钥（256 字符最小） |
| `DATABASE_URL` | `postgresql://user:pass@db:5432/ylai` | 生产数据库连接 |
| `REDIS_URL` | `redis://redis:6379/0` | 缓存服务地址 |
| `LOG_LEVEL` | INFO | 日志级别（生产推荐 INFO） |
| `API_WORKERS` | 8 | uvicorn 工作进程数（=CPU核心×2+1） |

### 3. 生成安全的 SECRET_KEY

```bash
# 生成 256 字符的随机密钥
python -c "import secrets; print(secrets.token_urlsafe(192))"
```

---

## Docker 部署

### 单主机部署

```bash
# 1. 克隆仓库
git clone <repository-url>
cd YLAI-AUTO-PLATFORM

# 2. 构建镜像
docker-compose -f docker/docker-compose.prod.yml build

# 3. 启动服务
docker-compose -f docker/docker-compose.prod.yml up -d

# 4. 验证部署
docker-compose -f docker/docker-compose.prod.yml ps
curl http://localhost:8001/health
```

### 多主机集群部署 (Docker Swarm)

```bash
# 1. 初始化 Swarm
docker swarm init

# 2. 添加工作节点
docker swarm join --token <token> <manager-ip>:2377

# 3. 部署堆栈
docker stack deploy -c docker/docker-compose.prod.yml ylai

# 4. 监控服务
docker stack services ylai
docker service logs ylai_backend
```

### 服务健康检查

```bash
# 检查后端健康状态
curl -s http://localhost:8001/health | jq .

# 预期响应
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2026-01-07T12:00:00Z"
}

# 查看容器日志
docker-compose -f docker/docker-compose.prod.yml logs -f backend

# 进入容器调试
docker exec -it ylai-backend-prod bash
```

---

## Kubernetes 部署

### 1. 准备 Kubernetes 清单

```bash
# 创建命名空间
kubectl create namespace ylai-prod

# 创建 ConfigMap（非敏感配置）
kubectl create configmap ylai-config \
  --from-literal=ENV=production \
  --from-literal=LOG_LEVEL=INFO \
  -n ylai-prod

# 创建 Secret（敏感数据）
kubectl create secret generic ylai-secrets \
  --from-literal=SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(192))') \
  --from-literal=DB_PASSWORD=$(openssl rand -base64 32) \
  --from-literal=REDIS_PASSWORD=$(openssl rand -base64 32) \
  -n ylai-prod
```

### 2. 部署应用

```bash
# 应用部署清单
kubectl apply -f k8s/deployment.yml -n ylai-prod
kubectl apply -f k8s/service.yml -n ylai-prod
kubectl apply -f k8s/ingress.yml -n ylai-prod

# 验证部署
kubectl get pods -n ylai-prod
kubectl get svc -n ylai-prod
```

### 3. 弹性伸缩配置

```bash
# 创建 HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment ylai-backend \
  --min=3 --max=10 \
  --cpu-percent=70 \
  -n ylai-prod

# 监控自动扩展
kubectl get hpa -n ylai-prod --watch
```

---

## 监控与告警

### Prometheus 指标

访问 http://localhost:9090 查看以下关键指标：

```promql
# API 响应时间 (p95)
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# 错误率
rate(http_requests_total{status=~"5.."}[5m])

# 活跃连接数
http_connections_active

# 数据库查询时间
db_query_duration_seconds
```

### Grafana 仪表板

1. 访问 http://localhost:3000
2. 默认用户：`admin`
3. 导入预置仪表板：[Dashboard ID: 1860]

### 告警规则

编辑 `monitoring/prometheus.yml`:

```yaml
groups:
  - name: ylai-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "Database server is down"
```

---

## 故障排查

### 常见问题

#### 1. 容器无法启动

```bash
# 查看详细日志
docker logs ylai-backend-prod

# 常见原因：
# - 数据库连接失败 → 检查 DATABASE_URL
# - 端口被占用 → 检查 sudo lsof -i :8001
# - 权限问题 → 检查文件权限：chmod 755 data/ logs/
```

#### 2. API 响应缓慢

```bash
# 监控系统资源
docker stats ylai-backend-prod

# 检查数据库性能
psql -h localhost -U ylai -d ylai_prod -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# 查看 Prometheus 指标
# 访问 http://localhost:9090 查询：
# - http_request_duration_seconds
# - db_query_duration_seconds
```

#### 3. Redis 连接失败

```bash
# 验证 Redis 连接
redis-cli -h redis -p 6379 PING

# 检查 Redis 内存
redis-cli INFO memory

# 清理过期键
redis-cli FLUSHDB
```

---

## 灾难恢复

### 备份策略

```bash
# 1. 数据库备份（每日）
docker exec ylai-postgres pg_dump \
  -U ylai ylai_prod > backup-$(date +%Y%m%d).sql

# 2. 应用数据备份
tar -czf app-data-$(date +%Y%m%d).tar.gz data/

# 3. 配置备份
tar -czf config-$(date +%Y%m%d).tar.gz \
  backend/.env.production \
  docker/docker-compose.prod.yml
```

### 恢复流程

```bash
# 1. 停止应用
docker-compose -f docker/docker-compose.prod.yml down

# 2. 恢复数据库
docker-compose -f docker/docker-compose.prod.yml up postgres redis
sleep 10
docker exec ylai-postgres psql -U ylai < backup-20260107.sql

# 3. 恢复应用数据
tar -xzf app-data-20260107.tar.gz

# 4. 启动应用
docker-compose -f docker/docker-compose.prod.yml up -d
```

### 蓝绿部署（零停机更新）

```bash
# 1. 启动新版本（绿）
docker-compose -f docker/docker-compose.prod.yml up -d --scale backend=2

# 2. 等待新服务就绪
docker wait $(docker ps -q --filter "label=version=green")

# 3. 切换流量（使用 nginx）
docker exec nginx nginx -s reload

# 4. 移除旧版本（蓝）
docker-compose -f docker/docker-compose.prod.yml down --scale backend=1
```

---

## 📊 性能优化

### 数据库优化

```sql
-- 创建必要索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);

-- 启用查询分析
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
SELECT pg_reload_conf();
```

### Redis 优化

```bash
# 配置 Redis 过期策略
CONFIG SET maxmemory-policy allkeys-lru
CONFIG REWRITE

# 启用 AOF 持久化
CONFIG SET appendonly yes
CONFIG SET appendfsync everysec
```

### 应用优化

```python
# 在 backend/app.py 中配置
app.add_middleware(
    GZipMiddleware, 
    minimum_size=1000,  # 启用 gzip 压缩
)

# 启用缓存
@cache(expire=3600)
def get_expensive_data():
    pass
```

---

## 📞 技术支持

遇到问题？检查以下资源：

- 📖 文档：[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- 🐛 问题追踪：[GitHub Issues](https://github.com/hil6626/YLAI-AUTO-PLATFORM/issues)
- 💬 讨论：[GitHub Discussions](https://github.com/hil6626/YLAI-AUTO-PLATFORM/discussions)

---

**更新于**: 2026-01-07  
**版本**: 1.0.0  
**状态**: ✅ 生产就绪
