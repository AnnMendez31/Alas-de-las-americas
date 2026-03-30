from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import ProtectedError
from django.db import transaction
import random
from django.urls import reverse
import string
from .models import (
    Aeropuerto,
    Vuelo,
    Tarifa,
    Asiento,
    AsientoReservado,
    Reserva,
    SegmentoReserva,
    Pasajero,
    Cliente,
    EquipajeReserva,
    TipoEquipaje,
    Pais,
    Ciudad,
    Itinerario,
    Aeronave,
    PeriodoItinerario,
    ConfiguracionClase,
)
from .forms import (
    PasajeroForm,
    PaisForm,
    CiudadForm,
    ItinerarioForm,
    BusquedaVueloForm,
    PasajeroReservaForm,
    AeropuertoForm,
    VueloForm,
    TipoEquipajeForm,
    TarifaForm,
    AeronaveForm,
    ConfiguracionFormSet,
    EscalaForm,
    EscalaFormSet,
    PoliticaEquipajeFormSet,
)

from django.forms import inlineformset_factory
import json


def construir_url_pasos(sesion):
    if not sesion:
        return json.dumps(["", "", "", ""])

    urls = ["", "", "", ""]

    # Paso 1
    urls[0] = reverse("buscar_vuelos")

    selecciones = sesion.get("selecciones")
    tipo = sesion.get("tipo", "IDA")

    if selecciones:
        try:
            primera = selecciones[0]
            vuelo0 = Vuelo.objects.select_related(
                "itinerario__origen", "itinerario__destino"
            ).get(pk=primera["vuelo_id"])

            origen = vuelo0.itinerario.origen.id
            destino = vuelo0.itinerario.destino.id
            fecha = vuelo0.fecha_salida.strftime("%Y-%m-%d")
            pax = sesion.get("pasajeros", 1)

            params = f"tipo={tipo}&origen={origen}&destino={destino}&fecha={fecha}&pasajeros={pax}"

            if tipo == "IDA_VUELTA" and len(selecciones) > 1:
                vuelo1 = Vuelo.objects.get(pk=selecciones[1]["vuelo_id"])
                params += f"&fecha_regreso={vuelo1.fecha_salida.strftime('%Y-%m-%d')}"

            # Paso 2
            urls[1] = f"{reverse('resultados_vuelo')}?{params}"

            urls[2] = reverse("datos_pasajeros")

        except Exception:
            pass

    return json.dumps(urls)


def index(request):
    # Lógica para agrupar destinos por país (para el footer del dashboard)
    paises_con_ciudades = Pais.objects.prefetch_related("ciudades").all()
    destinos_dict = {}
    for p in paises_con_ciudades:
        destinos_dict[p.nombre] = [c.nombre for c in p.ciudades.all()]

    context = {
        "total_vuelos": Vuelo.objects.filter(estado="PROGRAMADO").count(),
        "total_reservas": Reserva.objects.count(),
        "total_pasajeros": Pasajero.objects.count(),
        "total_aeronaves": Aeronave.objects.filter(activa=True).count(),
        "ultimas_reservas": Reserva.objects.select_related("cliente").order_by(
            "-fecha_creacion"
        )[:8],
        "proximos_vuelos": Vuelo.objects.select_related(
            "itinerario__origen", "itinerario__destino"
        )
        .filter(estado="PROGRAMADO")
        .order_by("fecha_salida")[:5],
        # Enviar el diccionario de destinos al HTML
        "destinos_por_region": destinos_dict,
    }
    return render(request, "app/index.html", context)


# 1. LISTAR (Read)

def lista_pasajeros(request):
    pasajeros = Pasajero.objects.all()
    return render(request, "app/lista.html", {"pasajeros": pasajeros})


# 2. CREAR (Create)
def crear_pasajero(request):
    if request.method == "POST":
        form = PasajeroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_pasajeros")
    else:
        form = PasajeroForm()
    return render(
        request, "app/formulario.html", {"form": form,
                                         "titulo": "Registrar Pasajero"}
    )


# 3. EDITAR (Update)
def editar_pasajero(request, pk):
    pasajero = get_object_or_404(Pasajero, pk=pk)
    if request.method == "POST":
        form = PasajeroForm(request.POST, instance=pasajero)
        if form.is_valid():
            form.save()
            return redirect("lista_pasajeros")
    else:
        form = PasajeroForm(instance=pasajero)
    return render(
        request, "app/formulario.html", {"form": form,
                                         "titulo": "Editar Pasajero"}
    )


# 4. ELIMINAR (Delete)
def eliminar_pasajero(request, pk):
    pasajero = get_object_or_404(Pasajero, pk=pk)
    if request.method == "POST":
        pasajero.delete()
        return redirect("lista_pasajeros")
    return render(request, "app/confirmar_eliminar.html", {"pasajero": pasajero})


def panel_configuracion(request):
    context = {
        "paises": Pais.objects.all(),
        "ciudades": Ciudad.objects.select_related("pais").all(),
        "aeropuertos": Aeropuerto.objects.select_related("ciudad").all(),
        "aeronaves": Aeronave.objects.all(),
    }
    return render(request, "app/admin/admin_panel.html", context)


def panel_pais_ciudades_aeropuertos(request):
    context = {
        "paises": Pais.objects.all(),
        "ciudades": Ciudad.objects.select_related("pais").all(),
        "aeropuertos": Aeropuerto.objects.select_related("ciudad").all(),
        "aeronaves": Aeronave.objects.all(),
    }
    return render(request, "app/admin/lista_p_c_a.html", context)


