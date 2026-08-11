# Django 知识速查与本项目实现导读

本文面向第一次接触 Django 的读者。建议一边阅读本文，一边运行项目并按文中路径查看源代码。

## 1. Django 在项目中负责什么

Django 是一个采用 **MTV（Model–Template–View）** 模式的 Python Web 框架：

- **Model（模型）**：用 Python 类描述数据库表、字段、关系和约束。本项目的模型位于三个应用的 `models.py`。
- **Template（模板）**：带有 Django 模板语法的 HTML，负责把视图传来的上下文渲染成页面，位于 `templates/`。
- **View（视图）**：接收 HTTP 请求、执行业务逻辑并返回 HTML、JSON 或文件，位于各应用的 `views.py`。
- **URLconf（路由）**：把 URL 映射到视图。总入口是 `config/urls.py`，再分发到各应用的 `urls.py`。

一次请求的典型流程是：

```text
浏览器 → config/urls.py → app/urls.py → views.py
      → forms.py 校验输入 → models.py/服务层访问数据库
      → template 渲染 HTML → 浏览器
```

## 2. 项目与应用的区别

- `config/` 是 **Django 项目配置**，管理整个站点的设置、总路由和部署入口。
- `core/`、`attendance/`、`grades/` 是 **Django 应用**，分别封装班级学生、签到抽人、成绩管理三个业务领域。
- `manage.py` 是管理命令入口，它会设置 `DJANGO_SETTINGS_MODULE=config.settings`，然后调用 Django。

这种拆分让每个应用保持单一职责，也便于分别测试。

## 3. 设置文件 `config/settings.py`

最重要的配置包括：

- `INSTALLED_APPS`：启用 Django 自带应用和三个业务应用。只有注册后，Django 才会发现模型、模板、管理后台等。
- `MIDDLEWARE`：请求/响应的处理链。认证、Session、CSRF 防护都由中间件提供。
- `DATABASES`：本项目使用 SQLite，数据文件为根目录的 `db.sqlite3`。
- `TEMPLATES`、`STATIC_URL`、`MEDIA_ROOT`：分别配置模板、CSS/JavaScript 静态文件和用户媒体文件。
- `USE_TZ=True`：数据库时间使用带时区时间；业务代码通过 `timezone.now()` 比较签到窗口，避免直接使用 `datetime.now()`。
- `LOGIN_REDIRECT_URL`：登录后回到仪表盘。

当前项目把三个业务应用加入 `MIGRATION_MODULES` 并设置为 `None`，因此首次执行 `migrate --run-syncdb` 时由 Django 同步创建业务表；Django 自带认证表仍使用标准迁移。正式长期维护时，建议删除该配置，再运行 `makemigrations` 生成版本化迁移文件并提交到 Git。

## 4. 模型、ORM 与关系

模型类继承 `django.db.models.Model`。常见字段：

- `CharField`：短文本；必须给出 `max_length`。
- `DecimalField`：适合成绩等要求十进制精度的数据。
- `DateTimeField(auto_now_add=True)`：创建时自动写入时间。
- `ForeignKey`：多对一关系，例如多个学生属于一个班级。

本项目主要关系：

```text
User 1 ── N ClassRoom 1 ── N Student
ClassRoom 1 ── N AttendanceSession 1 ── N AttendanceRecord
Student 1 ── N QuestionDrawRecord
ClassRoom 1 ── N ExamBatch 1 ── N ExamScore / FinalScore
```

`related_name` 用于反向查询。例如 `classroom.students.all()` 得到班级全部学生，`student.draw_records.all()` 得到学生全部课堂回答记录。

ORM 常用写法：

```python
Student.objects.create(class_room=room, student_no="001", name="张三")
student = room.students.filter(student_no="001").first()
room = get_object_or_404(ClassRoom, pk=pk, teacher=request.user)
```

`UniqueConstraint` 在数据库层确保同班学号、同场学生签到、同场设备签到等规则。即使两个请求同时到达，也只有一个能写入成功；视图捕获 `IntegrityError` 后显示重复签到。

## 5. 表单与输入校验

Django 表单把“不可信的请求数据”转换成经过验证的 Python 数据：

```python
form = SignForm(request.POST)
if form.is_valid():
    latitude = form.cleaned_data["lat"]
```

不要直接相信 `request.POST`。`is_valid()` 会检查必填、类型、长度等规则，`cleaned_data` 只能在校验成功后使用。`ModelForm` 可根据模型自动生成字段，并通过 `save(commit=False)` 暂缓保存，以补充当前教师等不可由浏览器指定的字段。

所有 POST HTML 表单都包含 `{% csrf_token %}`。CSRF token 防止其他网站冒用已登录教师的身份发起修改请求。JavaScript `fetch` 请求则通过 `X-CSRFToken` 请求头提交 token。

## 6. 登录、权限和数据隔离

- `@login_required` 保护所有教师端视图；未登录时会跳转登录页。
- 学生扫码 URL `/s/<token>/` 特意不加 `login_required`。
- 查询教师资源时同时限制 `teacher=request.user`，例如 `get_object_or_404(ClassRoom, pk=pk, teacher=request.user)`。不能只按主键查询，否则教师可能通过修改 URL 访问他人的班级。
- Django 登录使用 Session：服务器在 Session 中保存用户身份，浏览器只保存 Session Cookie。

## 7. 模板语法

模板默认自动转义变量，降低 XSS 风险：

