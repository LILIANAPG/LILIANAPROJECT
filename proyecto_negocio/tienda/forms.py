from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import Categoria, Producto, Cliente, Compra, DetalleCompra


class EstiloMixin:
    """Marca con aria-invalid / .is-invalid los campos que tienen error (accesibilidad)."""

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:
                w = self.fields[nombre].widget
                w.attrs['aria-invalid'] = 'true'
                w.attrs['class'] = (w.attrs.get('class', '') + ' is-invalid').strip()


class CategoriaForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        labels = {'nombre': 'Nombre de la categoría', 'descripcion': 'Descripción'}
        help_texts = {
            'nombre': 'Ejemplo: Cuadernos, Plumas, Papel para impresión.',
            'descripcion': 'Opcional. Una frase que ayude a identificar la categoría.',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la categoría'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción (opcional)'}),
        }


class ProductoForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'categoria', 'activo']
        labels = {
            'nombre': 'Nombre del producto',
            'descripcion': 'Descripción',
            'precio': 'Precio de venta (MXN)',
            'stock': 'Existencias',
            'categoria': 'Categoría',
            'activo': 'Producto activo en el catálogo',
        }
        help_texts = {
            'nombre': 'Ejemplo: Cuaderno profesional raya 100 hojas.',
            'descripcion': 'Opcional. Marca, tamaño, color u otros detalles.',
            'precio': 'Precio por pieza, con centavos. Ejemplo: 45.50',
            'stock': 'Piezas disponibles en este momento.',
            'categoria': 'Elige la sección donde se mostrará el producto.',
            'activo': 'Desmarca para ocultarlo del catálogo y de nuevas compras.',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClienteForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'email', 'telefono', 'direccion']
        labels = {
            'nombre': 'Nombre completo',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
        }
        help_texts = {
            'nombre': 'Nombre y apellidos del cliente.',
            'email': 'Ejemplo: cliente@correo.com',
            'telefono': 'Diez dígitos, con o sin lada.',
            'direccion': 'Calle, número, colonia y ciudad.',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'tel'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ---------- COMPRAS ----------
class CompraForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['fecha', 'cliente', 'estado', 'notas']
        labels = {
            'fecha': 'Fecha y hora',
            'cliente': 'Cliente',
            'estado': 'Estado del pedido',
            'notas': 'Notas',
        }
        help_texts = {
            'fecha': 'Por defecto es el momento actual.',
            'cliente': 'Déjalo en "Mostrador" si fue una venta sin registrar cliente.',
            'estado': 'Pendiente y Pagado reservan inventario; Cancelado lo devuelve.',
            'notas': 'Opcional. Ejemplo: entrega el viernes, factura solicitada.',
        }
        widgets = {
            'fecha': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].empty_label = 'Mostrador (sin cliente)'
        self.fields['fecha'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']


class ProductoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.nombre} — ${obj.precio} (stock: {obj.stock})'


class DetalleCompraForm(EstiloMixin, forms.ModelForm):
    producto = ProductoChoiceField(
        queryset=Producto.objects.none(),
        label='Producto',
        empty_label='— Elige un producto —',
        widget=forms.Select(attrs={'class': 'form-control', 'aria-label': 'Producto'}),
    )

    class Meta:
        model = DetalleCompra
        fields = ['producto', 'cantidad']
        labels = {'cantidad': 'Cantidad'}
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'aria-label': 'Cantidad'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        filtro = Q(activo=True)
        if self.instance.pk and self.instance.producto_id:
            filtro |= Q(pk=self.instance.producto_id)  # conserva productos ya vendidos aunque estén inactivos
        self.fields['producto'].queryset = Producto.objects.filter(filtro)

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get('producto')
        # Guarda el precio del momento de la venta (no cambia si luego sube el precio)
        if producto and (not self.instance.pk or 'producto' in self.changed_data):
            self.instance.precio_unitario = producto.precio
        return cleaned


class BaseDetalleFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        vistos = set()
        for form in self.forms:
            datos = getattr(form, 'cleaned_data', None)
            if not datos or datos.get('DELETE'):
                continue
            producto = datos.get('producto')
            if not producto:
                continue
            if producto.pk in vistos:
                raise ValidationError(
                    f'"{producto.nombre}" aparece más de una vez. Suma las cantidades en una sola fila.'
                )
            vistos.add(producto.pk)
        if not vistos:
            raise ValidationError('Agrega al menos un artículo a la compra.')


def crear_detalle_formset(extra=4):
    return forms.inlineformset_factory(
        Compra, DetalleCompra,
        form=DetalleCompraForm, formset=BaseDetalleFormSet,
        extra=extra, can_delete=True,
    )
