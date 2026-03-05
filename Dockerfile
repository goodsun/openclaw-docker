# bon-soleil OpenClaw base image
# Mephi-approved version (98/100) — Phase 1 ready

FROM node:22-slim

# タイムゾーン
ENV TZ=Asia/Tokyo
RUN apt-get update && apt-get install -y tzdata git wget python3 python3-pip python3-venv && \
    ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    echo "Asia/Tokyo" > /etc/timezone && \
    pip3 install --break-system-packages google-generativeai pillow requests && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# OpenClaw インストール（バージョン固定）
RUN npm install -g openclaw@2026.3.2

# エントリーポイントスクリプト追加
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# OpenClaw用ディレクトリ作成（rootで作成してからnode所有権に）
RUN mkdir -p /home/node/.openclaw && \
    chown -R node:node /home/node

# 非rootユーザーで実行（セキュリティ）
USER node
WORKDIR /home/node

# 環境変数
ENV HOME=/home/node
ENV OPENCLAW_WORKSPACE=/home/node/workspace

# ボリュームマウントポイント
VOLUME ["/home/node/workspace", "/home/node/sessions", "/home/node/config"]

# ポート
EXPOSE 18789

# ヘルスチェック（Mephi requirement）
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --spider -q http://localhost:18789/health || exit 1

# エントリーポイント
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["openclaw", "gateway"]
