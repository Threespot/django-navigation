from itertools import chain

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.datastructures import SortedDict

from navigation.models import Menu, MenuFolder, MenuItem, MenuLink, MenuPage

from pagemanager.models import Page
from pagemanager.signals import page_edited, page_moved


class Node(object):
    """
    A base class representing a navigation or page node and providing some 
    dictionary-like behavior for navigating the tree.
    """

    def __init__(self):
        super(Node, self).__init__()
        self.children = SortedDict()

    def __getitem__(self, key):
        return self.children.__getitem__(key)

    def __iter__(self):
        return self.children.__iter__()

    def __setitem__(self, key, value):
        return self.children.__setitem__(key, value)

    def __unicode__(self):
        return self.title

    def keys(self):
        return self.children.keys()

    def values(self):
        return self.children.values()

    @property
    def is_leaf(self):
        return not bool(self.children)


class MenuNav(Node):
    
    __slots__ = ( # This keeps memory usage down.
        'html_class_name','pk', 'slug', 
        'template', 'title', 'type', 'url'
    )
    is_public = True
    is_published = True
    show_in_nav = True

    def __init__(self, obj):
        super(MenuNav, self).__init__()
        self.pk = obj.pk
        self.template = None
        self.html_class_name = getattr(obj, 'html_class_name', '')
        self.title = getattr(obj, 'name', None)
        self.url = None
        if isinstance(obj, Menu):
            self.template = obj.template
            self.type = "menu"
        elif isinstance(obj, MenuFolder):
            self.type = "folder"
        elif isinstance(obj, MenuLink):
            self.type = "link"
            self.url =obj.url
        elif isinstance(obj, MenuPage):
            raise TypeError("MenuPage objects cannot be instantiated.")
        elif isinstance(obj, MenuItem):
            raise TypeError("MenuItem objects cannot be instantiated.")
        else:
            raise TypeError("Must be initialized with a navigation model instance.")

    def __repr__(self):
        representation = super(MenuNav, self).__repr__()
        return representation.replace(
            " at ", ' "%s" at ' % self.title.encode("ascii", "ignore")
        ).replace(" object", " %s object" % self.type)

    def __unicode__(self):
        return self.title


class PageNav(Node):
    """
    A model of a page, storing only what is needed to render the navigation.
    """

    __slots__ = ( # This keeps memory usage down.
        'html_class_name', 'limit_depth_to', 'pk', 'slug', 'title',
        'status', 'visibility', 'show_in_nav', 'show_children', 'url'
    )
    type = "page"

    def __eq__(self, other):
        """
        Allows us to compare one page node to another.
        
        >>> page = Page.objects.get(pk=1)
        >>> p2 = PageNav(page)
        >>> p1 = PageNav(page)
        >>> p1 == p2
        True
        
        """
        for attr in self.__slots__:
            if getattr(self, attr, None) != getattr(other, attr, None):
                return False
        return True

    def __init__(self, page):
        super(PageNav, self).__init__()
        if not isinstance(page, Page):
            raise KeyError("Must be initialized with an instance of a Page object.")
        for page_field in ('pk', 'slug', 'title', 'visibility', 'status'):
            setattr(self, page_field, getattr(page, page_field))
        layout  = page.page_layout
        for layout_field in ('show_in_nav', 'show_children'):
            setattr(self, layout_field, getattr(layout, layout_field, True  ))
        if getattr(layout, 'nav_name_override', False):
            self.title = layout.nav_name_override
        # Note that we don't call ``page.get_absolute_url()`` here even though it would seem
        # to be the obvious solution. This is becuase the project's urls file has likely not
        # been loaded when this code is called (in a WSGI environment, at lest). This would
        # create a circular dependency. Instead, figure out the URL without invoking the
        # URL/view routing machinery.
        self.url = "/" + page.materialized_path + "/"
        self.html_class_name = getattr(page, 'html_class_name', '')
        self.limit_depth_to = getattr(page, 'depth', None)

    def __repr__(self):
        representation = super(PageNav, self).__repr__()
        return representation.replace(
            " at ", ' "%s" at ' % self.title.encode("ascii", "ignore")
        )

    def __unicode__(self):
        return self.title

    @property
    def is_public(self):
        """
        Boolean specifying whether the page is publicly visible. Users who
        are logged in should still see such pages in the nav.
        """
        return self.visibility == 'public'

    @property
    def is_published(self):
        """
        Boolean specifying whether the page has been published and should be shown.
        Users should *not* see unpublished pages regardless of whether they are logged-in.
        """
        return self.status == 'published' and self.show_in_nav


