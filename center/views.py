from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import StudentRegistrationForm, StudentUpdateForm
from .models import Batch, Center, Test, TestQuestion, Student, Remark, QuestionResponse, ClassName
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from user.models import BaseUser
from django.db import models
from django.db.models import Count
from collections import Counter, defaultdict
# Create your views here.

@login_required(login_url='staff_login')
def staff_dashboard(request):
    return render(request, 'center/dashboard.html')

@login_required(login_url='staff_login')
def staff_student_registration(request, is_batch=None):
    all_batches = Batch.objects.all()
    center = Center.objects.filter(name="Main Center").first()
    classes = ClassName.objects.all()

    class_students = [{'class': cls.name, 'students': Student.objects.filter(batches__class_name=cls).distinct()} for cls in classes ]

    if not center:
        messages.error(request, "No Center Found.")
        return redirect('staff_dashboard')

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        batches_ids = request.POST.getlist('batches') 
        center_id = center.id
        password = 'basu@123'  

        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'batches': Batch.objects.filter(id__in=batches_ids),
            'center': Center.objects.get(id=center_id),
            'password': password
        }

        form = StudentRegistrationForm(form_data)
        if form.is_valid():
            try:
                with transaction.atomic():
                    student = form.save() 
                return redirect('staff_student_registration')
            except Exception as e:
                messages.error(request, e)
                return redirect('staff_student_registration')


        return render(request, 'center/staff_student_registration.html', {
            'form': form,
            'batches': all_batches,
            'center': center
        })

    return render(request, 'center/staff_student_registration.html', {'batches': all_batches, 'center': center, 'class_students': class_students, 'is_batch': is_batch})


@login_required(login_url='staff_login')
def staff_student_delete(request, user_id):
    try:
        user = BaseUser.objects.get(id=user_id)
        user.delete()
        messages.success(request, "Student deleted.")

    except BaseUser.DoesNotExist:
        messages.error(request, "Student not found")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
    
    return redirect('staff_student_registration')

@login_required(login_url='staff_login')
def staff_student_update(request, student_id):

    student = Student.objects.get(id=student_id)
    all_batches = Batch.objects.all()

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        batches_ids = request.POST.getlist('batches') 

        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'batches': Batch.objects.filter(id__in=batches_ids),
        }

        form = StudentUpdateForm(form_data, instance=student)
        if form.is_valid():
            try:
                with transaction.atomic():
                    student = form.save()
                messages.success(request, "Student details updated successfully!")
                return redirect('staff_student_registration')
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                return redirect('staff_student_update', student_id=student.id)

        return render(request, 'center/staff_student_update.html', {
            'form': form,
            'batches': all_batches,
        })

    form = StudentUpdateForm(instance=student)
    return render(request, 'center/staff_student_update.html', {
        'form': form,
        'batches': all_batches,
    })


@login_required(login_url='staff_login')
def create_test_template(request, batch_id=None):
    all_batches = Batch.objects.all()

    if batch_id and request.method == "POST":
        if Batch.objects.filter(id=batch_id).first() == None:
            messages.error("Invalid Batch")
            return redirect('create_test_template')
        
        batch = Batch.objects.filter(id=batch_id).first()
        test = Test.objects.create(batch=batch)
        test.save()

        return redirect("create_template", batch_id=batch_id, test_id=test.id )

    return render(request, 'center/create_test_template.html', {"batches": all_batches})

@login_required(login_url='staff_login')
def create_template(request, batch_id, test_id):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("create_test_template")
    
    if request.method == 'POST':
        test_name = request.POST.get('test_name')
        test.name = test_name
        test.save()

        return redirect('create_test_template')
    
    questions = TestQuestion.objects.filter(test = test, is_main=True).order_by('question_number')
    
    return render(request,"center/create_template.html", {"batch":batch, "test":test, "questions": questions})

@login_required(login_url='staff_login')
def delete_template(request, batch_id, test_id):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("create_test_template")
    
    test.delete()
    messages.info(request, "Test Deleted.")
    
    return redirect("create_test_template")


