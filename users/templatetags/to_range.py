from django import template
register = template.Library()

@register.filter
def to(start, end):
    """Возвращает диапазон от start до end (не включая end)"""
    return range(int(start), int(end)) 