class SiteNav(object):
    """
    A dictionary-like container class for all site navigation
    """
    
    def __getitem__(self, key):
        return self.menu_containers.__getitem__(key), self.menu_list.__getitem__(key)

    def __init__(self):
        menus = list(Menu.objects.all())
        self.menu_list = dict(
            [(menu.name, self.grow(menu)) for menu in menus]
        )
        self.menu_containers = dict(
            [(menu.name, MenuNav(menu)) for menu in menus]
        )

    def __iter__(self):
        return self.menu_list.__iter__()

    def _get_node_id_sets(self, key):
        """
        Returns a dictionary of sets of all node type IDs associated 
        with a particular nav item tree.
        """
        _, menu_list = self[key]

        def crawl(node, acc):
            if not node.type in acc:
                acc[node.type] = set()
            acc[node.type].add(node.pk)
            if not node.is_leaf:
                [crawl(child, acc) for child in node.children.values()]
            return acc

        dicts = [crawl(node, {}) for node in menu_list]
        all_keys = set(chain(*[d.keys() for d in dicts]))
        all_dicts = [dict([(key, d.get(key, set())) for key in all_keys]) for d in dicts]
        
        def merge_dicts(a, b):
            for key, value in a.iteritems():
                a[key] = a[key] | b[key]
            return a

        retval = reduce(merge_dicts, all_dicts)
        # Make sure that all types of items are represented in the returned dictionary,
        # even if it's just an empty set.
        for required_key in ('page', 'link', 'folder'):
            if required_key not in retval:
                retval[required_key] = set([])
        return retval

    @classmethod
    def _grow_menu(cls, menu):
        """
        Given a ``Menu`` instance, recursively construct a tree of ``Menu`` objects
        using all children of the given ``Menu``.
        """
        if isinstance(menu, MenuItem):
            menu = menu.obj
        if isinstance(menu, MenuFolder):
            root = MenuNav(menu)
            for child in menu.menu_item.get_children():
                root[child.pk] = cls._grow_menu(child)
            return root
        if isinstance(menu, MenuPage):
            menu.page.html_class_name = menu.html_class_name
            menu.page.depth = menu.depth
            return cls._grow_page(menu.page)
        # MenuLink instances are always terminal.
        if isinstance(menu, MenuLink) or menu.is_leaf_node():
            return MenuNav(menu)
        else:
            root = MenuNav(menu)
            for child in menu.get_children():
                root[child.pk] = cls._grow_menu(child)
            return root

    @classmethod
    def _grow_page(cls, page):
        """
        Given a ``Page`` instance recursively construct a tree of ``Page`` objects
        using all children of the given ``Page``.
        """
        root = PageNav(page)
        if page.is_leaf_node() or root.limit_depth_to == 0:
            return root
        for child in page.get_children():
            if root.limit_depth_to is None:
                child.limit_depth_to = None
            else:
                child.limit_depth_to = root.limit_depth_to - 1
            root[child.slug] = cls._grow_page(child)
        return root

    def get_items_for_type(self, t):
        assert t in ('page', 'link', 'folder'), "Incorrect type."
        return [(key, site_nav._get_node_id_sets(key).get(t, [])) for key in site_nav.keys()]

    @classmethod
    def grow(cls, menu_obj):
        assert isinstance(menu_obj, Menu), "You must provide a Menu object."
        menu_children = menu_obj.menuitem_set.filter(level=0)

        def climb(item):
            if isinstance(item, Page):
                return cls._grow_page(item)
            elif isinstance(item, MenuItem):
                return cls._grow_menu(item.obj)
            else:
                return cls._grow_menu(item)

        menu_children = map(climb, menu_children)
        if menu_children:
            menu_children[0].first = True
            menu_children[-1].last = True
        return menu_children

    def keys(self):
        return self.menu_list.keys()

    def recache(self, key):
        """
        Recache the menu tree with the given key.
        """
        try:
            menu_item, _ = self[key]
            menu = Menu.objects.get(pk=menu_item.pk)
        except KeyError:
            menu = Menu.objects.get(name=key)
        self.menu_list[key] = self.grow(menu)

    def recache_all(self):
        """
        Recache all menu trees.
        """
        for key in self.keys():
            self.recache(key)

    def values(self):
        return self.menu_list.values()


# This global object represents the default navigation set for the site.
site_nav = SiteNav()


############################################################################
#
#     Signal handlers for recaching on changes to Page tree or navigation.
#
############################################################################


@receiver(post_save, sender=MenuFolder)
def folder_save(sender, instance, raw, using, **kwargs):
    items = site_nav.get_items_for_type('folder')
    for nav_key, id_set in items:
        if instance.pk in id_set:
            site_nav.recache(nav_key)


@receiver(post_save, sender=MenuLink)
def link_save(sender, instance, raw, using, **kwargs):
    items = site_nav.get_items_for_type('link')
    for nav_key, id_set in items:
        if instance.pk in id_set:
            site_nav.recache(nav_key)


@receiver(post_save, sender=Menu)
def menu_save(sender, instance, raw, using, **kwargs):
    site_nav.recache(instance.name)


@receiver(post_delete, sender=Page)
def page_deleted(sender, instance, using, **kwargs):
    # If the page being deleted was not showing up in the nav, anyway then
    # there is no need to recache.
    if not instance.is_published() or instance.page_layout.show_in_nav:
        return
    for nav_name in site_nav.keys():
        nav_page_ids = site_nav._get_node_id_sets(nav_name)['page']
        if instance.pk in nav_page_ids:
            site_nav.recache(nav_name)


@receiver(page_edited)
def menu_item_edited(sender, page, created=False, **kwargs):
    """
    This custom signal is fired by page manager whenever a page is edited
    in the admin.
    """    
    if created:
        # If the page is not going to appear in the nav, don't bother
        # to recache.
        if page.is_published() and page.page_layout.show_in_nav:
            # If the item is newly-created, it won't be in the cache yet, so
            # it's parent will be used instead.
            page = page.parent
    for nav_name in site_nav.keys():
        nav_page_ids = site_nav._get_node_id_sets(nav_name)['page']
        if page.pk in nav_page_ids:
            _, pages = site_nav[nav_name]
            site_nav.recache(nav_name)


@receiver(page_moved)
def menu_item_moved(sender, branch_ids, **kwargs):
    """
    A custom signal fired when pages are moved in the admin.
    
    The branch IDs passed in here represent page IDs which may have been affected
    by the move. Find all Nav items that also contain these IDs.
    """
    for nav_name in site_nav.keys():
        nav_page_ids = site_nav._get_node_id_sets(nav_name)['page']
        if nav_page_ids.intersection(branch_ids):
            site_nav.recache(nav_name)