@login_required(login_url='staff_login')
def create_question(request, batch_id, test_id):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("create_test_template")

    if request.method == 'POST':
        chapter_name = request.POST.get('chapter_name')
        chapter_no = request.POST.get('chapter_no')
        max_marks = request.POST.get('max_marks')

        is_optional = request.POST.get('is_option')
        opt_chapter_name = request.POST.get('opt_chapter_name')
        opt_chapter_no = request.POST.get('opt_chapter_no')
        opt_max_marks = request.POST.get('opt_max_marks')

        try:
            with transaction.atomic():
                question = TestQuestion.objects.create(
                    test = test,
                    question_number = TestQuestion.objects.filter(test=test, is_main=True).count() + 1,
                    chapter_no = int(chapter_no),
                    max_marks = max_marks,
                    chapter_name=chapter_name
                )
                question.save()

                if is_optional:
                    opt_question = TestQuestion.objects.create(
                        test = test,
                        is_main = False,
                        question_number = question.question_number,
                        chapter_no = int(opt_chapter_no),
                        max_marks = opt_max_marks,
                        chapter_name= opt_chapter_name
                    )
                    opt_question.save()

                    question.optional_question = opt_question
                    question.save()

        except Exception as e:
            messages.error(request, "Invalid Input.")

        return redirect("create_template", batch_id=batch_id, test_id=test_id )
    return redirect("create_template", batch_id=batch_id, test_id=test_id )
    

@login_required(login_url='staff_login')
def update_question(request, batch_id, test_id, question_id):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    question = TestQuestion.objects.filter(id=question_id).first()
    if not batch or not test or not question:
        messages.error(request, "Invalid Question")
        return redirect("create_test_template")

    if request.method == 'POST':
        chapter_name = request.POST.get('chapter_name')
        chapter_no = request.POST.get('chapter_no')
        max_marks = request.POST.get('max_marks')

        question.chapter_no = chapter_no
        question.max_marks = max_marks
        question.chapter_name= chapter_name
        question.save()

        if question.optional_question:
            opt_question = question.optional_question
            opt_chapter_name = request.POST.get('opt_chapter_name')
            opt_chapter_no = request.POST.get('opt_chapter_no')
            opt_max_marks = request.POST.get('opt_max_marks')

            opt_question.chapter_no = opt_chapter_no
            opt_question.max_marks = opt_max_marks
            opt_question.chapter_name= opt_chapter_name
            opt_question.save()

        return redirect("create_template", batch_id=batch_id, test_id=test_id )
    return redirect("create_template", batch_id=batch_id, test_id=test_id )
    
@login_required(login_url='staff_login')
def create_test_response(request):
    all_batches = Batch.objects.all()
    return render(request, "center/create_test_response.html", {"batches":all_batches})

@login_required(login_url='staff_login')
def create_response(request, batch_id, test_id, student_id=None, question_id = None):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    student = None
    question_response = None
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("create_test_response")

    students = Student.objects.filter(batches=batch)
    questions = TestQuestion.objects.filter(test=test).order_by('question_number')
    remarks = Remark.objects.all()

    if student_id and Student.objects.filter(id=student_id).first():
        student = Student.objects.filter(id=student_id).first()
        question = TestQuestion.objects.filter(id=question_id).first()

        if request.method == 'POST' and question:
            marks_obtained = request.POST.get("marks_obtained")
            remark_ids = request.POST.getlist("remark")

            response = QuestionResponse.objects.create(
                question = question,
                student=student,
                test=test,
                marks_obtained = float(question.max_marks) - float(marks_obtained)
            )

            response.remark.set(Remark.objects.filter(id__in=remark_ids))
            return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)
        
        responses = QuestionResponse.objects.filter(student=student, test=test).select_related("question")

        # Create a dictionary to map questions to their responses
        response_map = {response.question.id: response for response in responses}
        question_nums = [response.question.question_number for response in responses]

        # Build the question_response list
        # question_response = [
        #     {"response": response_map.get(question.id)} if question.id in response_map else {"question": question}
        #     for question in questions
        # ]
        question_response = []

        for question in questions:
            if question.id in response_map:
                question_response.append({"response": response_map.get(question.id)})
            elif question.is_main and question.question_number not in question_nums:
                question_response.append({"question": question})


    return render(request, "center/create_response.html", {
        "batch":batch, 
        "test":test,
        "students": students,
        "questions": questions,
        "student":student,
        "remarks":remarks,
        "question_response": question_response
    })


@login_required(login_url='staff_login')
def create_all_pending_response(request, batch_id, test_id, student_id):
    test = Test.objects.filter(id=test_id).first()
    student = Student.objects.filter(id=student_id).first()

    if not student or not test:
        messages.error(request, "Invalid Student or Test")
        return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)

    unanswered_questions = TestQuestion.objects.filter(
        test=test
    ).exclude(
        response__student=student
    )

    for question in unanswered_questions:
        obj = QuestionResponse.objects.create(
            question=question,
            student=student,
            test=test,
            marks_obtained=question.max_marks,  # Default marks
        )
        obj.save()

    return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)


