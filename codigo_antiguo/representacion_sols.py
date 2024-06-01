import matplotlib.pyplot as plt
import os



def plot_schedule(schedule, estudio, paciente):
    # Crear listas para almacenar las coordenadas de las citas
    rooms = []
    start_times = []
    end_times = []
    fases = []
    trabajadores = []
    dias = []
    total_dias = 30
    total_horas = 22
    colores = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray']

    # Recorrer el diccionario y extraer la información de las citas
    for key, appointment in schedule.items():
        rooms.append(appointment.operation_room)
        start_times.append(appointment.start_time)
        end_times.append(appointment.end_time)
        trabajadores.append(appointment.personal.id)
        dias.append(appointment.day)
        fases.append(key.fase)


    # Configurar el gráfico
    plt.figure(figsize=(10, 6))
    plt.title(estudio+": " + str(paciente))
    plt.xlabel('Hora')
    plt.ylabel('Día')
    plt.yticks(range(1, total_dias+ 1))
    plt.xticks(range(7, total_horas + 1))

    plt.grid(True)
    print()
    # Dibujar las citas como segmentos de línea
    for start, end, dia, room, fase, trabajador in zip(start_times, end_times, dias, rooms, fases, trabajadores):
        plt.plot([start, end], [dia, dia], marker='o', markersize=6, color=colores[fases.index(fase)], label=f'Fase: {fase}')
        plt.text((start + end) / 2, dia, f'C{room};Per: {trabajador}', ha='center', va='bottom', fontsize=9)



    plt.legend(loc='upper left', fontsize='small', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    # Crear la carpeta si no existe
    if not os.path.exists('../resultados_citas_agenda_paciente'):
        os.makedirs('../resultados_citas_agenda_paciente')

    # Guardar la figura en la carpeta deseada
    plt.savefig(f'./resultados_citas_agenda_paciente/{estudio}_{paciente}_plot.png')
    #plt.show()

