# accounts/templatetags/whatsapp_tags.py
from django import template
from accounts.whatsapp import lien_whatsapp as _lien_whatsapp

register = template.Library()


@register.simple_tag
def lien_whatsapp(telephone, message):
    """Usage : {% lien_whatsapp client.telephone message_texte as url %}"""
    return _lien_whatsapp(telephone, message)
