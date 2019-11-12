# Generated by Django 2.2.7 on 2019-11-12 12:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cluster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=100)),
                ('port', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='InfobaseCredentials',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('login', models.CharField(max_length=100)),
                ('pwd', models.CharField(max_length=100)),
                ('cluster', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='infobase_credentials', to='clusterconfig.Cluster')),
            ],
        ),
        migrations.CreateModel(
            name='ClusterCredentials',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('login', models.CharField(max_length=100)),
                ('pwd', models.CharField(max_length=100)),
                ('cluster', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cluster_credentials', to='clusterconfig.Cluster')),
            ],
        ),
        migrations.AddField(
            model_name='cluster',
            name='host',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clusters', to='clusterconfig.Host'),
        ),
    ]
