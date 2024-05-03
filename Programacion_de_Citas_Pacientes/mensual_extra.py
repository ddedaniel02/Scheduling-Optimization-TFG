from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Choice
from objetos_variables import Cita, Fase, Personal, consistencia_horas
import numpy as np
import math
import json

slots_ocupados = []
lista_contador = [0, 0, 0, 0]



class MultiObjectiveMixedVariableProblem(ElementwiseProblem):

    def __init__(self, estudio, identificador_paciente, myinput, **kwargs):
        """Implementación de los parámetros"""


        # Número de consultas disponibles
        self.consultorios = myinput["n_consultorios"]
        self.fases = myinput["fases"]
        self.roles = myinput["roles"]
        self.recursos = myinput["personal"]

        # Diccionario de asignación de cada fase a un Rol
        self.cargo_actividad = myinput["cargos"]
        # Duración de cada actividad
        self.duracion_actividad = myinput["duracion"]

        self.dias = myinput["n_dias"]

        self.horas = np.array([horas for horas in range(myinput["hora_inicio"], myinput["hora_fin"] + 1)])

        #Se crean todas las actividades que se deben llevar a cabo en el horario
        #self.actividades = [Fase(estudio, tipo_actividad) for tipo_actividad in self.tipo_actividades_totales]
        self.actividades = []
        for fase in self.fases:
            self.actividades.append(Fase(estudio, fase, identificador_paciente))
        #print(self.actividades)
        self.personal = []
        identificador_personal = 1
        for rol in self.roles:
            for i in range(self.recursos[rol]):
                if i % 2 == 0:
                    self.personal.append(Personal(rol + str(identificador_personal), rol, "Mañana"))
                    print('Mañana: ', rol + str(identificador_personal))
                else:
                    self.personal.append(Personal(rol + str(identificador_personal), rol, "Tarde"))
                    print('Tarde: ', rol + str(identificador_personal))
                identificador_personal += 1
        #print(self.personal)
        """Sección implementación de Variables"""

        vars = dict()
        # Se crean todas las combinaciones posibles de asignar una Fase a una cita
        self.combinations = []
        for consultorio in range(1, self.consultorios + 1):
            for dia in range(1, self.dias +1):
                for personal in self.personal:
                    for start_time in self.horas:
                        for end_time in self.horas:
                            if (int(end_time) - int(start_time)) == int(max(self.duracion_actividad.values())):
                                if personal.turno == "Mañana" and start_time < 15:
                                    cita = Cita(consultorio, start_time, end_time, dia, personal)
                                    if not self.check_slot(cita):
                                        self.combinations.append(cita)
                                elif personal.turno == "Tarde" and start_time >= 15:
                                    cita = Cita(consultorio, start_time, end_time, dia, personal)
                                    if not self.check_slot(cita):
                                        self.combinations.append(cita)

        #print(self.combinations)
        # Se filtran aquellas variables que sabemos de antemano que no serán válidas
        for actividad in self.actividades:
            opciones = []
            for opcion in self.combinations:
                if actividad.fase in self.cargo_actividad[opcion.personal.role]:
                    opciones.append(opcion)
            vars[actividad] = Choice(options=opciones)
        super().__init__(vars=vars, n_obj=2, n_constr = 4, **kwargs)

    def _evaluate(self, X, out, *args, **kwargs):
        # X = Fase:Cita
        penalizacion_1 = 0
        penalizacion_2 = 0
        penalizacion_3 = 0
        penalizacion_4 = 0

        for day in range(1, self.dias +1):
            # Restriccion 1: Una sala no puede contener dos citas al mismo tiempo:
            for sala in range(1, self.consultorios +1):
                citas_sala_time = np.sort(
                    np.array(
                        [cita.start_time for cita in X.values() if cita.operation_room == sala and cita.day == day]))
                start_time = 0
                for cita_time in citas_sala_time:
                    if cita_time == start_time:
                        penalizacion_1 += 100
                    start_time = cita_time

            # Restriccion 2: No se pueden asignar más personal del disponible en una misma hora
            for start_time in self.horas:
                # Lista que contiene todas las citas de un respectivo día y de una hora
                lista_time_day = [cita for cita in X.values() if cita.day == day and cita.start_time == start_time]
                lista_contador = []
                for i in range(len(self.roles)): # No se cuantos roles hay GENERICO
                    lista_contador.append(0)
                #Funcion que cuenta cuantos roles hay asignado a dichar hora
                penalizacion_2 += self.contador_personal(lista_contador, lista_time_day)
                penalizacion_2 += self.contador_personal_asignado(day, start_time, lista_contador)

                # Restriccion 3: Un mismo trabajador no puede estar en dos citas distintas a la misma hora
                for personal in lista_time_day:
                    citas = [cita for cita in X.values() if cita.personal.id == personal.personal.id and cita.start_time == start_time and cita.day == day]
                    if len(citas) > 1:
                        penalizacion_3 += 100

        # Restriccion 4: Una fase anterior en el orden no puede ir después ni a la misma hora que otra que va más
        # tarde en el orden. Por ejemplo: 1ºPC y 2ºR (incorrecto)
        evaluados = set()
        for cita_i in X:
            if cita_i.fase in evaluados:
                continue
            evaluados.add(cita_i)
            hora_inicio_i = int(X[cita_i].start_time) + 24 * int(X[cita_i].day)
            for cita_j in X:
                if cita_j in evaluados:
                    continue
                hora_inicio_j = int(X[cita_j].start_time) + 24 * int(X[cita_j].day)
                if self.fases.index(cita_i.fase) == self.fases.index(cita_j.fase) - 1 and hora_inicio_i >= hora_inicio_j:
                    penalizacion_4 += 100



        #Funcion Objetivo 1: Reducir tiempos de espera en citas del mismo estudio
        funcion_objetivo_1 = 0
        for cita_i in X:
            if cita_i.fase == self.fases[len(self.fases)-1]:
                continue
            hora_fin_i = int(X[cita_i].end_time) + 24 * int(X[cita_i].day)
            for cita_j in X:
                if cita_j.fase == self.fases[0]:
                    continue
                if cita_j.fase == cita_i.fase:
                    continue
                if self.fases.index(cita_i.fase) == self.fases.index(cita_j.fase) - 1:
                    hora_inicio_j = int(X[cita_j].start_time) + 24 * int(X[cita_j].day)
                    funcion_objetivo_1 += abs(hora_inicio_j - hora_fin_i)
                    break

        # Funcion objetivo 2: Minimizar las horas de trabajo del grupo de trabajadores
        funcion_objetivo_2 = 0
        for dia in range(1, self.dias +1):
            for rol in self.roles:
                lista_citas_personal_morning = []
                lista_citas_personal_afternoon = []
                for personal in self.personal:
                    if personal.role == rol:
                        if personal.turno == "Mañana":
                            citas_rol_personal = [citas for citas in X.values() if citas.day == dia
                                                  and citas.personal.id == personal.id]
                            self.conteo_trabajadores(citas_rol_personal, dia, personal.id)
                            lista_citas_personal_morning.append(len(citas_rol_personal))
                        elif personal.turno == "Tarde":
                            citas_rol_personal = [citas for citas in X.values() if citas.day == dia
                                                  and citas.personal.id == personal.id]
                            self.conteo_trabajadores(citas_rol_personal, dia, personal.id)
                            lista_citas_personal_afternoon.append(len(citas_rol_personal))

                funcion_objetivo_2 += self.repartir_carga(lista_citas_personal_morning)
                funcion_objetivo_2 += self.repartir_carga(lista_citas_personal_afternoon)


        out["F"] = [funcion_objetivo_1, funcion_objetivo_2]
        out["G"] = [penalizacion_1, penalizacion_2, penalizacion_3, penalizacion_4]

    def contador_personal(self, lista_contador, lista_time_day):
        penalizacion_2 = 0
        for rol in self.roles:
            for cita in lista_time_day:
                if cita.personal.role == rol:
                    if lista_contador[self.roles.index(rol)] < self.recursos[rol]:
                        lista_contador[self.roles.index(rol)] += 1
                    else:
                        penalizacion_2 += 100
        return penalizacion_2
    def contador_personal_asignado(self, day, start_time, lista_contador):
        penalizacion_2 = 0
        for rol in self.roles:
            for cita in slots_ocupados:
                if cita.day == day and cita.start_time == start_time:
                    if cita.personal.role == rol:
                        if lista_contador[self.roles.index(rol)] < self.recursos[rol]:
                            lista_contador[self.roles.index(rol)] += 1
                        else:
                            penalizacion_2 += 100
        return penalizacion_2
    def check_slot(self, cita):
        for elements in slots_ocupados:
            if cita.day == elements.day and cita.start_time == elements.start_time and cita.operation_room == elements.operation_room:
                return True
        return False

    def conteo_trabajadores(self, lista_citas, dia, identificador):
        for cita in slots_ocupados:
            if cita.day == dia and cita.personal.id == identificador:
                lista_citas.append(cita)

    def repartir_carga(self, lista_citas):
        funcion_objetivo_2 = 0
        total_citas = sum(lista_citas)
        total_trabajadores = len(lista_citas)
        if total_citas % total_trabajadores != 0:
            if max(lista_citas) != (int(total_citas / total_trabajadores)) + 1:
                funcion_objetivo_2 += 100
        else:
            if max(lista_citas) != (int(total_citas / total_trabajadores)):
                funcion_objetivo_2 += 100
        return funcion_objetivo_2