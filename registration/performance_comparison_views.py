from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, FloatField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode

from .models import (
    AcademicSession,
    Batch,
    Chapter,
    QuestionResponse,
    ReportPeriod,
    Student,
    StudentEnrollment,
    Test,
    TestQuestion,
    TestResult,
)


def _get_default_date_range() -> tuple[date, date]:
    period = ReportPeriod.objects.all().order_by("-end_date").first()
    if period:
        return period.start_date, period.end_date

    today = date.today()
    return today.replace(day=1), today


def _parse_date_range_or_default(request) -> tuple[date, date] | None:
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return None
        return start_date, end_date

    return _get_default_date_range()


def _get_active_session() -> AcademicSession | None:
    return AcademicSession.get_active()


def _batches_base_qs_for_user(request):
    """Return batches scoped to the user (teacher vs superuser).

    Avoids importing any models from the `center` app.
    """
    teacher_profile = getattr(request.user, "teachers", None)
    if teacher_profile and not request.user.is_superuser:
        return teacher_profile.batches.all().distinct()

    return Batch.objects.all()


def _distinct_options(qs, id_field: str, label_field: str, order_field: str):
    return list(qs.values(id_field, label_field).distinct().order_by(order_field))


def _get_batch_students(batch: Batch):
    enrollments_qs = StudentEnrollment.objects.filter(batch_links__batch=batch)
    if batch.session_id:
        enrollments_qs = enrollments_qs.filter(session_id=batch.session_id)
        if getattr(batch.session, "is_active", False):
            enrollments_qs = enrollments_qs.filter(active=True)

    student_ids = enrollments_qs.values_list("student_id", flat=True).distinct()
    return (
        Student.objects.filter(id__in=student_ids)
        .select_related("user")
        .order_by("user__first_name", "user__last_name")
    )


def _test_has_any_activity(test: Test, student: Student) -> bool:
    # Activity means at least one other student has a response/result.
    return (
        QuestionResponse.objects.filter(test=test).exclude(student=student).exists()
        or TestResult.objects.filter(test=test).exclude(student=student).exists()
    )


def _student_participated(test: Test, student: Student) -> bool:
    return (
        QuestionResponse.objects.filter(test=test, student=student).exists()
        or TestResult.objects.filter(test=test, student=student).exists()
    )


def _is_absent(test: Test, student: Student) -> bool:
    return _test_has_any_activity(test, student) and not _student_participated(test, student)


def _get_chapters_from_questions(test: Test) -> dict[int, str]:
    questions = TestQuestion.objects.filter(test=test).order_by("chapter_no")
    return {q.chapter_no: q.chapter_name for q in questions if q.chapter_no is not None}


def _calculate_marks(responses_qs, test: Test) -> dict[str, float]:
    obtained = float(responses_qs.aggregate(total=Coalesce(Sum("marks_obtained"), 0.0))[
        "total"
    ])

    total_max = float(getattr(test, "total_max_marks", 0) or 0)
    if total_max <= 0:
        total_max = float(
            TestQuestion.objects.filter(test=test, is_main=True).aggregate(
                total=Coalesce(Sum("max_marks"), 0.0)
            )["total"]
        )

    percentage = round((obtained / total_max) * 100, 2) if total_max > 0 else 0.0

    return {
        "obtained": obtained,
        "total": total_max,
        "percentage": percentage,
    }


