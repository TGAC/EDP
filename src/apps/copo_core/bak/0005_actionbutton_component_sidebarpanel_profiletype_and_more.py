# Generated by Django 4.2.4 on 2024-05-30 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('copo_core', '0004_alter_sequencingcentre_contact_details'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionButton',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.CharField(max_length=100)),
                ('icon', models.CharField(max_length=100)),
                ('action', models.CharField(max_length=100)),
                ('action_type', models.CharField(max_length=100)),
                ('action_url', models.CharField(max_length=100)),
                ('action_data', models.CharField(max_length=100)),
                ('action_target', models.CharField(max_length=100)),
                ('action_icon', models.CharField(max_length=100)),
                ('action_icon_class', models.CharField(max_length=100)),
                ('action_colour', models.CharField(max_length=100)),
                ('action_class', models.CharField(max_length=100)),
                ('action_text', models.CharField(max_length=100)),
                ('action_tooltip', models.CharField(max_length=100)),
                ('action_tooltip_class', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('title', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.CharField(max_length=100)),
                ('widget_icon', models.CharField(max_length=100)),
                ('widget_colour', models.CharField(max_length=200)),
                ('widget_icon_class', models.CharField(max_length=100)),
                ('table_id', models.CharField(max_length=100)),
                ('action_buttons', models.ManyToManyField(to='copo_core.actionbutton')),
            ],
        ),
        migrations.CreateModel(
            name='SidebarPanel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.CharField(max_length=100)),
                ('icon', models.CharField(max_length=100)),
                ('action', models.CharField(max_length=100)),
                ('action_type', models.CharField(max_length=100)),
                ('action_url', models.CharField(max_length=100)),
                ('action_data', models.CharField(max_length=100)),
                ('action_target', models.CharField(max_length=100)),
                ('action_icon', models.CharField(max_length=100)),
                ('action_icon_class', models.CharField(max_length=100)),
                ('action_colour', models.CharField(max_length=100)),
                ('action_class', models.CharField(max_length=100)),
                ('action_text', models.CharField(max_length=100)),
                ('action_tooltip', models.CharField(max_length=100)),
                ('action_tooltip_class', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ProfileType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=20, unique=True)),
                ('description', models.CharField(max_length=100)),
                ('widget_colour', models.CharField(blank=True, max_length=200, null=True)),
                ('is_dtol_profile', models.BooleanField(default=False)),
                ('is_permission_required', models.BooleanField(default=True)),
                ('components', models.ManyToManyField(to='copo_core.component')),
            ],
        ),
        migrations.AddField(
            model_name='component',
            name='sidebar_panels',
            field=models.ManyToManyField(to='copo_core.sidebarpanel'),
        ),
    ]
