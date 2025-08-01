from django.shortcuts import render, redirect, get_object_or_404
from registration.models import (  
    Batch, 
    Teacher,
    Chapter, 
    )

from lesson.models import ChapterSequence, Lesson, Holiday
from django.utils.timezone import now

from registration.models import Subject, ClassName
from django.contrib import messages

from datetime import datetime, timedelta


from django.contrib.auth.decorators import login_required

from django.db.models import Q
from django.urls import reverse

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