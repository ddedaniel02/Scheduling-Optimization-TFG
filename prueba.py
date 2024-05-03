horas_lista = []
for horas in range(7, 22):
    for minutes in range(0, 60, 10):
        hora = str(horas) + "." + str(minutes)
        horas_lista.append(float(hora))

horas_lista.append(22.0)


print(horas_lista)