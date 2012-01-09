from django import template
from django.template.loader import render_to_string

from navigation.models import Menu, MenuPage, MenuLink, MenuFolder

register = template.Library()


class CurrentPageNode(template.Node):
    def render(self, context):
        try:
            context['current_page'] = context['request'].path
        except KeyError:
            context['current_page'] = None
        return ''


@register.tag
def load_current_page(parser, token):
    """
    """
    return CurrentPageNode()


class PageManagerTreeNode(template.Node):
    def __init__(self, base):
        self.base = base

    def render(self, context):
        return render_to_string('navigation/pagemanager_tree.html', {
            'page': context[self.base],
            'depth': int(context['depth']) - 1
        })


@register.tag
def _render_pagemanager_tree(parser, token):
    try:
        tag_name, base = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" \
            % tag_name)
    return PageManagerTreeNode(base)


class LeafNode(template.Node):
    def __init__(self, leaf):
        self.leaf = leaf

    def render(self, context):
        menu_item = context[self.leaf]
        item_obj = menu_item.obj

        if isinstance(item_obj, MenuFolder):
            return render_to_string('navigation/folder.html', {
                'menu_item': menu_item,
                'folder': item_obj
            })

        elif isinstance(item_obj, MenuLink):
            return render_to_string('navigation/link.html', {
                'link': item_obj
            })

        elif isinstance(item_obj, MenuPage):
            return render_to_string('navigation/page.html', {
                'menu_item': menu_item,
                'depth': item_obj.depth,
                'page': item_obj.page
            })

        else:
            raise template.TemplateSyntaxError((
                "The argument for _render_leaf must be an instance of MenuItem"
            ))


@register.tag
def _render_leaf(parser, token):
    try:
        tag_name, leaf = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" \
            % tag_name)
    return LeafNode(leaf)


class NavigationNode(template.Node):
    def __init__(self, menu):
        self.menu = menu

    def render(self, context):
        return render_to_string('navigation/menu.html', {
            'menu': self.menu,
            'leaves': self.menu.menuitem_set.filter(parent=None),
            'request': context['request']
        })


@register.tag
def navigation(parser, token):
    """
    """
    try:
        tag_name, menu_token = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" \
            % tag_name)

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
