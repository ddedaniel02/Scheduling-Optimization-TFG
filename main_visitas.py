from pymoo.operators.mutation.pm import PolynomialMutation
from pymoo.optimize import minimize
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.mixed import MixedVariableMating, MixedVariableSampling, MixedVariableDuplicateElimination
from mensual_visitas import *
import numpy as np
from representacion_sols_visitas import plot_schedule
import json
import random
from crear_estadisticas import *
import time
from input_validator import *

inicio_tiempo = time.time()

lista_sols = []
consultas_usadas = []
citas_totales = []
trabajadores_usados = []

##SETUP##
with open("Programacion_de_Citas_Pacientes/input_visitas.json", "r") as file:
    myinput = json.load(file)


POP_SIZE = load_number("pop_size")
N_GENS = load_number("n_gens")
MUTATION_PERCENTAGE = load_percentage("mutation_percentage")
WEIGHT_F1 = load_percentage("weight_f1")
WEIGHT_F2 = load_percentage("weight_f2")
WEIGHT_F3 = load_percentage("weight_f3")
WEIGHT_F4 = load_percentage("weight_f4")
WEIGHT_F5 = load_percentage("weight_f5")

TOTAL_WEIGHT = round(WEIGHT_F1 + WEIGHT_F2 + WEIGHT_F3 + WEIGHT_F4 + WEIGHT_F5, 2)
correct_percentage(TOTAL_WEIGHT, "total_weight")

limpiar_base_datos()

validar_parametros(myinput)

for dias in range(myinput["n_dias"]):
    horarios_dias.append(set())
    consultas_usadas.append([])
    trabajadores_usados.append({})
    identificador_trabajador = 1
    for consultorios in range(myinput["n_consultorios"]):
        consultas_usadas[dias].append(0)
    for rol in myinput["roles"]:
        for identificador in range(1, myinput["personal"][rol] + 1):
            trabajadores_usados[dias][rol+str(identificador_trabajador)] = 0
            identificador_trabajador += 1






pacientes_dict = myinput["n_personas"]
identificador_pacientes = 1
# print(
for estudio in pacientes_dict:
    tiempo_espera = 0
    for visita in myinput[estudio]:
        tiempo_espera += int(myinput[estudio][visita]["tiempo_espera"])
    for n_pacientes in range(pacientes_dict[estudio]):
        citas_paciente = []
        objetivos_paciente = [0, 0, 0]
        lista_dias = []
        enrolamiento = True
        print("Paciente: ", identificador_pacientes)

        for visita in myinput[estudio]:
            print("Visita: ",visita)
            problem = MultiObjectiveMixedVariableProblem(estudio, visita, identificador_pacientes, myinput, enrolamiento
                                                         , tiempo_espera, lista_dias)
            algorithm = NSGA2(pop_size=POP_SIZE,
                              sampling=MixedVariableSampling(),
                              mating=MixedVariableMating(eliminate_duplicates=MixedVariableDuplicateElimination()),
                              mutation=PolynomialMutation(prob=MUTATION_PERCENTAGE),
                              eliminate_duplicates=MixedVariableDuplicateElimination(),
                              )

            termination = ('n_gen', N_GENS)

            res = minimize(problem,
                           algorithm,
                           termination,
                           seed=random.randint(1, 10000),
                           verbose=False)
            if enrolamiento:
                enrolamiento = False

            X = res.X
            F = res.F


            approx_ideal = F.min(axis=0)
            approx_nadir = F.max(axis=0)

            nF = (F - approx_ideal) / (approx_nadir - approx_ideal)

            weights = np.array([WEIGHT_F1, WEIGHT_F2, WEIGHT_F3, WEIGHT_F4, WEIGHT_F5])

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
                trabajadores_usados[dia - 1][citas.personal.id] += 1
            citas_totales.append(X[i])
        plot_schedule(citas_paciente, estudio, identificador_pacientes)
        escribir_resultados_paciente(objetivos_paciente, identificador_pacientes)
        identificador_pacientes += 1

escribir_estadisticas_dia(myinput, citas_totales, consultas_usadas, trabajadores_usados, horarios_dias)


fin_tiempo = time.time()
diferencia_tiempo = fin_tiempo - inicio_tiempo
print(f"Diferencia tiempo {diferencia_tiempo}")


