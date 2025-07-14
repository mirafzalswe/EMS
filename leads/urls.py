from django.urls import path
from . import views

urlpatterns = [
    # Основная страница с канбан-доской
    path('leads/', views.kanban_board, name='kanban_board'),
    
    # API для работы с лидами
    path('add-lead/', views.add_lead, name='add_lead'),
    path('edit-lead/<int:lead_id>/', views.edit_lead, name='edit_lead'),
    path('move_lead/', views.move_lead, name='move_lead'),
    path('add-section/', views.add_section, name='add_section'),
    path('add-group/', views.add_group, name='add_group'),
    path('add-source/', views.add_source, name='add_source'),
    
    # Работа с лидами
    path('assign-lead-to-group/<int:lead_id>/', views.assign_lead_to_group, name='assign_lead_to_group'),
    path('add-lead-note/<int:lead_id>/', views.add_lead_note, name='add_lead_note'),
    
    # Временные студенты
    path('process-temp-lead/<int:temp_lead_id>/', views.process_temp_lead, name='process_temp_lead'),
    
    # Статистика
    path('statistics/', views.lead_statistics, name='lead_statistics'),
    path('lidlar-hisobotlari/', views.lidlar_hisobotlari, name='lidlar_hisobotlari'),
]