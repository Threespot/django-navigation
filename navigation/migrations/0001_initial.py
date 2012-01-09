# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MenuItem'
        db.create_table('navigation_menuitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('menu', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['navigation.Menu'], null=True, blank=True)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(blank=True, related_name='parent_menuitem', null=True, to=orm['navigation.MenuItem'])),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=999)),
            ('obj_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('obj_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('navigation', ['MenuItem'])

        # Adding model 'MenuPage'
        db.create_table('navigation_menupage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('mptt.fields.TreeForeignKey')(to=orm['pagemanager.Page'])),
            ('depth', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('navigation', ['MenuPage'])

        # Adding model 'MenuFolder'
        db.create_table('navigation_menufolder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('navigation', ['MenuFolder'])

        # Adding model 'MenuLink'
        db.create_table('navigation_menulink', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=512)),
        ))
        db.send_create_signal('navigation', ['MenuLink'])

        # Adding model 'Menu'
        db.create_table('navigation_menu', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('navigation', ['Menu'])


    def backwards(self, orm):
        
        # Deleting model 'MenuItem'
        db.delete_table('navigation_menuitem')

        # Deleting model 'MenuPage'
        db.delete_table('navigation_menupage')

        # Deleting model 'MenuFolder'
        db.delete_table('navigation_menufolder')

        # Deleting model 'MenuLink'
        db.delete_table('navigation_menulink')

        # Deleting model 'Menu'
        db.delete_table('navigation_menu')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'navigation.menu': {
            'Meta': {'ordering': "['name']", 'object_name': 'Menu'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'navigation.menufolder': {
            'Meta': {'object_name': 'MenuFolder'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'navigation.menuitem': {
            'Meta': {'object_name': 'MenuItem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'menu': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['navigation.Menu']", 'null': 'True', 'blank': 'True'}),
            'obj_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'obj_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '999'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'parent_menuitem'", 'null': 'True', 'to': "orm['navigation.MenuItem']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'navigation.menulink': {
            'Meta': {'object_name': 'MenuLink'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '512'})
        },
        'navigation.menupage': {
            'Meta': {'object_name': 'MenuPage'},
            'depth': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('mptt.fields.TreeForeignKey', [], {'to': "orm['pagemanager.Page']"})
        },
        'pagemanager.page': {
            'Meta': {'unique_together': "(('parent', 'slug'),)", 'object_name': 'Page'},
            'copy_of': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pagemanager.Page']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_homepage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'layout_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '99999', 'null': 'True', 'blank': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['pagemanager.Page']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '32', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'draft'", 'max_length': '32'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'visibility': ('django.db.models.fields.CharField', [], {'default': "'public'", 'max_length': '32'})
        }
    }

    complete_apps = ['navigation']
