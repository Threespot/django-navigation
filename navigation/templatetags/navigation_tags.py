from functools import partial
import re

from django import template
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType

from navigation.models import Menu, MenuItem
from pagemanager.models import Page
from pagemanager.models import attach_generics as attach_page_generics


# Regex that matches on leading or trailing slashes.
outer_slashes = re.compile("(^/|/$)")


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
        try:
            path = context.get('request').META['PATH_INFO']
        except AttributeError:
            # homepage
            path = "/"

        menu = Menu.objects.get(name__iexact=self.menu_name)
        nodes = list(MenuItem.objects.filter(menu=menu))
        attach_menu_generics(nodes, prefetch_pages=True)
        template = menu.template

        return render_to_string(template, {
            'menu': menu,
            'path': path,
            'nodes': nodes,
        }, context)


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

@register.filter
def plustwo(value):
    return value + 2


def fast_menu(request, nav_name, prefix=None):
    """
    Render the given menu item (by name).

    Uses an in-memory version of the navigation tree to render the navigation
    very quickly.

    prefix can be a string with an initial, ignorable part of the path (e.g. resources)

    """
    from navigation.cache import site_nav
    if nav_name not in site_nav:
        #raise KeyError('Unknown site nav name: "%s"' % nav_name)
        return None
    container, menu_list = site_nav[nav_name]
    # Strip outer slashes and split path into a list of slugs.
    try:
        path = outer_slashes.sub("", request.META['PATH_INFO']).split("/")
        if prefix == path[0]:
            path = path[1:]
    except (KeyError, AttributeError):
        # We have a homepage path.
        path = []
    # Bind the ``container`` and ``request`` variables to the function: they will not change on any call.
    _render_node = partial(render_node, container, request)
    return "".join([_render_node(node, path) for node in menu_list])
fast_menu.function = True
fast_menu.takes_request = True


def get_html_class_name(node, is_open):
    """
    Calculate the proper HTML class name for the <li> object representing the given node 
    """
    class_name = "%s %s" % (
        node.html_class_name,
        is_open and 'open' or ''
    )
    return class_name.strip()


def render_node(container, request, node, path, level=2):
    """
    A function that can recursively render <li> elements representing a navigation object.
    """
    slug = getattr(node, 'slug', None)
    is_open = (path and path[0] == slug) or node.type == "folder"
    active = is_open and len(path) == 1
    html_class_name = get_html_class_name(node, is_open)
    lowest_level = level == 2
    if is_open and not node.is_leaf:
        path = path[1:]
        lower_level = level + 1
        children = "".join([render_node(container, request, child, path, level=lower_level) for child in node.values()])
    else:
        children = None
    return render_to_string(container.template, {
        'active': active,
        'children': children,
        'html_class_name': html_class_name,
        'level': level,
        'lowest_level': lowest_level,
        'node': node,
        'request': request 
    })

