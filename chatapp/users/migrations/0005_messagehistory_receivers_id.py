# Generated by Django 4.2.6 on 2023-11-29 08:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_session_chat_user_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagehistory',
            name='receivers_id',
            field=models.ForeignKey(blank=True, db_column='receivers_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receivers_id', to='users.usersmapping'),
        ),
    ]