def _calculate_testwise_remarks(testwise_responses, test_chapters: dict[int, str], is_objective: bool = False):
    chapter_keys = list(test_chapters.keys())

    chapter_wise_remarks = defaultdict(lambda: [0] * len(test_chapters))
    remarks_count = defaultdict(float)

    for response in testwise_responses:
        ch_no = response.question.chapter_no
        if ch_no not in test_chapters:
            continue

        idx = chapter_keys.index(ch_no)

        if is_objective:
            maxm = float(response.question.max_marks)
            obtained = float(response.marks_obtained)

            if obtained > 0:
                remark = "Correct"
                chapter_wise_remarks[remark][idx] += obtained
                remarks_count[remark] += obtained
            elif obtained < 0:
                remark = "Incorrect"
                chapter_wise_remarks[remark][idx] += abs(obtained)
                remarks_count[remark] += abs(obtained)

                # Track negative impact on correct as well (to keep net visible)
                chapter_wise_remarks["Correct"][idx] += obtained
                remarks_count["Correct"] += obtained
            else:
                remark = "Not Attempted"
                chapter_wise_remarks[remark][idx] += maxm
                remarks_count[remark] += maxm
            continue

        deducted = float(response.question.max_marks) - float(response.marks_obtained)

        chapter_wise_remarks["Correct"][idx] += float(response.marks_obtained)
        remarks_count["Correct"] += float(response.marks_obtained)

        if deducted == 0:
            continue

        if not response.remark:
            continue

        remark_name = response.remark.name
        chapter_wise_remarks[remark_name][idx] += deducted
        remarks_count[remark_name] += deducted

    total = sum(remarks_count.values())
    if total > 0:
        remarks_count = {k: round((v / total) * 100, 1) for k, v in remarks_count.items()}

    chapter_wise_remarks = dict(
        sorted(chapter_wise_remarks.items(), key=lambda item: item[0] != "Correct")
    )
    remarks_count = dict(sorted(remarks_count.items(), key=lambda item: item[1], reverse=True))

    return {
        "chapters": test_chapters,
        "remarks_count": remarks_count,
        "chapter_wise_remarks": chapter_wise_remarks,
    }


def _calculate_batch_chapter_remarks(student: Student, batch: Batch, start_date: date, end_date: date):
    chapters = {
        ch.chapter_no: ch.chapter_name
        for ch in Chapter.objects.filter(
            class_name=batch.class_name,
            subject=batch.subject,
        ).order_by("chapter_no")
    }

    if not chapters:
        return {
            "subject": batch.subject,
            "chapters": {},
            "remarks_count": {},
            "chapter_wise_remarks": {},
        }

    chapter_keys = list(chapters.keys())

    responses = (
        QuestionResponse.objects.filter(
            student=student,
            test__batch=batch,
            test__date__range=(start_date, end_date),
        )
        .select_related("question", "remark", "test")
        .order_by("test__date")
    )

    chapter_wise_remarks = defaultdict(lambda: [0] * len(chapters))
    remarks_count = defaultdict(float)

    for response in responses:
        ch_no = response.question.chapter_no
        if ch_no not in chapters:
            continue

        idx = chapter_keys.index(ch_no)

        if getattr(response.test, "objective", False):
            obtained = float(response.marks_obtained)
            if obtained > 0:
                remark = "Correct"
                chapter_wise_remarks[remark][idx] += obtained
                remarks_count[remark] += obtained
            elif obtained < 0:
                remark = "Incorrect"
                chapter_wise_remarks[remark][idx] += abs(obtained)
                remarks_count[remark] += abs(obtained)

                chapter_wise_remarks["Correct"][idx] += obtained
                remarks_count["Correct"] += obtained
            else:
                remark = "Not Attempted"
                chapter_wise_remarks[remark][idx] += float(response.question.max_marks)
                remarks_count[remark] += float(response.question.max_marks)
            continue

        deducted = float(response.question.max_marks) - float(response.marks_obtained)

        chapter_wise_remarks["Correct"][idx] += float(response.marks_obtained)
        remarks_count["Correct"] += float(response.marks_obtained)

        if deducted == 0:
            continue
        if not response.remark:
            continue

        remark_name = response.remark.name
        chapter_wise_remarks[remark_name][idx] += deducted
        remarks_count[remark_name] += deducted

    total = sum(remarks_count.values())
    if total > 0:
        remarks_count = {k: round((v / total) * 100, 1) for k, v in remarks_count.items()}

    chapter_wise_remarks = dict(
        sorted(chapter_wise_remarks.items(), key=lambda item: item[0] != "Correct")
    )
    remarks_count = dict(sorted(remarks_count.items(), key=lambda item: item[1], reverse=True))

    return {
        "subject": batch.subject,
        "chapters": chapters,
        "remarks_count": remarks_count,
        "chapter_wise_remarks": chapter_wise_remarks,
    }


