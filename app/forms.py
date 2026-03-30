from django import forms
from .models import Pasajero, Pais, Ciudad, Itinerario, Aeronave, Aeropuerto, PeriodoItinerario, Vuelo, Tarifa, ClaseServicio, ConfiguracionClase, Escala, PoliticaEquipaje, TipoEquipaje
from django.forms import inlineformset_factory


class PasajeroForm(forms.ModelForm):
    class Meta:
        model = Pasajero
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Juan'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Pérez'}),
            'numero_pasaporte': forms.TextInput(attrs={'class': 'form-control'}),
            'nacionalidad': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

# --- Formulario de Países ---


class PaisForm(forms.ModelForm):
    class Meta:
        model = Pais
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. República Dominicana'}),
            'codigo_iso': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. DOM'}),
        }

# --- Formulario de Ciudades ---


class CiudadForm(forms.ModelForm):
    class Meta:
        model = Ciudad
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Santo Domingo'}),
            'pais': forms.Select(attrs={'class': 'form-select'}),
        }

# --- Formulario de Aeropuertos ---


class AeropuertoForm(forms.ModelForm):
    class Meta:
        model = Aeropuerto
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Aeropuerto Internacional Las Américas'}),
            'codigo_iata': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. SDQ'}),
            'ciudad': forms.Select(attrs={'class': 'form-select'}),
        }


class ItinerarioForm(forms.ModelForm):
    class Meta:
        model = Itinerario
        fields = [
            'periodo', 'origen', 'destino',
            'hora_salida', 'hora_llegada',
            'duracion_minutos', 'dias_operacion'
        ]
        widgets = {
            'periodo': forms.Select(attrs={'class': 'form-select'}),
            'origen': forms.Select(attrs={'class': 'form-select'}),
            'destino': forms.Select(attrs={'class': 'form-select'}),
            'hora_salida': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_llegada': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'dias_operacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: LUN,MIE,VIE'}),
        }


class EscalaForm(forms.ModelForm):
    """Formulario para crear/editar una escala"""
    class Meta:
        model = Escala
        fields = ['aeropuerto_escala', 'orden', 'duracion_minutos']
        widgets = {
            'aeropuerto_escala': forms.Select(attrs={'class': 'form-select'}),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Ej: 1 (primera escala)'
            }),
            'duracion_minutos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '15',
                'value': '60',
                'placeholder': 'Duración en minutos'
            }),
        }
        labels = {
            'aeropuerto_escala': 'Aeropuerto de Escala',
            'orden': 'Orden (1ª, 2ª, 3ª...)',
            'duracion_minutos': 'Duración de la Escala (minutos)',
        }


# Formset para escalas
EscalaFormSet = inlineformset_factory(
    Itinerario, Escala,
    form=EscalaForm,
    extra=2,  # Permite 2 escalas adicionales por defecto
    can_delete=True
)


class VueloForm(forms.ModelForm):
    class Meta:
        model = Vuelo
        fields = [
            'itinerario',
            'aeronave',
            'fecha_salida',
            'estado',
        ]
        widgets = {
            'itinerario':  forms.Select(attrs={'class': 'form-select'}),
            'aeronave':    forms.Select(attrs={'class': 'form-select'}),
            'fecha_salida': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'estado':      forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'itinerario':   'Itinerario (ruta + horario)',
            'aeronave':     'Aeronave asignada',
            'fecha_salida': 'Fecha de operación',
            'estado':       'Estado inicial',
        }