# --- VISTAS PARA PAÍSES ---
def crear_pais(request):
    if request.method == "POST":
        form = PaisForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("panel_pais_ciudades_aeropuertos")
    else:
        form = PaisForm()
    # Usamos el nuevo template genérico
    return render(
        request,
        "app/admin/form_admin.html",
        {"form": form, "titulo": "Agregar Nuevo País"},
    )


# --- VISTAS PARA CIUDADES ---
def crear_ciudad(request):
    if request.method == "POST":
        form = CiudadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("panel_pais_ciudades_aeropuertos")
    else:
        form = CiudadForm()
    # Usamos el nuevo template genérico
    return render(
        request,
        "app/admin/form_admin.html",
        {"form": form, "titulo": "Agregar Nueva Ciudad"},
    )


# --- VISTAS PARA PAÍSES (Update/Delete) ---
def editar_pais(request, pk):
    pais = get_object_or_404(Pais, pk=pk)
    if request.method == "POST":
        form = PaisForm(request.POST, instance=pais)
        if form.is_valid():
            form.save()
            return redirect("panel_pais_ciudades_aeropuertos")
    else:
        form = PaisForm(instance=pais)
    return render(
        request, "app/admin/form_admin.html", {
            "form": form, "titulo": "Editar País"}
    )


def eliminar_pais(request, pk):
    pais = get_object_or_404(Pais, pk=pk)
    destino = "panel_pais_ciudades_aeropuertos"

    if request.method == "POST":
        pais.delete()
        return redirect(destino)

    return render(
        request,
        "app/admin/confirmar_eliminar_admin.html",
        {"objeto": pais, "tipo": "País", "url_cancelar": destino},
    )


# --- VISTAS PARA CIUDADES (Update/Delete) ---
def editar_ciudad(request, pk):
    ciudad = get_object_or_404(Ciudad, pk=pk)
    if request.method == "POST":
        form = CiudadForm(request.POST, instance=ciudad)
        if form.is_valid():
            form.save()
            return redirect("panel_pais_ciudades_aeropuertos")
    else:
        form = CiudadForm(instance=ciudad)
    return render(
        request, "app/admin/form_admin.html", {
            "form": form, "titulo": "Editar Ciudad"}
    )


def eliminar_ciudad(request, pk):
    ciudad = get_object_or_404(Ciudad, pk=pk)

    if request.method == "POST":
        try:
            ciudad.delete()
            messages.success(
                request, f"La ciudad {ciudad.nombre} fue eliminada.")
            return redirect(
                "panel_pais_ciudades_aeropuertos"
            )  # Cambia por tu ruta real
        except ProtectedError as e:
            # Obtenemos los nombres de los objetos que bloquean el borrado
            aeropuertos_relacionados = [str(obj)
                                        for obj in e.protected_objects]
            error_msg = (
                f"No se puede eliminar '{ciudad}'. "
                f"Está vinculada a: {', '.join(aeropuertos_relacionados)}."
            )
            messages.error(request, error_msg)
            return redirect("panel_pais_ciudades_aeropuertos")

    return render(
        request,
        "app/admin/confirmar_eliminar_admin.html",
        {
            "object": ciudad,
            "tipo": "Ciudad",
            "url_cancelar": "panel_pais_ciudades_aeropuertos",
        },
    )


# --- VISTAS PARA AEROPUERTOS (Create/Update/Delete) ---


def crear_aeropuerto(request):
    if request.method == "POST":
        form = AeropuertoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_aeronaves")
    else:
        form = AeropuertoForm()
    return render(
        request,
        "app/admin/form_admin.html",
        {"form": form, "titulo": "Agregar Nuevo Aeropuerto"},
    )


def editar_aeropuerto(request, pk):
    aeropuerto = get_object_or_404(Aeropuerto, pk=pk)
    if request.method == "POST":
        form = AeropuertoForm(request.POST, instance=aeropuerto)
        if form.is_valid():
            form.save()
            return redirect("lista_aeronaves")
    else:
        form = AeropuertoForm(instance=aeropuerto)
    return render(
        request,
        "app/admin/form_admin.html",
        {"form": form, "titulo": "Editar Aeropuerto"},
    )


def eliminar_aeropuerto(request, pk):
    aeropuerto = get_object_or_404(Aeropuerto, pk=pk)
    destino = "lista_aeronaves"

    if request.method == "POST":
        try:
            aeropuerto.delete()
            messages.success(
                request, f"El aeropuerto {aeropuerto.nombre} fue eliminado."
            )
            return redirect(destino)
        except ProtectedError as e:
            # Obtenemos los nombres de los objetos que bloquean el borrado
            itinerarios_relacionados = [str(obj)
                                        for obj in e.protected_objects]
            error_msg = (
                f"No se puede eliminar '{aeropuerto}'. "
                f"Está vinculado a: {', '.join(itinerarios_relacionados)}."
            )
            messages.error(request, error_msg)
            return redirect(destino)

    return render(
        request,
        "app/admin/confirmar_eliminar_admin.html",
        {
            "object": aeropuerto,
            "tipo": "Aeropuerto",
            "url_cancelar": "panel_pais_ciudades_aeropuertos",
        },
    )


