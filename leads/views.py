from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.urls import reverse
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from calendar import monthrange

from courses.models import Course, Group
from users.models import User
from .models import (
    Lead, LeadSource, LeadStatus, LeadActivity,
    Section, ScheduleType, GroupSchedule, TempLead
)
from .forms import (
    LeadForm, LeadFilterForm, SectionForm,
    GroupAssignmentForm, NewGroupForm, LeadNoteForm, TempLeadForm
)

import json
from datetime import datetime, timedelta, date

@login_required
def kanban_board(request):
    """Главная страница с канбан-доской"""
    
    filter_form = LeadFilterForm(request.GET)
    leads_query = Lead.objects.all()

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Если хотя бы одна дата выбрана — фильтруем
    if date_from or date_to:
        if not date_from:
            # Если только date_to выбрано, берем минимальную дату
            date_from = Lead.objects.order_by('created_at').first().created_at.date() if Lead.objects.exists() else None
        if not date_to:
            # Если только date_from выбрано, берем сегодняшнюю дату
            date_to = date.today()
        # Преобразуем строки в date
        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        if isinstance(date_to, str):
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        leads_query = leads_query.filter(created_at__gte=date_from, created_at__lte=date_to + timedelta(days=1))
    else:
        date_from = ''
        date_to = ''

    if filter_form.is_valid():
        source = filter_form.cleaned_data.get('source')
        search = filter_form.cleaned_data.get('search')
        
        if source:
            leads_query = leads_query.filter(source=source)
        
        if search:
            leads_query = leads_query.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
    
    # Получаем лиды по колонкам
    new_leads = leads_query.filter(board_column='new').order_by('order_in_column')
    waiting_leads = leads_query.filter(board_column='waiting').order_by('order_in_column')
    trial_leads = leads_query.filter(board_column='trial').order_by('order_in_column')
    attending_leads = leads_query.filter(board_column='attending').order_by('order_in_column')
    
    # Получаем временных студентов
    temp_leads = TempLead.objects.filter(is_processed=False).order_by('-created_at')
    
    # Получаем разделы
    sections = Section.objects.all().order_by('column', 'order')
    
    # Получаем источники для формы добавления лида
    lead_sources = LeadSource.objects.filter(is_active=True)
    
    # Получаем курсы для формы добавления лида
    courses = Course.objects.filter(is_active=True)
    
    # Получаем преподавателей для формы добавления группы
    teachers = User.objects.filter(user_type='teacher', is_active=True)
    
    # Формы
    temp_lead_form = TempLeadForm()
    section_form = SectionForm()
    group_form = NewGroupForm()
    
    # Статистика
    total_leads = leads_query.count()
    new_count = new_leads.count()
    waiting_count = waiting_leads.count()
    trial_count = trial_leads.count()
    attending_count = attending_leads.count()
    temp_leads_count = temp_leads.count()
    
    context = {
        'new_leads': new_leads,
        'waiting_leads': waiting_leads,
        'trial_leads': trial_leads,
        'attending_leads': attending_leads,
        'temp_leads': temp_leads,
        'sections': sections,
        'lead_sources': lead_sources,
        'courses': courses,
        'teachers': teachers,
        'temp_lead_form': temp_lead_form,
        'section_form': section_form,
        'group_form': group_form,
        'filter_form': filter_form,
        'total_leads': total_leads,
        'new_count': new_count,
        'waiting_count': waiting_count,
        'trial_count': trial_count,
        'attending_count': attending_count,
        'temp_leads_count': temp_leads_count,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'leads/kanban_board.html', context)

@login_required
@require_POST
def add_lead(request):
    """Добавление нового временного студента"""
    form = TempLeadForm(request.POST)
    
    if form.is_valid():
        temp_lead = form.save()
        messages.success(request, _('Новый студент успешно добавлен в очередь на рассмотрение!'))
        return redirect('kanban_board')
    
    messages.error(request, _('Произошла ошибка. Пожалуйста, проверьте данные формы.'))
    return redirect('kanban_board')

@login_required
@require_POST
def process_temp_lead(request, temp_lead_id):
    """Обработка временного студента и конвертация в лид"""
    temp_lead = get_object_or_404(TempLead, id=temp_lead_id, is_processed=False)
    lead = temp_lead.convert_to_lead()
    
    messages.success(request, _('Студент успешно добавлен в систему!'))
    return redirect('kanban_board')

