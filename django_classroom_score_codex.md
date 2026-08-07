# Django 课堂签到与成绩管理系统 Codex 执行文档

## 1. 给 Codex 的执行要求

请在一个空目录中实现一个可运行的 Python Web 项目。项目使用 Django 和 SQLite，面向教师使用，学生不需要登录，只通过课堂二维码进入签到页面。

不要停留在方案说明。需要直接创建项目文件、数据库模型、页面、业务逻辑、导入导出、测试和启动说明。实现完成后运行迁移和测试，保证本地可以启动。

项目名称建议：

```text
classroom_score_system
```

核心目标：

1. 分班级导入学生信息，支持 `.xlsx` 和 `.csv`。
2. 学生课堂扫码签到，填写学号、姓名，自动获取签到位置，并尽量防止代签。
3. 当前班级随机抽取学生回答问题，根据回答情况加平时分 1、2、3 分，并提供抽取学号动画。
4. 导入考试成绩 `.xlsx` 或 `.csv`，按 `七三`、`六四`、`五五` 比例生成最终成绩。最终成绩需要尽量符合正态分布。系统必须保留原始平时分和修正平时分，并给出平时分异常值修正建议。

## 2. 已确认需求和默认规则

### 2.1 已确认

| 项目 | 规则 |
| --- | --- |
| Web 框架 | Django |
| 数据库 | SQLite |
| 登录角色 | 只有老师登录 |
| 学生导入字段 | 班级、学号、姓名 |
| 导入方式 | 老师在页面选择班级，一个文件导入一个班级 |
| 正态分布要求 | 不固定均值和标准差，只要求最终成绩整体接近正态分布 |
| 平时分修正 | 先找异常值，再给出建议修正值，修正幅度尽量小 |

### 2.2 默认规则

| 项目 | 默认规则 |
| --- | --- |
| 学号重复 | 同一班级内学号唯一，重复导入时更新姓名 |
| 签到防代签 | GPS 定位、签到时间窗口、签到 token、设备指纹、同一设备同一场只能签一次 |
| 拍照签到 | 默认不做 |
| 签到地点 | 老师创建签到时使用当前位置，也允许手动输入经纬度 |
| 签到范围 | 默认 200 米，可在创建签到时修改 |
| 随机抽人范围 | 默认从本次已签到学生中抽取 |
| 同一节课重复抽取 | 默认不重复 |
| 回答加分 | 固定 `+1`、`+2`、`+3` 三档，可填写备注 |
| 考试成绩字段 | 学号、姓名、考试成绩 |
| 考试成绩数量 | 默认只有一个考试成绩 |
| 成绩比例 | 老师生成成绩时选择，比例含义为 `考试成绩:平时分` |
| 平时分原始分 | 默认 `60 + 课堂回答累计加分`，最高 100 分 |

## 3. 技术栈

请使用：

```text
Python 3.11+
Django 5.x
SQLite
Django Templates
HTML + CSS + JavaScript
pandas
openpyxl
numpy
scipy
qrcode[pil]
Pillow
```

不要引入复杂前端框架。页面使用 Django 模板即可。CSS 和 JavaScript 放在 `static/` 中。

## 4. 初始化命令

