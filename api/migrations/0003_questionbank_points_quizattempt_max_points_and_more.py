# Generated by Django 5.1.4 on 2024-12-27 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_class_section"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionbank",
            name="points",
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="max_points",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="total_points",
            field=models.IntegerField(default=0),
        ),
    ]
