from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse

from mptt.models import MPTTModel, TreeForeignKey

from staticpages.app_settings import STATICPAGES_PAGE_MODEL


class MenuItem(MPTTModel):
    menu = models.ForeignKey('Menu', null=True, blank=True)
    parent = TreeForeignKey('self', null=True, blank=True, \
        related_name='parent_menuitem')
    order = models.IntegerField(default=999)

    obj_type = models.ForeignKey(ContentType)
    obj_id = models.PositiveIntegerField()
    obj = generic.GenericForeignKey('obj_type', 'obj_id')

    def __unicode__(self):
        return 'Type %s, ID %s' % (self.obj_type, self.obj_id,)

    def get_edit_url(self):
        return self.obj.get_edit_url()

    def get_delete_url(self):
        return self.obj.get_delete_url()


class BaseMenuLeaf(models.Model):
    menu_items = generic.GenericRelation(MenuItem, object_id_field="obj_id", \
        content_type_field="obj_type")

    class Meta:
        abstract = True

    @property
    def menu_item(self):
        return self.menu_items.all()[0]

    def save(self, force_insert=False, force_update=False, using=None):
        super(BaseMenuLeaf, self).save(force_insert, force_update, using)
        mi = MenuItem(
            obj_type=ContentType.objects.get_for_model(self.__class__),
            obj_id=self.pk
        )
        mi.save()

    def get_edit_url(self):
        return reverse('admin:%s_%s_change' % (
            self._meta.app_label,
            self._meta.module_name,
        ), args=[self.pk])

    def get_delete_url(self):
        return reverse('admin:%s_%s_delete' % (
            self._meta.app_label,
            self._meta.module_name,
        ), args=[self.pk])

    @classmethod
    def hide_from_applist(self):
        return True


class MenuPage(BaseMenuLeaf):
    page = TreeForeignKey(STATICPAGES_PAGE_MODEL)
    depth = models.IntegerField(default=0)

    def __unicode__(self, plural='s'):
        if self.depth == 1:
            plural = ''
        return 'Page: %s (and %s level%s of descendants)' % (
            self.page,
            self.depth,
            plural,
        )


class MenuFolder(BaseMenuLeaf):
    name = models.CharField(max_length=128)

    def __unicode__(self):
        return 'Folder: %s' % self.name


class MenuLink(BaseMenuLeaf):
    name = models.CharField(max_length=128)
    url = models.URLField(verify_exists=False, max_length=512)

    def __unicode__(self):
        return 'Link: %s' % self.name


class Menu(models.Model):
    name = models.CharField(max_length=32)

    class Meta:
        ordering = ['name']

    class MPTTMeta:
        order_insertion_by = ['order']

    def __unicode__(self):
        return self.name

    @classmethod
    def get_add_url(self):
        return reverse('admin:%s_%s_add' % (
            self._meta.app_label,
            self._meta.module_name,
        ))

    def get_edit_url(self):
        return reverse('admin:%s_%s_change' % (
            self._meta.app_label,
            self._meta.module_name,
        ), args=[self.pk])

    def get_delete_url(self):
        return reverse('admin:%s_%s_delete' % (
            self._meta.app_label,
            self._meta.module_name,
        ), args=[self.pk])

    def _get_add_member_url(self, model):
        ret = reverse('admin:%s_%s_add' % (
            model._meta.app_label,
            model._meta.module_name,
        ))
        return '%s?menu=%s' % (ret, self.pk)

    def get_add_page_url(self):
        return self._get_add_member_url(MenuPage)

    def get_add_link_url(self):
        return self._get_add_member_url(MenuLink)

    def get_add_folder_url(self):
        return self._get_add_member_url(MenuFolder)

    @property
    def items(self):
        return self.menuitem_set.all()

    @classmethod
    def hide_from_applist(self):
        return True
