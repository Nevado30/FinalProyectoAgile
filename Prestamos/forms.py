from django import forms
from .models import Prestamo, MONEDAS

class DateInput(forms.DateInput):
    input_type = 'date'

class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = [
            'banco', 'descripcion', 'monto_total', 'tasa_interes',
            'fecha_inicio', 'cuotas_totales', 'moneda_prestamo', 'moneda_pago'
        ]
        labels = {
            'banco': 'Banco',
            'descripcion': 'Descripción',
            'monto_total': 'Monto total',
            'tasa_interes': 'Tasa de interés (%) TEA',
            'fecha_inicio': 'Fecha de inicio',
            'cuotas_totales': 'Cuotas totales',
            'moneda_prestamo': 'Moneda del préstamo',
            'moneda_pago': 'Moneda de pago/visualización',
        }
        widgets = {
            'banco': forms.TextInput(attrs={'class': 'input', 'placeholder': 'BCP, Interbank…'}),
            'descripcion': forms.Textarea(attrs={'class': 'textarea', 'rows': 2, 'placeholder': 'Ej. Préstamo para carrito'}),
            'monto_total': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'tasa_interes': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'fecha_inicio': DateInput(attrs={'class': 'input'}),
            'cuotas_totales': forms.NumberInput(attrs={'class': 'input', 'min': '1'}),
            'moneda_prestamo': forms.Select(attrs={'class': 'input'}, choices=MONEDAS),
            'moneda_pago': forms.Select(attrs={'class': 'input'}, choices=MONEDAS),
        }
