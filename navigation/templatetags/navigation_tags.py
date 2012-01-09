from django import template

from navigation.models import Menu

register = template.Library()


class NavigationNode(template.Node):
    def __init__(self, menu):
        self.menu = menu

    def render(self, context):
        return ''

    def render_folder(self, folder):
        pass

    def render_link(self, folder):
        pass

    def render_page(self, folder):
        pass


@register.tag
def navigation(parser, token):
    """
    """
    try:
        tag_name, menu_token = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])

    try:
        menu = Menu.objects.get(pk=menu_token)
    except ValueError:
        try:
            if (menu_token[0] == menu_token[-1] and menu_token[0] in ('"', "'")):
                menu_name = menu_token[1:-1]
            else:
                menu_name = menu_token
            menu = Menu.objects.get(name=menu_name)
        except Menu.DoesNotExist:
            menu = None

    return NavigationNode(menu)
