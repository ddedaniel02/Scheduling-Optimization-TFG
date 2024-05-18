from pymoo.operators.mutation.pm import PolynomialMutation
from pymoo.optimize import minimize
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.mixed import MixedVariableMating, MixedVariableSampling, MixedVariableDuplicateElimination
from mensual_visitas import MultiObjectiveMixedVariableProblem, slots_ocupados, horarios_dias
import matplotlib.pyplot as plt
import numpy as np
from representacion_sols_visitas import plot_schedule
from pymoo.visualization.scatter import Scatter
from pymoo.termination.robust import RobustTermination
from pymoo.termination.ftol import MultiObjectiveSpaceTermination
import json
import random




lista_sols = []
with open("Programacion_de_Citas_Pacientes/input_visitas.json", "r") as file:
    myinput = json.load(file)

with open('Txt/objetivos.txt', 'w') as f:
    pass

for dias in range(myinput["n_dias"]):
    horarios_dias.append(set())


pacientes_dict = myinput["n_personas"]
identificador_pacientes = 1
# print(pacientes_dict)
for estudio in pacientes_dict:
    for n_pacientes in range(pacientes_dict[estudio]):
        tiempo_espera = 0
        for visita in myinput[estudio]:
            print(visita," ",myinput[estudio][visita]["tiempo_espera"])
            tiempo_espera += int(myinput[estudio][visita]["tiempo_espera"])
        citas_paciente = []
        objetivos_paciente = [0, 0, 0]
        lista_dias = []
        enrolamiento = True
        consultas_usadas = []
        print("Paciente: ", identificador_pacientes)
        for visita in myinput[estudio]:
            print(visita)
            problem = MultiObjectiveMixedVariableProblem(estudio, visita, identificador_pacientes, myinput, enrolamiento
                                                         , tiempo_espera, lista_dias)
            algorithm = NSGA2(pop_size=100,
                              sampling=MixedVariableSampling(),
                              mating=MixedVariableMating(eliminate_duplicates=MixedVariableDuplicateElimination()),
                              mutation=PolynomialMutation(prob=0.1),
                              eliminate_duplicates=MixedVariableDuplicateElimination(),
                              )

            termination = ('n_gen', 100)

            res = minimize(problem,
                           algorithm,
                           termination,
                           seed=random.randint(1, 10000),
                           verbose=True)
            if enrolamiento:
                enrolamiento = False
            #tiempo_espera -= myinput[estudio][visita]["tiempo_espera"]
            X = res.X
            F = res.F

            # plot = Scatter()
            # plot.add(problem.pareto_front(), plot_type="line", color="black", alpha=0.7)
            # plot.add(F, facecolor="none", edgecolor="red")
            # plot.title = "Frente de Pareto"
            # plot.show()

            # print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))

            # plt.figure(figsize=(7, 5))
            # plt.scatter(F[:, 0], F[:, 1], s=30, facecolors='none', edgecolors='blue')
            # plt.title("Objective Space")
            # plt.show()

            fl = F.min(axis=0)
            fu = F.max(axis=0)
            # print(f"Scale f1: [{fl[0]}, {fu[0]}]")
            # print(f"Scale f2: [{fl[1]}, {fu[1]}]")

            approx_ideal = F.min(axis=0)
            approx_nadir = F.max(axis=0)

            # plt.figure(figsize=(7, 5))
            # plt.scatter(F[:, 0], F[:, 1], s=30, facecolors='none', edgecolors='blue')
            # plt.scatter(approx_ideal[0], approx_ideal[1], facecolors='none', edgecolors='red', marker="*", s=100,
            #             label="Ideal Point (Approx)")
            # plt.scatter(approx_nadir[0], approx_nadir[1], facecolors='none', edgecolors='black', marker="p", s=100,
            #             label="Nadir Point (Approx)")
            # plt.title("Puntos Nadir e Ideal (Approx)")
            # plt.legend()
            # plt.show()

            nF = (F - approx_ideal) / (approx_nadir - approx_ideal)

            fl = nF.min(axis=0)
            fu = nF.max(axis=0)
            # print(f"Scale f1: [{fl[0]}, {fu[0]}]")
            # print(f"Scale f2: [{fl[1]}, {fu[1]}]")

            # plt.figure(figsize=(7, 5))
            # plt.scatter(nF[:, 0], nF[:, 1], s=30, facecolors='none', edgecolors='blue')
            # plt.title("Frente de Pareto (Normalizado)")
            # plt.show()

            weights = np.array([0.3, 0.3, 0.3, 0.1])

            from pymoo.decomposition.asf import ASF

            decomp = ASF()

            i = decomp.do(nF, 1 / weights).argmin()

            # print("Best regarding ASF: Point \ni = %s\nF = %s \nX = %s" % (i, F[i], X[i]))

            # plt.figure(figsize=(7, 5))
            # plt.scatter(F[:, 0], F[:, 1], s=30, facecolors='none', edgecolors='blue')
            # plt.scatter(F[i, 0], F[i, 1], marker="x", color="red", s=200)
            # plt.title("Solución Subóptima Elegida por ASF")
            # plt.show()
            citas_paciente.append(X[i])
            # Horas de espera totales de una visita
            objetivos_paciente[0] += F[i][0]
            # Dia que acaba (cuanto menos mejor)
            objetivos_paciente[1] = F[i][1]
            # Número de consultas sin usar
            consultas_usadas.append(F[i][3])
            insert_uno = True
            with open("resultados_citas_pacientes/citas_paciente_"+str(identificador_pacientes) + ".txt" , "w") as file:
                file.write(str(X[i]) + "\n")
            for citas in X[i].values():
                if insert_uno:
                    dia = citas.day
                    lista_dias.append(citas.day)
                    insert_uno = False
                problem.insertar_horas(citas.start_time, citas.end_time, horarios_dias[dia - 1])
                slots_ocupados.append(citas)
            print("Slots ocupados: ",slots_ocupados)
        objetivos_paciente[2] = consultas_usadas
        plot_schedule(citas_paciente, estudio, identificador_pacientes)
        identificador_pacientes += 1
        with open('Txt/objetivos.txt', 'a') as f:
            f.write(f"Horas de espera total: {objetivos_paciente[0]}, Dia de fin: {objetivos_paciente[1]}\n")

contador = 1
for dia in horarios_dias:
    if len(dia) != 0:
        print("Dia: ",contador)
        print("Ocupados: ",dia)
        print("Longitud: ",len(dia))
    contador += 1


