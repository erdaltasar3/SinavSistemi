from django import template

register = template.Library()

@register.filter
def count_completed(oturumlar):
    """Count the number of completed sessions in a queryset"""
    return oturumlar.filter(tamamlandi=True).count()

@register.filter
def completion_percentage(oturumlar):
    """Calculate the completion percentage for a set of sessions"""
    total = oturumlar.count()
    if total == 0:
        return 0
    completed = oturumlar.filter(tamamlandi=True).count()
    return (completed / total) * 100 