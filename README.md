# koyun-ytdlp

可云视频下载工具是一个前后端分离的 yt-dlp 网页下载系统。它使用 Next.js 用户端和管理后台、FastAPI API、PostgreSQL、Redis/RQ、后台 Worker、定时清理与统计任务。

请仅下载你拥有权利或已获得授权的内容，禁止用于侵犯版权或违反平台规则的用途。

## 架构

- `frontend`: Next.js 15 + React + TypeScript + TailwindCSS
- `backend`: FastAPI + SQLAlchemy + Alembic
- `worker`: RQ Worker，执行 `yt-dlp` + `ffmpeg`
- `scheduler`: APScheduler，重置额度、清理文件、生成统计、处理卡死任务
- `postgres`: 保存用户、任务、文件、配置、日志、统计
- `redis`: 队列、限流、进度和取消标记

## 安装依赖

生产环境推荐 Docker Compose：

```sh
cp .env.example .env
mkdir -p data/downloads data/postgres logs
docker compose up -d --build
```

本地开发：

```sh
cd backend
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8100
```

```sh
cd frontend
npm install
npm run dev
```

## 配置环境变量

复制 `.env.example` 为 `.env`，至少修改：

- `POSTGRES_PASSWORD`
- `JWT_SECRET`
- `KOYUN_OAUTH_CLIENT_ID`
- `KOYUN_OAUTH_CLIENT_SECRET`
- `KOYUN_OAUTH_AUTHORIZE_URL`
- `KOYUN_OAUTH_TOKEN_URL`
- `KOYUN_OAUTH_USERINFO_URL`
- `KOYUN_OAUTH_REDIRECT_URI`

默认端口：

- 前端：`127.0.0.1:3100`
- 后端：`127.0.0.1:8100`

## 初始化数据库

Docker Compose 会在 backend 启动时自动执行：

```sh
alembic upgrade head
```

也可以手动执行：

```sh
docker compose exec backend alembic upgrade head
```

## 创建管理员

启动时会自动把 `ADMIN_EMAILS` 中配置的邮箱提升为管理员，默认包含 `4869150@qq.com`。也可以按邮箱手动创建或提升：

```sh
docker compose exec backend python -m app.scripts.make_admin --email 4869150@qq.com
```

可云 OAuth 登录后，可以按可云用户 ID 提升管理员：

```sh
docker compose exec backend python -m app.scripts.create_admin --koyun-user-id <KOYUN_USER_ID> --email admin@example.com --username Admin
```

## 启动服务

```sh
docker compose up -d --build
docker compose ps
```

访问：

- 用户端：`http://127.0.0.1:3100`
- API：`http://127.0.0.1:8100/api/health`
- API 文档：`http://127.0.0.1:8100/docs`
- 管理后台：`http://127.0.0.1:3100/admin`

## 配置 Caddy

示例见 [deploy/Caddyfile.example](deploy/Caddyfile.example)。

```caddy
download.shy521.com {
    encode gzip zstd

    reverse_proxy /api/* 127.0.0.1:8100
    reverse_proxy 127.0.0.1:3100
}
```

## 查看日志

```sh
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f scheduler
docker compose logs -f frontend
```

## 更新 yt-dlp

Worker 镜像内通过 pip 安装依赖。更新版本后重建：

```sh
docker compose build --no-cache worker backend
docker compose up -d
```

## API 文档

接口清单见 [backend/API.md](backend/API.md)，交互式文档由 FastAPI 自动生成在 `/docs`。

## 一键部署

```sh
sh deploy/bootstrap.sh
```

## 常见问题

1. OAuth 回调失败：确认 `KOYUN_OAUTH_REDIRECT_URI` 与可云后台配置完全一致。
2. 下载一直排队：检查 `docker compose logs -f worker` 和 Redis 健康状态。
3. ffmpeg 不可用：重建 backend/worker 镜像，镜像 Dockerfile 会安装 ffmpeg。
4. 域名被拒绝：管理后台的域名白名单默认开启，只允许默认平台和管理员添加的平台。
5. 文件无法下载：文件可能已过期，或当前用户不是任务拥有者。
