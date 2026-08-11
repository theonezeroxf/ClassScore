# ClassScore 部署步骤

本文分别说明本地体验和 Linux 生产部署。示例域名为 `score.example.com`，部署目录为 `/opt/classscore`，请替换成自己的值。

## 一、本地开发部署

### 1. 准备环境

安装 Python 3.11 或更高版本、pip 和 venv：

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Windows PowerShell 激活命令为：

```powershell
.venv\Scripts\Activate.ps1
```

### 2. 初始化数据库

```bash
python manage.py check
python manage.py migrate --run-syncdb
python manage.py createsuperuser
```

按提示输入教师用户名、邮箱和密码。SQLite 数据保存到 `db.sqlite3`。

### 3. 启动与访问

```bash
python manage.py runserver 0.0.0.0:8000
```

浏览器打开：

- 教师登录：`http://127.0.0.1:8000/accounts/login/`
- Django 管理后台：`http://127.0.0.1:8000/admin/`

先创建班级并导入学生，再创建签到。手机访问电脑服务时，应使用电脑局域网 IP，并确保防火墙放行 8000 端口。多数手机浏览器在普通 HTTP 局域网页面会禁止 GPS；完整签到测试建议配置 HTTPS。

### 4. 运行测试

```bash
python manage.py test
```

## 二、Linux 生产部署（Gunicorn + Nginx + HTTPS）

> `runserver` 只用于开发。生产环境使用 Gunicorn 运行 Django，由 Nginx 处理公网连接、静态文件和 TLS。

### 1. 创建专用用户和目录

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin classscore
sudo mkdir -p /opt/classscore
sudo chown classscore:classscore /opt/classscore
sudo -u classscore git clone <你的仓库地址> /opt/classscore
cd /opt/classscore
```

### 2. 建立虚拟环境并安装依赖

```bash
sudo -u classscore python3 -m venv /opt/classscore/.venv
sudo -u classscore /opt/classscore/.venv/bin/pip install --upgrade pip
sudo -u classscore /opt/classscore/.venv/bin/pip install -r requirements.txt
sudo -u classscore /opt/classscore/.venv/bin/pip install gunicorn
```

也可以把 `gunicorn` 固定到生产专用 requirements 文件中。

### 3. 配置生产设置

当前仓库的 `SECRET_KEY` 是开发占位值且 `DEBUG=True`。生产部署前必须修改 `config/settings.py`，至少做到：

```python
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = ["score.example.com"]
CSRF_TRUSTED_ORIGINS = ["https://score.example.com"]
STATIC_ROOT = BASE_DIR / "staticfiles"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

生成随机密钥（不要把输出提交到 Git）：

```bash
python -c 'import secrets; print(secrets.token_urlsafe(64))'
```

推荐通过 systemd 的 `EnvironmentFile` 提供密钥：

```bash
sudo install -m 600 -o root -g root /dev/null /etc/classscore.env
sudo sh -c 'printf "%s\n" "DJANGO_SECRET_KEY=替换为随机密钥" > /etc/classscore.env'
```

### 4. 初始化数据库和收集静态文件

```bash
cd /opt/classscore
sudo -u classscore /opt/classscore/.venv/bin/python manage.py check --deploy
sudo -u classscore /opt/classscore/.venv/bin/python manage.py migrate --run-syncdb
sudo -u classscore /opt/classscore/.venv/bin/python manage.py collectstatic --noinput
sudo -u classscore /opt/classscore/.venv/bin/python manage.py createsuperuser
```

确保运行用户可写 SQLite 文件及其目录：

```bash
sudo chown -R classscore:classscore /opt/classscore
sudo chmod 750 /opt/classscore
```

### 5. 配置 systemd

创建 `/etc/systemd/system/classscore.service`：

