from django import forms
from .models import Prestamo, MONEDAS, Acreedor


class DateInput(forms.DateInput):
    input_type = 'date'


class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = [
            'acreedor',
            'banco',
            'descripcion',
            'monto_total',
            'tasa_interes',
            'fecha_inicio',
            'cuotas_totales',
            'moneda_prestamo',
            'moneda_pago',
        ]
    labels = {
            'acreedor': 'Acreedor / Entidad',
            'banco': 'Banco / etiqueta corta',
            'descripcion': 'Descripción',
            'monto_total': 'Monto total',
            'tasa_interes': 'Tasa de interés (%) TEA',
            'fecha_inicio': 'Fecha de inicio',
            'cuotas_totales': 'Cuotas totales',
            'moneda_prestamo': 'Moneda del préstamo',
            'moneda_pago': 'Moneda de pago/visualización',
        }
    widgets = {
            'banco': forms.TextInput(
                attrs={'class': 'input', 'placeholder': 'BCP, Interbank…'}
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'textarea',
                    'rows': 2,
                    'placeholder': 'Ej. Préstamo para carrito',
                }
            ),
            'monto_total': forms.NumberInput(
                attrs={'min': '0.01', 'max': '400000', 'step': '0.01'}
            ),
            'tasa_interes': forms.NumberInput(
                attrs={'min': '0', 'max': '116', 'step': '0.01'}
            ),
            'fecha_inicio': DateInput(),
            'cuotas_totales': forms.NumberInput(
                attrs={'min': '1', 'max': '36', 'step': '1'}
            ),
            'moneda_prestamo': forms.Select(attrs={'class': 'input'}, choices=MONEDAS),
            'moneda_pago': forms.Select(attrs={'class': 'input'}, choices=MONEDAS),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        mt = cleaned.get('monto_total')
        ti = cleaned.get('tasa_interes')
        ct = cleaned.get('cuotas_totales')

        if mt is not None and mt > 400000:
            self.add_error('monto_total', 'El monto no puede superar 400 000.')
        if ti is not None and ti > 116:
            self.add_error('tasa_interes', 'La tasa de interés no puede ser mayor que 116.')
        if ct is not None and ct > 36:
            self.add_error('cuotas_totales', 'Las cuotas no pueden ser más de 36.')
        return cleaned

class AcreedorForm(forms.ModelForm):
    class Meta:
        model = Acreedor
        fields = [
            'nombre',
            'tipo',
            'documento',
            'banco',
            'nro_cuenta',
            'nro_cci',
            'alias_yape',
            'celular',
            'email',
        ]
        labels = {
            'nombre': 'Nombre / Razón social',
            'tipo': 'Tipo de acreedor',
            'documento': 'DNI / RUC',
            'banco': 'Banco',
            'nro_cuenta': 'N° de cuenta',
            'nro_cci': 'N° CCI',
            'alias_yape': 'Alias Yape / Plin',
            'celular': 'Celular',
            'email': 'Correo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'maxlength': '150'}),
            'documento': forms.TextInput(attrs={
                'maxlength': '11',
                'inputmode': 'numeric',
                'pattern': r'\d{8,11}',
                'placeholder': 'DNI (8) o RUC (11)',
            }),
            'banco': forms.TextInput(attrs={'maxlength': '100'}),
            'nro_cuenta': forms.TextInput(attrs={
                'maxlength': '40',
                'inputmode': 'numeric',
                'pattern': r'[0-9\- ]{10,30}',
            }),
            'nro_cci': forms.TextInput(attrs={
                'maxlength': '40',
                'inputmode': 'numeric',
                'pattern': r'\d{20}',
            }),
            'alias_yape': forms.TextInput(attrs={'maxlength': '50'}),
            'celular': forms.TextInput(attrs={
                'maxlength': '9',
                'inputmode': 'numeric',
                'pattern': r'\d{9}',
            }),
            'email': forms.EmailInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')
        doc = cleaned.get('documento') or ''

        if doc:
            if tipo == 'persona' and len(doc) != 8:
                self.add_error('documento', 'Para persona natural el DNI debe tener 8 dígitos.')
            if tipo == 'empresa' and len(doc) != 11:
                self.add_error('documento', 'Para empresa el RUC debe tener 11 dígitos.')

        return cleaned
