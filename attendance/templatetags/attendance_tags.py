from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using dot notation
    Usage: {{ dict|get_item:key }}
    """
    if not dictionary:
        return None
        
    # Handle nested attribute access (e.g., student.id.status)
    if '.' in str(key):
        attrs = str(key).split('.')
        value = dictionary.get(int(attrs[0]))
        for attr in attrs[1:]:
            if hasattr(value, attr):
                value = getattr(value, attr)
            else:
                return None
        return value
    
    # Handle simple dictionary access
    return dictionary.get(key) 