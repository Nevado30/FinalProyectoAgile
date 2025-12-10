from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from decimal import Decimal

from Persona.models import Persona


MONEDAS = (
    ('PEN', 'PEN'),
    ('USD', 'USD'),
    ('EUR', 'EUR'),
)

class Acreedor(models.Model):
    TIPO_CHOICES = [
        ('persona', 'Persona natural'),
        ('empresa', 'Empresa / negocio'),
    ]
    id_acreedor = models.AutoField(primary_key=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='acreedores',
        help_text="Usuario dueño de este acreedor (el que gestiona la deuda).",
    )
    nombre = models.CharField(
        max_length=150,
        help_text="Nombre del acreedor: persona, banco, empresa, etc.",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='persona',
    )
    documento = models.CharField(
        max_length=11,
        blank=True,
        help_text="DNI (8) o RUC (11). Solo números.",
        validators=[
            RegexValidator(
                r'^\d{8,11}$',
                'El documento debe contener solo números (8 para DNI o 11 para RUC).'
            )
        ],
    )
    banco = models.CharField(
        max_length=100,
        blank=True,
        help_text="Banco donde le vas a depositar (opcional).",
    )
    nro_cuenta = models.CharField(
        max_length=40,
        blank=True,
        help_text="N° de cuenta bancaria (10 a 30 dígitos).",
        validators=[
            RegexValidator(
                r'^[0-9\- ]{10,30}$',
                'La cuenta debe tener entre 10 y 30 caracteres numéricos (puede incluir espacios o guiones).'
            )
        ],
    )
    nro_cci = models.CharField(
        max_length=40,
        blank=True,
        help_text="N° CCI (20 dígitos).",
        validators=[
            RegexValidator(
                r'^\d{20}$',
                'El CCI debe tener exactamente 20 dígitos.'
            )
        ],
    )
    alias_yape = models.CharField(
        max_length=50,
        blank=True,
        help_text="Alias o nombre que usas para Yape/Plin (opcional).",
    )
    celular = models.CharField(
        max_length=9,
        blank=True,
        help_text="Celular para Yape/Plin u otro medio (9 dígitos).",
        validators=[
            RegexValidator(
                r'^\d{9}$',
                'El celular debe tener exactamente 9 dígitos.'
            )
        ],
    )
    email = models.EmailField(
        blank=True,
        help_text="Correo del acreedor (opcional).",
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
class Prestamo(models.Model):
    id_prestamo = models.AutoField(primary_key=True)
    persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        related_name='prestamos',
    )
    acreedor = models.ForeignKey(
        'Acreedor',
        on_delete=models.PROTECT,
        related_name='prestamos',
        null=True,
        blank=True,
        help_text="Persona o entidad a la que realmente le debes.",
    )
    banco = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    monto_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.01')),
            MaxValueValidator(Decimal('400000')),
        ],
    )

    fecha_inicio = models.DateField()

    cuotas_totales = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(36)]
    )

    tasa_interes = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('116')),
        ],
    )

    moneda_prestamo = models.CharField(
        max_length=3,
        choices=MONEDAS,
        default='PEN',
    )
    moneda_pago = models.CharField(
        max_length=3,
        choices=MONEDAS,
        default='PEN',
    )

    def __str__(self):
        return f"{self.banco} — {self.persona} — #{self.id_prestamo}"
