# Generated by Django 4.2.6 on 2023-10-22 06:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_room_last_msg_sender_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='last_msg',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='room',
            name='last_msg_sent_by',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
