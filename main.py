import flet as ft
import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# BASE DE DATOS LOCAL (SQLite)
# ---------------------------------------------------------
def get_db():
    conn = sqlite3.connect("enfermeria.db")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Tabla de Pacientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT,
            telefono TEXT,
            diagnostico TEXT
        )
    """)
    # Tabla de Signos Vitales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signos_vitales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            fecha TEXT,
            presion TEXT,
            temperatura TEXT,
            frecuencia_cardiaca TEXT,
            saturacion TEXT,
            notas TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    """)
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# INTERFAZ FLET
# ---------------------------------------------------------
def main(page: ft.Page):
    init_db()
    page.title = "Asistente de Enfermería"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 15

    # --- PESTAÑA 1: REGISTRO DE PACIENTES ---
    txt_nombre = ft.TextField(label="Nombre del Paciente", icon=ft.Icons.PERSON)
    txt_direccion = ft.TextField(label="Dirección / Ubicación", icon=ft.Icons.LOCATION_ON)
    txt_telefono = ft.TextField(label="Teléfono / WhatsApp", icon=ft.Icons.PHONE, keyboard_type=ft.KeyboardType.PHONE)
    txt_diagnostico = ft.TextField(label="Diagnóstico / Notas", icon=ft.Icons.MEDICAL_SERVICES, multiline=True)
    list_pacientes = ft.ListView(expand=True, spacing=10)

    def cargar_pacientes():
        list_pacientes.controls.clear()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, direccion, telefono, diagnostico FROM pacientes ORDER BY id DESC")
        pacientes = cursor.fetchall()
        conn.close()

        for p in pacientes:
            p_id, nom, dir_, tel, diag = p
            list_pacientes.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text(f"👤 {nom}", weight=ft.FontWeight.BOLD, size=16),
                            ft.Text(f"📍 {dir_}" if dir_ else "📍 Sin dirección"),
                            ft.Text(f"📞 {tel}" if tel else "📞 Sin teléfono"),
                            ft.Text(f"📋 Diagnóstico: {diag}" if diag else ""),
                        ])
                    )
                )
            )
        page.update()

    def guardar_paciente(e):
        if not txt_nombre.value:
            page.snack_bar = ft.SnackBar(ft.Text("Por favor ingresá al menos el nombre del paciente."))
            page.snack_bar.open = True
            page.update()
            return

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pacientes (nombre, direccion, telefono, diagnostico) VALUES (?, ?, ?, ?)",
            (txt_nombre.value, txt_direccion.value, txt_telefono.value, txt_diagnostico.value)
        )
        conn.commit()
        conn.close()

        txt_nombre.value = ""
        txt_direccion.value = ""
        txt_telefono.value = ""
        txt_diagnostico.value = ""
        
        cargar_pacientes()
        actualizar_dropdown_pacientes()
        
        page.snack_bar = ft.SnackBar(ft.Text("✅ Paciente registrado con éxito"))
        page.snack_bar.open = True
        page.update()

    btn_guardar_p = ft.ElevatedButton("Guardar Paciente", icon=ft.Icons.SAVE, on_click=guardar_paciente)

    view_pacientes = ft.Column([
        ft.Text("Nuevo Paciente", size=18, weight=ft.FontWeight.BOLD),
        txt_nombre,
        txt_direccion,
        txt_telefono,
        txt_diagnostico,
        btn_guardar_p,
        ft.Divider(),
        ft.Text("Pacientes Registrados", size=18, weight=ft.FontWeight.BOLD),
        list_pacientes
    ], expand=True)

    # --- PESTAÑA 2: SIGNOS VITALES ---
    dd_paciente = ft.Dropdown(label="Seleccionar Paciente")
    txt_presion = ft.TextField(label="Presión Arterial (ej. 120/80)", icon=ft.Icons.MONITOR_HEART)
    txt_temp = ft.TextField(label="Temperatura (°C)", icon=ft.Icons.THERMOSTAT, keyboard_type=ft.KeyboardType.NUMBER)
    txt_fc = ft.TextField(label="Frecuencia Cardíaca (BPM)", icon=ft.Icons.FAVORITE, keyboard_type=ft.KeyboardType.NUMBER)
    txt_sato2 = ft.TextField(label="Saturación O2 (%)", icon=ft.Icons.AIR, keyboard_type=ft.KeyboardType.NUMBER)
    txt_nota_vital = ft.TextField(label="Notas de la visita", multiline=True)
    list_historico = ft.ListView(expand=True, spacing=10)

    def actualizar_dropdown_pacientes():
        dd_paciente.options.clear()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM pacientes ORDER BY nombre ASC")
        for p_id, nom in cursor.fetchall():
            dd_paciente.options.append(ft.dropdown.Option(key=str(p_id), text=nom))
        conn.close()
        page.update()

    def guardar_signos(e):
        if not dd_paciente.value:
            page.snack_bar = ft.SnackBar(ft.Text("Seleccioná un paciente de la lista."))
            page.snack_bar.open = True
            page.update()
            return

        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signos_vitales (paciente_id, fecha, presion, temperatura, frecuencia_cardiaca, saturacion, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (dd_paciente.value, fecha_actual, txt_presion.value, txt_temp.value, txt_fc.value, txt_sato2.value, txt_nota_vital.value))
        conn.commit()
        conn.close()

        txt_presion.value = ""
        txt_temp.value = ""
        txt_fc.value = ""
        txt_sato2.value = ""
        txt_nota_vital.value = ""

        cargar_historico()

        page.snack_bar = ft.SnackBar(ft.Text("✅ Signos vitales guardados"))
        page.snack_bar.open = True
        page.update()

    def cargar_historico():
        list_historico.controls.clear()
        if not dd_paciente.value:
            return
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fecha, presion, temperatura, frecuencia_cardiaca, saturacion, notas 
            FROM signos_vitales 
            WHERE paciente_id = ? 
            ORDER BY id DESC
        """, (dd_paciente.value,))
        
        registros = cursor.fetchall()
        conn.close()

        for r in registros:
            f, p, t, fc, sat, n = r
            list_historico.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text(f"📅 {f}", weight=ft.FontWeight.BOLD),
                            ft.Text(f"🩸 P.A: {p or 'N/A'} | 🌡️ Temp: {t or 'N/A'} °C"),
                            ft.Text(f"💓 F.C: {fc or 'N/A'} BPM | 🫁 SatO2: {sat or 'N/A'} %"),
                            ft.Text(f"📝 Nota: {n}" if n else "")
                        ])
                    )
                )
            )
        page.update()

    dd_paciente.on_change = lambda e: cargar_historico()
    btn_guardar_v = ft.ElevatedButton("Registrar Control", icon=ft.Icons.CHECK, on_click=guardar_signos)

    view_vitales = ft.Column([
        ft.Text("Control de Visita", size=18, weight=ft.FontWeight.BOLD),
        dd_paciente,
        txt_presion,
        txt_temp,
        txt_fc,
        txt_sato2,
        txt_nota_vital,
        btn_guardar_v,
        ft.Divider(),
        ft.Text("Historial del Paciente", size=18, weight=ft.FontWeight.BOLD),
        list_historico
    ], expand=True)

    # --- NAVEGACIÓN MÓVIL NATIVA (NavigationBar) ---
    content_area = ft.Container(content=view_pacientes, expand=True)

    def cambiar_pantalla(e):
        if e.control.selected_index == 0:
            content_area.content = view_pacientes
        else:
            content_area.content = view_vitales
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=cambiar_pantalla,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.PEOPLE, label="Pacientes"),
            ft.NavigationBarDestination(icon=ft.Icons.FAVORITE, label="Signos Vitales"),
        ]
    )

    page.add(content_area)
    cargar_pacientes()
    actualizar_dropdown_pacientes()

ft.app(target=main)