def _build_batch_test_calendar(student: Student, batch: Batch, start_date: date, end_date: date):
    monthly_data: list[dict[str, Any]] = []

    doj = getattr(student, "doj", None)
    effective_start_date = max(start_date, doj) if doj else start_date

    tests = (
        Test.objects.filter(batch=batch, date__range=(effective_start_date, end_date))
        .order_by("date")
        .only("id", "date")
    )
    tests_by_date: dict[date, list[Test]] = defaultdict(list)
    for t in tests:
        tests_by_date[t.date].append(t)

    current = date(effective_start_date.year, effective_start_date.month, 1)
    last_date = date(end_date.year, end_date.month, calendar.monthrange(end_date.year, end_date.month)[1])

    while current <= last_date:
        year, month = current.year, current.month
        first_weekday, total_days = calendar.monthrange(year, month)
        first_weekday = (first_weekday + 1) % 7

        calendar_data = []
        week = [None] * first_weekday
        present_c, absent_c = 0, 0

        for day in range(1, total_days + 1):
            current_date = date(year, month, day)

            test_status = None
            if effective_start_date <= current_date <= end_date:
                date_tests = tests_by_date.get(current_date, [])
                if date_tests:
                    date_has_activity = any(_test_has_any_activity(t, student) for t in date_tests)
                    student_participated = any(_student_participated(t, student) for t in date_tests)

                    if date_has_activity and not student_participated:
                        test_status = "Absent"
                        absent_c += 1
                    elif student_participated:
                        test_status = "Present"
                        present_c += 1

            week.append({
                "date": current_date,
                "attendance": test_status,
            })

            if len(week) == 7:
                calendar_data.append(week)
                week = []

        if week:
            while len(week) < 7:
                week.append(None)
            calendar_data.append(week)

        if len(calendar_data) == 5:
            calendar_data.append([None] * 7)

        monthly_data.append({
            "calendar": calendar_data,
            "present_count": present_c,
            "absent_count": absent_c,
            "percentage": round((present_c / (present_c + absent_c) * 100) if (present_c + absent_c) > 0 else 0, 1),
            "month_name": calendar.month_name[month],
            "year": year,
        })

        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)

    return monthly_data


def _get_batch_subject_test_reports(student: Student, batch: Batch, start_date: date, end_date: date):
    doj = getattr(student, "doj", None)
    effective_start_date = max(start_date, doj) if doj else start_date

    tests = Test.objects.filter(
        batch=batch,
        date__range=(effective_start_date, end_date),
    ).order_by("date")

    percent_sum = 0.0
    test_count = 0
    present_count = 0
    absent_count = 0

    tests_by_date: dict[date, list[Test]] = defaultdict(list)
    for t in tests:
        tests_by_date[t.date].append(t)

    for test_date in sorted(tests_by_date.keys()):
        date_tests = tests_by_date[test_date]

        date_has_activity = any(_test_has_any_activity(t, student) for t in date_tests)
        student_participated = any(_student_participated(t, student) for t in date_tests)

        if date_has_activity and not student_participated:
            absent_count += 1
            continue

        if student_participated:
            present_count += 1
            for t in date_tests:
                test_result = TestResult.objects.filter(test=t, student=student).first()
                if test_result and test_result.percentage is not None:
                    percent_sum += float(test_result.percentage)
                    test_count += 1

    if test_count > 0:
        scored = round((percent_sum / test_count), 2)
        deducted = round(100 - scored, 2)
    else:
        scored = 0.0
        deducted = 0.0

    test_reports = []
    for t in tests:
        responses = QuestionResponse.objects.filter(test=t, student=student).select_related(
            "question", "remark"
        )
        test_reports.append({
            "test": t,
            "is_absent": _is_absent(t, student),
            "marks_data": _calculate_marks(responses, t),
            "remarks": _calculate_testwise_remarks(
                responses,
                _get_chapters_from_questions(t),
                is_objective=getattr(t, "objective", False),
            ),
        })

    return {
        "subject": batch.subject,
        "test_reports": test_reports,
        "subject_summary": _calculate_batch_chapter_remarks(student, batch, effective_start_date, end_date),
        "subject_calendar": _build_batch_test_calendar(student, batch, effective_start_date, end_date),
        "scored": round(scored, 2),
        "deducted": round(deducted, 2),
        "present": present_count or 0,
        "absent": absent_count or 0,
        "present_percentage": round(
            (present_count / (present_count + absent_count) * 100)
            if (present_count + absent_count) > 0
            else 0,
            2,
        ),
        "absent_percentage": round(
            (absent_count / (present_count + absent_count) * 100)
            if (present_count + absent_count) > 0
            else 0,
            2,
        ),
    }


