# 前端构建阶段 - 多阶段构建
FROM node:20-alpine AS builder

WORKDIR /app

# 接收构建时参数
ARG VITE_API_KEY
ENV VITE_API_KEY=$VITE_API_KEY

# 复制 package 文件
COPY package*.json ./

# 安装依赖 (使用 legacy-peer-deps 解决依赖冲突)
RUN npm ci --legacy-peer-deps

# 复制源码
COPY . .

# 写入 .env 文件供 Vite 读取 (ENV 变量在构建时不一定被 Vite 拾取)
RUN echo "VITE_API_KEY=${VITE_API_KEY}" > .env && cat .env

# 同时写入 .env.production 确保生产模式构建时读取
RUN echo "VITE_API_KEY=${VITE_API_KEY}" > .env.production

# 也设置环境变量直接传给 Vite (双重保险)
ENV VITE_API_KEY=${VITE_API_KEY}

# 构建生产版本 (Vite 会在构建时嵌入 VITE_API_KEY)
# 显式传递环境变量确保 Vite 拾取
RUN VITE_API_KEY=${VITE_API_KEY} npm run build

# 生产阶段 - Nginx
FROM nginx:alpine AS production

# 复制构建产物
COPY --from=builder /app/build /usr/share/nginx/html

# 修复权限: 确保 nginx worker 可读 assets
RUN chmod -R 755 /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost/health || exit 1

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]