import matplotlib.pyplot as plt
import os
import json


def plot_schedule(schedule, estudio, paciente):
    # Crear listas para almacenar las coordenadas de las citas
    rooms = []
    start_times = []
    end_times = []
    fases = []
    trabajadores = []
    dias = []
    visitas = []
    with open("Programacion_de_Citas_Pacientes/input_visitas.json", "r") as file:
        myinput = json.load(file)
    total_dias = int(myinput["n_dias"])
    total_horas = int(myinput["hora_fin"])
    colores = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray']

    # Recorrer el diccionario y extraer la información de las citas
    for citas in schedule:
        for key, appointment in citas.items():
            rooms.append(appointment.operation_room)
            start_times.append(appointment.start_time)
            end_times.append(appointment.end_time)
            trabajadores.append(appointment.personal.id)
            dias.append(appointment.day)
            fases.append(key.fase)
            visitas.append(key.visita)

    # Obtener los días únicos con citas
    dias_con_citas = sorted(set(dias))

    # Configurar el gráfico
    plt.figure(figsize=(15, len(dias_con_citas) * 1))  # Ajusta el valor para hacer el eje y más grande
    plt.title(estudio + ": " + str(paciente))
    plt.xlabel('Hora')
    plt.ylabel('Día')
    plt.yticks(dias_con_citas)
    plt.xticks(range(7, total_horas + 1))

    plt.grid(True)
    # Dibujar las citas como segmentos de línea
    for start, end, dia, room, fase, trabajador, visita in zip(start_times, end_times, dias, rooms, fases, trabajadores, visitas):
        plt.plot([start, end], [dia, dia], marker='o', markersize=6, color=colores[fases.index(fase)], label=f'Visita: {visita} Fase: {fase}')
        plt.text((start + end) / 2, dia, f'C{room};{trabajador}', ha='center', va='bottom', fontsize=7)

    plt.legend(loc='upper left', fontsize='small', bbox_to_anchor=(1, 1))
    # Ajustar los márgenes superior e inferior
    plt.tight_layout()

    # Crear la carpeta si no existe
    if not os.path.exists('resultados_citas_agenda_paciente'):
        os.makedirs('resultados_citas_agenda_paciente')

    # Guardar la figura en la carpeta deseada
    plt.savefig(f'./resultados_citas_agenda_paciente/agenda_paciente_{paciente}.png')

# Ejemplo de uso:
# plot_schedule(schedule, "Nombre del Estudio", "Nombre del Paciente")