```ini
[Unit]
Description=ClassScore Django application
After=network.target

[Service]
Type=simple
User=classscore
Group=classscore
WorkingDirectory=/opt/classscore
EnvironmentFile=/etc/classscore.env
ExecStart=/opt/classscore/.venv/bin/gunicorn config.wsgi:application \
  --workers 3 \
  --bind unix:/run/classscore.sock \
  --access-logfile - \
  --error-logfile -
RuntimeDirectory=classscore
RuntimeDirectoryMode=0755
Restart=on-failure
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

注意上例实际 socket 是 `/run/classscore.sock`；若希望放入 RuntimeDirectory，请统一改为 `/run/classscore/classscore.sock`，并在 Nginx 中使用相同地址。推荐后一种：

```ini
ExecStart=/opt/classscore/.venv/bin/gunicorn config.wsgi:application --workers 3 --bind unix:/run/classscore/classscore.sock
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now classscore
sudo systemctl status classscore
sudo journalctl -u classscore -f
```

### 6. 配置 Nginx

安装 Nginx，并创建 `/etc/nginx/sites-available/classscore`：

```nginx
server {
    listen 80;
    server_name score.example.com;

    client_max_body_size 10m;

    location /static/ {
        alias /opt/classscore/staticfiles/;
    }

    location /media/ {
        alias /opt/classscore/media/;
    }

    location / {
        include proxy_params;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/classscore/classscore.sock;
    }
}
```

启用并检查配置：

```bash
sudo ln -s /etc/nginx/sites-available/classscore /etc/nginx/sites-enabled/classscore
sudo nginx -t
sudo systemctl reload nginx
```

### 7. 配置 HTTPS

签到定位在生产环境必须使用 HTTPS。域名解析到服务器后，可用 Certbot：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d score.example.com
sudo certbot renew --dry-run
```

完成后使用 `https://score.example.com/accounts/login/` 登录，并用手机验证定位授权和签到。

## 三、发布新版本

部署前先备份。SQLite 在线复制可能得到不一致文件，推荐使用 SQLite 自带备份命令：

```bash
cd /opt/classscore
sudo -u classscore sqlite3 db.sqlite3 ".backup '/opt/classscore/db-$(date +%F-%H%M).sqlite3'"
```

更新步骤：

```bash
cd /opt/classscore
sudo -u classscore git pull --ff-only
sudo -u classscore /opt/classscore/.venv/bin/pip install -r requirements.txt
sudo -u classscore /opt/classscore/.venv/bin/python manage.py migrate --run-syncdb
sudo -u classscore /opt/classscore/.venv/bin/python manage.py collectstatic --noinput
sudo -u classscore /opt/classscore/.venv/bin/python manage.py test
sudo systemctl restart classscore
sudo systemctl status classscore
```

## 四、备份与恢复

至少备份：

- `db.sqlite3`：全部业务数据和用户；
- `media/`：未来可能加入的上传媒体；
- `/etc/classscore.env`：生产密钥（加密保存，不进入 Git）。

恢复时先停止服务，恢复数据库和媒体，再检查所有者：

```bash
sudo systemctl stop classscore
sudo cp /安全备份/db.sqlite3 /opt/classscore/db.sqlite3
sudo chown classscore:classscore /opt/classscore/db.sqlite3
sudo systemctl start classscore
```

## 五、常见故障检查

```bash
sudo systemctl status classscore                 # Gunicorn 是否运行
sudo journalctl -u classscore --since "10 min ago" # 应用错误
sudo nginx -t                                    # Nginx 配置语法
sudo tail -f /var/log/nginx/error.log            # 反向代理错误
curl --unix-socket /run/classscore/classscore.sock http://localhost/ # 绕过 Nginx 测试应用
```

- **400 Bad Request**：检查 `ALLOWED_HOSTS`。
- **403 CSRF verification failed**：检查 `CSRF_TRUSTED_ORIGINS`、代理 HTTPS 请求头和服务器时间。
- **静态文件 404**：重新执行 `collectstatic`，核对 `STATIC_ROOT` 与 Nginx `alias`。
- **GPS 不可用**：确认页面是 HTTPS、浏览器位置权限已开启、设备定位服务已开启。
- **502 Bad Gateway**：检查 Gunicorn 状态、socket 路径和 Nginx 对 socket 的访问权限。
- **SQLite database is locked**：减少 Gunicorn 写并发；用户量增长后应迁移到 PostgreSQL。
