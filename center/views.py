from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import StudentRegistrationForm
from .models import Batch, Center, Test, TestQuestion, Student, Remark, QuestionResponse
from django.contrib import messages
from datetime import date

# Create your views here.

def staff_dashboard(request):
    return render(request, 'center/dashboard.html')


def staff_student_registration(request):
    all_batches = Batch.objects.all()
    center = Center.objects.filter(name="Main Center").first()

    if not center:
        messages.error(request, "No Center Found.")
        return redirect('staff_dashboard')

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        batches_ids = request.POST.getlist('batches') 
        center_id = center.id
        password = 'basu@123'  

        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
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
                return HttpResponse(f"Error: {str(e)}", status=500)

        else:
            messages.error(request, "Invalid Form")
            return render(request, 'center/staff_student_registration.html', {
                'form': form,
                'batches': all_batches,
                'center': center
            })

    return render(request, 'center/staff_student_registration.html', {'batches': all_batches, 'center': center})


def create_test_template(request, batch_id=None):
    all_batches = Batch.objects.all()

    if batch_id and request.method == "POST":
        if Batch.objects.filter(id=batch_id).first() == None:
            messages.error("Invalid Batch")
            return redirect('create_test_template')
        
        batch = Batch.objects.filter(id=batch_id).first()
        test = Test.objects.create(batch=batch, date=date.today())
        test.save()

        return redirect("create_template", batch_id=batch_id, test_id=test.id )

    return render(request, 'center/create_test_template.html', {"batches": all_batches})


def create_template(request, batch_id, test_id):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("create_test_template")
    
    if request.method == 'POST':
        test_name = request.POST['test_name']
        test.name = test_name
        test.save()

        return redirect('create_test_template')
    
    questions = TestQuestion.objects.filter(test = test)
    
    return render(request,"center/create_template.html", {"batch":batch, "test":test, "questions": questions})


def delete_template(request, batch_id, test_id):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("create_test_template")
    
    test.delete()
    messages.info(request, "Test Deleted.")
    
    return redirect("create_test_template")

def create_question(request, batch_id, test_id):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("create_test_template")

    if request.method == 'POST':
        chapter_name = request.POST['chapter_name']
        chapter_no = request.POST['chapter_no']
        max_marks = request.POST['max_marks']

        question = TestQuestion.objects.create(
            test = test,
            question_number = TestQuestion.objects.all().count() + 1,
            chapter_no = int(chapter_no),
            max_marks = max_marks,
            chapter_name=chapter_name
        )
        question.save()

        return redirect("create_template", batch_id=batch_id, test_id=test_id )
    return redirect("create_template", batch_id=batch_id, test_id=test_id )
    
def update_question(request, batch_id, test_id, question_id):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    question = TestQuestion.objects.filter(id=question_id).first()
    if not batch or not test or not question:
        messages.error(request, "Invalid Question")
        return redirect("create_test_template")

    if request.method == 'POST':
        chapter_name = request.POST['chapter_name']
        chapter_no = request.POST['chapter_no']
        max_marks = request.POST['max_marks']

        question.chapter_no = chapter_no
        question.max_marks = max_marks
        question.chapter_name= chapter_name

        question.save()

        return redirect("create_template", batch_id=batch_id, test_id=test_id )
    return redirect("create_template", batch_id=batch_id, test_id=test_id )
    
# batch, test, student
def create_test_response(request):
    all_batches = Batch.objects.all()
    return render(request, "center/create_test_response.html", {"batches":all_batches})


def create_response(request, batch_id, test_id, student_id=None, question_id = None):
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    student = None
    question_response = None
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("create_test_response")

    students = Student.objects.filter(batches=batch)
    questions = TestQuestion.objects.filter(test=test)
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
                marks_obtained = marks_obtained
            )

            response.remark.set(Remark.objects.filter(id__in=remark_ids))
            return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)
        
        responses = QuestionResponse.objects.filter(student=student, test=test).select_related("question")

        # Create a dictionary to map questions to their responses
        response_map = {response.question.id: response for response in responses}

        # Build the question_response list
        question_response = [
            {"response": response_map.get(question.id)} if question.id in response_map else {"question": question}
            for question in questions
        ]

    return render(request, "center/create_response.html", {
        "batch":batch, 
        "test":test,
        "students": students,
        "questions": questions,
        "student":student,
        "remarks":remarks,
        "question_response": question_response
    })



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

        response.marks_obtained = marks_obtained
        response.remark.set(Remark.objects.filter(id__in=remark_ids))
        response.save()
    
    return redirect("create_student_response", batch_id=batch_id, test_id=test_id, student_id=student_id)
