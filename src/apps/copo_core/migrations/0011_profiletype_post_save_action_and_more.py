# Generated by Django 4.2.4 on 2024-08-15 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('copo_core', '0010_profiletype_associated_profile_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiletype',
            name='post_save_action',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='profiletype',
            name='pre_save_action',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