def lista_itinerarios(request):
    itinerarios = Itinerario.objects.select_related(
        "periodo", "origen__ciudad", "destino__ciudad",
        "origen__ciudad__pais"
    ).prefetch_related(
        "escalas__aeropuerto_escala"
    ).all()

    return render(
        request, "app/admin/lista_itinerarios.html", {
            "itinerarios": itinerarios
        }
    )


def crear_itinerario(request):
    if request.method == "POST":
        form = ItinerarioForm(request.POST)
        formset = EscalaFormSet(request.POST)  # Agregar formset

        if form.is_valid() and formset.is_valid():  # Validar ambos
            itinerario = form.save()
            formset.instance = itinerario
            formset.save()
            return redirect("lista_itinerarios")
    else:
        form = ItinerarioForm()
        formset = EscalaFormSet()  # Formset vacío

    return render(
        request,
        "app/admin/form_admin.html",
        {
            "form": form,
            "formset": formset,
            "titulo": "Programar Nuevo Itinerario",
            "url_cancelar": "lista_itinerarios",
        },
    )


def editar_itinerario(request, pk):
    itinerario = get_object_or_404(Itinerario, pk=pk)

    if request.method == "POST":
        form = ItinerarioForm(request.POST, instance=itinerario)
        formset = EscalaFormSet(request.POST, instance=itinerario)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("lista_itinerarios")
    else:
        form = ItinerarioForm(instance=itinerario)
        formset = EscalaFormSet(instance=itinerario)

    return render(
        request,
        "app/admin/form_admin.html",
        {
            "form": form,
            "formset": formset,
            "titulo": "Editar Itinerario",
            "url_cancelar": "lista_itinerarios",
        },
    )


def eliminar_itinerario(request, pk):
    itinerario = get_object_or_404(Itinerario, pk=pk)
    # Definimos el destino una sola vez para evitar errores
    destino = "lista_itinerarios"

    if request.method == "POST":
        itinerario.delete()
        return redirect(destino)

    return render(
        request,
        "app/admin/confirmar_eliminar_admin.html",
        {
            "objeto": itinerario,
            "tipo": "Itinerario",
            "url_cancelar": destino,  # Pasamos el destino al botón "No, mantener"
        },
    )


# ============================================================
# VISTAS PARA VUELOS
# ============================================================


def lista_vuelos(request):
    vuelos = Vuelo.objects.select_related(
        "itinerario__periodo",
        "itinerario__origen__ciudad",
        "itinerario__destino__ciudad",
        "itinerario__origen__ciudad__pais",
    ).all()
    return render(request, "app/admin/lista_vuelos.html", {"vuelos": vuelos})


def detalle_vuelo(request, pk):
    vuelo = get_object_or_404(Vuelo, pk=pk)

    # Traer todos los segmentos asociados a este vuelo
    segmentos = (
        SegmentoReserva.objects
        .filter(vuelo=vuelo)
        .select_related(
            "pasajero",
            "tarifa",
            "reserva"
        )
        .prefetch_related("asiento_reservado")
        .order_by("orden")
    )

    data_pasajeros = []

    for seg in segmentos:
        asiento_res = getattr(seg, "asiento_reservado", None)

        data_pasajeros.append({
            "pasajero": seg.pasajero,
            "reserva": seg.reserva,
            "tarifa": seg.tarifa,
            "orden": seg.orden,
            "asiento": asiento_res.asiento if asiento_res else None,
            "cargo_asiento": asiento_res.cargo_adicional if asiento_res else 0,
        })

    context = {
        "vuelo": vuelo,
        "data_pasajeros": data_pasajeros,
        "total_pasajeros": len(data_pasajeros),
    }

    return render(request, "app/admin/detalle_vuelo.html", context)


def crear_vuelo(request):
    if request.method == "POST":
        form = VueloForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_vuelos")
    else:
        form = VueloForm()
    return render(
        request,
        "app/admin/form_admin.html",
        {
            "form": form,
            "titulo": "Programar Nuevo Vuelo",
            "url_cancelar": "lista_vuelos",
        },
    )


def editar_vuelo(request, pk):
    vuelo = get_object_or_404(Vuelo, pk=pk)
    if request.method == "POST":
        form = VueloForm(request.POST, instance=vuelo)
        if form.is_valid():
            form.save()
            # REDIRECCIÓN CORRECTA TRAS GUARDAR
            return redirect("lista_vuelos")
    else:
        form = VueloForm(instance=vuelo)

    return render(
        request,
        "app/admin/form_admin.html",
        {
            "form": form,
            "titulo": "Editar Vuelo",
            "url_cancelar": "lista_vuelos",  # Le decimos al template a dónde volver
        },
    )


def eliminar_vuelo(request, pk):
    vuelo = get_object_or_404(Vuelo, pk=pk)
    # Definimos el destino una sola vez para evitar errores
    destino = "lista_vuelos"

    if request.method == "POST":
        vuelo.delete()
        return redirect(destino)

    return render(
        request,
        "app/admin/confirmar_eliminar_admin.html",
        {
            "objeto": vuelo,
            "tipo": "Vuelo",
            "url_cancelar": destino,  # Pasamos el destino al botón "No, mantener"
        },
    )


# ============================================================
# VISTAS PARA AERONAVES
# ============================================================