@login_required
def edit_lead(request, lead_id):
    """Редактирование лида"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            
            # Создаем запись активности
            LeadActivity.objects.create(
                lead=lead,
                activity_type='note_added',
                description=f'Данные лида обновлены',
                performed_by=request.user
            )
            
            messages.success(request, _('Данные лида успешно обновлены!'))
            return redirect('kanban_board')
    else:
        form = LeadForm(instance=lead)
    
    # Получаем группы для формы назначения в группу
    groups = Group.objects.filter(is_active=True)
    group_form = GroupAssignmentForm()
    note_form = LeadNoteForm()
    
    # Получаем историю активности по лиду
    activities = lead.activities.all().order_by('-created_at')
    
    context = {
        'lead': lead,
        'form': form,
        'group_form': group_form,
        'note_form': note_form,
        'groups': groups,
        'activities': activities,
    }
    
    return render(request, 'leads/edit_lead.html', context)

@csrf_exempt
def move_lead(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lead_id = data.get("lead_id")
            section_id = data.get("section_id")
            lead = Lead.objects.get(id=lead_id)
            section = Section.objects.get(id=section_id)
            lead.section = section
            lead.board_column = section.column  # чтобы карточка ушла в нужную колонку
            lead.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})

@login_required
@require_POST
def add_section(request):
    """Добавление нового раздела в колонку"""
    form = SectionForm(request.POST)
    
    if form.is_valid():
        section = form.save(commit=False)
        
        # Устанавливаем порядок - в конец
        max_order = Section.objects.filter(column=section.column).aggregate(
            max_order=models.Max('order'))['max_order'] or 0
        section.order = max_order + 1
        section.save()
        
        messages.success(request, _('Новый раздел успешно добавлен!'))
        return redirect('kanban_board')
    
    messages.error(request, _('Произошла ошибка. Пожалуйста, проверьте данные формы.'))
    return redirect('kanban_board')

@login_required
@require_POST
def add_group(request):
    """Добавление новой группы"""
    form = NewGroupForm(request.POST)
    
    if form.is_valid():
        group = form.save(commit=False)
        group.teacher = form.cleaned_data['teacher']
        group.save()
        
        # Добавляем расписание
        schedule_type, created = ScheduleType.objects.get_or_create(
            name=dict(form.fields['schedule_type'].choices)[form.cleaned_data['schedule_type']]
        )
        
        GroupSchedule.objects.create(
            group=group,
            schedule_type=schedule_type,
            start_time=form.cleaned_data['start_time'],
            end_time=form.cleaned_data['end_time']
        )
        
        messages.success(request, _('Новая группа успешно создана!'))
        return redirect('kanban_board')
    
    messages.error(request, _('Произошла ошибка. Пожалуйста, проверьте данные формы.'))
    return redirect('kanban_board')

@login_required
@require_POST
def assign_lead_to_group(request, lead_id):
    """Назначение лида в группу"""
    lead = get_object_or_404(Lead, id=lead_id)
    form = GroupAssignmentForm(request.POST)
    
    if form.is_valid():
        group = form.cleaned_data['group']
        notes = form.cleaned_data['notes']
        
        # Проверяем не заполнена ли группа
        if group.is_full:
            messages.error(request, _('Группа заполнена. Пожалуйста, выберите другую группу.'))
            return redirect('edit_lead', lead_id=lead_id)
        
        # Если лид еще не конвертирован в студента, создаем пользователя
        if not lead.converted_to_student:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Создаем уникальный username
            username = f"{lead.first_name.lower()}{lead.last_name.lower()}{Lead.objects.count()}"
            
            # Генерируем временный пароль
            from django.utils.crypto import get_random_string
            temp_password = get_random_string(12)
            
            # Создаем пользователя
            user = User.objects.create_user(
                username=username,
                password=temp_password,
                email=lead.email,
                first_name=lead.first_name,
                last_name=lead.last_name,
                user_type='student',
                phone=lead.phone
            )
            
            # Конвертируем лид в студента
            lead.convert_to_student(user)
            
            # Добавляем запись активности
            LeadActivity.objects.create(
                lead=lead,
                activity_type='status_change',
                description=f'Лид конвертирован в студента',
                performed_by=request.user
            )
        
        # Создаем зачисление
        from courses.models import Enrollment
        enrollment = Enrollment.objects.create(
            student=lead.student,
            group=group,
            notes=notes
        )
        
        # Перемещаем лид в колонку "Посещают занятия"
        lead.board_column = 'attending'
        lead.save()
        
        # Добавляем запись активности
        LeadActivity.objects.create(
            lead=lead,
            activity_type='group_assignment',
            description=f'Лид назначен в группу "{group.name}"',
            performed_by=request.user
        )
        
        messages.success(request, _('Студент успешно назначен в группу!'))
        return redirect('kanban_board')
    
    messages.error(request, _('Произошла ошибка. Пожалуйста, проверьте данные формы.'))
    return redirect('edit_lead', lead_id=lead_id)

@login_required
@require_POST
def add_lead_note(request, lead_id):
    """Добавление заметки к лиду"""
    lead = get_object_or_404(Lead, id=lead_id)
    form = LeadNoteForm(request.POST)
    
    if form.is_valid():
        note = form.cleaned_data['note']
        
        # Создаем запись активности с заметкой
        LeadActivity.objects.create(
            lead=lead,
            activity_type='note_added',
            description=note,
            performed_by=request.user
        )
        
        messages.success(request, _('Заметка успешно добавлена!'))
        return redirect('edit_lead', lead_id=lead_id)
    
    messages.error(request, _('Произошла ошибка. Пожалуйста, проверьте данные формы.'))
    return redirect('edit_lead', lead_id=lead_id)

@login_required
def lead_statistics(request):
    """Страница со статистикой по лидам"""
    # Статистика по источникам
    sources_stats = Lead.objects.values('source__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Статистика по статусам
    status_stats = Lead.objects.values('board_column').annotate(
        count=Count('id')
    ).order_by('board_column')
    
    # Статистика по времени
    now = datetime.now()
    one_week_ago = now - timedelta(days=7)
    one_month_ago = now - timedelta(days=30)
    
    leads_week = Lead.objects.filter(created_at__gte=one_week_ago).count()
    leads_month = Lead.objects.filter(created_at__gte=one_month_ago).count()
    
    # Статистика по конверсии
    total_leads = Lead.objects.count()
    converted_leads = Lead.objects.filter(converted_to_student=True).count()
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    context = {
        'sources_stats': sources_stats,
        'status_stats': status_stats,
        'leads_week': leads_week,
        'leads_month': leads_month,
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'conversion_rate': conversion_rate,
    }
    
    return render(request, 'leads/statistics.html', context)

@login_required
@require_POST
def add_source(request):
    """Добавление нового источника"""
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    
    if name:
        source = LeadSource.objects.create(
            name=name,
            description=description,
            is_active=True
        )
        
        # Возвращаем данные нового источника для обновления select
        return JsonResponse({
            'status': 'success',
            'source': {
                'id': source.id,
                'name': source.name
            },
            'message': _('Источник успешно добавлен!')
        })
    
    return JsonResponse({
        'status': 'error',
        'message': _('Пожалуйста, укажите название источника.')
    })

@login_required
def lidlar_hisobotlari(request):
    today = date.today()
    first_day = today.replace(day=1)
    next_month = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1)
    last_day = next_month - timedelta(days=1)

    leads = Lead.objects.filter(
        board_column='new',
        created_at__gte=first_day,
        created_at__lt=next_month
    )

    pie_data = (
        leads.values('source__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    pie_labels = [item['source__name'] or 'Без источника' for item in pie_data]
    pie_counts = [item['count'] for item in pie_data]

    year_start = today.replace(month=1, day=1)
    bar_leads = (
        Lead.objects.filter(board_column='new', created_at__gte=year_start)
        .annotate(month=models.functions.TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    bar_labels = [item['month'].strftime('%Y-%m') for item in bar_leads]
    bar_counts = [item['count'] for item in bar_leads]

    context = {
        'pie_labels': pie_labels,
        'pie_counts': pie_counts,
        'bar_labels': bar_labels,
        'bar_counts': bar_counts,
        'first_day': first_day,
        'last_day': last_day,
        'total_leads': leads.count(),
    }
    return render(request, 'leads/lidlar_hisobotlari.html', context)