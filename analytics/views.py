from django.shortcuts import render
from finance.models import MonthlyIncomeStat

# Create your views here.

def income_chart(request):
    stats = MonthlyIncomeStat.objects.order_by('year', 'month')
    labels = [f'{s.year}-{s.month:02d}' for s in stats]
    income = [float(s.total_income) for s in stats]
    total_income = sum(income)
    return render(request, 'analytics/income_chart.html', {
        'labels': labels,
        'income': income,
        'total_income': total_income
    })