Codex 应在空目录中执行类似命令：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install django pandas openpyxl numpy scipy qrcode[pil] pillow
django-admin startproject config .
python manage.py startapp core
python manage.py startapp attendance
python manage.py startapp grades
```

生成 `requirements.txt`：

```text
Django>=5.0,<6.0
pandas>=2.0
openpyxl>=3.1
numpy>=1.26
scipy>=1.11
qrcode[pil]>=7.4
Pillow>=10.0
```

## 5. 项目结构

建议结构：

```text
classroom_score_system/
├── manage.py
├── requirements.txt
├── README.md
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── services/
│   │   └── import_students.py
│   └── tests.py
├── attendance/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── services/
│   │   ├── geo.py
│   │   └── draw.py
│   └── tests.py
├── grades/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── services/
│   │   ├── import_exam.py
│   │   └── score_adjustment.py
│   └── tests.py
├── templates/
│   ├── base.html
│   ├── registration/login.html
│   ├── core/
│   ├── attendance/
│   └── grades/
├── static/
│   ├── css/app.css
│   └── js/
│       ├── attendance.js
│       └── draw_animation.js
└── media/
```

## 6. 数据模型

### 6.1 core.models

创建 `ClassRoom`：

字段：

```text
name: CharField，班级名称
teacher: ForeignKey(User)
regular_base_score: DecimalField，默认 60
created_at: DateTimeField
updated_at: DateTimeField
```

创建 `Student`：

字段：

```text
class_room: ForeignKey(ClassRoom)
student_no: CharField，学号
name: CharField，姓名
created_at: DateTimeField
updated_at: DateTimeField
```

约束：

```text
同一 class_room 下 student_no 唯一
```

### 6.2 attendance.models

创建 `AttendanceSession`：

```text
class_room: ForeignKey(ClassRoom)
title: CharField
token: UUIDField，唯一
center_lat: DecimalField
center_lng: DecimalField
radius_m: PositiveIntegerField，默认 200
start_time: DateTimeField
end_time: DateTimeField
is_active: BooleanField
created_by: ForeignKey(User)
created_at: DateTimeField
```

创建 `AttendanceRecord`：

```text
session: ForeignKey(AttendanceSession)
student: ForeignKey(Student)
student_no_snapshot: CharField
student_name_snapshot: CharField
lat: DecimalField
lng: DecimalField
distance_m: FloatField
device_hash: CharField
ip_address: GenericIPAddressField，允许为空
user_agent: TextField
status: CharField，可选 valid、duplicate_student、duplicate_device、out_of_range、expired
signed_at: DateTimeField
```

约束：

```text
同一 session 下 student 唯一
同一 session 下 device_hash 唯一
```

创建 `QuestionDrawRecord`：

```text
class_room: ForeignKey(ClassRoom)
attendance_session: ForeignKey(AttendanceSession, null=True, blank=True)
student: ForeignKey(Student)
score_delta: PositiveSmallIntegerField，只允许 1、2、3
remark: CharField，允许为空
drawn_at: DateTimeField
created_by: ForeignKey(User)
```

业务规则：

```text
同一个 AttendanceSession 内已经抽过的学生不再进入候选池
如果没有传 AttendanceSession，则按当前班级抽取，但也要避免本轮重复
```

### 6.3 grades.models

创建 `ExamBatch`：

```text
class_room: ForeignKey(ClassRoom)
name: CharField
ratio: CharField，可选 7:3、6:4、5:5
created_by: ForeignKey(User)
created_at: DateTimeField
```

创建 `ExamScore`：

```text
batch: ForeignKey(ExamBatch)
student: ForeignKey(Student)
exam_score: DecimalField，0 到 100
created_at: DateTimeField
```

约束：

```text
同一 batch 下 student 唯一
```

创建 `FinalScore`：

```text
batch: ForeignKey(ExamBatch)
student: ForeignKey(Student)
exam_score: DecimalField
original_regular_score: DecimalField
adjusted_regular_score: DecimalField
final_score: DecimalField
is_regular_outlier: BooleanField
adjust_reason: TextField
normality_p_value: FloatField，允许为空
created_at: DateTimeField
```

约束：

```text
同一 batch 下 student 唯一
```

## 7. URL 和页面

### 7.1 老师端

实现以下页面：

| URL | 页面 |
| --- | --- |
| `/accounts/login/` | 老师登录 |
| `/` | 首页仪表盘 |
| `/classes/` | 班级列表 |
| `/classes/create/` | 新建班级 |
| `/classes/<id>/` | 班级详情 |
| `/classes/<id>/students/import/` | 导入学生 |
| `/attendance/create/` | 创建签到 |
| `/attendance/<id>/` | 签到详情和二维码 |
| `/attendance/<id>/records/` | 签到记录 |
| `/draw/<class_id>/` | 随机抽人页面 |
| `/grades/<class_id>/import/` | 导入考试成绩 |
| `/grades/batches/<id>/` | 成绩批次详情 |
| `/grades/batches/<id>/export/` | 导出最终成绩 |

### 7.2 学生扫码端

实现：

```text
/s/<token>/
```

页面内容：

```text
学号输入框
姓名输入框
自动定位状态
提交签到按钮
签到结果提示
```

学生页面不需要登录。

## 8. 功能一：分班级导入学生

### 8.1 导入规则

支持：

```text
.xlsx
.csv
```

字段支持中文列名：

```text
班级
学号
姓名
```

也支持英文列名：

```text
class_name
student_no
name
```

由于老师已经在页面选择班级，导入时以页面选择的班级为准。文件里的班级列可以存在，但不作为最终分班依据。

### 8.2 校验规则

必须校验：

```text
学号不能为空
姓名不能为空
学号转成字符串保存，不能因为 Excel 数字格式丢失前导 0
同一班级内学号重复时更新姓名
导入完成后显示新增数量、更新数量、失败行数、失败原因
```

## 9. 功能二：学生扫码签到

### 9.1 创建签到

老师创建签到时需要填写：

```text
班级
签到标题
签到开始时间
签到结束时间
签到中心纬度
签到中心经度
允许范围，默认 200 米
```

页面提供按钮：

```text
使用当前位置
生成签到二维码
```

二维码内容为：

```text
http://当前域名/s/<token>/
```

### 9.2 学生签到流程

学生扫码打开页面后：

1. 输入学号和姓名。
2. 浏览器调用 Geolocation API 获取经纬度。
3. 前端把学号、姓名、经纬度、device_id 提交给后端。
4. 后端校验 token、时间窗口、学生身份、地理范围、设备唯一性。
5. 校验通过后创建 `AttendanceRecord`。

### 9.3 防代签实现

网页端不能绝对阻止代签，但必须实现以下组合校验：

```text
签到链接 token 随机且不可猜
签到必须在 start_time 和 end_time 之间
学生学号和姓名必须匹配
签到位置距离课堂中心点不能超过 radius_m
同一学生同一场签到只能成功一次
同一设备同一场签到只能成功一次
记录 IP、User-Agent、设备哈希、经纬度、距离和签到时间
```

前端生成或读取 `localStorage.device_id`，后端计算：

```text
device_hash = sha256(session_token + device_id + user_agent)
```

### 9.4 距离计算

不要依赖第三方地图服务。使用 Haversine 公式计算两点距离，单位为米。

## 10. 功能三：随机抽人和平时分

### 10.1 抽取规则

默认从当前课堂已签到学生中抽取。如果没有选择签到场次，则从当前班级全部学生中抽取。

同一节课内已经抽过的学生不再进入候选池。

### 10.2 抽取动画

页面显示一个大号学号区域：

```text
点击“开始抽取”
学号快速滚动 2 到 3 秒
逐渐减速
最终停在被抽中的学生
显示姓名和学号
```

动画用 JavaScript 实现，文件放在：

```text
static/js/draw_animation.js
```

### 10.3 加平时分

抽中学生后，老师选择：

```text
+1
+2
+3
```

可以填写备注。提交后创建 `QuestionDrawRecord`。

原始平时分计算：

```text
original_regular_score = min(100, class_room.regular_base_score + sum(score_delta))
```

默认基础分为 60 分。课堂回答加分累计，最高 100 分。

## 11. 功能四：考试成绩、平时分修正和最终成绩

### 11.1 考试成绩导入

支持：

```text
.xlsx
.csv
```

字段：

```text
学号
姓名
考试成绩
```

也支持英文：

```text
student_no
name
exam_score
```

导入规则：

```text
老师选择班级
老师选择成绩比例：7:3、6:4、5:5
按学号匹配学生
姓名不一致时给出警告，但以学号为准
考试成绩必须在 0 到 100
同一批次内重复学号时更新考试成绩
```

### 11.2 成绩比例

比例含义：

```text
7:3 = 考试成绩 70%，平时分 30%
6:4 = 考试成绩 60%，平时分 40%
5:5 = 考试成绩 50%，平时分 50%
```

公式：

```text
final_score = exam_weight * exam_score + regular_weight * adjusted_regular_score
```

## 12. 平时分异常值和正态分布算法

算法放在：

```text
grades/services/score_adjustment.py
```

### 12.1 输入

输入数据：

```text
student_id
exam_score
original_regular_score
ratio
```

### 12.2 第一步：计算原始平时分

对每个学生计算：

```text
original_regular_score = min(100, class_room.regular_base_score + sum(QuestionDrawRecord.score_delta))
```

保留该值，不能覆盖。

### 12.3 第二步：检测平时分异常值

同时使用 IQR 和 Z-Score：

```text
Q1 = 25% 分位数
Q3 = 75% 分位数
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
```

异常判断：

```text
regular_score < lower
regular_score > upper
或者样本标准差不为 0 且 abs(z_score) > 3
```

异常值建议修正：

```text
低于 lower 的建议修正到 lower
高于 upper 的建议修正到 upper
修正值限制在 0 到 100
保留 1 位小数
```

如果 `IQR = 0`，只使用 Z-Score；如果标准差也为 0，则不标记异常。

### 12.4 第三步：尽量小幅修正平时分

先得到一个基础建议值：

```text
regular_suggested_0
```

其中：

```text
非异常学生 = original_regular_score
异常学生 = IQR/Z-Score 修正建议值
```

然后基于 `regular_suggested_0` 做正态化优化，目标是：

```text
最终成绩尽量接近正态分布
平时分调整幅度尽量小
调整后的平时分仍在 0 到 100
尽量保持学生原始综合成绩排名
```

### 12.5 第四步：生成正态目标分布

计算初始综合成绩：

```text
initial_final = exam_weight * exam_score + regular_weight * regular_suggested_0
```

按 `initial_final` 从低到高排序，生成正态分位点：

```text
p_i = (rank_i - 0.5) / n
z_i = scipy.stats.norm.ppf(p_i)
```

不要固定均值和标准差。使用优化算法寻找最合适的 `mu` 和 `sigma`：

```text
target_final_i = mu + sigma * z_i
adjusted_regular_i = (target_final_i - exam_weight * exam_score_i) / regular_weight
```

优化目标：

```text
minimize sum((adjusted_regular_i - regular_suggested_0_i)^2)
```

约束：

```text
0 <= adjusted_regular_i <= 100
0 <= target_final_i <= 100
sigma > 0
```

可以使用：

```text
scipy.optimize.minimize
```

如果优化失败，降级策略：

1. 使用 `regular_suggested_0`。
2. 对最终成绩做正态性检测。
3. 在页面提示“当前考试成绩和平时分边界限制较强，无法通过小幅平时分修正完全正态化”。

### 12.6 第五步：正态性检测

使用 Shapiro-Wilk 检验：

```text
scipy.stats.shapiro(final_scores)
```

规则：

```text
样本数 n < 3：无法检验，显示样本过少
3 <= n <= 5000：使用 Shapiro-Wilk
p_value >= 0.05：认为没有显著偏离正态分布
p_value < 0.05：认为偏离正态分布，需要显示提示
```

最终保存：

```text
exam_score
original_regular_score
adjusted_regular_score
final_score
is_regular_outlier
adjust_reason
normality_p_value
```

### 12.7 页面展示要求

成绩批次详情页必须展示：

```text
学号
姓名
考试成绩
原始平时分
是否平时分异常
建议/修正平时分
最终成绩
修正原因
正态性检验结果
```

老师可以手动修改 `adjusted_regular_score`，修改后重新计算最终成绩和正态性检测。

## 13. 导出成绩

导出 `.xlsx`，文件名格式：

```text
班级名称_成绩批次名称_最终成绩.xlsx
```

导出字段：

```text
班级
学号
姓名
考试成绩
原始平时分
修正平时分
最终成绩
是否平时分异常
修正原因
正态性检验 p 值
```

可选增加 `.csv` 导出按钮。

## 14. 权限和安全

必须实现：

```text
老师端页面必须登录
老师只能管理自己创建的班级
学生扫码签到页不需要登录
上传文件限制扩展名，只允许 xlsx 和 csv
上传文件限制大小，建议最大 10 MB
所有表单使用 Django CSRF
所有输入做后端校验
生产环境提醒：浏览器定位功能需要 HTTPS
```

## 15. 页面体验

整体页面简洁，适合教师日常使用。不要做复杂花哨页面。

基础页面：

```text
顶部导航：首页、班级、签到、随机抽人、成绩
所有列表页面要有空状态提示
所有导入页面要显示导入结果
所有危险或失败操作要显示明确错误原因
```

签到二维码页面：

```text
显示二维码图片
显示签到链接
显示签到开始/结束时间
显示已签到人数/班级总人数
提供刷新记录按钮
```

随机抽人页面：

```text
醒目显示滚动学号
抽中后显示姓名
提供 +1、+2、+3 按钮
显示本节课已抽名单
```

## 16. 测试要求

至少实现以下测试：

### 16.1 学生导入测试

```text
csv 导入成功
xlsx 导入成功
重复学号更新姓名
缺少学号或姓名时报错
学号前导 0 不丢失
```

### 16.2 签到测试

```text
学生姓名学号匹配才能签到
超出时间不能签到
超出距离不能签到
同一学生不能重复签到
同一设备不能替不同学生签到
Haversine 距离计算正确
```

### 16.3 随机抽人测试

```text
只从已签到学生中抽取
同一节课不重复抽取
加 1、2、3 分后能正确累计
```

### 16.4 成绩测试

```text
考试成绩导入成功
成绩比例计算正确
原始平时分被保留
异常平时分能被识别
修正平时分不超出 0 到 100
最终成绩能生成
导出 xlsx 字段完整
```

## 17. README 要求

生成 `README.md`，必须包含：

```text
项目功能简介
安装依赖
数据库迁移
创建老师账号
启动服务
导入学生模板说明
签到定位说明
成绩生成说明
测试命令
```

示例命令：

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
python manage.py test
```

