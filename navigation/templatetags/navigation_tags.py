from django import template
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType

from navigation.models import Menu, MenuItem, MenuPage, MenuLink, MenuFolder
from pagemanager.models import Page
from pagemanager.models import attach_generics as attach_page_generics

register = template.Library()

def attach_menu_generics(queryset, prefetch_pages=False):
    # manually attach generic relations to avoid a ridiculous
    # amount of database calls
    generics = {}
    for item in queryset:
        # create a dictionary of object ids per content type id
        generics.setdefault(item.obj_type_id, set()).add(item.obj_id)
    # fetch all associated content types with the queryset
    content_types = ContentType.objects.in_bulk(generics.keys())
    relations = {}
    for ct, fk_list in generics.items():
        # for every content type, fetch all the object ids of that type
        ct_model = content_types[ct].model_class()
        relations[ct] = ct_model.objects.in_bulk(list(fk_list))
    for item in queryset:
        setattr(item, 'obj', relations[item.obj_type_id][item.obj_id])
    # prefetch page for all page items
    if not prefetch_pages:
        return
    pages = []
    for item in queryset:
        if item.obj.node_type == "page":
            pages.append(item.obj.page_id)
    pages = Page.objects.filter(id__in=pages)
    attach_page_generics(pages)
    pages = dict((page.id, page) for page in pages)
    for item in queryset:
        if item.obj.node_type == "page":
            item.obj.page = pages[item.obj.page_id]


class RenderMenuNode(template.Node):
    """
    The node used by the {% menu %} template tag
    """
    def __init__(self, menu_name):
        self.menu_name = menu_name

    def render(self, context):

        path = context.get('request').META['PATH_INFO']

        menu = Menu.objects.get(name__iexact=self.menu_name)
        nodes = list(MenuItem.tree.filter(menu=menu))
        attach_menu_generics(nodes, prefetch_pages=True)
        template = menu.template

        whitelist = [
            "navigation/utility.html",
            "navigation/about.html",
            "navigation/main.html",
            ]

        if not template in whitelist:
            template = "navigation/menu.html"
        
        return render_to_string(template, {
            'menu': menu,
            'path': path,
            'nodes': nodes,
        })


@register.tag
def menu(parser, token):
    """
    The template tag used to render a menu.

    - Menu identifier, which can be one of several things:
        - A quoted string containing the name of a Menu object
        - An unquoted string containing the PK of a Menu object
        - A MenuItem instance
    """
    menu_name = token.split_contents().pop().replace('"', '')
    return RenderMenuNode(menu_name)


@register.filter(name='show_active_page')
def show_active_page(value, arg):
    if value.get_absolute_url() == arg:
        return "active"
    else:
        return ""

@register.filter(name='show_active_trail')
def show_active_trail(value, arg):
    if arg.startswith(value.get_absolute_url()):
        return "active-trail"
    else:
        return ""

@register.filter(name="get_nav_name")
def get_nav_name(value):
    """ helper filter to use instead of the inefficient get_nav_name """
    """ value should be a Page """
    if value.page_layout.nav_name_override:
        return value.page_layout.nav_name_override
    else:
        return value.title
