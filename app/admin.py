from django.contrib import admin
from .models import (
    Pais, Ciudad, Aeropuerto,
    ModeloAeronave, Aeronave, ClaseServicio,
    ConfiguracionClase, Asiento,
    PeriodoItinerario, Itinerario, Vuelo,
    TipoEquipaje, Tarifa, PoliticaEquipaje,
    Cliente, Pasajero, Reserva,
    SegmentoReserva, AsientoReservado, EquipajeReserva
)


# ============================================================
# BLOQUE 1 — GEOGRAFÍA
# ============================================================

@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_iso')
    search_fields = ('nombre', 'codigo_iso')
    ordering = ('nombre',)


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'pais')
    search_fields = ('nombre',)
    list_filter = ('pais',)
    ordering = ('pais', 'nombre')


@admin.register(Aeropuerto)
class AeropuertoAdmin(admin.ModelAdmin):
    list_display = ('codigo_iata', 'nombre', 'ciudad')
    search_fields = ('codigo_iata', 'nombre')
    list_filter = ('ciudad__pais',)
    ordering = ('codigo_iata',)


# ============================================================
# BLOQUE 2 — FLOTA
# ============================================================

@admin.register(ModeloAeronave)
class ModeloAeronaveAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fabricante', 'capacidad_maxima')
    search_fields = ('nombre', 'fabricante')


@admin.register(Aeronave)
class AeronaveAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'modelo', 'anio_fabricacion', 'activa')
    search_fields = ('matricula',)
    list_filter = ('modelo', 'activa')
    ordering = ('matricula',)


@admin.register(ClaseServicio)
class ClaseServicioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')


@admin.register(ConfiguracionClase)
class ConfiguracionClaseAdmin(admin.ModelAdmin):
    list_display = ('aeronave', 'clase', 'cantidad_asientos')
    list_filter = ('clase',)


@admin.register(Asiento)
class AsientoAdmin(admin.ModelAdmin):
    list_display = ('aeronave', 'fila', 'letra', 'clase', 'junto_ventana', 'junto_pasillo')
    list_filter = ('aeronave', 'clase')
    ordering = ('aeronave', 'fila', 'letra')


# ============================================================
# BLOQUE 3 — ITINERARIOS Y VUELOS
# ============================================================

@admin.register(PeriodoItinerario)
class PeriodoItinerarioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'fecha_inicio', 'fecha_fin')


@admin.register(Itinerario)
class ItinerarioAdmin(admin.ModelAdmin):
    list_display = ('origen', 'destino', 'hora_salida', 'hora_llegada', 'duracion_minutos', 'periodo')
    list_filter = ('periodo', 'origen', 'destino')
    search_fields = ('origen__codigo_iata', 'destino__codigo_iata')


@admin.register(Vuelo)
class VueloAdmin(admin.ModelAdmin):
    list_display = ('numero_vuelo', 'itinerario', 'aeronave', 'fecha_salida', 'fecha_llegada', 'estado')
    list_filter = ('estado', 'fecha_salida', 'aeronave')
    search_fields = ('numero_vuelo',)
    ordering = ('fecha_salida',)


# ============================================================
# BLOQUE 4 — TARIFAS Y EQUIPAJE
# ============================================================

@admin.register(TipoEquipaje)
class TipoEquipajeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')


@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display = ('vuelo', 'clase', 'precio', 'moneda', 'seleccion_asiento_incluida', 'disponible', 'fecha_actualizacion')
    list_filter = ('clase', 'disponible', 'moneda')
    search_fields = ('vuelo__numero_vuelo',)


@admin.register(PoliticaEquipaje)
class PoliticaEquipajeAdmin(admin.ModelAdmin):
    list_display = ('tarifa', 'tipo_equipaje', 'cantidad_maxima', 'peso_maximo_kg')


# ============================================================
# BLOQUE 5 — CLIENTES, PASAJEROS Y RESERVAS
# ============================================================

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'email', 'telefono', 'fecha_registro')
    search_fields = ('nombre', 'apellido', 'email')
    ordering = ('apellido', 'nombre')


@admin.register(Pasajero)
class PasajeroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'numero_pasaporte', 'nacionalidad', 'fecha_nacimiento')
    search_fields = ('nombre', 'apellido', 'numero_pasaporte')
    list_filter = ('nacionalidad',)
    ordering = ('apellido', 'nombre')


class SegmentoReservaInline(admin.TabularInline):
    model = SegmentoReserva
    extra = 1
    fields = ('vuelo', 'tarifa', 'pasajero', 'orden')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('codigo_reserva', 'cliente', 'tipo', 'estado', 'precio_total', 'moneda', 'fecha_creacion')
    list_filter = ('tipo', 'estado', 'moneda')
    search_fields = ('codigo_reserva', 'cliente__email')
    ordering = ('-fecha_creacion',)
    inlines = [SegmentoReservaInline]


@admin.register(SegmentoReserva)
class SegmentoReservaAdmin(admin.ModelAdmin):
    list_display = ('reserva', 'orden', 'vuelo', 'pasajero', 'tarifa')
    list_filter = ('vuelo__estado',)
    ordering = ('reserva', 'orden')


@admin.register(AsientoReservado)
class AsientoReservadoAdmin(admin.ModelAdmin):
    list_display = ('segmento', 'asiento', 'cargo_adicional')


@admin.register(EquipajeReserva)
class EquipajeReservaAdmin(admin.ModelAdmin):
    list_display = ('segmento', 'tipo_equipaje', 'cantidad', 'peso_kg', 'cargo_adicional')