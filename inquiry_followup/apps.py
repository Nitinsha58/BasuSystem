from django.apps import AppConfig


class InquiryFollowupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inquiry_followup'

    def ready(self):
        import inquiry_followup.signals