```django
{% extends "base.html" %}
{% block content %}
  <h1>{{ classroom.name }}</h1>
  {% for student in classroom.students.all %}
    <p>{{ student.student_no }} {{ student.name }}</p>
  {% empty %}
    <p>暂无学生</p>
  {% endfor %}
{% endblock %}
```

- `{{ value }}` 输出变量。
- `{% tag %}` 执行循环、判断、URL 反向解析等模板指令。
- `{% extends %}` 和 `{% block %}` 实现页面继承；公共导航在 `base.html`。
- `{% url 'class-detail' classroom.pk %}` 根据路由名称生成 URL，避免把地址硬编码在多个页面。

## 8. 文件导入为何放在服务层

视图负责 HTTP，`core/services/import_students.py` 和 `grades/services/import_exam.py` 负责可复用业务逻辑：

1. 只接受 `.csv` 和 `.xlsx`，限制 10 MB。
2. pandas 读取为字符串，尽可能保留文本学号。
3. 中文列名统一映射为内部英文名。
4. 逐行校验并累计新增、更新、错误和警告。
5. `update_or_create` 让重复学号更新而不是重复插入。

服务函数不依赖模板，因此可以直接单元测试，也可将来被管理命令或 API 重用。

> Excel 若把 `001` 本身保存成数字 `1`，读取程序无法推断被删除的两个零。制作表格时应把学号列设为“文本”。

## 9. 签到的完整实现

### 9.1 创建与二维码

教师创建 `AttendanceSession` 后，模型自动生成 UUID token。详情视图使用当前域名组成 `/s/<token>/` 链接，再由 `qrcode` 生成 PNG 并以 Base64 内嵌页面。

### 9.2 浏览器定位与设备标识

`static/js/attendance.js` 调用 Geolocation API，把经纬度写进隐藏字段。它还在 `localStorage` 保存随机 `device_id`。生产环境中定位通常只允许 HTTPS 页面。

### 9.3 后端校验顺序

签到视图依次检查：

1. 场次启用且当前时间在开始、结束之间；
2. 学号和姓名在当前班级匹配；
3. Haversine 公式计算的距离不超过半径；
4. `sha256(token + device_id + user_agent)` 生成设备哈希；
5. 数据库唯一约束阻止学生或设备在同一场重复签到。

网页无法绝对阻止代签，设备 ID 和 GPS 也可能被技术用户伪造；这些措施用于提高代签成本并留下审计信息。

## 10. 随机抽人和平时分

`attendance/services/draw.py` 构造候选集：指定签到场次时只包含有效签到学生，并排除该场已产生抽取记录的学生；不指定场次时使用班级全部学生。服务器使用 `random.choice` 决定结果，前端滚动动画只负责展示，不能决定最终人选。

抽中后教师提交 `score_delta`。模型验证范围为 1–3，视图也使用白名单检查。原始平时分在生成成绩时计算：

```text
min(100, 班级基础分 + 该学生所有回答加分之和)
```

## 11. 最终成绩算法

`grades/services/score_adjustment.py` 的步骤如下：

1. 使用 IQR 与样本 Z-Score 检测平时分异常值；IQR 为 0 时仅使用 Z-Score。
2. 把 IQR 异常值夹到上下边界，保留原始平时分不覆盖。
3. 按初始综合成绩排序，为每个名次生成正态分位数 `z`。
4. 使用 SciPy SLSQP 优化正态分布的 `mu`、`sigma`，目标是让修正平时分与建议值的平方差最小。
5. 约束修正平时分和最终分均在 0–100；优化失败则退回基础建议值。
6. 3–5000 个样本使用 Shapiro-Wilk 检验；`p >= 0.05` 表示没有证据认为它显著偏离正态分布，而不是证明数据“一定正态”。

成绩比例 `7:3` 表示考试 70%、平时 30%，其他比例同理。教师手动修改修正平时分时，后端会用同一比例重新计算最终成绩。

## 12. 测试怎么工作

`TestCase` 会创建隔离的测试数据库，每个测试结束后回滚，不会污染开发数据库。常见断言：

- `assertEqual`：比较 Python 值；
- `assertContains`：检查响应 HTML；
- Django test client：模拟 GET/POST、登录和请求头；
- `reverse()`：通过 URL 名称生成测试地址。

运行全部测试：

```bash
python manage.py test
```

只运行某个应用：

```bash
python manage.py test attendance
```

## 13. 推荐阅读顺序

1. `config/settings.py` 和 `config/urls.py`：理解应用注册与路由入口。
2. 三个 `models.py`：画出数据关系。
3. 各应用 `forms.py`：理解输入边界。
4. `core/views.py`：从简单 CRUD 和文件上传开始。
5. `attendance/views.py`：理解公开页面、权限、GPS 和数据库约束。
6. `grades/services/score_adjustment.py`：最后阅读数值算法。
7. `templates/` 与 `static/js/`：把后端上下文与浏览器交互对应起来。
8. 三个 `tests.py`：从测试反向确认业务规则。

## 14. 开发时常用命令

```bash
python manage.py check               # 检查配置和模型问题
python manage.py shell               # 带 Django 环境的 Python Shell
python manage.py show_urls           # 本项目未安装该扩展，默认不可用
python manage.py test                # 测试
python manage.py runserver           # 开发服务器（不要用于生产）
```

进入 shell 后可用 ORM 探索数据：

```python
from core.models import ClassRoom
ClassRoom.objects.all()
ClassRoom.objects.prefetch_related("students").first().students.all()
```