def lista_aeronaves(request):
    # Traemos las aeronaves con su modelo y sus clases configuradas
    aeronaves = (
        Aeronave.objects.select_related("modelo")
        .prefetch_related("configuraciones__clase")
        .all()
    )
    return render(request, "app/admin/lista_aeronaves.html", {"aeronaves": aeronaves})


def gestionar_aeronave(request, pk=None):
    """Crea o edita una aeronave y sus clases al mismo tiempo"""
    aeronave = get_object_or_404(Aeronave, pk=pk) if pk else None

    if request.method == "POST":
        form = AeronaveForm(request.POST, instance=aeronave)
        formset = ConfiguracionFormSet(request.POST, instance=aeronave)

        if form.is_valid() and formset.is_valid():
            nueva_aeronave = form.save()
            formset.instance = nueva_aeronave
            formset.save()
            return redirect("lista_aeronaves")
    else:
        form = AeronaveForm(instance=aeronave)
        formset = ConfiguracionFormSet(instance=aeronave)

    return render(
        request,
        "app/admin/form_admin.html",
        {
            "form": form,
            "formset": formset,
            "titulo": "Editar Aeronave" if pk else "Registrar Nueva Aeronave",
            "url_cancelar": "lista_aeronaves",
        },
    )


def eliminar_aeronave(request, pk):
    aeronave = get_object_or_404(Aeronave, pk=pk)
    destino = "lista_aeronaves"

    if request.method == "POST":
        try:
            aeronave.delete()
            messages.success(request, f"Aeronave eliminada correctamente.")
            return redirect(destino)
        except ProtectedError as e:
            # Si tiene vuelos asignados, no se puede borrar
            vuelos_relacionados = [str(obj) for obj in e.protected_objects]
            error_msg = (
                f"No se puede eliminar la aeronave '{aeronave}'. "
                f"Está asignada a: {', '.join(vuelos_relacionados)}."
            )
            messages.error(request, error_msg)
            return redirect(destino)

    return render(
        request,
        "app/admin/confirmar_eliminar_admin.html",
        {"objeto": aeronave, "tipo": "Aeronave", "url_cancelar": destino},
    )

# ACTUALIZAR LA VISTA gestionar_tarifas() EN views.py


def gestionar_tarifas(request, pk):
    vuelo = get_object_or_404(Vuelo, pk=pk)

    clases_avion = ConfiguracionClase.objects.filter(aeronave=vuelo.aeronave)
    cantidad_clases = clases_avion.count()
    tarifas_existentes = Tarifa.objects.filter(vuelo=vuelo).count()
    campos_extra = cantidad_clases if tarifas_existentes == 0 else 0

    TarifaFormSet = inlineformset_factory(
        Vuelo, Tarifa, form=TarifaForm, extra=campos_extra, can_delete=True
    )

    if request.method == "POST":
        formset = TarifaFormSet(request.POST, instance=vuelo)

        if formset.is_valid():
            tarifas_guardadas = formset.save()

            # Guardar políticas de equipaje por cada tarifa existente
            politica_errores = False
            politica_formsets = {}

            for tarifa in Tarifa.objects.filter(vuelo=vuelo):
                pf = PoliticaEquipajeFormSet(
                    request.POST,
                    instance=tarifa,
                    prefix=f"politica_{tarifa.id}"
                )

                if pf.is_valid():
                    # ========== NUEVA LÓGICA: Guardar solo formularios con datos ==========
                    for form in pf:
                        # Si tiene DELETE marcado, ejecutar eliminación
                        if form.cleaned_data.get('DELETE') and form.instance.pk:
                            form.instance.delete()
                        # Si tiene tipo_equipaje (es decir, está completo), guardar
                        elif form.cleaned_data.get('tipo_equipaje'):
                            form.save()
                        # Si está completamente vacío, ignorar (no hacer nada)
                else:
                    # Hay errores de validación - solo reportar si son reales
                    politica_errores = True
                    politica_formsets[tarifa.id] = pf

            if not politica_errores:
                messages.success(
                    request, "✅ Tarifas y políticas de equipaje guardadas correctamente.")
                return redirect("lista_vuelos")
            else:
                messages.error(
                    request, "⚠️ Completa todos los campos de las políticas de equipaje (tipo, cantidad y peso).")
        # Si el formset de tarifas no es válido, cae al render de abajo

    else:
        initial_data = []
        if tarifas_existentes == 0:
            for conf in clases_avion:
                initial_data.append({"clase": conf.clase, "moneda": "USD"})

        formset = TarifaFormSet(instance=vuelo, initial=initial_data)

    # Construir formsets de políticas para cada tarifa ya guardada
    tarifas_con_politicas = []
    for tarifa in Tarifa.objects.filter(vuelo=vuelo).select_related('clase'):
        # CAMBIO: extra=0 para no mostrar campos vacíos
        pf = PoliticaEquipajeFormSet(
            instance=tarifa,
            prefix=f"politica_{tarifa.id}"
        )
        tarifas_con_politicas.append({
            "tarifa":          tarifa,
            "politica_formset": pf,
        })

    # Obtener lista de tipos de equipaje para el JavaScript
    tipos_equipaje = TipoEquipaje.objects.all().order_by('nombre')

    return render(request, "app/admin/gestionar_tarifas.html", {
        "vuelo":                 vuelo,
        "formset":               formset,
        "tarifas_con_politicas": tarifas_con_politicas,
        "tipos_equipaje":        tipos_equipaje,  # ← NUEVO
        "titulo":                f"Tarifas — {vuelo.numero_vuelo}",
        "url_cancelar":          "lista_vuelos",
    })

