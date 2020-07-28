from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from classes.models import Class
from students.models import Student
from teachers.models import Teacher
from users.utils import get_user_role


class get_classes(APIView):
    def get(self, request):
        classes = Class.objects.all()
        params = {}
        if len(classes) == 0:
            params["message"] = "No classes found"
            params["status"] = 400
        else:
            params["classes"] = []
            for clas in classes:
                params["classes"].append({"name": clas.name, "id": clas.id})
            params["status"] = 200
        return Response(params, status=200)


class list_classes(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        params = {}
        user = request.user
        if request.method == "GET":
            student, is_in_class = _is_student(user)
            teacher, teaches_class = _is_teacher(user)

            if student is not None:
                params["student_classes"] = []
                for c in student.classes.all():
                    params["student_classes"].append(
                        {"class_id": c.id, "class_name": c.name}
                    )
            if teacher is not None:
                params["teacher_classes"] = []
                for c in Class.objects.filter(teacher=teacher):
                    params["teacher_classes"].append(
                        {"class_id": c.id, "class_name": c.name}
                    )

        return Response(params, status=200)


class enrolled(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, class_id):
        params = {}
        request_user = request.user
        user_data = get_user_role(request_user)[1]

        if user_data["is_student"] is False:
            params[
                "message"
            ] = "User is not a student, therefore cannot be enrolled in a class"
            params["status"] = 401
            return Response(params, params["status"])

        try:
            c = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            params["message"] = "Invalid class"
            params["status"] = 404
            return Response(params, params["status"])

        if c in user_data["user"].classes.all():
            params["message"] = "Student is enrolled."
            params["status"] = 200
        else:
            params["message"] = "Student is not enrolled."
            params["status"] = 401

        return Response(params, params["status"])


class enroll(APIView):
    permission_classes = (IsAuthenticated,)

    # Modify to post, bring in passcode, figure out why teaches_class
    # from utils doesn't work.
    def post(self, request):
        params = {}
        request_user = request.user
        class_id = request.data.get("class_id", None)
        passcode = request.data.get("passcode", None)

        if class_id is None or passcode is None:
            params["message"] = "Missing parameters class_id or passcode"
            params["status"] = 400
            return Response(params, params["status"])

        try:
            class_id = int(class_id)
        except ValueError:
            params["message"] = "class_id must be numerical"
            params["status"] = 400
            return Response(params, params["status"])

        try:
            c = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            params["message"] = "Invalid class"
            params["status"] = 404
            return Response(params, params["status"])

        if c.allow_registration is False:
            params["message"] = "Class not configured for registration"
            params["status"] = 403
            return Response(params, params["status"])

        user_data = get_user_role(request_user, c)[1]

        print(user_data)

        if user_data["teaches_class"] is True:
            params[
                "message"
            ] = "User teaches this class, therefore cannot enroll"
            params["status"] = 401
            return Response(params, params["status"])

        if user_data["is_in_class"] is True:
            params["message"] = "User is already enrolled in this class"
            params["status"] = 401
            return Response(params, params["status"])

        if user_data["is_student"] is False:
            if user_data["user"] is None:
                student = Student.objects.create(user=request_user)
                student.classes.add(c)
                student.save()
                params["message"] = "User was enrolled in class"
                params["status"] = 200
            elif user_data["is_teacher"] is True:
                student = Student.objects.create(user=user_data["user"].user)
                student.classes.add(c)
                student.save()
                params["message"] = "User was enrolled in class"
                params["status"] = 200
        else:
            student = Student.objects.get(user=user_data["user"].user)
            student.classes.add(c)
            student.save()
            params["message"] = "User was enrolled in class"
            params["status"] = 200

        return Response(params, params["status"])


class get_class(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, class_id):
        params = {}
        user = request.user
        try:
            c = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            params["message"] = "Invalid class"
            return Response(params, status=404)

        student, is_in_class = _is_student(user, c)
        teacher, teaches_class = _is_teacher(user, c)

        if is_in_class is True or teaches_class is True:
            print(c.teacher_set.all())
            params["teacher(s)"] = []
            for teach in c.teacher_set.all():
                params["teacher(s)"].append(
                    teach.user.last_name + ", " + teach.user.first_name
                )
            params["name"] = c.name
            params["droplet_image"] = c.droplet_image
            params["droplet_size"] = c.droplet_size
            params["droplet_region"] = c.droplet_region
            params["droplet_limit"] = c.droplet_student_limit
        if teaches_class is True:
            params["created_at"] = c.created_at
            params["prefix"] = c.prefix
            params["priv_net"] = c.droplet_priv_net
            params["ipv6"] = c.droplet_ipv6
            params["user_data"] = c.droplet_user_data

        return Response(params, status=200)


class create_class(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        params = {}

        x = request.data.get("class_id", None)
        params["test"] = x
        return Response(params, status=200)


# local helper functions
def _is_student(user, class_obj=None):
    is_in_class = None
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        student = None
    else:
        if class_obj in student.classes.all():
            is_in_class = True
        else:
            is_in_class = False

    return student, is_in_class


def _is_teacher(user, class_obj=None):
    teaches_class = None
    try:
        teacher = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        teacher = None
    else:
        if class_obj in teacher.classes.all():
            teaches_class = True
        else:
            teaches_class = False
    return teacher, teaches_class
