from pymoo.operators.mutation.pm import PolynomialMutation
from pymoo.optimize import minimize
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.mixed import MixedVariableMating, MixedVariableSampling, MixedVariableDuplicateElimination
from mensual_visitas import MultiObjectiveMixedVariableProblem, slots_ocupados, horarios_dias
import numpy as np
from representacion_sols_visitas import plot_schedule
import json
import random
from crear_estadisticas import *




lista_sols = []
consultas_usadas = []

##SETUP##
with open("Programacion_de_Citas_Pacientes/input_visitas.json", "r") as file:
    myinput = json.load(file)


limpiar_base_datos()


for dias in range(myinput["n_dias"]):
    horarios_dias.append(set())
    consultas_usadas.append([])
    for consultorios in range(myinput["n_consultorios"]):
        consultas_usadas[dias].append(0)


pacientes_dict = myinput["n_personas"]
identificador_pacientes = 1
# print(pacientes_dict)
for estudio in pacientes_dict:
    for n_pacientes in range(pacientes_dict[estudio]):
        tiempo_espera = 0
        for visita in myinput[estudio]:
            tiempo_espera += int(myinput[estudio][visita]["tiempo_espera"])
        citas_paciente = []
        objetivos_paciente = [0, 0, 0]
        lista_dias = []
        enrolamiento = True
        print("Paciente: ", identificador_pacientes)
        for visita in myinput[estudio]:
            print("Visita: ",visita)
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

            X = res.X
            F = res.F


            approx_ideal = F.min(axis=0)
            approx_nadir = F.max(axis=0)

            nF = (F - approx_ideal) / (approx_nadir - approx_ideal)

            weights = np.array([0.3, 0.3, 0.3, 0.1])

            from pymoo.decomposition.asf import ASF

            decomp = ASF()

            i = decomp.do(nF, 1 / weights).argmin()
            citas_paciente.append(X[i])
            # Horas de espera totales de una visita
            objetivos_paciente[0] += F[i][0]
            # Dia que acaba (cuanto menos mejor)
            objetivos_paciente[1] = F[i][1]

            escribir_citas_paciente(X[i], identificador_pacientes)

            insert_uno = True
            for citas in X[i].values():
                if insert_uno:
                    dia = citas.day
                    lista_dias.append(citas.day)
                    insert_uno = False
                problem.insertar_horas(citas.start_time, citas.end_time, horarios_dias[dia - 1])
                slots_ocupados.append(citas)
                consultas_usadas[dia - 1][citas.operation_room - 1] += 1

        plot_schedule(citas_paciente, estudio, identificador_pacientes)

        identificador_pacientes += 1
        escribir_resultados(objetivos_paciente[0], objetivos_paciente[1])


escribir_estadisticas(myinput, consultas_usadas, horarios_dias)





