Como usar:
En primer lugar hay 4 programas que forman el funcionamiento del programa: Dos relacionados con el algoritmo y los 
otros dos con respecto a impresión de soluciones. Además esta el json input_visitas donde podrás personalizar
los aspectos de la cita:
- input_json: En este json (dentro de Programacion de Citas Pacientes)
podrás modificar la mayoría de los datos, con especial cuidado de no cambiar ciertas claves
que se usarán para acceder al recurso en nuestro algoritmo. Además es importante que mantenga lógica entre si.
A continuación los cambios que se pueden hacer:
  - n_personas: puedes cambiar las personas asignadas a cada estudio (si añades un estudio tienes que añadir su 
  correspondiente clave y pacientes asignados)
  - n_consultorios: puedes cambiar el número de consultorios
  - Estudio: visita: fase: duracion-> puedes cambiar lo que quieras, pero recuerda que mantenga consistencia, es decir,
  si añades un estudio, asignar en n_personas el número de pacientes asociados, si añades o eliminas visitas que no haya
  que tengan fases dentro con su correspondiente duración, si añades fases, asignarles más abajo responsables que se hagan
  cargo, si modificas la duración siempre en minutos por favor y en multiplos de 10. Es importante que al añadir una visita
  se especifique a través de la clave "tiempo_espera" el número de días que tiene que pasar para hacer dicha visita,
  no se considera una fase pero es esencial que se incluya para la lógica y facilita la interpretación para el programa
  - roles: puedes añadir los que quieras manteniendo la consistencia con personal y cargos
  - personal: basado en los roles definidos puedes cambiar el número de trabajadores por cada rol según como desees
  - cargos: segun las fases y roles definidos puedes ajustar la carga como quieras, conservando la lógica
  - n_dias: puedes poner los días que quieras (te aconsejo dejar 30 días, cuantos más pongas más lenta será la ejecución)
  - hora_inicio y hora_fin: te aconsejo dejar la jornada como esta pero puedes poner la que quieras (deben ser siempre
  en formato hora)

Dentro de Programacion_de_Citas_Pacientes está el programa mensuañ_visitas.py que incluye toda la definición del problema
y el método de evaluación donde se procesa si cumple las restricciones y optimiza las funciones objetivo. Más o menos 
está comentado que es cada cosa pero aun falta trabajo detrás. Si hay algo que no entiendes muy bien no dudes en 
preguntarme

Finalmente está main_visitas.py donde está toda la parte que llama a las librerias de pymoo, crea el problema, llama
a la funcion de minimize y después procesa las soluciones. Para separarlo en módulos se llama a numerosas funciones del
programa crear_estadisticas que escribe en distintos ficheros las soluciones y después está representacion_sols_visitas
que incluye toda la lógica para crear una gráfica con la agenda del paciente (aunque tiene que refinarse ya que no
es muy visual). Si quieres iniciar el programa ejecuta main_visitas.py

Para ver las soluciones tienes tres carpetas donde se almacena: resultados_citas_paciente_graficos, que almacena
estas representaciones visuales de las citas de los pacientes
resultados_citas_dia: que contiene todas las citas puestas en cada una de los dias (cada fichero será un día) que viene
información de interés asi como ciertas estadísticas finales
resultados_citas_pacientes: que viene todas las citas que tiene cada paciente y muestra las horas de espera (u horas 
muertas, es decir, horas que tiene que esperar entre fase y fase) totales en todo el recorrido del paciente por el estudio

Eso sería el resumen de todo, igualmente en el capítulo de analisis de la memoria del TFG se explica con más detalle cada
concepto por si tienes dudas.