from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Choice
from objetos_variables import Cita, Fase, consistencia_horas
import numpy as np

slots_ocupados = []

class MultiObjectiveMixedVariableProblem(ElementwiseProblem):

    def __init__(self, estudio, **kwargs):
        """Implementación de los parámetros"""
        self.tipo_actividades = np.array(["R", "Cs", "ME", "CM", "LB", "Vc", "Obs", "PC"]) # Array de actividades
        # Diccionario de asignación de cada fase a un Rol
        self.cargo_actividad = {"R": "E", "Cs": "E", "ME": "MG", "CM": "MG", "LB": "LB", "Vc": "MS", "Obs": "E", "PC": "MG"}
        # Duración de cada actividad
        self.duracion_actividad = {"R": 1, "Cs": 1, "ME": 1, "CM": 1, "LB": 1, "Vc": 1, "Obs": 1, "PC": 1}
        # Array de estudios a llevar a cabo
        self.estudio = estudio

        #Se crean todas las actividades que se deben llevar a cabo en el horario
        self.actividades = [Fase(estudio, tipo_actividad) for tipo_actividad in self.tipo_actividades]
        # Número de consultas disponibles
        self.consultorios = np.array([1, 2, 3, 4, 5, 6])

        #Días totales
        self.dias = np.array([dias for dias in range(1,31)])
        # Horario de la clínica (horas a las que se pueden asignar las citas)
        self.horas = np.array([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22])
        # Array de roles dentro de la clínica
        self.roles = np.array(["MG", "MS", "E", "LB"])
        # Total de trabajadores en cada rol
        self.recursos = {"MG": 7, "MS": 3, "E": 7, "LB": 3} #typed.Dict()

        # Se crea la lista de trabajadores disponible

        """Sección implementación de Variables"""

        vars = dict()
        # Se crean todas las combinaciones posibles de asignar una Fase a una cita
        self.combinations = []
        for consultorio in self.consultorios:
            for dia in self.dias:
                for personal in self.roles:
                    for start_time in self.horas:
                        for end_time in self.horas:
                            if (int(end_time) - int(start_time)) == int(max(self.duracion_actividad.values())):
                                cita = Cita(consultorio, start_time, end_time, dia, personal)
                                if not self.check_slot(cita):
                                    self.combinations.append(cita)

        # Se filtran aquellas variables que sabemos de antemano que no serán válidas
        for actividad in self.actividades:
            opciones = []
            for opcion in self.combinations:
                if self.cargo_actividad[actividad.tipo_actividad] == opcion.personal:
                    if opcion.day == 1 or opcion.day == 30:
                        if consistencia_horas(actividad.tipo_actividad, opcion.start_time, opcion.day):
                            opciones.append(opcion)
                    else:
                        opciones.append(opcion)
            vars[actividad] = Choice(options=opciones)
        super().__init__(vars=vars, n_obj=2, n_constr = 3, **kwargs)


    def _evaluate(self, X, out, *args, **kwargs):
        # X = Fase:Cita
        penalizacion_1 = 0
        penalizacion_2 = 0
        contador = 0
        fin_medio_dias = 0
        for day in self.dias:
            # Restriccion 1: Una sala no puede contener dos citas al mismo tiempo:
            for sala in self.consultorios:
                citas_sala_time = np.sort(
                    np.array(
                        [cita.start_time for cita in X.values() if cita.operation_room == sala and cita.day == day]))
                start_time = 0
                for cita_time in citas_sala_time:
                    if cita_time == start_time:
                        penalizacion_1 += 100
                    start_time = cita_time
            for start_time in self.horas:
                # Restriccion 2: No se pueden asignar más personal del disponible en una misma hora
                lista_time_day = np.sort(np.array([cita.personal for cita in X.values() if cita.day == day and cita.start_time == start_time]))
                lista_contador = [0, 0, 0, 0]
                penalizacion_2 += self.contador_personal(lista_time_day, lista_contador)
                penalizacion_2 += self.contador_personal_asignado(day, start_time, lista_contador)


            # Funcion Objetivo 2
            lista_citas_dia = np.sort(np.array([cita.end_time for cita in X.values() if cita.day == day]))[::-1]
            if np.size(lista_citas_dia) != 0:
                contador += 1
                fin_medio_dias += lista_citas_dia[0]

        funcion_objetivo_2 = fin_medio_dias / contador

        # Restriccion 3: Una fase anterior en el orden no puede ir después ni a la misma hora que otra que va más
        # tarde en el orden. Por ejemplo: 1ºPC y 2ºR (incorrecto)
        penalizacion_3 = 0
        evaluados = set()
        for cita_i in X:
            if cita_i.tipo_actividad in evaluados:
                continue
            evaluados.add(cita_i)
            hora_inicio_i = int(X[cita_i].start_time) + 24 * int(X[cita_i].day)
            for cita_j in X:
                if cita_j in evaluados:
                    continue
                hora_inicio_j = int(X[cita_j].start_time) + 24 * int(X[cita_j].day)
                if np.where(self.tipo_actividades == cita_i.tipo_actividad)[0] < \
                        np.where(self.tipo_actividades == cita_j.tipo_actividad)[0] and hora_inicio_i >= hora_inicio_j:
                    penalizacion_3 += 100



        #Funcion Objetivo 1: Reducir tiempos de espera en citas del mismo estudio
        funcion_objetivo_1 = 0
        for cita_i in X:
            if cita_i.tipo_actividad == 'PC':
                continue
            hora_fin_i = int(X[cita_i].end_time) + 24 * int(X[cita_i].day)
            for cita_j in X:
                if cita_j.tipo_actividad == 'R':
                    continue
                if cita_j.tipo_actividad == cita_i.tipo_actividad:
                    continue
                if np.where(self.tipo_actividades == cita_i.tipo_actividad)[0] == \
                        np.where(self.tipo_actividades == cita_j.tipo_actividad)[0] - 1:
                    hora_inicio_j = int(X[cita_j].start_time) + 24 * int(X[cita_j].day)
                    funcion_objetivo_1 += abs(hora_inicio_j - hora_fin_i)
                    break

        penalizacion = penalizacion_1 + penalizacion_2 + penalizacion_3
        funcion_objetivo_1 += penalizacion
        funcion_objetivo_2 += penalizacion
        out["F"] = [funcion_objetivo_1, int(funcion_objetivo_2)]
        out["G"] = [penalizacion_1, penalizacion_2, penalizacion_3]

    def contador_personal(self, lista_time_day, lista_contador):
        penalizacion_2 = 0
        for personal in lista_time_day:
            if personal == 'E':
                if lista_contador[0] < self.recursos[personal]:
                    lista_contador[0] += 1
                else:
                    penalizacion_2 += 100
            if personal == 'MG':
                if lista_contador[1] < self.recursos[personal]:
                    lista_contador[1] += 1
                else:
                    penalizacion_2 += 100
            if personal == 'MS':
                if lista_contador[2] < self.recursos[personal]:
                    lista_contador[2] += 1
                else:
                    penalizacion_2 += 100
            if personal == 'LB':
                if lista_contador[3] < self.recursos[personal]:
                    lista_contador[3] += 1
                else:
                    penalizacion_2 += 100
        return penalizacion_2
    def contador_personal_asignado(self, day, start_time, lista_contador):
        penalizacion_2 = 0
        for cita in slots_ocupados:
            if cita.day == day and cita.start_time == start_time:
                if cita.personal == 'E':
                    if lista_contador[0] < self.recursos[cita.personal]:
                        lista_contador[0] += 1
                    else:
                        penalizacion_2 += 100
                if cita.personal == 'MG':
                    if lista_contador[1] < self.recursos[cita.personal]:
                        lista_contador[1] += 1
                    else:
                        penalizacion_2 += 100
                if cita.personal == 'MS':
                    if lista_contador[2] < self.recursos[cita.personal]:
                        lista_contador[2] += 1
                    else:
                        penalizacion_2 += 100
                if cita.personal == 'LB':
                    if lista_contador[3] < self.recursos[cita.personal]:
                        lista_contador[3] += 1
                    else:
                        penalizacion_2 += 100
        return penalizacion_2
    def check_slot(self, cita):
        for elements in slots_ocupados:
            if cita.day == elements.day and cita.start_time == elements.start_time and cita.operation_room == elements.operation_room:
                return True
        return False