# Vistas para TipoEquipaje


def lista_tipos_equipaje(request):
    tipos = TipoEquipaje.objects.all()
    return render(request, "app/admin/lista_tipos_equipaje.html", {"tipos": tipos})


def crear_tipo_equipaje(request):
    if request.method == "POST":
        form = TipoEquipajeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_tipos_equipaje")
    else:
        form = TipoEquipajeForm()
    return render(request, "app/admin/form_admin.html", {
        "form": form,
        "titulo": "Agregar Tipo de Equipaje",
        "url_cancelar": "lista_tipos_equipaje",
    })


def editar_tipo_equipaje(request, pk):
    tipo = get_object_or_404(TipoEquipaje, pk=pk)
    if request.method == "POST":
        form = TipoEquipajeForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect("lista_tipos_equipaje")
    else:
        form = TipoEquipajeForm(instance=tipo)
    return render(request, "app/admin/form_admin.html", {
        "form": form,
        "titulo": "Editar Tipo de Equipaje",
        "url_cancelar": "lista_tipos_equipaje",
    })


def eliminar_tipo_equipaje(request, pk):
    tipo = get_object_or_404(TipoEquipaje, pk=pk)
    if request.method == "POST":
        try:
            tipo.delete()
            messages.success(request, "Tipo de equipaje eliminado.")
        except ProtectedError:
            messages.error(
                request, "No se puede eliminar, está en uso en tarifas.")
        return redirect("lista_tipos_equipaje")
    return render(request, "app/admin/confirmar_eliminar_admin.html", {
        "objeto": tipo, "tipo": "Tipo de Equipaje", "url_cancelar": "lista_tipos_equipaje"
    })

# ============================================================
# PASO 1 — Buscar vuelo
# ============================================================


def buscar_vuelo(request):
    form = BusquedaVueloForm(request.GET or None)

    aeropuertos = Aeropuerto.objects.select_related(
        'ciudad__pais').order_by('ciudad__pais__nombre', 'nombre')
    aeropuertos_opts = "".join(
        f'<option value="{a.id}">{a.codigo_iata} - {a.ciudad.nombre}</option>'
        for a in aeropuertos
    )
    destinos_default = ["Miami", "New York",
                        "Bogotá", "Lima", "São Paulo", "Buenos Aires"]

    if form.is_valid():
        tipo = form.cleaned_data['tipo_viaje']
        origen_id = form.cleaned_data['origen'].id
        destino_id = form.cleaned_data['destino'].id
        fecha = form.cleaned_data['fecha'].strftime('%Y-%m-%d')
        pasajeros = form.cleaned_data['num_pasajeros']

        # ← 'tipo' (no 'tipo_viaje') para que resultados_vuelo lo lea con GET.get('tipo')
        params = f"tipo={tipo}&origen={origen_id}&destino={destino_id}&fecha={fecha}&pasajeros={pasajeros}"

        if tipo == 'IDA_VUELTA':
            fecha_regreso_val = form.cleaned_data.get('fecha_regreso')
            if fecha_regreso_val:
                params += f"&fecha_regreso={fecha_regreso_val.strftime('%Y-%m-%d')}"
            else:
                messages.error(request, "Debes indicar la fecha de regreso.")
                return render(request, 'app/cliente/buscar_vuelo.html', {
                    'form': form,
                    'aeropuertos_opts': aeropuertos_opts,
                    'destinos_default': destinos_default,
                })

        elif tipo == 'MULTIDESTINO':
            idx = 1
            while request.GET.get(f'tramo_{idx}_origen'):
                o = request.GET.get(f'tramo_{idx}_origen')
                d = request.GET.get(f'tramo_{idx}_destino')
                fec = request.GET.get(f'tramo_{idx}_fecha')
                params += f"&tramo_{idx}_origen={o}&tramo_{idx}_destino={d}&tramo_{idx}_fecha={fec}"
                idx += 1

        return redirect(f"{reverse('resultados_vuelo')}?{params}")

    return render(request, 'app/cliente/buscar_vuelo.html', {
        'form':             form,
        'aeropuertos_opts': aeropuertos_opts,
        'destinos_default': destinos_default,
    })


# ACTUALIZAR LA VISTA resultados_vuelo EN views.py

# Reemplaza la función resultados_vuelo actual con esta versión optimizada:

