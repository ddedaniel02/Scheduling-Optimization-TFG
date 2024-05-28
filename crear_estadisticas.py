import os



def limpiar_base_datos():
    with open('Txt/objetivos.txt', 'w') as f:
        pass
    with open('Txt/estadisticas.txt', 'w') as f:
        pass

    ruta_carpeta_citas = "./resultados_citas_pacientes"
    archivos = os.listdir(ruta_carpeta_citas)

    for archivo in archivos:
        ruta_completa = os.path.join(ruta_carpeta_citas, archivo)
        if os.path.isfile(ruta_completa):
            os.remove(ruta_completa)

    ruta_carpeta_plots = "./imagenes_plots"
    archivos = os.listdir(ruta_carpeta_plots)

    for archivo in archivos:
        ruta_completa = os.path.join(ruta_carpeta_plots, archivo)
        if os.path.isfile(ruta_completa):
            os.remove(ruta_completa)

def escribir_citas_paciente(citas, identificador_paciente):
    lista_claves = list(citas.keys())
    visita = lista_claves[0].visita
    with open("resultados_citas_pacientes/citas_paciente_" + str(identificador_paciente) + ".txt", "a") as file:
        file.write(f"Visita: {visita} \t Dia:  {citas[lista_claves[0]].day}\n")
        for cita in citas:
            file.write(f"\t Tipo: {cita.fase} \t Consulta: {citas[cita].operation_room} \t "
                       f"Hora Inicio: {citas[cita].start_time} \t Hora Fin: {citas[cita].end_time}\t "
                       f"Personal {citas[cita].personal.id} \n")

def escribir_resultados(horas_espera, dia_fin):
    with open('Txt/objetivos.txt', 'a') as f:
        f.write(f"Horas de espera total: {horas_espera}, Dia de fin: {dia_fin}\n")

def escribir_estadisticas(myinput, consultas_usadas, horarios_dias):
    slots_totales = 1 #empezamos en 1 para contar también la última
    for horas in range(myinput["hora_inicio"], myinput["hora_fin"]):
        for minutos in range(0, 60, 10):
            slots_totales += 1

    with open("Txt/estadisticas.txt", "a") as f:
        for dia in range(1, myinput["n_dias"] + 1):
            sorted_list = sorted(horarios_dias[dia - 1])
            slots_ocupados = len(sorted_list)
            porcentaje_ocupacion = (slots_ocupados / slots_totales) * 100
            f.write(
                f"Dia {dia} \tCitas en cada consulta: {consultas_usadas[dia - 1]} "
                f"\tPorcentaje de ocupacion: {porcentaje_ocupacion}%"
                f"\tSlots ocupados: {sorted_list}\n")
