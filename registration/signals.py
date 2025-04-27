from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from .models import TestQuestion, Test, QuestionResponse, RemarkCount, TestResult
from django.db import models

@receiver(pre_save, sender=TestQuestion)
def question_pre_save(sender, instance, **kwargs):
    if instance.pk:
        old_question = TestQuestion.objects.get(pk=instance.pk)
        instance._old_max_marks = old_question.max_marks

@receiver(post_save, sender=TestQuestion)
def question_post_save(sender, instance, created, **kwargs):
    test = instance.test
    if created:
        test.no_of_questions += 1
        test.total_max_marks += instance.max_marks
    else:
        old_max_marks = getattr(instance, '_old_max_marks', None)
        test.total_max_marks -= old_max_marks
        test.total_max_marks += instance.max_marks
    test.save()


@receiver(post_delete, sender=TestQuestion)
def question_post_delete(sender, instance, **kwargs):
    test = instance.test
    test.no_of_questions -= 1
    test.total_max_marks -= instance.max_marks
    test.save()


# TestResult and RemarkCount Update
@receiver(pre_save, sender=QuestionResponse)
def test_result_pre_save(sender, instance, **kwargs):
    if instance.pk:
        old_response = QuestionResponse.objects.get(pk=instance.pk)
        instance._old_marks_obtained = old_response.marks_obtained
        instance._old_remark = old_response.remark


@receiver(post_save, sender=QuestionResponse)
def result_post_update(sender, instance, created, *args, **kwargs):
    if getattr(instance, '_signal_processed', False):
        return
    
    instance._signal_processed = True

    test = instance.test
    student = instance.student
    remark = instance.remark

    # Get or create a TestResult for the student and test
    test_result, result_created = TestResult.objects.get_or_create(
        test=test, 
        student=student,
        defaults={'total_marks_obtained': 0, 'percentage': 0, 'total_max_marks':test.total_max_marks, 'no_of_questions_attempted':0}
    )


    if created:
        test_result.no_of_questions_attempted += 1
        test_result.total_marks_obtained += instance.marks_obtained
        test_result.percentage = (test_result.total_marks_obtained / test_result.total_max_marks) * 100

        if remark:
            test_remark, remark_created = RemarkCount.objects.get_or_create(
                test=test,
                student=student,
                remark=remark,
                defaults={'count': 1}
            )
            if not remark_created:
                test_remark.count += 1
                test_remark.save()
        
    else:
        _old_marks_obtained = getattr(instance, '_old_marks_obtained', 0)
        _old_remark = getattr(instance, '_old_remark', '')
        test_result.total_marks_obtained -= _old_marks_obtained
        test_result.total_marks_obtained += instance.marks_obtained
        test_result.percentage = (test_result.total_marks_obtained / test_result.total_max_marks) * 100


        if _old_remark and _old_remark != remark:
            old_remark_count = RemarkCount.objects.filter(
                test=test,
                student=student,
                remark=_old_remark
            ).first()
            if old_remark_count:
                old_remark_count.count -= 1
                if old_remark_count.count == 0:
                    old_remark_count.delete()
                else:
                    old_remark_count.save()

        if remark:
            test_remark, _ = RemarkCount.objects.get_or_create(
                test=test,
                student=student,
                remark=remark,
                defaults={'count': 1}
            )
            if not _:
                test_remark.count += 1
                test_remark.save()

    test_result.save()


@receiver(post_delete, sender=QuestionResponse)
def result_post_delete(sender, instance, **kwargs):
    
    test_result = TestResult.objects.filter(test=instance.test, student=instance.student).first()

    if test_result:
        test_result.no_of_questions_attempted -= 1
        test_result.total_marks_obtained -= instance.marks_obtained
        test_result.percentage = (test_result.total_marks_obtained / test_result.total_max_marks) * 100

        test_result.save()


    # Remark Count
    if instance.remark:
        # Decrement count for the old remark
        old_remark_count = RemarkCount.objects.filter(
            test=instance.test,
            student=instance.student,
            remark=instance.remark
        ).first()
        if old_remark_count:
            old_remark_count.count -= 1
            if old_remark_count.count == 0:
                old_remark_count.delete()
            else:
                old_remark_count.save()