"""考试成绩 CSV/XLSX 导入与逐行校验服务。"""

from core.services.import_students import _frame


def import_exam(upload, batch):
    from grades.models import ExamScore

    df = _frame(upload).rename(
        columns={"学号": "student_no", "姓名": "name", "考试成绩": "exam_score"}
    )
    if not {"student_no", "name", "exam_score"} <= set(df.columns):
        raise ValueError("文件必须包含学号、姓名和考试成绩")
    result = {"created": 0, "updated": 0, "errors": [], "warnings": []}
    for i, row in df.iterrows():
        no = str(row.student_no).strip()
        try:
            student = batch.class_room.students.get(student_no=no)
            score = float(row.exam_score)
            assert 0 <= score <= 100
        except Exception:
            result["errors"].append(f"第 {i+2} 行：学号不存在或成绩无效")
            continue
        if student.name.strip() != str(row["name"]).strip():
            result["warnings"].append(f"{no} 姓名不一致，以学号为准")
        _, created = ExamScore.objects.update_or_create(
            batch=batch, student=student, defaults={"exam_score": score}
        )
        result["created" if created else "updated"] += 1
    return result
