# Generated by Django 3.1.14 on 2022-03-09 22:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0005_auto_20220307_1524'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='menupermission',
            options={'default_permissions': [], 'permissions': [('view_console', 'Can view console view'), ('view_audit', 'Can view audit view'), ('view_workspace', 'Can view workspace view'), ('view_webterminal', 'Can view web terminal'), ('view_filemanager', 'Can view file manager') ], 'verbose_name': 'Menu permission'},
        ),
    ]
