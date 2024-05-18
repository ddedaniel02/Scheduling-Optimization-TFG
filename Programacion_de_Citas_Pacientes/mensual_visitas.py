from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Choice
from objetos_variables_visitas import Cita, Fase, Personal
import numpy as np
import random

slots_ocupados = []
lista_contador = [0, 0, 0, 0]

horarios_dias = []



class MultiObjectiveMixedVariableProblem(ElementwiseProblem):

    def __init__(self, estudio, visita, identificador_paciente, myinput, enrolamiento, tiempo_espera, lista_dias,  **kwargs):
        """Implementación de los parámetros"""
        self.estudio = estudio
        self.visita = visita
        self.identificador_paciente = identificador_paciente
        self.enrolamiento = enrolamiento
        self.tiempo_espera = tiempo_espera

        # Número de consultas disponibles
        self.consultorios = myinput["n_consultorios"]
        self.fases = []
        self.duracion = []
        for keys in myinput[self.estudio][self.visita]:
            if keys != "tiempo_espera":
                self.fases.append(keys)
                self.duracion.append(myinput[self.estudio][self.visita][keys])
        self.roles = myinput["roles"]
        self.recursos = myinput["personal"]

        # Diccionario de asignación de cada fase a un Rol
        self.cargo_actividad = myinput["cargos"]
        # Duración de cada actividad
        self.dias = myinput["n_dias"]
        self.horas = []
        for horas in range(myinput["hora_inicio"], myinput["hora_fin"]):
            if horas != 14:
                for minutes in range(0, 60, 10):
                    hora = str(horas) + "." + str(minutes)
                    self.horas.append(float(hora))
            else:
                self.horas.append(float(horas))
        self.horas.append(myinput["hora_fin"])

        #Se crean todas las actividades que se deben llevar a cabo en el horario
        #self.actividades = [Fase(estudio, tipo_actividad) for tipo_actividad in self.tipo_actividades_totales]
        self.actividades = []

        for fase in self.fases:
            self.actividades.append(Fase(self.estudio, self.visita, fase, identificador_paciente))
        #print(self.actividades)
        self.personal = []
        identificador_personal = 1
        for rol in self.roles:
            for i in range(self.recursos[rol]):
                if i % 2 == 0:
                    self.personal.append(Personal(rol + str(identificador_personal), rol, "Mañana"))
                else:
                    self.personal.append(Personal(rol + str(identificador_personal), rol, "Tarde"))
                identificador_personal += 1
        #print(self.personal)
        """Sección implementación de Variables"""

        vars = dict()
        # Se crean todas las combinaciones posibles de asignar una Fase a una cita
        self.combinations = []

        if self.enrolamiento:
            self.create_combinations()
        else:
            self.dia_actual = lista_dias[len(lista_dias)-1] + myinput[estudio][visita]["tiempo_espera"]
            self.create_combinations_next_visits(self.dia_actual)
        #print(self.combinations)
        # Se filtran aquellas variables que sabemos de antemano que no serán válidas
        for actividad in self.actividades:
            opciones = []
            for opcion in self.combinations:
                if self.asignar_hora(opcion, actividad, myinput):
                    if actividad.fase in self.cargo_actividad[opcion.personal.role]:
                        opciones.append(opcion)
            vars[actividad] = Choice(options=opciones)
        super().__init__(vars=vars, n_obj=4, n_constr=6, **kwargs)


    def _evaluate(self, X, out, *args, **kwargs):
        # X = Fase:Cita
        horario_local = set()
        penalizacion_1 = 0
        penalizacion_2 = 0
        penalizacion_3 = 0
        penalizacion_4 = 0
        penalizacion_5 = 0
        penalizacion_6 = 0

        # Restriccion 1: Las fases deben estar asignadas al mismo día:
        if self.enrolamiento:
            dia_primero = 1
            primero = True
            for citas in X.values():
                dia_actual = citas.day
                if primero:
                    self.dia_actual = dia_primero
                    dia_primero = dia_actual
                    primero = False
                else:
                    if dia_actual != dia_primero:
                        penalizacion_1 += 100
            # Restriccion 2: El dia inicial no puede superar sumando el tiempo de espera, los dias totales
            if dia_primero + self.tiempo_espera > self.dias:
                penalizacion_2 += 1000


        # Restriccion 3: Una sala no puede contener dos citas al mismo tiempo:
        for sala in range(1, self.consultorios +1):
            citas_sala_time = np.sort(
                np.array(
                    [cita.start_time for cita in X.values() if cita.operation_room == sala]))
            start_time = 0
            for cita_time in citas_sala_time:
                if cita_time == start_time:
                    penalizacion_3 += 100
                start_time = cita_time

        # Restriccion 4: No se pueden asignar más personal del disponible en una misma hora
        for start_time in self.horas:
            # Lista que contiene todas las citas de un respectivo día y de una hora
            lista_time_day = [cita for cita in X.values() if cita.start_time == start_time]
            lista_contador = []
            for i in range(len(self.roles)):
                lista_contador.append(0)
            #Funcion que cuenta cuantos roles hay asignado a dichar hora
            penalizacion_4 += self.contador_personal(lista_contador, lista_time_day)
            penalizacion_4 += self.contador_personal_asignado(self.dia_actual, start_time, lista_contador)

            # Restriccion 5: Un mismo trabajador no puede estar en dos citas distintas a la misma hora
            for personal in lista_time_day:
                citas = [cita for cita in X.values() if cita.personal.id == personal.personal.id and cita.start_time == start_time]
                if len(citas) > 1:
                    penalizacion_5 += 100

        # Restriccion 6: Una fase anterior en el orden no puede ir después ni a la misma hora que otra que va más
        # tarde en el orden. Por ejemplo: 1ºPC y 2ºR (incorrecto)
        evaluados = set()
        for cita_i in X:
            if cita_i.fase in evaluados:
                continue
            evaluados.add(cita_i)
            hora_fin_i = X[cita_i].end_time
            for cita_j in X:
                if cita_j in evaluados:
                    continue
                hora_inicio_j = X[cita_j].start_time
                if self.fases.index(cita_i.fase) == self.fases.index(cita_j.fase) - 1 and \
                    hora_inicio_j < hora_fin_i:
                    penalizacion_6 += 100



        #Funcion Objetivo 1: Reducir tiempos de espera en citas del mismo estudio
        funcion_objetivo_1 = 0
        for cita_i in X:
            if cita_i.fase == self.fases[len(self.fases)-1]:
                continue
            hora_fin_i = X[cita_i].end_time
            for cita_j in X:
                if cita_j.fase == self.fases[0]:
                    continue
                if cita_j.fase == cita_i.fase:
                    continue
                if self.fases.index(cita_i.fase) == self.fases.index(cita_j.fase) - 1:
                    hora_inicio_j = X[cita_j].start_time
                    funcion_objetivo_1 += self.restar_horas(hora_inicio_j, hora_fin_i)
                    break

        # Funcion objetivo 2: Minimizar las horas de trabajo del grupo de trabajadores
        funcion_objetivo_2 = self.dia_actual

        # Funcion Objetivo 3: Minimizar slots ocupados (paralelizar las citas)
        # Funcion Objetivo 4: Minimizar las consultas vacias:
        funcion_objetivo_3 = 0
        for citas in X.values():
            self.insertar_horas(citas.start_time, citas.end_time, horario_local)


        for slot in horario_local:
            if slot not in horarios_dias[self.dia_actual - 1]:
                funcion_objetivo_3 += 1

        funcion_objetivo_3 += len(horarios_dias[self.dia_actual - 1])
        funcion_objetivo_4 = self.consultas_ocupadas(X)


        out["F"] = [funcion_objetivo_1, funcion_objetivo_2, funcion_objetivo_3, funcion_objetivo_4]
        out["G"] = [penalizacion_1, penalizacion_2, penalizacion_3, penalizacion_4, penalizacion_5, penalizacion_6]

    def consultas_ocupadas(self, citas):
        contador_citas = len(citas)
        citas_consulta = []

        for consulta in range(0, self.consultorios):
            citas_consulta.append(0)
            for cita in citas.values():
                if cita.operation_room == consulta + 1:
                    citas_consulta[consulta] += 1
            for citas_pasadas in slots_ocupados:
                if citas_pasadas.day == self.dia_actual:
                    contador_citas += 1
                    if citas_pasadas.operation_room == consulta + 1:
                        citas_consulta[consulta] += 1
        average = contador_citas / len(citas_consulta)
        maximum_weight = max(citas_consulta)
        minimum_weight = min(citas_consulta)

        difference = max(maximum_weight - average, average - minimum_weight)
        return difference




    def insertar_horas(self, hora_inicio, hora_fin, horario_local):
        hora_insertar = hora_inicio
        acumulacion = 0
        inicio = True

        while hora_insertar < hora_fin:
            hora_insertar = round(hora_insertar + acumulacion, 2)
            hora_entera = int(hora_insertar)
            parte_float = round(hora_insertar - hora_entera, 2)

            if parte_float == 0.6:
                hora_insertar = int(hora_insertar) + 1
            horario_local.add(hora_insertar)
            if inicio:
                acumulacion += 0.10
                inicio = False

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

    def create_combinations(self):
        for consultorio in range(1, self.consultorios + 1):
            for dia in range(1, self.dias + 1):
                for personal in self.personal:
                    for start_time in self.horas:
                        for end_time in self.horas:
                            if end_time > start_time:
                                if (end_time <= 14 and (start_time <= 14.0)) or (end_time >= 15 and (15 <= start_time)):
                                    if self.comprobar_horas(end_time, start_time):
                                        if personal.turno == "Mañana" and start_time < 15:
                                            cita = Cita(consultorio, start_time, end_time, dia, personal)
                                            if not self.check_slot(cita):
                                                self.combinations.append(cita)
                                        elif personal.turno == "Tarde" and start_time >= 15:
                                            cita = Cita(consultorio, start_time, end_time, dia, personal)
                                            if not self.check_slot(cita):
                                                self.combinations.append(cita)

    def create_combinations_next_visits(self, dia):
        for consultorio in range(1, self.consultorios + 1):
            for personal in self.personal:
                for start_time in self.horas:
                    for end_time in self.horas:
                        if self.comprobar_horas(end_time, start_time):
                            if personal.turno == "Mañana" and start_time < 15:
                                cita = Cita(consultorio, start_time, end_time, dia, personal)
                                if not self.check_slot(cita):
                                    self.combinations.append(cita)
                            elif personal.turno == "Tarde" and start_time >= 15:
                                cita = Cita(consultorio, start_time, end_time, dia, personal)
                                if not self.check_slot(cita):
                                    self.combinations.append(cita)

    def comprobar_horas(self, end_time, start_time):
        resultado = round(end_time - start_time, 2)
        for duracion in self.duracion:
            mod = (duracion % 60) * 0.01
            div = int(duracion / 60)
            duracion = div + mod
            if resultado == duracion:
                return True
        return False

    def asignar_hora(self, opcion, actividad, myinput):
        duracion = myinput[self.estudio][self.visita][actividad.fase]
        mod = (duracion % 60) * 0.01
        div = int(duracion / 60)
        duracion = div + mod
        resultado = round(opcion.end_time - opcion.start_time, 2)
        if resultado == duracion:
            return True
        return False

    def restar_horas(self, start_time, end_time):
        if end_time > start_time:
            return 100
        parte_entera_start_time = int(start_time)
        parte_entera_end_time = int(end_time)
        parte_decimal_start_time = start_time - parte_entera_start_time
        parte_decimal_end_time = end_time - parte_entera_end_time
        diferencia_entera = parte_entera_start_time - parte_entera_end_time
        diferencia_decimal = round(parte_decimal_start_time - parte_decimal_end_time, 2)
        if diferencia_decimal < 0:
            diferencia_entera -= 1
            diferencia_decimal = diferencia_decimal * (-1)
        numero = diferencia_entera + diferencia_decimal
        return numero


