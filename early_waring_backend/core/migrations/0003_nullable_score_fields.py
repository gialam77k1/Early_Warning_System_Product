from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_approval_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bangdiem',
            name='homework_1',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)], verbose_name='Bài tập 1'),
        ),
        migrations.AlterField(
            model_name='bangdiem',
            name='homework_2',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)], verbose_name='Bài tập 2'),
        ),
        migrations.AlterField(
            model_name='bangdiem',
            name='homework_3',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)], verbose_name='Bài tập 3'),
        ),
        migrations.AlterField(
            model_name='bangdiem',
            name='quiz_1',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)], verbose_name='Kiểm tra 1'),
        ),
        migrations.AlterField(
            model_name='bangdiem',
            name='quiz_2',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)], verbose_name='Kiểm tra 2'),
        ),
        migrations.AlterField(
            model_name='bangdiem',
            name='midterm_score',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)], verbose_name='Điểm giữa kỳ'),
        ),
        migrations.AlterField(
            model_name='bangdiem',
            name='final_exam',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)], verbose_name='Điểm cuối kỳ'),
        ),
        migrations.AlterField(
            model_name='bangdiem',
            name='attendance_rate',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)], verbose_name='Tỷ lệ chuyên cần'),
        ),
        migrations.AlterField(
            model_name='bangdiem',
            name='final_score',
            field=models.FloatField(blank=True, help_text='= 0.2*homework_avg + 0.2*quiz_avg + 0.25*midterm + 0.35*final_exam', null=True, verbose_name='Điểm tổng kết'),
        ),
    ]