@login_required(login_url='staff_login')
def update_response(request, batch_id, test_id, student_id, response_id):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    student = Student.objects.filter(id=student_id).first()
    response = QuestionResponse.objects.filter(id = response_id).first()

    if ( not batch or not test or not student or not response ) :
        messages.error("Invalid Details.")
        return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)
    
    if request.method == 'POST':
        marks_obtained = request.POST.get("marks_obtained")
        remark_ids = request.POST.getlist("remark")

        response.marks_obtained = float(response.question.max_marks) - abs(float(marks_obtained))
        response.remark.set(Remark.objects.filter(id__in=remark_ids))
        response.save()
    
    return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)

@login_required(login_url='staff_login')
def delete_response(request, batch_id, test_id, student_id, response_id):
    try:
        if not Batch.objects.filter(id=batch_id).exists():
            messages.error(request, "Invalid batch ID.")
            return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)

        if not Test.objects.filter(id=test_id).exists():
            messages.error(request, "Invalid test ID.")
            return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)

        if not Student.objects.filter(id=student_id).exists():
            messages.error(request, "Invalid student ID.")
            return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)

        response = QuestionResponse.objects.get(id=response_id)

        response.delete()
        messages.success(request, "Response deleted.")

    except QuestionResponse.DoesNotExist:

        messages.error(request, "Response not found. Unable to delete.")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")


    return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)


def getQuery(request):

    batch = Batch.objects.all().first()


    all_remarks = Remark.objects.all()
    chapters = {}
    questions = TestQuestion.objects.filter(test__batch=batch).order_by('chapter_no')
    for question in questions:
        ch_no = question.chapter_no
        ch_name = question.chapter_name

        chapters.setdefault(ch_no, set()).add(ch_name)
    
    remarks_count = {}
    for remark in all_remarks:
        for ch_no in chapters:
            r_count = QuestionResponse.objects.filter(question__chapter_no=ch_no, remark=remark).count()
            remarks_count.setdefault(remark, []).append(r_count)
    






    # for chapter_no in chapters:
    #     chapter_responses = QuestionResponse.objects.filter(question__chapter_no=chapter_no)
    #     # for response in chapter_responses:
    #         # remark_ctr.update(response.remark.all())

    #     chapter_wise_response.setdefault(chapter_no, []).extend(chapter_responses)
    # chapter_wise_remark = {}

    # for no, resps in chapter_wise_response.items():
    #     remark_ctr = Counter([])
    #     for res in resps:
    #         remark_ctr.update(res.remark.all())
    #     chapter_wise_remark[no] = dict(remark_ctr)
    

    '''
        1. Batchwise Marks 
        2. Batchwise Remarks

        pending
        3. Chapterwise remarks
        4. Chapterwise marks
    '''



    return HttpResponse()


def batchwise_report(request, batch_id=None):
    batches = Batch.objects.all()
    
    if batch_id:
        try:
            batch = Batch.objects.get(id=batch_id)
        except Exception as e:
            messages.error(request, "Invalid Batch")
            return redirect('batchwise_report')
        
        remarks_count = {}
        responses = QuestionResponse.objects.filter(test__batch=batch)

        for response in responses:
            remark = response.remark.all().first()
            if remarks_count.get(remark):
                remarks_count[remark]+=1 * (response.question.max_marks - response.marks_obtained)
            else:
                remarks_count[remark] = 1 * (response.question.max_marks - response.marks_obtained)
        
        remarks_list = [r.name for r in remarks_count.keys()]
        count_list = list(remarks_count.values()) 



        test_reports = []

        tests = Test.objects.filter(batch=batch)

        for test in tests:
            students = Student.objects.filter(batches=test.batch)
            testwise_response = QuestionResponse.objects.filter(test=test)

            attempt_count = 0

            remarks = {}
            students_list = []
            marks_list = []
            total_marks = 0
            total_max = 0


            max_marks = test.question.aggregate(total=models.Sum('max_marks'))['total'] or 0
            for student in students:
                student_responses = testwise_response.filter(student=student)
                marks = 0
                for response in student_responses:
                    marks += response.marks_obtained # count total marks

                    #count remarks
                    for remark in response.remark.all():
                        if remarks.get(remark):
                            remarks[remark]+=1
                        else:
                            remarks[remark] = 1

                    
                if student_responses:
                    attempt_count += 1

                students_list.append(f'{student.user.first_name} {student.user.last_name}')
                marks_list.append(marks)
                total_marks += marks
                total_max += max_marks

            test_reports.append({
                'test' : test,
                'students': students_list,
                'marks' : marks_list,
                'remarks': dict(sorted(remarks.items(), key=lambda d: d[1], reverse=True)),
                'max_marks': max_marks,
                'avg': (total_marks/(total_max or 1)) * 100,
                'attempted': round( (attempt_count/students.count())*100  ,2),
            })




        remarks_count = dict(sorted(remarks_count.items(), key=lambda d: d[1], reverse=True))
        return render(request, "center/batchwise_report.html", {
            'batches': batches,
            'batch': batch,
            'remarks_list':remarks_list,
            'count_list':count_list,

            'remarks_count': remarks_count,
            'tests': test_reports,
        })

    return render(request, "center/batchwise_report.html", {
        'batches': batches,
    })


