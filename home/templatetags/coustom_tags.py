from django import template

register = template.Library()


def  modify_url(value):
    if value == '/':
        value += "?d=10"
    return value

register.filter('modify_url',modify_url)
