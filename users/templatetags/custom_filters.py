from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def percentage(value, arg):
    try:
        value = float(value)
        arg = float(arg)
        if arg == 0:
            return '0%'
        return '{:.0f}%'.format(value * 100 / arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''