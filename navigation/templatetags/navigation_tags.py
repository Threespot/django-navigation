from django import template
from django.template.loader import render_to_string

from navigation.models import Menu, MenuPage, MenuLink, MenuFolder

register = template.Library()


class RenderMenuNode(template.Node):
    """
    The node used by the {% menu %} template tag
    """
    def __init__(self, node_name, inherited_depth):
        self.node_name = node_name
        self.inherited_depth = inherited_depth

    def render(self, context):

        is_active_page = False
        is_active_trail = False

        # Since we are calling this recursively, values inserted to the context
        # by context processors tend to get lost. We bypass this by extracting
        # the info we need from request.META and manually inserting it into the
        # context of future calls.
        try:
            path = context['path']
        except KeyError:
            path = context.get('request').META['PATH_INFO']

        try:
            node = context[self.node_name]

        # This was not a recursive call, so we need to gather all the
        # constituent items in this menu.
        except KeyError:
            node_obj = None
            level = 1
            is_recursive_call = False
            node_name = self.node_name
            node_type = None
            try:
                node = Menu.objects.get(pk=self.node_name)
            except ValueError:
                if (node_name[0] == node_name[-1] and node_name[0] \
                    in ('"', "'")):
                    menu_name = node_name[1:-1]
                else:
                    menu_name = node_name
                node = Menu.objects.get(name=menu_name)
            try:
                inherited_depth = node.depth
            except AttributeError:
                inherited_depth = 0
            children = node.menuitem_set.filter(parent=None)
            use_template = node.template

        # This call was performed automatically by the {% menu %} tag
        else:

            is_recursive_call = True
            node = context.get(self.node_name)
            use_template = context.get('template')
            level = int(context.get('level')) + 1

            try:
                node_obj = node.obj

            # This is the child of a page that is inherited from the site tree
            # via MenuPage with depth, so there is no corresponding MenuPage for
            # this node.
            except AttributeError:
                children = node.get_children()
                inherited_depth = int(context[self.inherited_depth]) - 1
                node_type = 'page'
                node_obj = {
                    'page': node
                }
                is_active_page = path == node.get_absolute_url()
                is_active_trail = path.startswith(node.get_absolute_url())

            else:

                # This is a Folder
                if isinstance(node_obj, MenuFolder):
                    children = node.get_children()
                    inherited_depth = 0
                    node_type = 'folder'

                # This is a link
                elif isinstance(node_obj, MenuLink):
                    children = node.get_children()
                    inherited_depth = 0
                    node_type = 'link'

                # This is a page directly added to the hierarchy
                elif isinstance(node_obj, MenuPage):
                    children = node_obj.page.get_children()
                    inherited_depth = node_obj.depth
                    node_type = 'page'
                    is_active_page = path == node_obj.page.get_absolute_url()
                    is_active_trail = path.startswith(node_obj.page.get_absolute_url())

        return render_to_string(use_template, {
            'template': use_template,
            'node': node,
            'leaf': node_obj,
            'inherited_depth': inherited_depth,
            'is_recursive_call': is_recursive_call,
            'type': node_type,
            'children': children,
            'path': path,
            'is_active_page': is_active_page,
            'is_active_trail': is_active_trail,
            'level': level
        })


@register.tag
def menu(parser, token):
    """
    The template tag used to render a menu. Accepts two arguments:

    - Menu identifier, which can be one of several things:
        - A quoted string containing the name of a Menu object
        - An unquoted string containing the PK of a Menu object
        - A MenuItem instance
    - The remaining depth to traverse, if you are displaying children inherited
      from the site tree by using a MenuPage with a nonzero depth. This should
      be a string parsable by int().

    """
    token = token.split_contents()
    node_name = token.pop(1)
    try:
        inherited_depth = token.pop(1)
    except IndexError:
        inherited_depth = 0

    return RenderMenuNode(node_name, inherited_depth)
