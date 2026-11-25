from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    CategoriaForm, ClienteForm, CompraForm, ProductoForm, crear_detalle_formset,
)
from .models import Categoria, Cliente, Compra, Producto, StockInsuficiente


# ---------- INICIO ----------
def inicio(request):
    productos = Producto.objects.filter(activo=True).select_related('categoria')
    categorias = Categoria.objects.all()
    return render(request, 'tienda/inicio.html', {
        'productos': productos,
        'categorias': categorias,
    })


# ---------- CATEGORÍAS (CRUD) ----------
def lista_categorias(request):
    categorias = Categoria.objects.annotate(num_productos=Count('producto'))
    return render(request, 'tienda/categorias/lista.html', {'categorias': categorias})


@login_required
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada correctamente.')
            return redirect('lista_categorias')
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = CategoriaForm()
    return render(request, 'tienda/categorias/form.html', {'form': form, 'titulo': 'Crear categoría'})


@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada correctamente.')
            return redirect('lista_categorias')
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'tienda/categorias/form.html', {'form': form, 'titulo': 'Editar categoría'})


@login_required
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, 'Categoría eliminada correctamente.')
        except ProtectedError:
            messages.error(
                request,
                'No se puede eliminar: la categoría tiene productos que ya forman parte de compras registradas.',
            )
        return redirect('lista_categorias')
    return render(request, 'tienda/categorias/eliminar.html', {'categoria': categoria})


# ---------- PRODUCTOS (CRUD) ----------
def lista_productos(request):
    productos = Producto.objects.select_related('categoria')
    q = request.GET.get('q', '').strip()
    categoria_sel = request.GET.get('categoria', '')
    stock_sel = request.GET.get('stock', '')

    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    if categoria_sel.isdigit():
        productos = productos.filter(categoria_id=categoria_sel)
    if stock_sel == 'sin':
        productos = productos.filter(stock__lte=0)
    elif stock_sel == 'con':
        productos = productos.filter(stock__gt=0)

    return render(request, 'tienda/productos/lista.html', {
        'productos': productos,
        'categorias': Categoria.objects.all(),
        'q': q,
        'categoria_sel': categoria_sel,
        'stock_sel': stock_sel,
        'hay_filtros': bool(q or categoria_sel or stock_sel),
    })


@login_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado correctamente.')
            return redirect('lista_productos')
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = ProductoForm()
    return render(request, 'tienda/productos/form.html', {'form': form, 'titulo': 'Crear producto'})


@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('lista_productos')
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'tienda/productos/form.html', {'form': form, 'titulo': 'Editar producto'})


@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        try:
            producto.delete()
            messages.success(request, 'Producto eliminado correctamente.')
        except ProtectedError:
            messages.error(
                request,
                'No se puede eliminar: el producto aparece en compras registradas. '
                'Edítalo y desmarca "activo" para ocultarlo.',
            )
        return redirect('lista_productos')
    return render(request, 'tienda/productos/eliminar.html', {'producto': producto})


# ---------- CLIENTES (CRUD) ----------
@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'tienda/clientes/lista.html', {'clientes': clientes})


@login_required
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado correctamente.')
            return redirect('lista_clientes')
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = ClienteForm()
    return render(request, 'tienda/clientes/form.html', {'form': form, 'titulo': 'Crear cliente'})


@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente.')
            return redirect('lista_clientes')
        messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'tienda/clientes/form.html', {'form': form, 'titulo': 'Editar cliente'})


@login_required
def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado correctamente.')
        return redirect('lista_clientes')
    return render(request, 'tienda/clientes/eliminar.html', {'cliente': cliente})


# ---------- COMPRAS / PEDIDOS (CRUD) ----------
@login_required
def lista_compras(request):
    compras = Compra.objects.select_related('cliente')
    q = request.GET.get('q', '').strip()
    estado_sel = request.GET.get('estado', '')

    if q:
        compras = compras.filter(Q(numero__icontains=q) | Q(cliente__nombre__icontains=q))
    if estado_sel in Compra.Estado.values:
        compras = compras.filter(estado=estado_sel)
    else:
        estado_sel = ''

    total_listado = compras.exclude(estado=Compra.Estado.CANCELADO).aggregate(t=Sum('total'))['t'] or Decimal('0')
    return render(request, 'tienda/compras/lista.html', {
        'compras': compras,
        'estados': Compra.Estado.choices,
        'q': q,
        'estado_sel': estado_sel,
        'hay_filtros': bool(q or estado_sel),
        'total_listado': total_listado,
    })


