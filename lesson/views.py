from django.shortcuts import render, redirect, get_object_or_404
from registration.models import (  
    Batch, 
    )

from lesson.models import ChapterSequence, Lesson, Holiday
from django.utils.timezone import now

from registration.models import Subject, ClassName
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from collections import defaultdict
from .models import Lesson, Lecture


@login_required(login_url='login')
def lesson(request, sequence_id, class_id, batch_id):
    chapter_sequence = get_object_or_404(ChapterSequence, id=sequence_id, batch__id=batch_id)
    lessons = Lesson.objects.filter(chapter_sequence=chapter_sequence).order_by('sequence')

    if request.method == 'POST':
        lessons_data = request.POST.getlist('lessons[]')
        topics = request.POST.getlist('lessons[][topic]')
        homeworks = request.POST.getlist('lessons[][homework]')
        classworks = request.POST.getlist('lessons[][classwork]')

        # Collect lesson IDs from submitted data
        submitted_ids = set()
        for idx, lesson_data in enumerate(lessons_data):
            parts = lesson_data.split(':')
            lesson_id = parts[1] if len(parts) > 1 and parts[1] else None
            if lesson_id:
                submitted_ids.add(int(lesson_id))

        # Delete lessons that are not in submitted_ids
        existing_ids = set(lessons.values_list('id', flat=True))
        to_delete = existing_ids - submitted_ids
        if to_delete:
            Lesson.objects.filter(id__in=to_delete).delete()

        # Update or create lessons
        for idx, lesson_data in enumerate(lessons_data):
            parts = lesson_data.split(':')
            sequence = int(parts[0]) if parts[0] else idx + 1
            lesson_id = parts[1] if len(parts) > 1 and parts[1] else None

            topic = topics[idx] if idx < len(topics) else ''
            homework = homeworks[idx] if idx < len(homeworks) else ''
            classwork = classworks[idx] if idx < len(classworks) else ''

            if lesson_id:
                lesson = get_object_or_404(Lesson, id=lesson_id, chapter_sequence=chapter_sequence)
                lesson.sequence = sequence
                lesson.topic = topic
                lesson.homework = homework
                lesson.classwork = classwork
                lesson.save()
            else:
                Lesson.objects.create(
                    chapter_sequence=chapter_sequence,
                    sequence=sequence,
                    topic=topic,
                    homework=homework,
                    classwork=classwork
                )
        messages.success(request, "Lessons saved successfully.")
        return redirect('lesson', sequence_id=sequence_id, class_id=class_id, batch_id=batch_id)

    return render(request, 'lesson/lesson.html', {
        'sq': chapter_sequence,
        'lessons': lessons,
        'class_id': class_id,
        'batch_id': batch_id,
    })

@login_required(login_url='login')
def lesson_plan(request, class_id=None, batch_id=None):
    cls = None
    batch = None

    if class_id and not ClassName.objects.filter(id=class_id).exists():
        messages.error(request, "Invalid Class")
        return redirect('lesson_plan')
    
    if batch_id and not Batch.objects.filter(id=batch_id).exists():
        messages.error(request, "Invalid Batch")
        return redirect('lesson_plan_class', class_id=class_id)

    if class_id:
        cls = ClassName.objects.filter(id=class_id).first()
        batches = Batch.objects.filter(class_name=cls).order_by('created_at').exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        )
    else:
        batches = None
    
    if batch_id:
        batch = Batch.objects.filter(id=batch_id).first()

    if batch_id and not batch:
        messages.error(request, "Invalid Batch")
        return redirect('attendance_class', class_id=class_id)

    classes = ClassName.objects.all().order_by('created_at')
    chapters = ChapterSequence.objects.filter(batch=batch).order_by('sequence') if batch else ChapterSequence.objects.none()

    if batch_id and request.method == 'POST':
        chapters_data = request.POST.getlist('chapters[]')
 
        # Collect submitted ChapterSequence IDs
        submitted_ids = set()
        for chapter_data in chapters_data:
            parts = chapter_data.split(':')
            seq_id = int(parts[1]) if len(parts) > 1 and parts[1] else None
            if seq_id:
                submitted_ids.add(seq_id)

        # Delete ChapterSequences not in submitted_ids
        existing_ids = set(chapters.values_list('id', flat=True))
        to_delete = existing_ids - submitted_ids
        if to_delete:
            ChapterSequence.objects.filter(id__in=to_delete, batch=batch).delete()

        # Update or create ChapterSequences
        for chapter_data in chapters_data:
            parts = chapter_data.split(':')
            sequence = int(parts[0])
            chapter_no = int(parts[2])
            chapter_name = parts[3]
            seq_id = parts[1]
            
            if seq_id:
                chapter_sequence = get_object_or_404(ChapterSequence, id=seq_id, batch=batch)
                chapter_sequence.sequence = sequence
                chapter_sequence.chapter_no = chapter_no
                chapter_sequence.chapter_name = chapter_name
                chapter_sequence.save()
            else:
                ChapterSequence.objects.create(
                    batch=batch,
                    sequence=sequence,
                    chapter_no=chapter_no,
                    chapter_name=chapter_name
                )
        messages.success(request, "Chapters Updated.")

    return render(request, 'lesson/lesson_plan.html', {
        'classes': classes,
        'batches': batches,
        'cls': cls,
        'batch': batch,

        'chapters': chapters,
    })


