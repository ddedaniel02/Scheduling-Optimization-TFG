"""
Clase objetos
"""


#create a surgery class with the operation room, the start time and the end time
class Cita():
    def __init__(self, operation_room, start_time, end_time, dia, personal):
        self.operation_room = operation_room # Consulta donde se alberga la cita
        self.start_time = int(start_time) # Hora de inicio de la cita
        self.end_time = int(end_time) # Hora de fin de la cita
        self.duration = self.end_time - self.start_time # Duración de la cita
        self.day = dia # Día que se hace la cita
        self.personal = personal # Personal asignado a la cita

    def __str__(self):
        return f"'Room: {self.operation_room} ST: {self.start_time} ET: {self.end_time} Dia: {self.day} Personal: [{self.personal}]'"

    def __repr__(self):
        return f"'Room: {self.operation_room} ST: {self.start_time} ET: {self.end_time} Dia: {self.day} Personal: [ {self.personal}]'"

    def __eq__(self, other):
        return self.operation_room == other.operation_room and self.start_time == other.start_time and self.end_time == other.end_time and self.day == other.day and self.day == other.day and self.personal == other.personal

    def __hash__(self):
        return hash((self.operation_room, self.start_time, self.end_time, self.day, self.personal))

#create a class for a personal, only with an id and its role
class Personal():
    def __init__(self, id, role, turno):
        self.id = id # Identificador del trabajador
        self.role = role # Rol que ejerce el trabajador
        self.turno = turno

    def __str__(self):
        return f"ID: {self.id} Role: {self.role} Turno: {self.turno}"

    def __repr__(self):
        return f"ID: {self.id} Role: {self.role} Turno: {self.turno}"

    def __eq__(self, other):
        return self.id == other.id and self.role == other.role and self.turno == other.turno

    def __hash__(self):
        return hash((self.id, self.role, self.turno))

#create a class for each activity, with the studie that its needed, the tipe of the activity and the duration and the personal needed for each activity
class Fase():
    def __init__(self, estudio, fase, paciente):
        self.estudio = estudio # Estudio en el que se basará la cita
        self.fase = fase # Que fase se está llevando a cabo en dicho estudio
        self.paciente = paciente

    def __str__(self):
        return f"'Estudio: {self.estudio} Tipo: {self.fase} Paciente: {self.paciente}'"

    def __repr__(self):
        return f"'Estudio: {self.estudio} Tipo: {self.fase} Paciente {self.paciente}'"

    def __eq__(self, other):
        return self.estudio == other.estudio and self.fase == other.tipo_actividad and self.paciente == other.paciente

    def __hash__(self):
        return hash((self.estudio, self.fase, self.paciente))