def chapterwise_report(request, batch_id=None):
    batches = Batch.objects.all()
    
    if batch_id:
        try:
            batch = Batch.objects.get(id=batch_id)
        except Exception as e:
            messages.error(request, "Invalid Batch")
            return redirect('batchwise_report')

        chapters = {
            question.chapter_no: question.chapter_name
            for question in TestQuestion.objects.filter(test__batch=batch).order_by('chapter_no')
        }
        question_responses = QuestionResponse.objects.filter(test__batch=batch).select_related('question')

        chapter_wise_remarks = defaultdict(lambda: [0] * len(chapters))
        remarks_count = defaultdict(int)

        # Populate counts
        for response in question_responses:
            ch_no = response.question.chapter_no
            remark = response.remark.all().first()
            chapter_index = list(chapters.keys()).index(ch_no)
            chapter_wise_remarks[remark][chapter_index] += 1 * (response.question.max_marks - response.marks_obtained)
            remarks_count[remark] += 1 * (response.question.max_marks - response.marks_obtained)

        # Convert defaultdict to a normal dict if needed
        chapter_wise_remarks = dict(chapter_wise_remarks)
        remarks_count = dict(remarks_count)


        test_reports = []
        tests = Test.objects.filter(batch=batch)

        for test in tests:
            testwise_response = QuestionResponse.objects.filter(test=test)

            total_marks = defaultdict(int)
            marks_obtained = defaultdict(int)
            chapter_remarks_count = defaultdict(lambda: defaultdict(int))

            for response in testwise_response:
                test = response.question.test
                ch_no = response.question.chapter_no

                # Add to total marks
                total_marks[ch_no] += response.question.max_marks

                # Add marks obtained (if your QuestionResponse model has marks or score field)
                marks_obtained[ch_no] += response.marks_obtained
                # Count remarks chapter-wise
                for remark in response.remark.all():
                    chapter_remarks_count[ch_no][remark] += 1

            attempt_count = 0
            remarks = {}
            students_list = []
            marks_list = []
            total_marks = 0
            total_max = 0


            max_marks = test.question.aggregate(total=models.Sum('max_marks'))['total'] or 0
            # for student in students:
            #     student_responses = testwise_response.filter(student=student)
            #     marks = 0
            #     for response in student_responses:
            #         marks += response.marks_obtained # count total marks

            #         #count remarks
            #         for remark in response.remark.all():
            #             if remarks.get(remark):
            #                 remarks[remark]+=1
            #             else:
            #                 remarks[remark] = 1
            #     if student_responses:
            #         attempt_count += 1
            #     students_list.append(f'{student.user.first_name} {student.user.last_name}')
            #     marks_list.append(marks)
            #     total_marks += marks
            #     total_max += max_marks

            test_reports.append({
                'test' : test,
                'students': students_list,
                'marks' : marks_list,
                'remarks': dict(sorted(remarks.items(), key=lambda d: d[1], reverse=True)),
                'max_marks': max_marks,
                'avg': (total_marks/(total_max or 1)) * 100,
                # 'attempted': round( (attempt_count/students.count())*100  ,2),
            })


        remarks_count = dict(sorted(remarks_count.items(), key=lambda d: d[1], reverse=True))
        return render(request, "center/chapterwise_report.html", {
            'batches': batches,
            'batch': batch,
            'chapter_wise_remarks': chapter_wise_remarks,
            'chapters': chapters,

            'remarks_count': remarks_count,
            'tests': test_reports,
        })

    return render(request, "center/chapterwise_report.html", {
        'batches': batches,
    })






