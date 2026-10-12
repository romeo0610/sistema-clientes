from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from supabase import create_client, Client
import numpy as np

st.title("BASE DE DATOS - SUPABASE")

# ==========================================
# CREDENCIALES DE SUPABASE
# ==========================================
# Pega aquí tus credenciales de Supabase
SUPABASE_URL = "https://pbwxafykvuoigkwdxiym.supabase.co"
SUPABASE_KEY = "sb_publishable_r0H-L94seOLClcRSInICJQ_1C9S-KWF"  

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# SISTEMA DE LOGIN (CONTROL DE ACCESO)
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.subheader("🔒 Acceso Restringido")
    st.write("Ingresa tus credenciales para entrar al sistema:")

    user_input = st.text_input("Usuario")
    pass_input = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        if user_input == "12345678" and pass_input == "123456":
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos, mi pana.")

    st.stop()


# ==========================================
# CARGAR DATOS DESDE SUPABASE
# ==========================================
try:
    response = supabase.table("registros").select("*").execute()
    resultados = response.data

    st.write("¡Conexión establecida correctamente con Supabase en la nube!")

    if not resultados:
        # Si la tabla está vacía, creamos un DataFrame vacío con las columnas base
        df = pd.DataFrame(
            columns=[
                "id",
                "Usuario",
                "Contraseña",
                "Cliente 1",
                "Cliente 2",
                "Cliente 3",
                "Cliente 4",
                "Fecha",
                "Observacion",
                "usuario completo",
                "clientes",
            ]
        )
    else:
        df = pd.DataFrame(resultados)

    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    hoy = datetime.now()
    limite = hoy + timedelta(days=3)

    # Asegurar columnas de texto si existen filas
    if "Usuario" in df.columns and "Contraseña" in df.columns:
        df["usuario completo"] = (
            "USUARIO:    " + df["Usuario"].astype(str) + "    CONTRASEÑA:    " + df["Contraseña"].astype(str)
        )
    if all(col in df.columns for col in ["Cliente 1", "Cliente 2", "Cliente 3", "Cliente 4"]):
        df["clientes"] = (
            df["Cliente 1"].astype(str)
            + ", "
            + df["Cliente 2"].astype(str)
            + ", "
            + df["Cliente 3"].astype(str)
            + ", "
            + df["Cliente 4"].astype(str)
        )

    # Asegurarnos de tener las columnas ordenadas
    columnas_ordenadas = [
        "id",
        "Usuario",
        "Contraseña",
        "Cliente 1",
        "Cliente 2",
        "Cliente 3",
        "Cliente 4",
        "usuario completo",
        "Fecha",
        "Observacion",
        "clientes",
    ]
    for col in columnas_ordenadas:
        if col not in df.columns:
            df[col] = None
    df = df[columnas_ordenadas]

    st.subheader("------------------------------------------------------------------")
    st.markdown("RESUMEN DE LA BASE:")
    st.subheader("------------------------------------------------------------------")
    col1, col2 = st.columns(2)
    Usuario_count = len(df)
    total_clientes_1 = df["Cliente 1"].count() if "Cliente 1" in df.columns else 0
    total_clientes2 = df["Cliente 2"].count() if "Cliente 2" in df.columns else 0
    total_clientes3 = df["Cliente 3"].count() if "Cliente 3" in df.columns else 0
    total_clientes4 = df["Cliente 4"].count() if "Cliente 4" in df.columns else 0

    totalclientes = (
        total_clientes_1 + total_clientes2 + total_clientes3 + total_clientes4
    )

    col1.metric("TOTAL USUARIOS:", Usuario_count)
    col2.metric("clientes en general: ", totalclientes)

    proximos_vencer = df[(df["Fecha"] >= hoy) & (df["Fecha"] <= limite)] if "Fecha" in df.columns else pd.DataFrame()
    if not proximos_vencer.empty:
        st.warning(
            f"⚠️ ¡Hay {len(proximos_vencer)} registro(s) con fecha próxima a cumplirse en los siguientes 3 días!"
        )

    busqueda = st.text_input("Buscar usuario o cliente:")

    if busqueda:
        cont_usu = df["Usuario"].astype(str).str.contains(busqueda, case=False, na=False)
        cont_cli1 = df["Cliente 1"].astype(str).str.contains(busqueda, case=False, na=False)
        cont_cli2 = df["Cliente 2"].astype(str).str.contains(busqueda, case=False, na=False)
        cont_cli3 = df["Cliente 3"].astype(str).str.contains(busqueda, case=False, na=False)
        cont_cli4 = df["Cliente 4"].astype(str).str.contains(busqueda, case=False, na=False)

        df_mostrar = df[
            cont_usu | cont_cli1 | cont_cli2 | cont_cli3 | cont_cli4
        ]
    else:
        df_mostrar = df

    st.subheader("📋 Vista General de Registros")


    def resaltar_proximos(row):
        fecha_val = row["Fecha"]
        if pd.notnull(fecha_val):
            if (
                pd.Timestamp(hoy).normalize()
                <= pd.Timestamp(fecha_val).normalize()
                <= pd.Timestamp(limite).normalize()
            ):
                return ["background-color: #4A0B00"] * len(row)
        return [""] * len(row)


    df_estilizado = df_mostrar.style.apply(resaltar_proximos, axis=1)
    st.dataframe(df_estilizado)

    st.subheader("✏️ Editor y Añadir Nuevos Registros")
    st.write(
        "Puedes modificar celdas existentes, agregar filas nuevas o eliminar filas usando el editor:"
    )

    # Se agregó num_rows="dynamic" para permitir eliminar y añadir filas directamente
    df_editado = st.data_editor(df, key="editor_tabla_registros", num_rows="dynamic")

    if st.button("Guardar cambios y nuevos registros en Supabase"):
        # Limpiar valores nulos o NaN para evitar error de JSON
        df_editado = df_editado.replace({np.nan: None})

        # Filtrar filas vacías o con 'nan' en Usuario
        df_editado = df_editado[
            df_editado["Usuario"].notna()
            & (df_editado["Usuario"].astype(str).str.strip() != "")
            & (df_editado["Usuario"].astype(str).str.lower() != "nan")
        ]

        # DETECCIÓN DE ELIMINACIONES: IDs que estaban en la base original pero ya no están en el editor
        ids_originales = set(df["id"].dropna().tolist()) if "id" in df.columns else set()
        ids_actuales = set(df_editado["id"].dropna().tolist()) if "id" in df_editado.columns else set()
        ids_a_eliminar = ids_originales - ids_actuales

        # Borrar en Supabase los registros eliminados por el usuario
        for id_borrar in ids_a_eliminar:
            supabase.table("registros").delete().eq("id", id_borrar).execute()

        for index, row in df_editado.iterrows():
            usuario_actual = str(row["Usuario"]).strip()
            
            # Formatear la fecha correctamente para Supabase si existe y no es nula
            fecha_val = row["Fecha"]
            if fecha_val is not None and str(fecha_val).strip() != "" and str(fecha_val).lower() != "nan":
                try:
                    fecha_val = pd.to_datetime(fecha_val).strftime("%Y-%m-%d")
                except:
                    fecha_val = None
            else:
                fecha_val = None

            datos_fila = {
                "Usuario": usuario_actual,
                "Contraseña": row["Contraseña"] if row["Contraseña"] is not None else "",
                "Cliente 1": row["Cliente 1"] if row["Cliente 1"] is not None else "",
                "Cliente 2": row["Cliente 2"] if row["Cliente 2"] is not None else "",
                "Cliente 3": row["Cliente 3"] if row["Cliente 3"] is not None else "",
                "Cliente 4": row["Cliente 4"] if row["Cliente 4"] is not None else "",
                "Fecha": fecha_val,
                "Observacion": row["Observacion"] if row["Observacion"] is not None else "",
                "usuario completo": f"USUARIO:    {usuario_actual}    CONTRASEÑA:    {row['Contraseña'] if row['Contraseña'] is not None else ''}",
                "clientes": f"{row['Cliente 1'] if row['Cliente 1'] is not None else ''}, {row['Cliente 2'] if row['Cliente 2'] is not None else ''}, {row['Cliente 3'] if row['Cliente 3'] is not None else ''}, {row['Cliente 4'] if row['Cliente 4'] is not None else ''}"
            }

            fila_id = row.get("id")
            if pd.notnull(fila_id) and fila_id != "" and fila_id in ids_originales:
                # Actualizar registro existente por ID
                supabase.table("registros").update(datos_fila).eq("id", int(fila_id)).execute()
            else:
                # Insertar nuevo registro (quitamos el id para que la BD lo autogenere)
                datos_fila.pop("id", None)
                supabase.table("registros").insert(datos_fila).execute()

        st.success("¡Base de datos actualizada con éxito en Supabase!")
        st.rerun()

except Exception as e:
    st.error(f"Ocurrió un error inesperado al conectar con Supabase: {e}")
