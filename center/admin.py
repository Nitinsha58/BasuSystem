from django.contrib import admin
from .models import (Center, 
                     Batch, 
                     Student, 
                     Test, 
                     TestQuestion, 
                     ClassName,
                     Section,
                     Subject, 
                     QuestionResponse, Remark,

                     TestResult, RemarkCount
                     )


admin.site.register(Center) 
admin.site.register(Batch) 

admin.site.register(Student, )
admin.site.register(Test, )
admin.site.register(TestQuestion, )
admin.site.register(ClassName, )
admin.site.register(Section, )
admin.site.register(Subject, )
admin.site.register(QuestionResponse, )
admin.site.register(Remark, )

admin.site.register(TestResult )
admin.site.register(RemarkCount )
 