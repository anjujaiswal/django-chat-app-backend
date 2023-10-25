# Generated by Django 4.2.6 on 2023-10-23 05:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_room_last_msg_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmembers',
            name='removed_by',
            field=models.ForeignKey(blank=True, db_column='removed_by', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='removed', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='groupmembers',
            name='member_id',
            field=models.ForeignKey(db_column='member_id', on_delete=django.db.models.deletion.CASCADE, related_name='member', to=settings.AUTH_USER_MODEL),
        ),
    ]
