from django.contrib import admin
from .models import Categoria, Producto, Cliente, Compra, DetalleCompra


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion')
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'precio', 'stock', 'categoria', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'categoria', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'stock', 'activo')
    ordering = ('nombre',)
    date_hierarchy = 'fecha_creacion'


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'email', 'telefono', 'fecha_registro')
    search_fields = ('nombre', 'email')
    ordering = ('nombre',)
    date_hierarchy = 'fecha_registro'


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 0


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('numero', 'fecha', 'cliente', 'estado', 'total')
    list_filter = ('estado', 'fecha')
    search_fields = ('numero', 'cliente__nombre')
    inlines = [DetalleCompraInline]