@login_required(login_url='login')
def lecture_plan(request, class_id=None, batch_id=None):
    cls = None
    batch = None

    if class_id and not ClassName.objects.filter(id=class_id).exists():
        messages.error(request, "Invalid Class")
        return redirect('lecture_plan')
    
    if batch_id and not Batch.objects.filter(id=batch_id).exists():
        messages.error(request, "Invalid Batch")
        return redirect('lecture_plan_class', class_id=class_id)

    if class_id:
        cls = ClassName.objects.filter(id=class_id).first()
        batches = Batch.objects.filter(class_name=cls).order_by('created_at').exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        )
    else:
        batches = None
    
    if batch_id:
        batch = Batch.objects.filter(id=batch_id).first()

    if batch_id and not batch:
        messages.error(request, "Invalid Batch")
        return redirect('attendance_class', class_id=class_id)

    classes = ClassName.objects.all().order_by('created_at')
    chapters = ChapterSequence.objects.filter(batch=batch).order_by('sequence') if batch else ChapterSequence.objects.none()

    data = defaultdict(list)

    all_lectures = Lecture.objects.filter(
        lesson__chapter_sequence__batch=batch
    ).select_related('lesson__chapter_sequence').order_by(
        'date',
        'lesson__chapter_sequence__sequence',
        'lesson__sequence'
    )


    latest_completed_lecture = all_lectures.filter(status='completed').last()
    latest_chapter_seq = latest_completed_lecture.lesson.chapter_sequence.sequence if latest_completed_lecture else -1
    latest_lesson_seq = latest_completed_lecture.lesson.sequence if latest_completed_lecture else -1

    # Build a map of lesson.id -> lectures
    lecture_map = defaultdict(list)
    for lecture in all_lectures:
        lecture_map[lecture.lesson.id].append(lecture)

    # Loop through each chapter and lesson to build structured data
    for chapter in chapters:
        for lesson in chapter.lessons.all().order_by('sequence'):
            lesson_info = {
                'lesson': lesson,
                'status': '',
                'date': None,
                'is_completed': False,
                'is_behind_latest': False,
                'is_next_lecture': False,
            }

            # Determine lesson position compared to latest completed lecture
            if (chapter.sequence, lesson.sequence) < (latest_chapter_seq, latest_lesson_seq):
                lesson_info['is_behind_latest'] = True
            elif latest_completed_lecture and latest_completed_lecture.lesson.next() and latest_completed_lecture.lesson.next() == lesson:
                lesson_info['is_next_lecture'] = True


            # Check if this lesson has lectures
            lectures = lecture_map.get(lesson.id)
            if lectures:
                # Get latest lecture for this lesson
                latest_lecture = lectures[-1]
                lesson_info['status'] = latest_lecture.status
                lesson_info['date'] = latest_lecture.date
                if latest_lecture.status == 'completed':
                    lesson_info['is_completed'] = True

            data[chapter].append(lesson_info)
        
        if not chapter.lessons.all():
            data[chapter] = []

    return render(request, 'lesson/lecture_plan.html', {
        'classes': classes,
        'batches': batches,
        'cls': cls,
        'batch': batch,
        'data': dict(data),
        
        'chapters': chapters,
    })