FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# apt の インストール時の対話プロンプトを無効化
ENV DEBIAN_FRONTEND=noninteractive

# ==============================
# tool versions (docker-compose から注入)
# ==============================
ARG UV_VERSION
ARG TRIVY_VERSION
ARG GITLEAKS_VERSION

# ==============================
# base packages
# ==============================
# Codex CLI を入れるために nodejs / npm を追加
# ca-certificates / gnupg / apt-transport-https: APT repo 登録用
# コンテナ内部でgit操作しないので openssh-client は不要
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    ca-certificates \
    tar \
    apt-transport-https \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# ==============================
# Trivy install (root install)
# ==============================
# Trivy: 公式APTリポジトリを追加
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | \
    sh -s -- -b /tmp/bin "v${TRIVY_VERSION}" \
    && mv /tmp/bin/trivy /usr/local/bin/trivy \
    && trivy --version

# =========================
# Gitleaks (root install)
# =========================
RUN curl -fL -o /tmp/gitleaks.tar.gz \
    "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
    && tar -xzf /tmp/gitleaks.tar.gz -C /tmp \
    && mv /tmp/gitleaks /usr/local/bin/gitleaks \
    && chmod +x /usr/local/bin/gitleaks \
    && rm -f /tmp/gitleaks.tar.gz \
    && gitleaks version

USER vscode
WORKDIR /workspace

# ==============================
# uv install (user install)
# ==============================
RUN curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh

# コンテナの PATH 環境変数に設定して GithubActions も含めてどこからでも uv を使えるようにする
ENV PATH=/home/vscode/.local/bin:/home/vscode/.npm-global/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
