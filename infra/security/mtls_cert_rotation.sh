#!/bin/bash
# 15.6 mTLS 证书轮换机制
# 混合云网络通道证书有效期 ≤ 90 天，本脚本实现自动轮换
#
# 使用场景：
#   私有化 DRP 节点 ←→ 公有云 Celery Worker 之间的 mTLS 通道
#
# 配置说明：
#   - CA 证书：自签名根 CA，有效期 3 年（手动轮换）
#   - 服务证书：有效期 90 天，由 CA 签发（自动轮换）
#   - 轮换触发：证书距过期 < 30 天时自动轮换
#
# 在 crontab 中配置：0 3 * * * /infra/security/mtls_cert_rotation.sh

set -euo pipefail

CERT_DIR="${CERT_DIR:-/etc/drp/certs}"
CA_CERT="${CERT_DIR}/ca.crt"
CA_KEY="${CERT_DIR}/ca.key"
SERVER_CERT="${CERT_DIR}/server.crt"
SERVER_KEY="${CERT_DIR}/server.key"
CLIENT_CERT="${CERT_DIR}/client.crt"
CLIENT_KEY="${CERT_DIR}/client.key"
CERT_DAYS=90
RENEW_BEFORE_DAYS=30
SERVICE_NAME="${SERVICE_NAME:-drp-backend}"
NOTIFY_EMAIL="${NOTIFY_EMAIL:-ops@example.com}"

mkdir -p "${CERT_DIR}"

# ── 函数：检查证书剩余有效期（天数）──
cert_days_remaining() {
    local cert_file="$1"
    if [ ! -f "${cert_file}" ]; then
        echo "0"
        return
    fi
    local expiry_date
    expiry_date=$(openssl x509 -noout -enddate -in "${cert_file}" | cut -d= -f2)
    local expiry_epoch
    expiry_epoch=$(date -d "${expiry_date}" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "${expiry_date}" +%s)
    local now_epoch
    now_epoch=$(date +%s)
    echo $(( (expiry_epoch - now_epoch) / 86400 ))
}

# ── 步骤 1：初始化 CA（仅首次运行）──
if [ ! -f "${CA_CERT}" ]; then
    echo "[$(date)] 初始化根 CA 证书（有效期 3 年）"
    openssl genrsa -out "${CA_KEY}" 4096
    openssl req -new -x509 -days 1095 \
        -key "${CA_KEY}" \
        -out "${CA_CERT}" \
        -subj "/C=CN/ST=Beijing/O=DRP/CN=DRP Root CA"
    echo "[$(date)] 根 CA 创建完成: ${CA_CERT}"
fi

# ── 步骤 2：检查并轮换服务端证书 ──
SERVER_DAYS_REMAINING=$(cert_days_remaining "${SERVER_CERT}")
echo "[$(date)] 服务端证书剩余有效期: ${SERVER_DAYS_REMAINING} 天"

if [ "${SERVER_DAYS_REMAINING}" -lt "${RENEW_BEFORE_DAYS}" ]; then
    echo "[$(date)] 服务端证书即将过期，开始轮换"

    # 备份旧证书
    if [ -f "${SERVER_CERT}" ]; then
        cp "${SERVER_CERT}" "${SERVER_CERT}.$(date +%Y%m%d).bak"
        cp "${SERVER_KEY}" "${SERVER_KEY}.$(date +%Y%m%d).bak"
    fi

    # 生成新私钥和 CSR
    openssl genrsa -out "${SERVER_KEY}.new" 2048
    openssl req -new \
        -key "${SERVER_KEY}.new" \
        -out "${CERT_DIR}/server.csr" \
        -subj "/C=CN/ST=Beijing/O=DRP/CN=${SERVICE_NAME}" \
        -addext "subjectAltName=DNS:${SERVICE_NAME},DNS:localhost,IP:127.0.0.1"

    # 由 CA 签发
    openssl x509 -req -days "${CERT_DAYS}" \
        -in "${CERT_DIR}/server.csr" \
        -CA "${CA_CERT}" \
        -CAkey "${CA_KEY}" \
        -CAcreateserial \
        -out "${SERVER_CERT}.new" \
        -extensions v3_req

    # 原子替换（先写新文件再 mv，避免中间状态）
    mv "${SERVER_KEY}.new" "${SERVER_KEY}"
    mv "${SERVER_CERT}.new" "${SERVER_CERT}"
    rm -f "${CERT_DIR}/server.csr"

    echo "[$(date)] 服务端证书轮换完成，新有效期 ${CERT_DAYS} 天"

    # 热重载（向服务发送 SIGHUP，部分服务支持无中断证书重载）
    if command -v systemctl &>/dev/null; then
        systemctl reload "${SERVICE_NAME}" 2>/dev/null || true
    fi

    # 发送通知
    echo "DRP mTLS 服务端证书已轮换，新证书有效至 $(openssl x509 -noout -enddate -in ${SERVER_CERT} | cut -d= -f2)" | \
        mail -s "[DRP] mTLS 证书轮换通知" "${NOTIFY_EMAIL}" 2>/dev/null || true
fi

# ── 步骤 3：检查并轮换客户端证书（Celery Worker 用）──
CLIENT_DAYS_REMAINING=$(cert_days_remaining "${CLIENT_CERT}")
echo "[$(date)] 客户端证书剩余有效期: ${CLIENT_DAYS_REMAINING} 天"

if [ "${CLIENT_DAYS_REMAINING}" -lt "${RENEW_BEFORE_DAYS}" ]; then
    echo "[$(date)] 客户端证书即将过期，开始轮换"

    openssl genrsa -out "${CLIENT_KEY}.new" 2048
    openssl req -new \
        -key "${CLIENT_KEY}.new" \
        -out "${CERT_DIR}/client.csr" \
        -subj "/C=CN/ST=Beijing/O=DRP/CN=drp-celery-worker"

    openssl x509 -req -days "${CERT_DAYS}" \
        -in "${CERT_DIR}/client.csr" \
        -CA "${CA_CERT}" \
        -CAkey "${CA_KEY}" \
        -CAcreateserial \
        -out "${CLIENT_CERT}.new"

    mv "${CLIENT_KEY}.new" "${CLIENT_KEY}"
    mv "${CLIENT_CERT}.new" "${CLIENT_CERT}"
    rm -f "${CERT_DIR}/client.csr"

    echo "[$(date)] 客户端证书轮换完成，新有效期 ${CERT_DAYS} 天"
fi

# ── 步骤 4：输出当前证书状态 ──
echo ""
echo "=== 证书状态摘要 ==="
for cert in "${CA_CERT}" "${SERVER_CERT}" "${CLIENT_CERT}"; do
    if [ -f "${cert}" ]; then
        expiry=$(openssl x509 -noout -enddate -in "${cert}" | cut -d= -f2)
        days=$(cert_days_remaining "${cert}")
        echo "  $(basename ${cert}): 过期时间 ${expiry}（剩余 ${days} 天）"
    fi
done