## 18. 验收标准

完成后必须满足：

```text
可以登录老师账号
可以创建班级
可以导入 xlsx/csv 学生名单
可以创建课堂签到并生成二维码
学生扫码后可以自动定位并签到
系统能限制同一学生重复签到
系统能限制同一设备替多名学生签到
老师可以从当前签到学生中随机抽人
抽取动画可见
老师可以给抽中学生加 1、2、3 平时分
可以导入考试成绩
可以选择 7:3、6:4、5:5 生成最终成绩
可以看到原始平时分、修正平时分、最终成绩
可以看到平时分异常值和修正原因
可以导出最终成绩 xlsx
测试通过
README 完整
```

## 19. 建议执行顺序

Codex 请按以下顺序实现：

1. 创建 Django 项目和三个 app。
2. 配置 settings、templates、static、media。
3. 实现 core 的班级和学生模型。
4. 实现老师登录和班级管理。
5. 实现学生 xlsx/csv 导入。
6. 实现签到模型、创建签到、二维码生成。
7. 实现学生扫码签到页面和定位 JS。
8. 实现设备指纹、地理距离、重复签到校验。
9. 实现随机抽人页面和动画。
10. 实现回答加分和平时分累计。
11. 实现考试成绩导入。
12. 实现平时分异常值检测和建议修正。
13. 实现最终成绩生成、正态化优化和正态性检测。
14. 实现成绩详情页和导出 xlsx。
15. 补充测试。
16. 运行迁移、测试和本地启动验证。

## 20. 重要说明

1. 不要把 Django 当成单纯 ORM。Django 是完整 Web 框架，包含 URL 路由、模板、表单、认证、ORM、后台管理等能力。本项目只使用 Django，不再同时使用 Flask。
2. “不允许帮同学签到”在普通网页中不能做到绝对防止，只能通过定位、设备、时间、token 和记录追踪提高代签成本。
3. “最终成绩符合正态分布”受样本量、考试成绩分布、分数边界和平时分调整幅度影响。实现时要尽量通过小幅修正平时分使最终成绩接近正态分布，同时保留所有原始数据和修正原因，保证可追溯。
4. 所有业务规则必须写在后端，前端只做交互辅助。
5. 所有文件导入都要给出清晰错误提示，不能静默失败。

