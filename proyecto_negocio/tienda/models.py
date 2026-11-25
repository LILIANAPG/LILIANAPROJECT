from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorías"


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']


class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


# ---------------------------------------------------------------------------
# MÓDULO DE COMPRAS / PEDIDOS (Práctica 8)
# ---------------------------------------------------------------------------
class StockInsuficiente(Exception):
    """Se lanza cuando un artículo pedido supera las existencias."""


class Compra(models.Model):
    class Estado(models.TextChoices):
        PAGADO = 'pagado', 'Pagado'
        PENDIENTE = 'pendiente', 'Pendiente'
        CANCELADO = 'cancelado', 'Cancelado'

    numero = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    fecha = models.DateTimeField(default=timezone.now)
    cliente = models.ForeignKey(
        Cliente, null=True, blank=True, on_delete=models.SET_NULL, related_name='compras'
    )
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    notas = models.TextField(blank=True)
    # Indica si los artículos de esta compra ya fueron descontados del inventario
    stock_descontado = models.BooleanField(default=False, editable=False)

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ['-fecha', '-id']

    def __str__(self):
        return self.numero or f'Compra #{self.pk}'

    def save(self, *args, **kwargs):
        creando = self.pk is None
        super().save(*args, **kwargs)
        if creando and not self.numero:
            self.numero = f'P-{self.pk:05d}'
            super().save(update_fields=['numero'])

    @property
    def nombre_cliente(self):
        return self.cliente.nombre if self.cliente_id else 'Mostrador'

    def recalcular_total(self):
        self.total = sum((d.subtotal for d in self.detalles.all()), Decimal('0.00'))
        return self.total

    # --- manejo de inventario -------------------------------------------
    def descontar_stock(self):
        """Resta del inventario cada artículo. Si no alcanza, lanza StockInsuficiente."""
        for d in self.detalles.select_related('producto'):
            producto = Producto.objects.select_for_update().get(pk=d.producto_id)
            if producto.stock < d.cantidad:
                raise StockInsuficiente(
                    f'Stock insuficiente de "{producto.nombre}": '
                    f'hay {producto.stock} y se pidieron {d.cantidad}.'
                )
            producto.stock -= d.cantidad
            producto.save(update_fields=['stock'])
        self.stock_descontado = True

    def devolver_stock(self):
        """Regresa al inventario lo que se había descontado (editar, cancelar o eliminar)."""
        if not self.stock_descontado:
            return
        for d in self.detalles.all():
            Producto.objects.filter(pk=d.producto_id).update(stock=F('stock') + d.cantidad)
        self.stock_descontado = False

    def sincronizar_stock(self):
        """Cancelado devuelve existencias; Pagado/Pendiente las reservan."""
        if self.estado == self.Estado.CANCELADO:
            self.devolver_stock()
        elif not self.stock_descontado:
            self.descontar_stock()
        self.save(update_fields=['total', 'stock_descontado'])


class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Detalle de compra"
        verbose_name_plural = "Detalles de compra"

    def __str__(self):
        return f'{self.cantidad} x {self.producto}'

    def save(self, *args, **kwargs):
        if self.precio_unitario is None:
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return (self.precio_unitario or Decimal('0')) * self.cantidad
