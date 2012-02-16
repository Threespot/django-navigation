from django.contrib import admin
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.utils.encoding import force_unicode

from navigation.models import Menu, MenuItem, MenuPage, MenuFolder, MenuLink


class MenuAdmin(admin.ModelAdmin):
    change_form_template = 'navigation/menu_change.html'

    def changelist_view(self, request, extra_context=None):
        """
        Redirect the PageLayout changelist_view to the Page changelist_view
        """
        return HttpResponseRedirect(reverse('admin:index'))

    def render_change_form(self, request, context, add=False, change=False, \
        form_url='', obj=None):
        context.update({'obj': obj})
        return super(MenuAdmin, self).render_change_form(request, context, \
            add, change, form_url, obj)

    def get_urls(self):
        from django.conf.urls.defaults import patterns
        urls = super(MenuAdmin, self).get_urls()
        more = patterns('',
            (r'^parentsorders/$', self.admin_site.admin_view(self.parents_orders))
        )
        return more + urls

    def parents_orders(self, request):
        if request.method == 'POST':
            for item_id, values in request.POST.iteritems():
                menu_id, po = values.split(':')
                parent, order = po.split(',')
                menu = Menu.objects.get(pk=int(menu_id))
                item = MenuItem.objects.get(pk=int(item_id))
                try:
                    item.parent = MenuItem.objects.get(pk=parent)
                except ValueError:
                    item.parent = None
                item.order = order
                item.save()
            return HttpResponse()
        raise Http404


class MenuLeafAdmin(admin.ModelAdmin):
    change_form_template = 'navigation/menuleaf_change.html'

    def add_view(self, request, form_url='', extra_context=None):
        if not request.GET.has_key('menu'):
            raise Http404
        return super(MenuLeafAdmin, self).add_view(request, form_url, \
            extra_context)

    def save_model(self, request, obj, form, change):
        obj.save()
        if not change:
            item = obj.menu_item
            menu = Menu.objects.get(pk=int(form.data['menu']))
            item.menu = menu
            item.save()

    def changelist_view(self, request, extra_context=None):
        """
        Redirect the PageLayout changelist_view to the Page changelist_view
        """
        return HttpResponseRedirect(reverse('admin:index'))

    def response_add(self, request, obj, post_url_continue='../%s/'):
        """
        Determines the HttpResponse for the add_view stage.
        """
        opts = obj._meta
        pk_value = obj._get_pk_val()

        msg = '"%s" was successfully added to the "%s" menu.' % (
            force_unicode(obj),
            obj.menu_item.menu
        )

        if "_continue" in request.POST:
            self.message_user(request, msg + ' ' + "You may edit it again below.")
            return HttpResponseRedirect(post_url_continue % pk_value)

        elif "_addanother" in request.POST:
            self.message_user(request, msg + ' ' + ("You may add another %s below." % force_unicode(opts.verbose_name)))
            return HttpResponseRedirect('%s?menu=%s' % (
                request.path,
                obj.menu_item.menu.pk,
            ))

        else:
            self.message_user(request, msg)
            return HttpResponseRedirect(obj.menu_item.menu.get_edit_url())

    def response_change(self, request, obj):
        """
        Determines the HttpResponse for the change_view stage.
        """
        opts = obj._meta
        pk_value = obj._get_pk_val()

        msg = 'The menu item "%s" was changed successfully.' % force_unicode(obj)

        if "_continue" in request.POST:
            self.message_user(request, msg + ' ' + "You may edit it again below.")
            return HttpResponseRedirect(request.path)

        elif "_addanother" in request.POST:
            self.message_user(request, msg + ' ' + ("You may add another %s below." % force_unicode(opts.verbose_name)))
            return HttpResponseRedirect(obj.menu_item.menu.get_add_page_url())

        else:
            self.message_user(request, msg)
            return HttpResponseRedirect(obj.menu_item.menu.get_edit_url())


admin.site.unregister(Site)
admin.site.register(Menu, MenuAdmin)
admin.site.register(MenuPage, MenuLeafAdmin)
admin.site.register(MenuFolder, MenuLeafAdmin)
admin.site.register(MenuLink, MenuLeafAdmin)
