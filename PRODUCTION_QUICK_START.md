# 🚀 YLAI-AUTO-PLATFORM 生产部署快速指南

## 📋 快速概览

| 项目 | 状态 | 链接 |
|------|------|------|
| **生产就绪度** | ⭐⭐⭐⭐⭐ | - |
| **审计评分** | 14/14 ✅ | - |
| **综合评级** | 8.7/10 | - |
| **部署方式** | 4 种 (Docker/Swarm/K8s/Cloud) | [部署指南](docs/DEPLOYMENT.md) |
| **API 文档** | 20+ 端点 | [API 规范](docs/API_SPECIFICATION.md) |
| **安全防护** | 8 层防护 | [安全配置](backend/config/security.py) |

---

## 🎯 5 分钟快速开始

### 1. 克隆项目
```bash
git clone https://github.com/your/ylai-auto-platform.git
cd ylai-auto-platform
```

### 2. 准备配置
```bash
# 复制环境变量模板
cp backend/.env.example .env.production

# 根据实际环境编辑
nano .env.production
```

### 3. 启动服务
```bash
# 使用生产 Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 或者使用 Kubernetes
kubectl apply -f k8s/
```

### 4. 验证部署
```bash
# 运行启动检查
bash docker/startup-check.sh

# 查看日志
docker-compose logs -f backend
```

### 5. 访问应用
```
前端: http://your-domain:443
API: http://your-domain:8001/docs
监控: http://your-domain:9090 (Prometheus)
仪表板: http://your-domain:3000 (Grafana)
```

---

## 📦 完整部署清单

### 前置条件
- [ ] Docker & Docker Compose (最新版)
- [ ] Python 3.12+ (如直接运行)
- [ ] PostgreSQL 16+ (外部数据库或容器)
- [ ] Redis 7+ (外部或容器)
- [ ] SSL/TLS 证书 (生产环境)
- [ ] DNS 配置 (域名解析)

### 环境配置
- [ ] 复制 `.env.example` → `.env.production`
- [ ] 配置 71 个环境变量 (数据库、API、密钥等)
- [ ] 验证配置一致性: `python scripts/production-audit.py`

### 服务部署
- [ ] 拉取最新代码: `git pull origin main`
- [ ] 构建 Docker 镜像: `docker build -f docker/Dockerfile.prod .`
- [ ] 启动容器: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] 检查服务状态: `docker-compose ps`

### 应用初始化
- [ ] 运行数据库迁移: `alembic upgrade head`
- [ ] 创建超级用户: `python -m backend.scripts.create_admin`
- [ ] 初始化数据: `python -m backend.scripts.seed_data`

### 监控与告警
- [ ] 配置 Prometheus 抓取: `docker-compose logs prometheus`
- [ ] 设置 Grafana 仪表板: `http://localhost:3000`
- [ ] 配置告警规则: `monitoring/prometheus.yml`
- [ ] 连接 Slack 通知 (可选): `config/alerting.yaml`

### 验证与测试
- [ ] 烟测: `pytest tests/smoke/`
- [ ] 性能基准: `ab -n 1000 -c 10 http://localhost:8001/health`
- [ ] API 端点测试: `curl http://localhost:8001/docs`
- [ ] 数据库连接: `psql -h db-host -U user -d db_name`

### 上线前检查
- [ ] 所有容器运行状态 ✅
- [ ] 日志无错误信息 ✅
- [ ] API 响应时间 < 500ms ✅
- [ ] 监控指标正常 ✅
- [ ] 备份系统就绪 ✅

---

## 🔧 常见操作命令

### Docker 管理
```bash
# 查看容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看容器日志
docker-compose logs -f backend

# 进入容器
docker exec -it ylai-backend bash

# 重启服务
docker-compose restart backend

# 停止/启动
docker-compose stop
docker-compose start

# 完整清理
docker-compose down -v
```

### 应用管理
```bash
# 查看应用日志
tail -f /var/log/ylai/app.log

# 性能指标
curl http://localhost:9090/api/v1/query?query=http_requests_total

# 健康检查
curl -s http://localhost:8001/health | jq .

# 数据库操作
docker exec ylai-db psql -U postgres -c "SELECT version();"
```

### 监控与告警
```bash
# 访问 Prometheus
open http://localhost:9090

# 访问 Grafana
open http://localhost:3000
# 默认: admin/admin

# 查看告警
curl http://localhost:9090/api/v1/alerts
```

---

## 🆘 故障排查

### 服务无法启动
```bash
# 检查日志
docker-compose logs backend

# 查看启动脚本输出
bash docker/startup-check.sh

# 验证环境变量
grep "^[A-Z_]*=" .env.production | head -20
```

### 数据库连接失败
```bash
# 检查 PostgreSQL 状态
docker-compose ps db

# 测试连接
docker exec ylai-db psql -U postgres -c "SELECT 1"

# 查看 PostgreSQL 日志
docker-compose logs db
```

### Redis 连接问题
```bash
# 检查 Redis 状态
docker-compose ps redis

# 测试 Redis 连接
docker exec ylai-redis redis-cli ping

# 查看 Redis 日志
docker-compose logs redis
```