class BusquedaVueloForm(forms.Form):
    TIPOS_VIAJE = [
        ('IDA',          'Solo ida'),
        ('IDA_VUELTA',   'Ida y vuelta'),
        ('MULTIDESTINO', 'Multidestino'),
    ]
    tipo_viaje = forms.ChoiceField(
        choices=TIPOS_VIAJE,
        initial='IDA',
        widget=forms.RadioSelect(attrs={'class': 'tipo-viaje-radio'}),
        label=''
    )
    origen = forms.ModelChoiceField(
        queryset=Aeropuerto.objects.select_related(
            'ciudad__pais').order_by('ciudad__pais__nombre', 'nombre'),
        empty_label='Selecciona origen...',
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
        label='Origen'
    )
    destino = forms.ModelChoiceField(
        queryset=Aeropuerto.objects.select_related(
            'ciudad__pais').order_by('ciudad__pais__nombre', 'nombre'),
        empty_label='Selecciona destino...',
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
        label='Destino'
    )
    fecha = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control form-control-lg'}),
        label='Fecha de salida'
    )
    # Solo ida y vuelta
    fecha_regreso = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control form-control-lg'}),
        label='Fecha de regreso'
    )
    num_pasajeros = forms.IntegerField(
        min_value=1, max_value=9, initial=1,
        widget=forms.NumberInput(
            attrs={'class': 'form-control form-control-lg', 'min': 1, 'max': 9}),
        label='Pasajeros'
    )

    def clean(self):
        cleaned = super().clean()
        origen = cleaned.get('origen')
        destino = cleaned.get('destino')
        tipo = cleaned.get('tipo_viaje')

        if origen and destino and origen == destino:
            raise forms.ValidationError(
                'El origen y el destino no pueden ser iguales.')

        if tipo == 'IDA_VUELTA' and not cleaned.get('fecha_regreso'):
            self.add_error('fecha_regreso',
                           'Debes indicar la fecha de regreso.')

        fecha = cleaned.get('fecha')
        fecha_regreso = cleaned.get('fecha_regreso')
        if fecha and fecha_regreso and fecha_regreso < fecha:
            self.add_error(
                'fecha_regreso', 'La fecha de regreso debe ser igual o posterior a la de salida.')

        return cleaned


class TramoExtraForm(forms.Form):
    """Un tramo adicional para vuelos multidestino."""
    origen = forms.ModelChoiceField(
        queryset=Aeropuerto.objects.select_related(
            'ciudad__pais').order_by('ciudad__pais__nombre', 'nombre'),
        empty_label='Selecciona origen...',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Origen'
    )
    destino = forms.ModelChoiceField(
        queryset=Aeropuerto.objects.select_related(
            'ciudad__pais').order_by('ciudad__pais__nombre', 'nombre'),
        empty_label='Selecciona destino...',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Destino'
    )
    fecha = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha'
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('origen') and cleaned.get('destino') and cleaned['origen'] == cleaned['destino']:
            raise forms.ValidationError(
                'Origen y destino deben ser diferentes.')
        return cleaned


class PasajeroReservaForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
        label='Nombre'
    )
    apellido = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
        label='Apellido'
    )
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha de nacimiento'
    )
    numero_pasaporte = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Ej: AB123456'}),
        label='Número de pasaporte'
    )
    nacionalidad = forms.ModelChoiceField(
        queryset=Pais.objects.order_by('nombre'),
        empty_label='Selecciona país...',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Nacionalidad'
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
        label='Correo electrónico'
    )
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': '+1 809 000 0000'}),
        label='Teléfono'
    )
    asiento_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        self.index = kwargs.pop('index', 0)
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validar que si el email existe, los datos deben coincidir"""
        cleaned = super().clean()
        email = cleaned.get('email', '').strip()

        # Si no hay email, no hay validación que hacer
        if not email:
            return cleaned

        # Buscar si existe un cliente con este email
        from .models import Cliente
        cliente_existente = Cliente.objects.filter(email=email).first()

        if cliente_existente:
            # El email ya existe, verificar que los datos coincidan
            nombre_nuevo = cleaned.get('nombre', '').strip()
            apellido_nuevo = cleaned.get('apellido', '').strip()

            # Comparar nombre y apellido (case-insensitive)
            if (cliente_existente.nombre.strip().lower() != nombre_nuevo.lower() or
                    cliente_existente.apellido.strip().lower() != apellido_nuevo.lower()):

                # Los datos no coinciden
                self.add_error('email',
                               f"El email '{email}' ya está registrado con el nombre "
                               f"'{cliente_existente.nombre} {cliente_existente.apellido}'. "
                               f"Usa un email diferente o usa el mismo nombre y apellido que antes."
                               )

        return cleaned


class TarifaForm(forms.ModelForm):
    """
    Formulario para crear/editar tarifas de vuelo.
    Incluye campos para precio del asiento.
    """
    class Meta:
        model = Tarifa
        fields = [
            'clase',
            'precio',
            'moneda',
            'seleccion_asiento_incluida',
            'cargo_seleccion_asiento',
            'disponible'
        ]
        widgets = {
            'clase': forms.Select(attrs={
                'class': 'form-select',
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'min': '0'
            }),
            'moneda': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'USD',
                'maxlength': '3',
                'style': 'text-transform: uppercase;'
            }),
            'seleccion_asiento_incluida': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'cargo_seleccion_asiento': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'min': '0'
            }),
            'disponible': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'clase': 'Clase de servicio',
            'precio': 'Precio base',
            'moneda': 'Moneda',
            'seleccion_asiento_incluida': 'Selección de asiento incluida',
            'cargo_seleccion_asiento': 'Cargo por selección de asiento',
            'disponible': 'Tarifa disponible',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.vuelo_id:
            # Obtenemos solo las clases que ese avión específico tiene configuradas
            aeronave = self.instance.vuelo.aeronave
            clases_disponibles = ConfiguracionClase.objects.filter(
                aeronave=aeronave
            ).values_list('clase_id', flat=True)

            self.fields['clase'].queryset = ClaseServicio.objects.filter(
                id__in=clases_disponibles)

    def clean(self):
        cleaned = super().clean()

        # Si seleccion_asiento_incluida es False, cargo_seleccion_asiento debe ser > 0
        if not cleaned.get('seleccion_asiento_incluida'):
            cargo = cleaned.get('cargo_seleccion_asiento', 0)
            if cargo == 0:
                self.add_error(
                    'cargo_seleccion_asiento',
                    'Si la selección no está incluida, debe tener un cargo asociado.'
                )

        return cleaned


class AeronaveForm(forms.ModelForm):
    class Meta:
        model = Aeronave
        fields = ['matricula', 'modelo', 'anio_fabricacion', 'activa']
        # Agregamos esta sección para los nombres legibles:
        labels = {
            'anio_fabricacion': 'Año de fabricación',
            'matricula': 'Matrícula',
            'activa': '¿Está activa?',
        }
        widgets = {
            'matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: HI-1023'}),
            'modelo': forms.Select(attrs={'class': 'form-select'}),
            'anio_fabricacion': forms.NumberInput(attrs={'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ConfiguracionClaseForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionClase
        fields = ['clase', 'cantidad_asientos']
        widgets = {
            'clase': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_asientos': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }


# Formset para gestionar las clases de un avión al mismo tiempo
ConfiguracionFormSet = inlineformset_factory(
    Aeronave, ConfiguracionClase,
    form=ConfiguracionClaseForm,
    extra=4,
    can_delete=True
)

# Formset para gestionar las tarifas de un vuelo (con delete mejorado)
TarifaFormSet = inlineformset_factory(
    Vuelo, Tarifa,
    form=TarifaForm,
    extra=0,
    can_delete=True
)


class PoliticaEquipajeForm(forms.ModelForm):
    class Meta:
        model = PoliticaEquipaje
        fields = ['tipo_equipaje', 'cantidad_maxima', 'peso_maximo_kg']
        widgets = {
            'tipo_equipaje': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_maxima': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '1', 'placeholder': 'Ej: 1'
            }),
            'peso_maximo_kg': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'min': '0', 'placeholder': 'Ej: 23.0'
            }),
        }
        labels = {
            'tipo_equipaje':  'Tipo de equipaje',
            'cantidad_maxima': 'Cantidad máx.',
            'peso_maximo_kg':  'Peso máx. (kg)',
        }

    def clean(self):
        """Permitir formularios completamente vacíos (para los 'extra' no usados)"""
        cleaned = super().clean()

        # Obtener valores de los campos
        tipo_equipaje = cleaned.get('tipo_equipaje')
        cantidad = cleaned.get('cantidad_maxima')
        peso = cleaned.get('peso_maximo_kg')

        # CASO 1: Si TODOS están vacíos → es un "extra" no usado, permitir sin validación
        if not tipo_equipaje and not cantidad and not peso:
            return cleaned

        # CASO 2: Si hay datos COMPLETOS → validación normal (sin errores)
        if tipo_equipaje and cantidad and peso:
            return cleaned

        # CASO 3: Si hay datos PARCIALES → ERROR
        # (al menos un campo tiene algo, pero no todos)
        if tipo_equipaje or cantidad or peso:
            if not tipo_equipaje:
                self.add_error('tipo_equipaje',
                               'Selecciona un tipo de equipaje.')
            if not cantidad:
                self.add_error('cantidad_maxima', 'Indica la cantidad máxima.')
            if not peso:
                self.add_error('peso_maximo_kg', 'Indica el peso máximo.')

        return cleaned


PoliticaEquipajeFormSet = inlineformset_factory(
    Tarifa, PoliticaEquipaje,
    form=PoliticaEquipajeForm,
    extra=0,
    can_delete=True,
    validate_max=False
)


class TipoEquipajeForm(forms.ModelForm):
    class Meta:
        model = TipoEquipaje
        fields = ['nombre', 'descripcion', 'es_bodega']
        widgets = {
            'nombre':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Equipaje de mano'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'es_bodega':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'es_bodega': '¿Va en bodega?'
        }
