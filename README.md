# ClassScore — Django 课堂签到与成绩管理系统

面向教师的课堂管理系统：分班导入学生、二维码定位签到、课堂随机抽人加分、考试成绩导入、异常平时分建议修正、正态性优化与 XLSX 导出。学生无需账户，通过不可预测的签到 token 访问签到页；服务端综合校验时间、位置、身份及设备。

## 新手学习与部署文档

* [`notes.md`](notes.md)：Django 必备知识、请求流程、ORM、表单、权限以及本项目各业务实现导读。
* [`steps.md`](steps.md)：从本地初始化到 Gunicorn、Nginx、HTTPS、备份恢复的具体部署步骤。

## 环境与安装

要求 Python 3.11+。建议使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 初始化与启动

```bash
python manage.py migrate --run-syncdb
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

访问 `http://127.0.0.1:8000/accounts/login/`，使用教师账户登录。首次使用依次新建班级、导入学生，再创建签到或导入成绩。

## 导入文件

* 学生名单支持 `.csv`/`.xlsx`，不超过 10 MB；列名为 `学号, 姓名`（可选 `班级`），或 `student_no, name`。一个文件导入当前页面选择的班级；重复学号会更新姓名。为可靠保留前导零，建议在 Excel 中将学号列设为文本。
* 考试成绩支持 `.csv`/`.xlsx`；列名为 `学号, 姓名, 考试成绩`，或 `student_no, name, exam_score`。按学号匹配，分数须在 0–100。

## 签到与定位

教师填写课堂中心经纬度、时间窗口和半径（默认 200 米），系统生成二维码。学生扫码输入学号姓名并授权浏览器定位。普通网页无法绝对阻止代签；系统通过随机 token、Haversine 距离、时间窗口、设备指纹、学生/设备场次唯一约束，并记录 IP、User-Agent 和位置来提高代签成本。除 localhost 外，浏览器定位在生产环境通常要求 **HTTPS**。

## 成绩生成

可选考试:平时比例 `7:3`、`6:4`、`5:5`。原始平时分为班级基础分（默认 60）加课堂回答分，最高 100，始终保留。系统以 IQR 和 Z-Score 识别异常值，先生成小幅修正建议，再在 0–100 边界内用正态分位目标优化最终成绩，并用 Shapiro-Wilk 检验（少于 3 人不检验）。教师可手动修改修正平时分，所有结果可导出 XLSX。

## 测试

```bash
python manage.py test
```
