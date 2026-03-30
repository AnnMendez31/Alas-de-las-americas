from django.db import models

# ============================================================
# BLOQUE 1 — GEOGRAFÍA
# Países, ciudades y aeropuertos donde opera la aerolínea
# ============================================================


class Pais(models.Model):
    nombre = models.CharField(max_length=100)
    codigo_iso = models.CharField(
        max_length=3, unique=True)  # ej: DOM, USA, ARG

    class Meta:
        db_table = 'Pais'
        verbose_name_plural = 'Países'

    def __str__(self):
        return self.nombre


class Ciudad(models.Model):
    nombre = models.CharField(max_length=100)
    pais = models.ForeignKey(
        Pais, on_delete=models.PROTECT, related_name='ciudades')

    class Meta:
        db_table = 'Ciudad'

    def __str__(self):
        return f"{self.nombre}, {self.pais.nombre}"


class Aeropuerto(models.Model):
    nombre = models.CharField(max_length=150)
    codigo_iata = models.CharField(
        max_length=3, unique=True)  # ej: SDQ, MIA, JFK
    ciudad = models.ForeignKey(
        Ciudad, on_delete=models.PROTECT, related_name='aeropuertos')

    class Meta:
        db_table = 'Aeropuerto'

    def __str__(self):
        # Esto es lo que sale en el select
        return f"{self.codigo_iata} - {self.ciudad.nombre}"


# ============================================================
# BLOQUE 2 — FLOTA DE AERONAVES
# Modelos, aeronaves, clases de servicio y asientos
# ============================================================

class ModeloAeronave(models.Model):
    nombre = models.CharField(max_length=100)  # ej: Airbus A320
    fabricante = models.CharField(max_length=100)  # ej: Airbus, Boeing
    capacidad_maxima = models.PositiveIntegerField()

    class Meta:
        db_table = 'ModeloAeronave'

    def __str__(self):
        return self.nombre


class Aeronave(models.Model):
    matricula = models.CharField(max_length=20, unique=True)  # ej: HI-1023
    modelo = models.ForeignKey(
        ModeloAeronave, on_delete=models.PROTECT, related_name='aeronaves')
    anio_fabricacion = models.PositiveIntegerField()
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'Aeronave'

    def __str__(self):
        return f"{self.matricula} ({self.modelo.nombre})"


class ClaseServicio(models.Model):
    CLASES = [
        ('ECONOMICA', 'Económica'),
        ('ECONOMICA_PREMIUM', 'Económica Premium'),
        ('EJECUTIVA', 'Ejecutiva (Business)'),
        ('PRIMERA', 'Primera Clase'),
    ]
    codigo = models.CharField(max_length=20, choices=CLASES, unique=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = 'ClaseServicio'

    def __str__(self):
        return f"{self.nombre}"


class ConfiguracionClase(models.Model):
    aeronave = models.ForeignKey(
        Aeronave, on_delete=models.CASCADE, related_name='configuraciones')
    clase = models.ForeignKey(ClaseServicio, on_delete=models.PROTECT)
    cantidad_asientos = models.PositiveIntegerField()

    class Meta:
        db_table = 'ConfiguracionClase'
        unique_together = ('aeronave', 'clase')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._generar_asientos()

    def _generar_asientos(self):
        from math import ceil
        LETRAS = ["A", "B", "C", "D", "E", "F"]

        # Calcular desde qué fila empieza esta clase,
        # contando las filas ya usadas por otras clases anteriores
        clases_anteriores = ConfiguracionClase.objects.filter(
            aeronave=self.aeronave
        ).exclude(pk=self.pk)

        filas_usadas = sum(
            ceil(c.cantidad_asientos / len(LETRAS))
            for c in clases_anteriores
        )
        fila_inicio = filas_usadas + 1

        generados = 0
        fila = fila_inicio
        while generados < self.cantidad_asientos:
            for letra in LETRAS:
                if generados >= self.cantidad_asientos:
                    break
                Asiento.objects.get_or_create(
                    aeronave=self.aeronave,
                    fila=fila,
                    letra=letra,
                    defaults={
                        "clase":         self.clase,
                        "junto_ventana": letra in ["A", "F"],
                        "junto_pasillo": letra in ["C", "D"],
                        "estado":        "OPERATIVO",
                    }
                )
                generados += 1
            fila += 1

    def __str__(self):
        return f"{self.aeronave.matricula} — {self.clase.nombre} ({self.cantidad_asientos} asientos)"


class Asiento(models.Model):
    ESTADOS = [
        ('OPERATIVO', 'Operativo'),
        ('MANTENIMIENTO', 'En Mantenimiento'),  # Por si un asiento está dañado
    ]
    aeronave = models.ForeignKey(
        'Aeronave', on_delete=models.CASCADE, related_name='asientos')
    clase = models.ForeignKey('ClaseServicio', on_delete=models.PROTECT)
    fila = models.PositiveIntegerField()
    letra = models.CharField(max_length=2)
    junto_ventana = models.BooleanField(default=False)
    junto_pasillo = models.BooleanField(default=False)
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='OPERATIVO')

    class Meta:
        db_table = 'Asiento'
        unique_together = ('aeronave', 'fila', 'letra')

    def __str__(self):
        return f"{self.aeronave.matricula} — {self.fila}{self.letra} ({self.clase.nombre})"

    def get_posicion_display(self):
        """
        Retorna la posición del asiento para agrupar en selects
        """
        if self.junto_ventana:
            return "Ventana"
        elif self.junto_pasillo:
            return "Pasillo"
        else:
            return "Centro"


