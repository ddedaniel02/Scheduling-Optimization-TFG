from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Choice
from objetos_variables_visitas import Cita, Fase, Personal
import numpy as np
import random

slots_ocupados = []
lista_contador = [0, 0, 0, 0]



class MultiObjectiveMixedVariableProblem(ElementwiseProblem):

    def __init__(self, estudio, visita, identificador_paciente, myinput, conteo_dias, **kwargs):
        """Implementación de los parámetros"""


        # Número de consultas disponibles
        self.consultorios = myinput["n_consultorios"]
        self.fases = []
        for keys in myinput["horario_atencion"][visita]:
            self.fases.append(keys)
        self.roles = myinput["roles"]
        self.recursos = myinput["personal"]

        self.duracion = [duracion for duracion in myinput["horario_atencion"][visita].values()]

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
            self.actividades.append(Fase(estudio, visita, fase, identificador_paciente))
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
        waiting_day = self.check_day(visita, myinput)
        if waiting_day == 0:
            print("Visita inicial")
            print("Waiting day: ", waiting_day)
            self.create_combinations(myinput)
        else:
            print("Visitas venideras")
            print("Waiting day: ", waiting_day)
            self.create_next_visit(waiting_day, conteo_dias)


        #print(self.combinations)
        # Se filtran aquellas variables que sabemos de antemano que no serán válidas
        for actividad in self.actividades:
            opciones = []
            for opcion in self.combinations:
                if self.asignar_hora(opcion, actividad, myinput, visita):
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
        for value in X.values():
            day = value.day
            break

        # Restriccion 1: Una sala no puede contener dos citas al mismo tiempo:
        for sala in range(1, self.consultorios +1):
            citas_sala_time = np.sort(
                np.array(
                    [cita.start_time for cita in X.values() if cita.operation_room == sala]))
            start_time = 0
            for cita_time in citas_sala_time:
                if cita_time == start_time:
                    penalizacion_1 += 100
                start_time = cita_time

        # Restriccion 2: No se pueden asignar más personal del disponible en una misma hora
        for start_time in self.horas:
            # Lista que contiene todas las citas de un respectivo día y de una hora
            lista_time_day = [cita for cita in X.values() if cita.start_time == start_time]
            lista_contador = []
            for i in range(len(self.roles)):
                lista_contador.append(0)
            #Funcion que cuenta cuantos roles hay asignado a dichar hora
            penalizacion_2 += self.contador_personal(lista_contador, lista_time_day)
            penalizacion_2 += self.contador_personal_asignado(day, start_time, lista_contador)

            # Restriccion 3: Un mismo trabajador no puede estar en dos citas distintas a la misma hora
            for personal in lista_time_day:
                citas = [cita for cita in X.values() if cita.personal.id == personal.personal.id and cita.start_time == start_time]
                if len(citas) > 1:
                    penalizacion_3 += 100

        # Restriccion 4: Una fase anterior en el orden no puede ir después ni a la misma hora que otra que va más
        # tarde en el orden. Por ejemplo: 1ºPC y 2ºR (incorrecto)
        evaluados = set()
        for cita_i in X:
            if cita_i.fase in evaluados:
                continue
            evaluados.add(cita_i)
            hora_inicio_i = X[cita_i].start_time
            for cita_j in X:
                if cita_j in evaluados:
                    continue
                hora_inicio_j = X[cita_j].start_time
                if self.fases.index(cita_i.fase) == self.fases.index(cita_j.fase) - 1 and hora_inicio_i >= hora_inicio_j:
                    penalizacion_4 += 100



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
        list_consultorios = []
        for cita in X.values():
            if cita.operation_room not in list_consultorios:
                list_consultorios.append(cita.operation_room)
        funcion_objetivo_2 = len(list_consultorios)


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

    def check_day(self, visita, myinput):
        waiting_days = 0
        if myinput["tiempos_espera"].get(visita) != None:
            waiting_days = myinput["tiempos_espera"].get(visita)
        return waiting_days

    def create_combinations(self, myinput):
        day_found = False
        dia = 1
        while not day_found:
            dia = random.randint(1, self.dias + 1)
            print("Dia: ", dia)
            tiempo_espera = 0
            for tiempo in myinput["tiempos_espera"].values():
                tiempo_espera += tiempo
            if dia + tiempo_espera <= self.dias:
                day_found = True

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

    def create_next_visit(self, waiting_days, conteo_dias):
        dia = conteo_dias + waiting_days
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
            if duracion == 60:
                duracion = 1
            else:
                duracion = duracion * 0.01
            if resultado == duracion:
                return True
        return False

    def asignar_hora(self, opcion, actividad, myinput, visita):
        duracion = myinput["horario_atencion"][visita][actividad.fase]
        if duracion == 60:
            duracion = 1
        else:
            duracion = duracion * 0.01
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


