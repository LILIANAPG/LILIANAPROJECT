import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Compra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(blank=True, editable=False, max_length=20, null=True, unique=True)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('estado', models.CharField(choices=[('pagado', 'Pagado'), ('pendiente', 'Pendiente'), ('cancelado', 'Cancelado')], default='pendiente', max_length=10)),
                ('total', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=12)),
                ('notas', models.TextField(blank=True)),
                ('stock_descontado', models.BooleanField(default=False, editable=False)),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='compras', to='tienda.cliente')),
            ],
            options={
                'verbose_name': 'Compra',
                'verbose_name_plural': 'Compras',
                'ordering': ['-fecha', '-id'],
            },
        ),
        migrations.CreateModel(
            name='DetalleCompra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('precio_unitario', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('compra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='tienda.compra')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tienda.producto')),
            ],
            options={
                'verbose_name': 'Detalle de compra',
                'verbose_name_plural': 'Detalles de compra',
            },
        ),
    ]