# ============================================================
# BLOQUE 3 — ITINERARIOS Y VUELOS
# Periodos, rutas planificadas e instancias de vuelo
# ============================================================

class PeriodoItinerario(models.Model):
    PERIODOS = [
        ('MAR_JUL', 'Marzo – Julio'),
        ('JUL_NOV', 'Julio – Noviembre'),
        ('NOV_MAR', 'Noviembre – Marzo'),
    ]
    codigo = models.CharField(max_length=10, choices=PERIODOS, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        db_table = 'PeriodoItinerario'

    def __str__(self):
        return self.get_codigo_display()


class Itinerario(models.Model):
    """
    Ruta planificada: origen → destino con horario fijo.
    Se publica con al menos 6 meses de anticipación.
    Puede tener escalas (conexiones) intermedias.
    """
    periodo = models.ForeignKey(
        PeriodoItinerario, on_delete=models.PROTECT, related_name='itinerarios')
    origen = models.ForeignKey(
        Aeropuerto, on_delete=models.PROTECT, related_name='salidas')
    destino = models.ForeignKey(
        Aeropuerto, on_delete=models.PROTECT, related_name='llegadas')
    hora_salida = models.TimeField()
    hora_llegada = models.TimeField()
    duracion_minutos = models.PositiveIntegerField()
    dias_operacion = models.CharField(max_length=50)

    class Meta:
        db_table = 'Itinerario'

    def __str__(self):
        return f"{self.origen.codigo_iata} → {self.destino.codigo_iata} ({self.hora_salida}) ({self.hora_llegada})"

    @property
    def es_directo(self):
        """Retorna True si no tiene escalas"""
        return not self.escalas.exists()

    @property
    def num_escalas(self):
        """Retorna el número de escalas"""
        return self.escalas.count()


class Escala(models.Model):
    """
    Representa una escala (parada intermedia) en un itinerario.
    Ejemplo: DOM → EZA (Buenos Aires) CON ESCALA en MIA (Miami)

    Un itinerario puede tener 0, 1 o varias escalas.
    """
    itinerario = models.ForeignKey(
        Itinerario, on_delete=models.CASCADE, related_name='escalas')

    # Aeropuerto donde se hace la escala
    aeropuerto_escala = models.ForeignKey(
        Aeropuerto, on_delete=models.PROTECT, related_name='escalas_aqui')

    # Orden en el itinerario (1era escala, 2da escala, etc.)
    orden = models.PositiveIntegerField()

    # Duración de la escala en minutos
    duracion_minutos = models.PositiveIntegerField(default=60)

    class Meta:
        db_table = 'Escala'
        unique_together = ('itinerario', 'orden')
        ordering = ['orden']

    def __str__(self):
        return f"{self.itinerario} — Escala {self.orden}: {self.aeropuerto_escala.codigo_iata}"


class Vuelo(models.Model):
    """
    Instancia concreta de un itinerario en una fecha específica.
    """
    ESTADOS = [
        ('PROGRAMADO', 'Programado'),
        ('EMBARCANDO', 'Embarcando'),
        ('EN_VUELO', 'En vuelo'),
        ('ATERRIZADO', 'Aterrizado'),
        ('CANCELADO', 'Cancelado'),
        ('DEMORADO', 'Demorado'),
    ]
    # Editable=False para que no salga en el form
    numero_vuelo = models.CharField(max_length=15, unique=True, editable=False)
    itinerario = models.ForeignKey(
        Itinerario, on_delete=models.PROTECT, related_name='vuelos')
    aeronave = models.ForeignKey(
        Aeronave, on_delete=models.PROTECT, related_name='vuelos')
    fecha_salida = models.DateField()
    fecha_llegada = models.DateField()
    hora_salida_real = models.TimeField(null=True, blank=True)
    hora_llegada_real = models.TimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='PROGRAMADO')

    class Meta:
        db_table = 'Vuelo'
        unique_together = ('numero_vuelo', 'fecha_salida')

    def save(self, *args, **kwargs):
        # ── 1. Generar número de vuelo si no existe ──────────────
        if not self.numero_vuelo:
            ultimo_vuelo = Vuelo.objects.all().order_by('id').last()
            if not ultimo_vuelo or '-' not in ultimo_vuelo.numero_vuelo:
                self.numero_vuelo = 'ALAS-0001'
            else:
                try:
                    partes = ultimo_vuelo.numero_vuelo.split('-')
                    ultimo_numero = int(partes[1])
                    self.numero_vuelo = f'ALAS-{ultimo_numero + 1:04d}'
                except (IndexError, ValueError):
                    self.numero_vuelo = 'ALAS-0001'

        # ── 2. Calcular fecha_llegada desde el itinerario ────────
        # Solo si el itinerario está asignado y fecha_salida existe
        if self.itinerario_id and self.fecha_salida:
            from datetime import timedelta, datetime
            hora_salida = self.itinerario.hora_salida
            duracion_min = self.itinerario.duracion_minutos

            # Combinar fecha + hora de salida y sumar la duración
            dt_salida = datetime.combine(self.fecha_salida, hora_salida)
            dt_llegada = dt_salida + timedelta(minutes=duracion_min)
            self.fecha_llegada = dt_llegada.date()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_vuelo} — {self.fecha_salida} — {self.fecha_llegada}"


