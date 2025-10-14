from django import forms
from Persona.models import Persona

class NotificacionForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['noti_email', 'noti_sms', 'noti_dias', 'moneda_preferida', 'telefono']
        labels = {
            'noti_email': 'Recibir por correo',
            'noti_sms': 'Recibir por SMS/WhatsApp',
            'noti_dias': 'Días de anticipación (coma separada)',
            'moneda_preferida': 'Moneda preferida',
            'telefono': 'Teléfono (para SMS/WhatsApp)',
        }
        widgets = {
            'noti_email': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'noti_sms': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'noti_dias': forms.TextInput(attrs={'class': 'input', 'placeholder': '7,3,1,0'}),
            'moneda_preferida': forms.Select(attrs={'class': 'input'}, choices=[('PEN','PEN'),('USD','USD'),('EUR','EUR')]),
            'telefono': forms.TextInput(attrs={'class': 'input', 'placeholder': '+51...'}),
        }

    def clean_noti_dias(self):
        raw = (self.cleaned_data.get('noti_dias') or '').strip()
        if not raw:
            return '3,1,0'
        try:
            vals = [int(x) for x in raw.split(',') if str(x).strip()!='']
            vals = sorted(set([v for v in vals if v >= 0]), reverse=True)
            return ','.join(str(v) for v in vals) or '3,1,0'
        except Exception:
            raise forms.ValidationError('Usa números separados por comas. Ej: 7,3,1,0')
