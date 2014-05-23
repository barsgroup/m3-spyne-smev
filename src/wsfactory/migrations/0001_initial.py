# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'LogEntry'
        db.create_table('wsfactory_log', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('application', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('api', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('in_object', self.gf('django.db.models.fields.TextField')(null=True)),
            ('request_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True)),
            ('response_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True)),
            ('traceback_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True)),
        ))
        db.send_create_signal('wsfactory', ['LogEntry'])


    def backwards(self, orm):
        # Deleting model 'LogEntry'
        db.delete_table('wsfactory_log')


    models = {
        'wsfactory.logentry': {
            'Meta': {'object_name': 'LogEntry', 'db_table': "'wsfactory_log'"},
            'api': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'application': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_object': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'request_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True'}),
            'response_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'traceback_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['wsfactory']