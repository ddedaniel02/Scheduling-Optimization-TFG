import json


def load_json():
    with open("parametros_algoritmo.json", "r") as file:
        myparameters = json.load(file)
    return myparameters


def non_negative_number(number, topic):
    if topic != "tiempo_espera":
        if number <= 0 or type(number) != int:
            raise ValueError(topic + ": must be a positive integer")
    else:
        if number < 0 or type(number) != int:
            raise ValueError(topic + ": must be a positive integer")

def correct_minutes(minutes, topic):
    if topic != "tiempo_espera":
        if minutes <= 0 or minutes % 10 != 0:
            raise ValueError(topic + ": must be positive and multiple of 10")
    else:
        non_negative_number(minutes, topic)


def correct_percentage(percentage, topic):
    if percentage <= 0.0 or percentage > 1.0:
        raise ValueError(topic + ": must be between 0.0 and 1.0")


def load_number(key):
    my_parameter = load_json()
    non_negative_number(my_parameter[key], key)
    return my_parameter[key]


def load_percentage(key):
    my_parameter = load_json()
    correct_percentage(my_parameter[key], key)
    return my_parameter[key]


def validar_pacientes(n_personas, lista_estudios):
    for estudio in n_personas:
        non_negative_number(n_personas[estudio], "n_personas")
        if estudio not in lista_estudios:
            lista_estudios.append(estudio)
        else:
            raise ValueError("studies cannot be repeated")


def validar_visitas(myinput, lista_estudios):
    lista_fases = set()
    if len(lista_estudios) <= 0:
        raise ValueError("Must specify studies")
    for estudio in lista_estudios:
        try:
            lista_visitas = myinput[estudio]
            for visitas in lista_visitas:
                visita = myinput[estudio][visitas]
                for fase in visita:
                    correct_minutes(myinput[estudio][visitas][fase], fase)
                    lista_fases.add(fase)
        except Exception as e:
            raise e
    return lista_fases


def validar_roles(conjunto_roles, topic):
    lista_roles = []
    for rol in conjunto_roles:
        if type(rol) != str:
            raise TypeError(topic + ": must be a string")
        if rol not in lista_roles:
            lista_roles.append(rol)
        else:
            raise ValueError(topic + ": cannot be repeated in the list")
    return lista_roles


def validar_personal(personal, lista_roles):
    if len(lista_roles) < 0:
        raise ValueError("roles cannot be empty")
    for rol in lista_roles:
        try:
            non_negative_number(personal[rol], rol)
        except Exception as e:
            raise e


def validar_cargos(cargos, lista_fases, lista_roles):
    for rol in lista_roles:
        try:
            for fase in cargos[rol]:
                lista_fases.remove(fase)
        except Exception as e:
            raise e
    lista_fases.remove("tiempo_espera")
    if len(lista_fases) > 0:
        raise ValueError("All phases must be asigned to roles")


def validar_horas(hora_inicio, hora_fin):
    if type(hora_inicio) != int or hora_inicio < 0 or hora_inicio > 23:
        raise ValueError("start_time must be an integer and between 0 and 23")
    if type(hora_fin) != int or hora_fin < 0 or hora_fin > 23:
        raise ValueError("end_time must be an integer and between 0 and 23")
    if hora_inicio >= hora_fin:
        raise ValueError("start_time must be smaller than end_time")


def validar_parametros(myinput):
    lista_estudios = []
    validar_pacientes(myinput["n_personas"], lista_estudios)
    non_negative_number(myinput["n_consultorios"], "n_consultorios")
    lista_fases = validar_visitas(myinput, lista_estudios)
    lista_roles = validar_roles(myinput["roles"], "n_roles")
    validar_personal(myinput["personal"], lista_roles)
    validar_cargos(myinput["cargos"], lista_fases, lista_roles)
    non_negative_number(myinput["n_dias"], "n_dias")
    validar_horas(myinput["hora_inicio"], myinput["hora_fin"])
