# Generated by Django 2.2.1 on 2019-07-16 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0005_groupshare_usershare'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupshare',
            name='can_edit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='publicshare',
            name='can_edit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usershare',
            name='can_edit',
            field=models.BooleanField(default=False),
        ),
    ]
