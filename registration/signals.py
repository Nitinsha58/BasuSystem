from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from .models import TestQuestion, Test
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