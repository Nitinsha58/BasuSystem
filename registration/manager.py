from django.db import models

class AttendanceQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        # Only set 'type' if not explicitly provided
        if 'type' not in kwargs:
            kwargs['type'] = 'Regular'
        return super().filter(*args, **kwargs)

class AttendanceManager(models.Manager):
    def get_queryset(self):
        return AttendanceQuerySet(self.model, using=self._db)

    def filter(self, *args, **kwargs):
        return self.get_queryset().filter(*args, **kwargs)