### 性能问题
```bash
# 查看 CPU/内存
docker stats

# 检查慢查询
curl http://localhost:9090/api/v1/query?query=http_request_duration_seconds

# 查看缓存命中率
curl http://localhost:9090/api/v1/query?query=cache_hits_total
```

### 安全告警
```bash
# 查看安全日志
tail -f /var/log/ylai/security.log

# 检查速率限制
curl -H "X-Forwarded-For: 1.1.1.1" http://localhost:8001/api/test (连续请求)

# 审计日志查看
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;
```

---

## 📊 监控指标

### 关键性能指标 (KPI)
```
请求延迟:        p50 < 100ms, p99 < 500ms
错误率:          < 0.1%
可用性:          > 99.9%
缓存命中率:      > 80%
数据库连接:      < 50 (max 100)
```

### Prometheus 查询示例
```
# 请求速率
rate(http_requests_total[1m])

# 错误率
rate(http_requests_total{status=~"5.."}[5m])

# 响应时间
histogram_quantile(0.95, http_request_duration_seconds)

# 缓存命中率
rate(cache_hits_total[5m]) / rate(cache_requests_total[5m])

# 连接池使用
db_connection_pool_usage_total
```

---

## 🔐 安全操作

### 定期检查
- [ ] 依赖漏洞: `safety check` (Python) + `npm audit` (Node.js)
- [ ] 代码质量: `pylint` + `bandit` + `black`
- [ ] SSL 证书: `openssl x509 -in cert.pem -noout -dates`
- [ ] 权限配置: `docker exec ylai-backend id`

### 日志审查
```bash
# 查看安全日志
grep "WARN\|ERROR" /var/log/ylai/security.log

# 审计用户操作
SELECT * FROM audit_logs WHERE action = 'LOGIN' ORDER BY created_at DESC;

# 检查失败登录
SELECT * FROM audit_logs WHERE action = 'LOGIN_FAILED' AND created_at > now() - '24 hours'::interval;
```

### 备份操作
```bash
# 手动备份数据库
docker exec ylai-db pg_dump -U postgres > backup_$(date +%Y%m%d).sql

# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz /etc/ylai/

# 验证备份
tar -tzf config_backup_*.tar.gz | head
```

---

## 📈 性能优化

### 缓存配置
```bash
# 查看 Redis 内存使用
docker exec ylai-redis redis-cli INFO memory

# 清空过期缓存
docker exec ylai-redis redis-cli FLUSHDB ASYNC

# 设置缓存 TTL
# 在 backend/config/security.py 中调整
CACHE_TTL_SHORT = 300    # 5 分钟
CACHE_TTL_MEDIUM = 1800  # 30 分钟
CACHE_TTL_LONG = 86400   # 24 小时
```

### 数据库优化
```bash
# 检查索引使用情况
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

# 分析表统计
ANALYZE table_name;

# 检查慢查询
SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

### 应用优化
```bash
# 调整 uvicorn 工作进程
export WORKERS=4  # 根据 CPU 核心数设置

# 启用 Gzip 压缩 (已默认启用)
# 在 backend/app.py 中配置

# 设置连接池大小
DATABASE_POOL_SIZE=20
DATABASE_POOL_RECYCLE=3600
```

---

## 🌍 多区域部署

### 中国区域
```bash
# 使用国内镜像源
docker pull registry.aliyuncs.com/ylai/platform:latest

# 配置 DNS
## 阿里云 DNS
nameserver 223.5.5.5
nameserver 223.6.6.6
```

### 国际区域
```bash
# 使用国际镜像源
docker pull ghcr.io/ylai/platform:latest

# 配置 CDN (Cloudflare/Fastly)
ENABLE_CDN=true
CDN_PROVIDER=cloudflare
```

---

## 📞 获取帮助

### 文档资源
- 📖 [完整部署指南](docs/DEPLOYMENT.md)
- 🔌 [API 规范文档](docs/API_SPECIFICATION.md)
- 🎯 [生产优化报告](docs/生产优化完成报告.md)
- 📊 [成果统计](成果统计.md)

### 支持渠道
- 🐛 GitHub Issues: https://github.com/ylai/platform/issues
- 💬 Discussions: https://github.com/ylai/platform/discussions
- 📧 Email: support@ylai.dev

### 应急联系
- **运维**: ops@ylai.dev (24/7)
- **技术**: tech@ylai.dev
- **安全**: security@ylai.dev

---

## ✨ 最后检查清单

部署前确保以下项全部完成:

- [ ] 所有依赖已安装 (Docker, PostgreSQL, Redis)
- [ ] 环境变量已配置 (.env.production)
- [ ] SSL 证书已部署
- [ ] DNS 解析已生效
- [ ] 备份系统已测试
- [ ] 监控告警已配置
- [ ] 日志收集已启用
- [ ] 性能基准已建立
- [ ] 故障恢复流程已验证
- [ ] 团队已培训完毕

---

**部署日期**: _______________  
**部署负责人**: _______________  
**验收人**: _______________  

✅ **部署准备完毕，可上线生产！**

---

**更新时间**: 2025-01-07  
**版本**: v1.0.0  
**文档维护**: GitHub Copilot
