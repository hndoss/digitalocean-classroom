from django.urls import path
from . import views

app_name = "classes"

urlpatterns = [
    path("", views.get_classes.as_view(), name="get_classes"),
    path("open", views.get_open_classes.as_view(), name="get_open_classes"),
    path("<int:class_id>", views.get_class.as_view(), name="get_class"),
    path("enrolled", views.enrolled.as_view(), name="enrolled"),
    path("enroll", views.enroll.as_view(), name="enroll"),

    path("create", views.create_class.as_view(), name="create_class"),
    path("update", views.update_class.as_view(), name="update_class"),
    path("list", views.list_classes.as_view(), name="list_classes"),
    path("delete/<int:class_id>", views.delete_class.as_view(), name="delete_classes"),
]
