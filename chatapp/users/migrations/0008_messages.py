# Generated by Django 4.2.6 on 2023-10-23 11:44

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_room_is_archived'),
    ]

    operations = [
        migrations.CreateModel(
            name='Messages',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('message_type', models.CharField(blank=True, choices=[('text', 'text'), ('image', 'image'), ('video', 'video'), ('location', 'location'), ('contact', 'contact'), ('document', 'document'), ('None', None)], max_length=50, null=True)),
                ('file_path', models.FileField(blank=True, null=True, upload_to='uploads/')),
                ('thumbnail_file_path', models.FileField(blank=True, null=True, upload_to='uploads/')),
                ('delivered_to_users', django.contrib.postgres.fields.ArrayField(base_field=models.UUIDField(default=uuid.uuid4), blank=True, null=True, size=None)),
                ('read_by_users', django.contrib.postgres.fields.ArrayField(base_field=models.UUIDField(default=uuid.uuid4), blank=True, null=True, size=None)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('room_id', models.ForeignKey(db_column='room_id', on_delete=django.db.models.deletion.CASCADE, to='users.room')),
                ('sender_id', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'messages',
                'ordering': ['-created_at'],
            },
        ),
    ]
