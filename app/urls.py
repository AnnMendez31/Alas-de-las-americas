
from django.urls import path
from . import views

urlpatterns = [

    # ── Página principal ──────────────────────────────────────
    path('', views.index, name='index'),

    # ── Flujo cliente (reservas) ──────────────────────────────
    path('reservas/buscar/',
         views.buscar_vuelo,       name='buscar_vuelos'),
    path('reservas/resultados/',
         views.resultados_vuelo,   name='resultados_vuelo'),
    path('reservas/vuelo/<int:vuelo_id>/tarifas/',
         views.seleccionar_tarifa, name='seleccionar_tarifa'),
    path('reservas/pasajeros/',
         views.datos_pasajeros,    name='datos_pasajeros'),
    path('reservas/confirmar/',
         views.confirmar_reserva,  name='confirmar_reserva'),
    path('reservas/exitosa/<str:codigo>/',
         views.reserva_exitosa,    name='reserva_exitosa'),

    # ── Pasajeros (admin) ─────────────────────────────────────
    path('pasajeros/',                        views.lista_pasajeros,
         name='lista_pasajeros'),
    path('pasajeros/nuevo/',
         views.crear_pasajero,     name='crear_pasajero'),
    path('pasajeros/<int:pk>/editar/',
         views.editar_pasajero,    name='editar_pasajero'),
    path('pasajeros/<int:pk>/eliminar/',
         views.eliminar_pasajero,  name='eliminar_pasajero'),

    # ── Configuración geográfica (admin) ──────────────────────
    path('configuracion/',                    views.panel_configuracion,
         name='panel_configuracion'),
    path('geo/',                              views.panel_pais_ciudades_aeropuertos,
         name='panel_pais_ciudades_aeropuertos'),

    path('paises/nuevo/',
         views.crear_pais,         name='crear_pais'),
    path('paises/<int:pk>/editar/',
         views.editar_pais,        name='editar_pais'),
    path('paises/<int:pk>/eliminar/',
         views.eliminar_pais,      name='eliminar_pais'),

    path('ciudades/nuevo/',
         views.crear_ciudad,       name='crear_ciudad'),
    path('ciudades/<int:pk>/editar/',
         views.editar_ciudad,      name='editar_ciudad'),
    path('ciudades/<int:pk>/eliminar/',
         views.eliminar_ciudad,    name='eliminar_ciudad'),

    path('aeropuertos/nuevo/',
         views.crear_aeropuerto,   name='crear_aeropuerto'),
    path('aeropuertos/<int:pk>/editar/',
         views.editar_aeropuerto,  name='editar_aeropuerto'),
    path('aeropuertos/<int:pk>/eliminar/',
         views.eliminar_aeropuerto, name='eliminar_aeropuerto'),

    # ── Itinerarios (admin) ───────────────────────────────────
    path('itinerarios/',                      views.lista_itinerarios,
         name='lista_itinerarios'),
    path('itinerarios/nuevo/',
         views.crear_itinerario,   name='crear_itinerario'),
    path('itinerarios/<int:pk>/editar/',
         views.editar_itinerario,  name='editar_itinerario'),
    path('itinerarios/<int:pk>/eliminar/',
         views.eliminar_itinerario, name='eliminar_itinerario'),

    # ── Vuelos (admin) ────────────────────────────────────────
    path('vuelos/',                           views.lista_vuelos,
         name='lista_vuelos'),
    path('vuelos/nuevo/',
         views.crear_vuelo,        name='crear_vuelo'),
    path('vuelos/<int:pk>/editar/',
         views.editar_vuelo,       name='editar_vuelo'),
    path('vuelos/<int:pk>/eliminar/',
         views.eliminar_vuelo,     name='eliminar_vuelo'),
    path('vuelos/<int:pk>/tarifas/',
         views.gestionar_tarifas,  name='gestionar_tarifas'),
    path('vuelos/<int:pk>/detalle/',
         views.detalle_vuelo,  name='detalle_vuelo'),

    # ── Aeronaves (admin) ─────────────────────────────────────
    path('aeronaves/',                        views.lista_aeronaves,
         name='lista_aeronaves'),
    path('aeronaves/nueva/',
         views.gestionar_aeronave, name='crear_aeronave'),
    path('aeronaves/<int:pk>/editar/',
         views.gestionar_aeronave, name='editar_aeronave'),
    path('aeronaves/<int:pk>/eliminar/',
         views.eliminar_aeronave,  name='eliminar_aeronave'),

    # Tipos de equipaje
    path('equipaje/', views.lista_tipos_equipaje,
         name='lista_tipos_equipaje'),
    path('equipaje/nuevo/', views.crear_tipo_equipaje,
         name='crear_tipo_equipaje'),
    path('equipaje/<int:pk>/editar/',
         views.editar_tipo_equipaje,   name='editar_tipo_equipaje'),
    path('equipaje/<int:pk>/eliminar/',
         views.eliminar_tipo_equipaje, name='eliminar_tipo_equipaje'),


]