def resultados_vuelo(request):
    # El tipo siempre viene en GET (tanto en la carga inicial como en el POST,
    # porque el form de selección lleva tipo como hidden)
    tipo = request.GET.get('tipo', 'IDA')
    pasajeros = int(request.GET.get('pasajeros', 1))

    origen_id = request.GET.get('origen')
    destino_id = request.GET.get('destino')
    fecha = request.GET.get('fecha')

    # Construir tramos
    tramos_params = []

    if origen_id and destino_id and fecha:
        tramos_params.append(
            {'origen_id': origen_id, 'destino_id': destino_id, 'fecha': fecha})

    if tipo == 'IDA_VUELTA':
        fecha_regreso = request.GET.get('fecha_regreso')
        if fecha_regreso:
            # Tramo de regreso: origen y destino invertidos
            tramos_params.append({
                'origen_id':  destino_id,
                'destino_id': origen_id,
                'fecha':      fecha_regreso,
            })

    elif tipo == 'MULTIDESTINO':
        idx = 1
        while request.GET.get(f'tramo_{idx}_origen'):
            tramos_params.append({
                'origen_id':  request.GET.get(f'tramo_{idx}_origen'),
                'destino_id': request.GET.get(f'tramo_{idx}_destino'),
                'fecha':      request.GET.get(f'tramo_{idx}_fecha'),
            })
            idx += 1

    # Resolver vuelos para cada tramo
    # OPTIMIZADO: prefetch_related para escalas
    tramos_resultados = []
    for t in tramos_params:
        origen = get_object_or_404(Aeropuerto, pk=t['origen_id'])
        destino = get_object_or_404(Aeropuerto, pk=t['destino_id'])
        vuelos = (
            Vuelo.objects
            .select_related(
                'itinerario__origen',
                'itinerario__destino',
                'itinerario__periodo',
                'aeronave__modelo'
            )
            .prefetch_related(
                'tarifas__clase',
                'tarifas__politicas_equipaje__tipo_equipaje',
                'itinerario__escalas__aeropuerto_escala'  # ← IMPORTANTE: cargar escalas
            )
            .filter(
                itinerario__origen=origen,
                itinerario__destino=destino,
                fecha_salida=t['fecha'],
                estado='PROGRAMADO',
            )
        )
        tramos_resultados.append({
            'origen':  origen,
            'destino': destino,
            'fecha':   t['fecha'],
            'vuelos':  vuelos,
        })

    # POST: el usuario eligió tarifas y hace submit
    if request.method == 'POST':
        # El tipo viene en el body del POST (hidden input en el form de resultados)
        tipo_post = request.POST.get('tipo', tipo)
        pasajeros = int(request.POST.get('pasajeros', pasajeros))
        num_tramos = int(request.POST.get('num_tramos', 1))
        selecciones = []
        valido = True

        for i in range(num_tramos):
            vuelo_id = request.POST.get(f'vuelo_id_{i}')
            tarifa_id = request.POST.get(f'tarifa_id_{i}')
            if not vuelo_id or not tarifa_id:
                messages.error(
                    request, f'Selecciona un vuelo y tarifa para el tramo {i + 1}.')
                valido = False
                break
            vuelo = get_object_or_404(Vuelo,  pk=vuelo_id)
            tarifa = get_object_or_404(Tarifa, pk=tarifa_id, vuelo=vuelo)
            selecciones.append({
                'vuelo_id':  vuelo.id,
                'tarifa_id': tarifa.id,
                'precio':    str(tarifa.precio),
            })

        if valido:
            precio_total = sum(float(s['precio']) for s in selecciones)
            request.session['reserva'] = {
                'tipo':        tipo_post,
                'pasajeros':   pasajeros,
                'selecciones': selecciones,
                'precio_total': str(precio_total),
                # Compatibilidad con vistas que aún usan vuelo_id/tarifa_id directos
                'vuelo_id':   selecciones[0]['vuelo_id'],
                'tarifa_id':  selecciones[0]['tarifa_id'],
                'precio_base': selecciones[0]['precio'],
            }
            return redirect('datos_pasajeros')

        # Si no es válido, volver a mostrar la página con los tramos ya calculados
        # (los tramos_resultados ya están construidos arriba)
    import json
    return render(request, 'app/cliente/resultados_vuelo.html', {
        'tipo':              tipo,
        'tramos_resultados': tramos_resultados,
        'pasajeros':         pasajeros,
        'num_tramos':        len(tramos_resultados),
        'origen_id':         origen_id,
        'destino_id':        destino_id,
        "pasos_lista":    ["Buscar", "Tarifa", "Pasajeros", "Confirmar"],
        "paso_actual":    2,
        "url_pasos_json": json.dumps([reverse("buscar_vuelos"), "", "", ""]),
    })


# ============================================================
# PASO 3 — Seleccionar tarifa
# Al hacer POST guarda en sesión y redirige a datos_pasajeros
# ============================================================


def seleccionar_tarifa(request, vuelo_id):
    vuelo = get_object_or_404(Vuelo, pk=vuelo_id)
    pasajeros = int(request.GET.get(
        "pasajeros", request.POST.get("pasajeros", 1)))
    tarifas = vuelo.tarifas.select_related("clase").prefetch_related(
        "politicas_equipaje__tipo_equipaje"
    ).filter(disponible=True)

    if request.method == "POST":
        tarifa_id = request.POST.get("tarifa_id")
        if not tarifa_id:
            messages.error(request, "Por favor selecciona una tarifa.")
            return redirect(f"{reverse('seleccionar_tarifa', args=[vuelo_id])}?pasajeros={pasajeros}")

        tarifa = get_object_or_404(Tarifa, pk=tarifa_id, vuelo=vuelo)

        # Guardar en sesión — la tabla django_session debe existir (migrate)
        request.session["reserva"] = {
            "vuelo_id":    vuelo.id,
            "tarifa_id":   tarifa.id,
            "pasajeros":   pasajeros,
            "precio_base": str(tarifa.precio),
        }
        return redirect("datos_pasajeros")

    return render(request, "app/cliente/seleccionar_tarifa.html", {
        "vuelo":       vuelo,
        "tarifas":     tarifas,
        "pasajeros":   pasajeros,
        "pasos_lista": ["Buscar", "Tarifa", "Pasajeros", "Confirmar"],
        "paso_actual": 2,
    })


