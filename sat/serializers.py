from rest_framework import serializers
from .models import Question, TestPaper, TestAssignment


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'order', 'text', 'question_type', 'option_a', 'option_b', 'option_c', 'option_d', 'option_e',
                  'difficulty', 'subject_tag')
        # correct_answer intentionally excluded from student-facing output


class PaperSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    class_label = serializers.SerializerMethodField()

    class Meta:
        model = TestPaper
        fields = ('id', 'title', 'class_label', 'time_limit', 'marks_per_correct', 'questions')

    def get_class_label(self, obj):
        return obj.class_name.name if obj.class_name else ''


class AnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected = serializers.CharField(max_length=1, allow_blank=True, required=False, allow_null=True)
