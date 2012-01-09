from django import template

from navigation.models import Menu

register = template.Library()


class MenuNode(template.Node):
    def render(self, context):
        context['navigation_menus'] = Menu.objects.all()
        context['navigation_menu_model'] = Menu
        return ''


@register.tag
def load_menus(parser, token):
    """
    In any admin change_view, adds the object being changed to the context
    """
    return MenuNode()
