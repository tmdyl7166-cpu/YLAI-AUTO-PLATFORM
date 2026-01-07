#!/usr/bin/env bash
set -euo pipefail

# 简易 OpenVPN 管理脚本（PIA 示例）
# 用法：
#   ./scripts/vpn_openvpn.sh start /path/to/region.ovpn
#   ./scripts/vpn_openvpn.sh stop
#   ./scripts/vpn_openvpn.sh status
# 依赖：openvpn、/dev/net/tun、NET_ADMIN

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIA_DIR="$ROOT_DIR/pia"
LOG_FILE="/tmp/openvpn.log"
PID_FILE="/tmp/openvpn.pid"

ensure_deps() {
  if ! command -v openvpn >/dev/null 2>&1; then
    echo "[vpn] installing openvpn"
    sudo apt update && sudo apt install -y openvpn
  fi
}

preflight_check() {
  # 检查 /dev/net/tun 是否存在
  if [[ ! -e /dev/net/tun ]]; then
    echo "[vpn] ERROR: /dev/net/tun 不存在。请以 NET_ADMIN 能力并挂载 tun 设备运行容器："
    echo "        docker run --cap-add=NET_ADMIN --device /dev/net/tun ..."
    echo "        或在 docker-compose.yml 中添加 cap_add: [NET_ADMIN] 与 devices: [/dev/net/tun]"
    exit 1
  fi
  # 检查是否具备 sudo 或 root 权限
  if ! command -v sudo >/dev/null 2>&1; then
    if [[ "$(id -u)" != "0" ]]; then
      echo "[vpn] ERROR: 需要 root 或 sudo 来管理 openvpn 进程。"
      echo "        请在具备 sudo 的环境中运行，或以 root 用户登录容器。"
      exit 1
    fi
  fi
}

start_vpn() {
  local ovpn_file=${1:-}
  if [[ -z "$ovpn_file" ]]; then
    echo "[vpn] missing ovpn config path"; exit 1
  fi
  if [[ ! -f "$ovpn_file" ]]; then
    echo "[vpn] ovpn not found: $ovpn_file"; exit 1
  fi
  ensure_deps
  preflight_check

  local cred="$PIA_DIR/credentials.txt"
  if [[ ! -f "$cred" ]]; then
    echo "[vpn] missing credentials.txt; create from $PIA_DIR/credentials.example.txt"; exit 1
  fi

  # 确保 .ovpn 使用凭据文件
  if ! grep -q "^auth-user-pass" "$ovpn_file"; then
    echo "[vpn] injecting auth-user-pass into a temp config"
    local tmp_cfg="/tmp/ovpn.injected.conf"
    cp "$ovpn_file" "$tmp_cfg"
    echo "auth-user-pass $cred" >> "$tmp_cfg"
    ovpn_file="$tmp_cfg"
  fi

  echo "[vpn] starting openvpn with: $ovpn_file"
  sudo openvpn --config "$ovpn_file" --daemon --writepid "$PID_FILE" --log "$LOG_FILE"
  echo "[vpn] started. pid=$(cat "$PID_FILE") log=$LOG_FILE"
}

stop_vpn() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE")
    echo "[vpn] stopping pid=$pid"
    sudo kill "$pid" || true
    sleep 1
    if ps -p "$pid" >/dev/null 2>&1; then
      echo "[vpn] force kill"
      sudo kill -9 "$pid" || true
    fi
    rm -f "$PID_FILE"
  else
    echo "[vpn] no pid file: $PID_FILE"
  fi
}

status_vpn() {
  if [[ -f "$PID_FILE" ]] && ps -p "$(cat "$PID_FILE")" >/dev/null 2>&1; then
    echo "[vpn] running. pid=$(cat "$PID_FILE")"
  else
    echo "[vpn] not running"
  fi
  if [[ -f "$LOG_FILE" ]]; then
    echo "[vpn] recent logs:"; tail -n 30 "$LOG_FILE" || true
  fi
}

cmd=${1:-}
case "$cmd" in
  start)
    shift
    start_vpn "${1:-}"
    ;;
  stop)
    stop_vpn
    ;;
  status)
    status_vpn
    ;;
  *)
    echo "Usage: $0 {start <ovpn>|stop|status}"; exit 1
    ;;
 esac