# ============================================================
# BLOQUE 4 — TARIFAS Y EQUIPAJE
# ============================================================

class TipoEquipaje(models.Model):
    # ej: Equipaje de mano, Bodega
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    # <-- Nos ayuda a saber si va a la bodega o en cabina
    es_bodega = models.BooleanField(default=False)

    class Meta:
        db_table = 'TipoEquipaje'

    def __str__(self):
        return self.nombre


class Tarifa(models.Model):
    """
    Precio de un vuelo para una clase específica.
    Actualizado por sistema externo de IA.
    """
    vuelo = models.ForeignKey(
        Vuelo, on_delete=models.CASCADE, related_name='tarifas')
    clase = models.ForeignKey(ClaseServicio, on_delete=models.PROTECT)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='USD')
    seleccion_asiento_incluida = models.BooleanField(default=False)
    cargo_seleccion_asiento = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    disponible = models.BooleanField(default=True)

    class Meta:
        db_table = 'Tarifa'
        unique_together = ('vuelo', 'clase')

    def __str__(self):
        return f"{self.vuelo} — {self.clase.nombre} — {self.precio} {self.moneda}"


class PoliticaEquipaje(models.Model):
    """
    Define qué equipaje incluye cada tarifa.
    """
    tarifa = models.ForeignKey(
        Tarifa, on_delete=models.CASCADE, related_name='politicas_equipaje')
    tipo_equipaje = models.ForeignKey(TipoEquipaje, on_delete=models.PROTECT)
    cantidad_maxima = models.PositiveIntegerField()
    peso_maximo_kg = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'PoliticaEquipaje'
        unique_together = ('tarifa', 'tipo_equipaje')

    def __str__(self):
        return f"{self.tarifa} — {self.tipo_equipaje.nombre}"