# ============================================================
# PASO 4 — Datos de pasajeros
# ============================================================

def datos_pasajeros(request):
    sesion = request.session.get("reserva")
    if not sesion:
        messages.error(request, "La sesión expiró. Busca el vuelo de nuevo.")
        return redirect("buscar_vuelos")

    selecciones = sesion.get("selecciones", [{
        "vuelo_id":  sesion["vuelo_id"],
        "tarifa_id": sesion["tarifa_id"],
    }])
    num_pax = int(sesion["pasajeros"])

    # Construir info de tramos + asientos disponibles por tramo
    tramos_info = []
    for s in selecciones:
        v = get_object_or_404(Vuelo,  pk=s["vuelo_id"])
        t = get_object_or_404(Tarifa, pk=s["tarifa_id"])

        ocupados = AsientoReservado.objects.filter(
            segmento__vuelo=v
        ).values_list("asiento_id", flat=True)

        asientos = list(
            Asiento.objects
            .filter(aeronave=v.aeronave, clase=t.clase, estado="OPERATIVO")
            .exclude(id__in=ocupados)
            .order_by("fila", "letra")
        )
        for a in asientos:
            a.posicion = a.get_posicion_display()

        escalas = list(v.itinerario.escalas.all().order_by('orden'))

        tramos_info.append({
            "vuelo":    v,
            "tarifa":   t,
            "escalas": escalas,
            "asientos": asientos,
        })

    # Compatibilidad con template que usa vuelo/tarifa/asientos del primer tramo
    primer_vuelo = tramos_info[0]["vuelo"]
    primer_tarifa = tramos_info[0]["tarifa"]

    prefixes = [f"pax_{i}" for i in range(num_pax)]

    if request.method == "POST":
        forms_pax = [
            PasajeroReservaForm(request.POST, prefix=p, index=i)
            for i, p in enumerate(prefixes)
        ]
        if all(f.is_valid() for f in forms_pax):
            pax_data = []
            for f in forms_pax:
                cd = f.cleaned_data
                # Recoger asiento_id por tramo: asiento_id_0, asiento_id_1, ...
                asientos_por_tramo = []
                for ti in range(len(selecciones)):
                    key = f"asiento_tramo_{ti}"
                    asientos_por_tramo.append(request.POST.get(key, ""))

                pax_data.append({
                    "nombre":            cd["nombre"],
                    "apellido":          cd["apellido"],
                    "fecha_nacimiento":  cd["fecha_nacimiento"].strftime("%Y-%m-%d"),
                    "numero_pasaporte":  cd["numero_pasaporte"],
                    "nacionalidad_id":   cd["nacionalidad"].id,
                    "email":             cd.get("email", ""),
                    "telefono":          cd.get("telefono", ""),
                    # primer tramo (compatibilidad)
                    "asiento_id":        cd.get("asiento_id", ""),
                    "asientos_por_tramo": asientos_por_tramo,
                })
            request.session["reserva"]["pax_data"] = pax_data
            request.session.modified = True
            return redirect("confirmar_reserva")
        else:
            messages.error(
                request, "Por favor, corrige los errores en los datos de los pasajeros.")
    else:
        pax_guardados = sesion.get("pax_data", [])
        asientos_guardados = [
            p.get("asientos_por_tramo", [])
            for p in pax_guardados
        ]
        forms_pax = []
        for i, p in enumerate(prefixes):
            initial_data = pax_guardados[i] if i < len(pax_guardados) else {}

            forms_pax.append(
                PasajeroReservaForm(
                    prefix=p,
                    index=i,
                    initial={
                        "nombre": initial_data.get("nombre", ""),
                        "apellido": initial_data.get("apellido", ""),
                        "fecha_nacimiento": initial_data.get("fecha_nacimiento", ""),
                        "numero_pasaporte": initial_data.get("numero_pasaporte", ""),
                        "nacionalidad": initial_data.get("nacionalidad_id", ""),
                        "email": initial_data.get("email", ""),
                        "telefono": initial_data.get("telefono", ""),
                        "asiento_id": initial_data.get("asiento_id", ""),

                    }
                )
            )
    url_volver = construir_url_pasos(sesion)
    import json
    url_pasos_lista = json.loads(url_volver)
    return render(request, "app/cliente/datos_pasajeros.html", {
        "vuelo":                primer_vuelo,
        "tarifa":               primer_tarifa,
        "tramos_info":          tramos_info,
        "forms":                forms_pax,
        "asientos_disponibles": tramos_info[0]["asientos"],  # compatibilidad
        "pasos_lista":          ["Buscar", "Tarifa", "Pasajeros", "Confirmar"],
        "paso_actual":          3,
        "url_pasos_json": url_volver,
        "url_volver":     url_pasos_lista[1],  # índice 1 = paso 2 (resultados)
        "tipo":                 sesion.get("tipo", "IDA"),
        "num_tramos":           len(selecciones),
        "asientos_guardados": asientos_guardados,
    })