@login_required(login_url="login")
def student_performance_comparison(request):
    date_range = _parse_date_range_or_default(request)
    if date_range is None:
        return redirect("student_performance_comparison")
    start_date, end_date = date_range

    session_id = request.GET.get("session_id")
    class_id = request.GET.get("class_id")
    subject_id = request.GET.get("subject_id")
    section_id = request.GET.get("section_id")
    batch_id = request.GET.get("batch_id")

    base_qs_all_sessions = _batches_base_qs_for_user(request).select_related(
        "class_name", "subject", "section", "session"
    )

    active_session = _get_active_session()
    selected_session = None
    if session_id:
        selected_session = AcademicSession.objects.filter(id=session_id).first()
    if selected_session is None:
        selected_session = active_session

    if selected_session:
        batches_base_qs = base_qs_all_sessions.filter(session=selected_session)
    else:
        batches_base_qs = base_qs_all_sessions

    session_options = list(
        AcademicSession.objects.all().order_by("-start_date").values("id", "name")
    )

    # Options are built from what's available for the user.
    class_options = _distinct_options(
        batches_base_qs, "class_name_id", "class_name__name", "class_name__name"
    )

    filtered_batches = batches_base_qs
    if class_id:
        filtered_batches = filtered_batches.filter(class_name_id=class_id)

    subject_options = _distinct_options(
        filtered_batches, "subject_id", "subject__name", "subject__name"
    )

    if subject_id:
        filtered_batches = filtered_batches.filter(subject_id=subject_id)

    section_options = _distinct_options(
        filtered_batches, "section_id", "section__name", "section__name"
    )

    if section_id:
        filtered_batches = filtered_batches.filter(section_id=section_id)

    batch_options = filtered_batches.order_by(
        "class_name__name", "subject__name", "section__name"
    )

    selected_batch = None
    if batch_id:
        selected_batch = batch_options.filter(id=batch_id).first()
    elif class_id and subject_id and section_id and selected_session:
        # Batch is unique for (class, subject, section, session)
        selected_batch = batch_options.first()

    student_rows: list[dict[str, Any]] = []
    tests_with_activity_count = 0

    if selected_batch:
        students_qs = _get_batch_students(selected_batch)
        student_ids = list(students_qs.values_list("id", flat=True))

        tests_qs = Test.objects.filter(
            batch=selected_batch,
            date__range=(start_date, end_date),
        )
        tests_with_activity_qs = tests_qs.filter(
            Q(results__isnull=False) | Q(responses__isnull=False)
        ).distinct()

        tests_with_activity_count = tests_with_activity_qs.count()
        active_test_ids = list(tests_with_activity_qs.values_list("id", flat=True))

        results_agg = (
            TestResult.objects.filter(test_id__in=active_test_ids, student_id__in=student_ids)
            .values("student_id")
            .annotate(
                sum_obtained=Coalesce(
                    Sum("total_marks_obtained"), Value(0.0), output_field=FloatField()
                ),
                sum_max=Coalesce(
                    Sum("test__total_max_marks"), Value(0.0), output_field=FloatField()
                ),
                present_tests=Coalesce(Count("id"), Value(0)),
            )
        )
        results_by_student = {row["student_id"]: row for row in results_agg}

        common_query_params = {
            "session_id": str(selected_session.id) if selected_session else "",
            "class_id": class_id or "",
            "subject_id": subject_id or "",
            "section_id": section_id or "",
            "batch_id": str(selected_batch.id),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

        for stu in students_qs:
            agg = results_by_student.get(
                stu.id,
                {"sum_obtained": 0.0, "sum_max": 0.0, "present_tests": 0},
            )
            sum_max = float(agg["sum_max"])
            avg_score = (
                round((float(agg["sum_obtained"]) / sum_max) * 100, 2) if sum_max > 0 else 0.0
            )
            present_tests = int(agg["present_tests"]) if agg["present_tests"] is not None else 0
            absent_tests = max(tests_with_activity_count - present_tests, 0)

            detail_url = reverse(
                "student_performance_comparison_detail",
                kwargs={"batch_id": selected_batch.id, "student_id": stu.id},
            )
            detail_url = f"{detail_url}?{urlencode(common_query_params)}"

            student_rows.append(
                {
                    "student": stu,
                    "avg_score": avg_score,
                    "present_tests": present_tests,
                    "absent_tests": absent_tests,
                    "detail_url": detail_url,
                }
            )

        student_rows.sort(
            key=lambda r: (
                -r["avg_score"],
                (r["student"].user.first_name or "").lower(),
                (r["student"].user.last_name or "").lower(),
            )
        )

    return render(
        request,
        "registration/reports/student_performance_comparison.html",
        {
            "session_options": session_options,
            "selected_session": selected_session,
            "class_options": class_options,
            "subject_options": subject_options,
            "section_options": section_options,
            "batch_options": batch_options,
            "selected_batch": selected_batch,
            "selected_filters": {
                "session_id": str(selected_session.id) if selected_session else (session_id or ""),
                "class_id": class_id,
                "subject_id": subject_id,
                "section_id": section_id,
                "batch_id": str(selected_batch.id) if selected_batch else (batch_id or ""),
            },
            "start_date": start_date,
            "end_date": end_date,
            "tests_with_activity_count": tests_with_activity_count,
            "student_rows": student_rows,
            # Full catalog (scoped to user) so the UI can manage options client-side.
            "batch_catalog": list(
                base_qs_all_sessions.values(
                    "id",
                    "session_id",
                    "class_name_id",
                    "class_name__name",
                    "subject_id",
                    "subject__name",
                    "section_id",
                    "section__name",
                )
            ),
        },
    )


@login_required(login_url="login")
def student_performance_comparison_detail(request, batch_id: int, student_id: int):
    batch = get_object_or_404(Batch.objects.select_related("class_name", "subject", "section"), id=batch_id)
    student = get_object_or_404(Student.objects.select_related("user"), id=student_id)

    date_range = _parse_date_range_or_default(request)
    if date_range is None:
        return redirect(
            reverse("student_performance_comparison_detail", kwargs={"batch_id": batch.id, "student_id": student.id})
        )
    start_date, end_date = date_range

    subject_test_reports = _get_batch_subject_test_reports(student, batch, start_date, end_date)

    persist_params = {
        "session_id": request.GET.get("session_id") or "",
        "class_id": request.GET.get("class_id") or "",
        "subject_id": request.GET.get("subject_id") or "",
        "section_id": request.GET.get("section_id") or "",
        "batch_id": str(batch.id),
    }

    back_params = {
        **persist_params,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }
    back_url = f"{reverse('student_performance_comparison')}?{urlencode(back_params)}"

    return render(
        request,
        "registration/reports/student_performance_comparison_detail.html",
        {
            "student": student,
            "batch": batch,
            "start_date": start_date,
            "end_date": end_date,
            "subject_test_reports": subject_test_reports,
            "back_url": back_url,
            "persist_params": persist_params,
        },
    )
