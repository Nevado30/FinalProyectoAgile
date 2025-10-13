from django import forms
from .models import Prestamo

class DateInput(forms.DateInput):
    input_type = 'date'

class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ['banco', 'descripcion', 'monto_total', 'tasa_interes', 'fecha_inicio', 'cuotas_totales']
        labels = {
            'banco': 'Banco',
            'descripcion': 'Descripción',
            'monto_total': 'Monto total',
            'tasa_interes': 'Tasa de interés (%)',
            'fecha_inicio': 'Fecha de inicio',
            'cuotas_totales': 'Cuotas totales',
        }
        help_texts = {
            'descripcion': 'Ej. “Préstamo para carrito” (opcional)',
        }
        widgets = {
            'banco': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'BCP, Interbank…'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 2,
                'placeholder': 'Ej. Préstamo para carrito'
            }),
            'monto_total': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0'
            }),
            'tasa_interes': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0'
            }),
            'fecha_inicio': DateInput(attrs={
                'class': 'input'
            }),
            'cuotas_totales': forms.NumberInput(attrs={
                'class': 'input',
                'min': '1'
            }),
        }