def confirmar_reserva(request):
    sesion = request.session.get("reserva")
    if not sesion or "pax_data" not in sesion:
        messages.error(request, "La sesión expiró. Busca el vuelo de nuevo.")
        return redirect("buscar_vuelos")

    selecciones = sesion.get("selecciones", [{
        "vuelo_id":  sesion["vuelo_id"],
        "tarifa_id": sesion["tarifa_id"],
        "precio":    sesion.get("precio_base", "0"),
    }])
    tipo = sesion.get("tipo", "IDA")
    pax_data = sesion["pax_data"]

    # Calcular precio total: suma de todos los tramos × pasajeros
    precio_por_tramo = sum(float(s.get("precio", 0)) for s in selecciones)
    precio_total = precio_por_tramo * len(pax_data)

    # Info de tramos para mostrar en la confirmación
    tramos_info = []
    for s in selecciones:
        v = get_object_or_404(Vuelo,  pk=s["vuelo_id"])
        t = get_object_or_404(Tarifa, pk=s["tarifa_id"])
        tramos_info.append({"vuelo": v, "tarifa": t})

    if request.method == "POST":
        try:
            with transaction.atomic():
                primer = pax_data[0]
                email_cliente = primer["email"] or f"noemail_{primer['numero_pasaporte']}@alas.do"
                cliente_existente = Cliente.objects.filter(
                    email=email_cliente).first()

                if cliente_existente:
                    # Si existe, actualiza el nombre y apellido con los nuevos datos
                    cliente_existente.nombre = primer["nombre"]
                    cliente_existente.apellido = primer["apellido"]
                    cliente_existente.save()
                    cliente = cliente_existente
                else:
                    # Si no existe, crear un cliente nuevo
                    cliente = Cliente.objects.create(
                        email=email_cliente,
                        nombre=primer["nombre"],
                        apellido=primer["apellido"]
                    )

                while True:
                    codigo = "AA-" + \
                        "".join(random.choices(
                            string.ascii_uppercase + string.digits, k=5))
                    if not Reserva.objects.filter(codigo_reserva=codigo).exists():
                        break

                # Tipo Django: IDA / IDA_VUELTA / MULTIDESTINO
                tipo_reserva = tipo if tipo in [
                    'IDA', 'IDA_VUELTA', 'MULTIDESTINO'] else 'IDA'

                reserva = Reserva.objects.create(
                    codigo_reserva=codigo,
                    cliente=cliente,
                    tipo=tipo_reserva,
                    estado="CONFIRMADA",
                    precio_total=precio_total,
                    moneda="USD",
                )

                orden = 1
                for tramo_idx, sel in enumerate(selecciones):
                    vuelo = get_object_or_404(Vuelo,  pk=sel["vuelo_id"])
                    tarifa = get_object_or_404(Tarifa, pk=sel["tarifa_id"])

                    for pd in pax_data:
                        pasajero, _ = Pasajero.objects.get_or_create(
                            numero_pasaporte=pd["numero_pasaporte"],
                            defaults={
                                "nombre":           pd["nombre"],
                                "apellido":         pd["apellido"],
                                "fecha_nacimiento": pd["fecha_nacimiento"],
                                "nacionalidad":     Pais.objects.get(pk=pd["nacionalidad_id"]),
                                "email":            pd.get("email", ""),
                                "telefono":         pd.get("telefono", ""),
                            },
                        )
                        segmento = SegmentoReserva.objects.create(
                            reserva=reserva,
                            vuelo=vuelo,
                            tarifa=tarifa,
                            pasajero=pasajero,
                            orden=orden,
                        )
                        orden += 1

                        # Intentar asiento específico de este tramo
                        asientos_por_tramo = pd.get("asientos_por_tramo", [])
                        if tramo_idx < len(asientos_por_tramo):
                            asiento_id = asientos_por_tramo[tramo_idx]
                        else:
                            asiento_id = pd.get("asiento_id", "")

                        if asiento_id:
                            try:
                                asiento = Asiento.objects.get(pk=asiento_id)
                                if asiento.aeronave == vuelo.aeronave:
                                    cargo = 0 if tarifa.seleccion_asiento_incluida else tarifa.cargo_seleccion_asiento
                                    AsientoReservado.objects.create(
                                        segmento=segmento,
                                        asiento=asiento,
                                        cargo_adicional=cargo,
                                    )
                            except Asiento.DoesNotExist:
                                pass

            del request.session["reserva"]
            request.session.modified = True
            return redirect("reserva_exitosa", codigo=reserva.codigo_reserva)

        except Exception as e:
            messages.error(request, f"Error al crear la reserva: {e}")
    request.session.modified = True
    return render(request, "app/cliente/confirmar_reserva.html", {
        "tramos_info":   tramos_info,
        "pax_data":      pax_data,
        "precio_total":  precio_total,
        "num_pasajeros": len(pax_data),
        "tipo":          tipo,
        "pasos_lista":   ["Buscar", "Tarifa", "Pasajeros", "Confirmar"],
        "paso_actual":   4,
        "url_pasos_json": construir_url_pasos(sesion),
    })


# ============================================================
# RESULTADO — Reserva exitosa
# ============================================================

def reserva_exitosa(request, codigo):
    reserva = get_object_or_404(
        Reserva.objects
        .select_related("cliente")
        .prefetch_related(
            "segmentos__pasajero",
            "segmentos__vuelo__itinerario__origen__ciudad",
            "segmentos__vuelo__itinerario__destino__ciudad",
            "segmentos__asiento_reservado__asiento",
            "segmentos__tarifa__clase",
        ),
        codigo_reserva=codigo,
    )
    return render(request, "app/cliente/reserva_exitosa.html", {"reserva": reserva})
