from django.contrib import admin
from .models import (Center, 
                     Batch, 
                     Student, 
                     Attendance, 
                     Homework, 
                     Test, 
                     TestQuestion, 
                     ClassName,
                     Section,
                     Subject, 
                     QuestionResponse, Remark
                     )


admin.site.register(Center) 
admin.site.register(Batch) 

admin.site.register(Student, )
admin.site.register(Attendance, )
admin.site.register(Homework, )
admin.site.register(Test, )
admin.site.register(TestQuestion, )
admin.site.register(ClassName, )
admin.site.register(Section, )
admin.site.register(Subject, )
admin.site.register(QuestionResponse, )
admin.site.register(Remark, )
 