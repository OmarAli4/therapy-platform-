from django.urls import path
from .views import (
    CourseListView, CourseDetailView, ModuleDetailView,
    SaveJournalApiView, ToggleModuleProgressApiView
)

urlpatterns = [
    path('', CourseListView.as_view(), name='course_list'),
    path('api/journal/save/', SaveJournalApiView.as_view(), name='save_journal_api'),
    path('api/progress/toggle/', ToggleModuleProgressApiView.as_view(), name='toggle_progress_api'),
    path('<slug:slug>/', CourseDetailView.as_view(), name='course_detail'),
    path('<slug:slug>/module/<int:module_id>/', ModuleDetailView.as_view(), name='module_detail'),
]
