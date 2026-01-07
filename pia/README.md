# PIA VPN（容器内 OpenVPN 方式）

本目录提供在 Debian 容器中使用 OpenVPN 连接 Private Internet Access（PIA）的最简方案。

## 目录结构
- `credentials.example.txt`：凭据模板，复制为 `credentials.txt` 并填入账号/密码。
- `ovpn/`：放置 PIA 提供的 `.ovpn` 配置文件（各地区）。
- 使用脚本：`../scripts/vpn_openvpn.sh`。

## 使用步骤
1. 安装依赖（容器内）：
   ```bash
   sudo apt update && sudo apt install -y openvpn unzip curl
   ```

2. 准备凭据：
   ```bash
   cd /workspaces/YLAI-AUTO-PLATFORM/pia
   cp credentials.example.txt credentials.txt
   # 编辑 credentials.txt，将第一行改为 PIA 用户名，第二行改为密码
   chmod 600 credentials.txt
   ```

3. 导入配置：
   - 将 PIA 官方下载的 OpenVPN 配置包（zip）解压后，把 `.ovpn` 文件放到 `pia/ovpn/` 目录；或单独复制所需地区的 `.ovpn` 到该目录。

4. 启动 VPN（需要容器具备 NET_ADMIN 与 /dev/net/tun）：
   ```bash
   # 进入工作区根目录
   cd /workspaces/YLAI-AUTO-PLATFORM
   # 选择一个地区（例如 us_chicago.ovpn），名称以实际文件为准
   REGION_OVPN="pia/ovpn/us_chicago.ovpn" \
   ./scripts/vpn_openvpn.sh start "$REGION_OVPN"
   ```

5. 检查状态与 IP：
   ```bash
   ./scripts/vpn_openvpn.sh status
   curl -s https://ipinfo.io/ip
   ```

6. 断开连接：
   ```bash
   ./scripts/vpn_openvpn.sh stop
   ```

## 容器权限要求
运行容器时应添加：
- `--cap-add=NET_ADMIN`
- `--device /dev/net/tun`

若使用 docker compose，可在服务中增加：
```yaml
cap_add:
  - NET_ADMIN
devices:
  - /dev/net/tun
```

## 注意事项
- 官方 PIA 客户端依赖桌面环境/systemd，不适合在普通容器中运行；此方案使用 OpenVPN 直连。
- `.ovpn` 中可加入 `auth-user-pass /workspaces/YLAI-AUTO-PLATFORM/pia/credentials.txt` 以免交互输入。
- 如需全局走 VPN，请在宿主机安装官方客户端更稳妥；本方案只影响此容器的网络。