@login_required
def detalle_compra(request, pk):
    compra = get_object_or_404(Compra.objects.select_related('cliente'), pk=pk)
    detalles = compra.detalles.select_related('producto')
    return render(request, 'tienda/compras/detalle.html', {'compra': compra, 'detalles': detalles})


@login_required
def crear_compra(request):
    FormSet = crear_detalle_formset(extra=4)
    compra = Compra()
    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        formset = FormSet(request.POST, instance=compra)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    compra = form.save()
                    formset.instance = compra
                    formset.save()
                    compra.recalcular_total()
                    compra.sincronizar_stock()
            except StockInsuficiente as e:
                messages.error(request, str(e))
            else:
                messages.success(request, f'Compra {compra.numero} registrada correctamente.')
                return redirect('detalle_compra', pk=compra.pk)
        else:
            messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = CompraForm(instance=compra)
        formset = FormSet(instance=compra)
    return render(request, 'tienda/compras/form.html', {
        'form': form, 'formset': formset, 'titulo': 'Registrar compra',
    })


@login_required
def editar_compra(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    FormSet = crear_detalle_formset(extra=1)
    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        formset = FormSet(request.POST, instance=compra)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    compra.devolver_stock()      # regresa lo anterior al inventario
                    compra = form.save()
                    formset.save()
                    compra.recalcular_total()
                    compra.sincronizar_stock()   # vuelve a descontar si no está cancelada
            except StockInsuficiente as e:
                messages.error(request, str(e))
            else:
                messages.success(request, f'Compra {compra.numero} actualizada correctamente.')
                return redirect('detalle_compra', pk=compra.pk)
        else:
            messages.error(request, 'No se pudo guardar. Revisa los campos marcados.')
    else:
        form = CompraForm(instance=compra)
        formset = FormSet(instance=compra)
    return render(request, 'tienda/compras/form.html', {
        'form': form, 'formset': formset, 'titulo': f'Editar compra {compra.numero}', 'compra': compra,
    })


@login_required
def eliminar_compra(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        numero = compra.numero
        with transaction.atomic():
            compra.devolver_stock()
            compra.delete()
        messages.success(request, f'Compra {numero} eliminada. El inventario fue restaurado.')
        return redirect('lista_compras')
    return render(request, 'tienda/compras/eliminar.html', {'compra': compra})


# ---------- DASHBOARD ----------
@login_required
def dashboard(request):
    total_categorias = Categoria.objects.count()
    total_productos = Producto.objects.count()
    total_clientes = Cliente.objects.count()
    productos_activos = Producto.objects.filter(activo=True).count()
    productos_sin_stock = Producto.objects.filter(stock__lte=0).count()

    # Valor real del inventario = suma de (precio x existencias)
    valor_inventario = Producto.objects.aggregate(
        total=Sum(
            ExpressionWrapper(F('precio') * F('stock'),
                              output_field=DecimalField(max_digits=14, decimal_places=2))
        )
    )['total'] or Decimal('0')

    # Compras del mes en curso
    ahora = timezone.localtime()
    del_mes = Compra.objects.filter(fecha__year=ahora.year, fecha__month=ahora.month)
    compras_mes = del_mes.exclude(estado=Compra.Estado.CANCELADO).count()
    ventas_mes = del_mes.filter(estado=Compra.Estado.PAGADO).aggregate(t=Sum('total'))['t'] or Decimal('0')
    compras_pendientes = Compra.objects.filter(estado=Compra.Estado.PENDIENTE).count()

    context = {
        'total_categorias': total_categorias,
        'total_productos': total_productos,
        'total_clientes': total_clientes,
        'productos_activos': productos_activos,
        'productos_sin_stock': productos_sin_stock,
        'valor_inventario': valor_inventario,
        'compras_mes': compras_mes,
        'ventas_mes': ventas_mes,
        'compras_pendientes': compras_pendientes,
        'mes_actual': ahora,
        'ultimas_compras': Compra.objects.select_related('cliente')[:5],
        'ultimos_productos': Producto.objects.order_by('-id')[:5],
        'stock_bajo': Producto.objects.filter(activo=True, stock__lte=5).order_by('stock')[:5],
        'por_categoria': Categoria.objects.annotate(num_productos=Count('producto')).order_by('-num_productos'),
    }
    return render(request, 'tienda/dashboard.html', context)
