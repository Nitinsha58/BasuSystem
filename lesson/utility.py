from collections import defaultdict
from datetime import datetime
from lesson.models import Lecture, LectureDate, ChapterSequence
from django.contrib import messages

from registration.models import ClassName, Batch


def validate_class(class_id):
    return ClassName.objects.filter(id=class_id).first()


def validate_batch(batch_id):
    from lesson.models import Batch
    return Batch.objects.filter(id=batch_id).first()


def get_latest_completed_lecture(batch):
    return Lecture.objects.filter(
        lesson__chapter_sequence__batch=batch,
        status='completed'
    ).select_related('lesson__chapter_sequence').order_by('date').last()


def get_upcoming_available_dates(batch, d):
    today = datetime.today()
    future_dates = LectureDate.objects.filter(batch=batch, date__gte=today).order_by('date')
    return future_dates


def build_lesson_data(chapters, all_lectures, latest_completed_lecture, available_dates):
    data = defaultdict(list)
    count = 0
    lecture_map = defaultdict(list)

    for lec in all_lectures:
        lecture_map[lec.lesson.id].append(lec)

    latest_chapter_seq = latest_completed_lecture.lesson.chapter_sequence.sequence if latest_completed_lecture else -1
    latest_lesson_seq = latest_completed_lecture.lesson.sequence if latest_completed_lecture else -1

    for chapter in chapters:
        for lesson in chapter.lessons.all().order_by('sequence'):
            lectures = lecture_map.get(lesson.id, [])
            latest_lecture = lectures[-1] if lectures else None

            info = {
                'lesson': lesson,
                'lecture': latest_lecture,
                'status': latest_lecture.status if latest_lecture else '',
                'date': latest_lecture.date if latest_lecture else None,
                'lectures': lectures[:-1] if lectures else [],
                'is_completed': latest_lecture.status == 'completed' if latest_lecture else False,
                'is_next_lecture': False,
                'is_behind_latest': (chapter.sequence, lesson.sequence) < (latest_chapter_seq, latest_lesson_seq),
                'is_forward_lesson': (chapter.sequence, lesson.sequence) > (latest_chapter_seq, latest_lesson_seq)
            }

            if latest_completed_lecture:
                next_lesson = latest_completed_lecture.lesson.next()
                if next_lesson and next_lesson == lesson:
                    info['is_next_lecture'] = True

            # Only suggest dates for forward lessons without a lecture
            if info['is_forward_lesson'] and not latest_lecture and count < len(available_dates):
                info['scheduled_date'] = available_dates[count].date
                info['status'] = 'scheduled'
                info['date'] = available_dates[count].date
                count += 1

            data[chapter].append(info)

        if not chapter.lessons.exists():
            data[chapter] = []

    return data
