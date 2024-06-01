import os



def limpiar_base_datos():
    ruta_carpeta_citas = "./resultados_citas_pacientes"
    archivos = os.listdir(ruta_carpeta_citas)

    for archivo in archivos:
        ruta_completa = os.path.join(ruta_carpeta_citas, archivo)
        if os.path.isfile(ruta_completa):
            os.remove(ruta_completa)

    ruta_carpeta_plots = "./resultados_citas_agenda_paciente"
    archivos = os.listdir(ruta_carpeta_plots)

    for archivo in archivos:
        ruta_completa = os.path.join(ruta_carpeta_plots, archivo)
        if os.path.isfile(ruta_completa):
            os.remove(ruta_completa)

    ruta_carpeta_dia = "./resultados_citas_dia"
    archivos = os.listdir(ruta_carpeta_dia)
    for archivo in archivos:
        ruta_completa = os.path.join(ruta_carpeta_dia, archivo)
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
def escribir_resultados_paciente(resultados, identificador_paciente):
    with open("resultados_citas_pacientes/citas_paciente_"+str(identificador_paciente)+".txt", "a") as file:
        file.write(f"\nHoras de espera total: {resultados[0]}, Dia de fin: {resultados[1]}\n")


def escribir_estadisticas_dia(myinput, citas_totales, consulta_usadas, trabajadores_usados, horarios_dias):
    slots_totales = 1 #empezamos en 1 para contar también la última
    for horas in range(myinput["hora_inicio"], myinput["hora_fin"]):
        for minutos in range(0, 60, 10):
            slots_totales += 1

    for day in range(1, myinput["n_dias"] + 1):
        lista_ordenada = ordenar_citas(citas_totales, day)
        sorted_list = sorted(horarios_dias[day - 1])
        slots_ocupados = len(sorted_list)
        porcentaje_ocupacion = round((slots_ocupados / slots_totales) * 100, 2)
        if len(lista_ordenada) > 0:
            with open("resultados_citas_dia/agenda_dia_"+str(day)+".txt", "w") as file:
                for cita_paciente in lista_ordenada:
                    file.write(f"Franja: {cita_paciente[1].start_time}-{cita_paciente[1].end_time} \tConsulta: {cita_paciente[1].operation_room}"
                               f"\tPersonal: {cita_paciente[1].personal.id} --> Estudio: {cita_paciente[0].estudio} "
                               f"\tVisita: {cita_paciente[0].visita} \tFase: {cita_paciente[0].fase}"
                               f"\tPaciente: {cita_paciente[0].paciente}\n")

                file.write(f"\nCitas en cada consulta: {consulta_usadas[day - 1]}\n"
                            f"Porcentaje de ocupacion: {porcentaje_ocupacion}\n"
                            f"Slots Ocupados: {sorted_list}\n")
                file.write(f"Citas por trabajador: \n")
                for claves in trabajadores_usados[day - 1]:
                    value = trabajadores_usados[day - 1][claves]
                    if value != 0:
                        file.write(f"{claves}:{str(value)}\n")




def ordenar_citas(citas_totales, day):
    lista_ordenada = []
    for cita_global in citas_totales:
        for cita in cita_global:
            insertado = False
            if cita_global[cita].day == day:
                indice = 0
                for cita_lista in lista_ordenada:
                    if cita_global[cita].start_time <= cita_lista[1].start_time:
                        lista_ordenada.insert(indice, [cita, cita_global[cita]])
                        insertado = True
                        break
                    indice += 1
                if not insertado:
                    lista_ordenada.append([cita, cita_global[cita]])
    return lista_ordenada


