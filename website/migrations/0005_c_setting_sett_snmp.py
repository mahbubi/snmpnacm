# Generated by Django 2.1.7 on 2019-11-14 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0004_c_setting_sett_vlan'),
    ]

    operations = [
        migrations.AddField(
            model_name='c_setting',
            name='sett_snmp',
            field=models.TextField(blank=True, null=True),
        ),
    ]
