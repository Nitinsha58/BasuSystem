from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '-')

@register.filter
def get_suggestion(action_suggestions, batch):
    return action_suggestions.filter(batch=batch).first()