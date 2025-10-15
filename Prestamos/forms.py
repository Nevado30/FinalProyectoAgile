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
            'monto_total':   forms.NumberInput(attrs={'min':'0.01','max':'400000','step':'0.01'}),
            'tasa_interes':  forms.NumberInput(attrs={'min':'0','max':'116','step':'0.01'}),
            'fecha_inicio':  forms.DateInput(attrs={'type':'date'}),
            'cuotas_totales':forms.NumberInput(attrs={'min':'1','max':'36','step':'1'}),
            'moneda_prestamo': forms.Select(attrs={'class': 'input'}, choices=MONEDAS),
            'moneda_pago': forms.Select(attrs={'class': 'input'}, choices=MONEDAS),
        }
def clean(self):
        cleaned = super().clean()
        # redundante pero útil para mensajes más claros si quieres
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