# ============================================================
# BLOQUE 5 — CLIENTES, PASAJEROS Y RESERVAS
# ============================================================

class Cliente(models.Model):
    """
    Quien realiza la reserva.
    """
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Cliente'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Pasajero(models.Model):
    """
    Cada persona que viaja. Puede coincidir con el cliente o ser un tercero.
    """
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    numero_pasaporte = models.CharField(max_length=20, unique=True)
    nacionalidad = models.ForeignKey(Pais, on_delete=models.PROTECT)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'Pasajero'

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.numero_pasaporte})"


class Reserva(models.Model):
    """
    Agrupa todos los tramos y pasajeros de una reserva.
    Puede ser: solo ida, ida y vuelta, o multidestino.
    """
    TIPOS = [
        ('IDA', 'Solo ida'),
        ('IDA_VUELTA', 'Ida y vuelta'),
        ('MULTIDESTINO', 'Multidestino'),
    ]
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de pago'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('COMPLETADA', 'Completada'),
    ]
    codigo_reserva = models.CharField(
        max_length=10, unique=True)  # ej: AA-X7K29
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name='reservas')
    tipo = models.CharField(max_length=15, choices=TIPOS)
    estado = models.CharField(
        max_length=15, choices=ESTADOS, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    precio_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00)
    moneda = models.CharField(max_length=3, default='USD')

    class Meta:
        db_table = 'Reserva'

    def __str__(self):
        return f"Reserva {self.codigo_reserva} — {self.cliente}"


class SegmentoReserva(models.Model):
    """
    Cada tramo de vuelo dentro de una reserva.
    Una reserva multidestino puede tener 3 o más segmentos.
    """
    reserva = models.ForeignKey(
        Reserva, on_delete=models.CASCADE, related_name='segmentos')
    vuelo = models.ForeignKey(Vuelo, on_delete=models.PROTECT)
    tarifa = models.ForeignKey(Tarifa, on_delete=models.PROTECT)
    pasajero = models.ForeignKey(Pasajero, on_delete=models.PROTECT)
    orden = models.PositiveIntegerField()  # 1er tramo, 2do tramo, etc.

    class Meta:
        db_table = 'SegmentoReserva'
        unique_together = ('reserva', 'vuelo', 'pasajero')
        ordering = ['orden']

    def __str__(self):
        return f"{self.reserva.codigo_reserva} — Tramo {self.orden} — {self.pasajero}"


class AsientoReservado(models.Model):
    """
    Asiento asignado a un pasajero en un segmento específico.
    """
    segmento = models.OneToOneField(
        SegmentoReserva, on_delete=models.CASCADE, related_name='asiento_reservado')
    asiento = models.ForeignKey(Asiento, on_delete=models.PROTECT)
    cargo_adicional = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'AsientoReservado'
        constraints = [
            models.UniqueConstraint(
                fields=['segmento', 'asiento'],
                name='unique_asiento_por_segmento'
            )
        ]

    def __str__(self):
        return f"{self.segmento} — Asiento {self.asiento}"


class EquipajeReserva(models.Model):
    """
    Equipaje adicional agregado por un pasajero en un segmento.
    """
    segmento = models.ForeignKey(
        SegmentoReserva, on_delete=models.CASCADE, related_name='equipajes')
    pasajero = models.ForeignKey(
        Pasajero, on_delete=models.CASCADE)  # De quién es la maleta
    tipo_equipaje = models.ForeignKey(TipoEquipaje, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2)
    cargo_adicional = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'EquipajeReserva'

    def __str__(self):
        return f"{self.segmento} — {self.tipo_equipaje.nombre} x{self.cantidad}"
