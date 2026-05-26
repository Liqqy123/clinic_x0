from django import template

register = template.Library()


@register.filter
def split_lines(text):
    """
    Разбивает текст по новым строкам и возвращает список непустых строк.
    Использование в шаблоне:
        {% for line in doctor.specialization_list|split_lines %}
            <li>{{ line }}</li>
        {% endfor %}
    """
    if not text:
        return []
    return [line.strip() for line in text.split('\n') if line.strip()]
