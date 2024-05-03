from pymoo.operators.mutation.pm import PolynomialMutation
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter
import matplotlib.pyplot as plt
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.mixed import MixedVariableMating, MixedVariableSampling, MixedVariableDuplicateElimination
import matplotlib
from Programación_Mensual import MultiObjectiveMixedVariableProblem

matplotlib.use('TkAgg')

# class MyRepair(Repair):
#     def _do(self, problem, X, **kwargs):
#         print(X)
#         # print(problem)
#         return X



problem = MultiObjectiveMixedVariableProblem()

algorithm = NSGA2(pop_size=10,
                  sampling=MixedVariableSampling(),
                  mating=MixedVariableMating(eliminate_duplicates=MixedVariableDuplicateElimination()),
                  mutation=PolynomialMutation(prob=0.1),
                  eliminate_duplicates=MixedVariableDuplicateElimination(),
                  )


#
# # algorithm = MixedVariableGA(pop=250, survival=RankAndCrowding(), repair = MyRepair())
#
#
res = minimize(problem,
               algorithm,
               termination=('n_gen', 10),
               seed=2,
               verbose=True)
X = res.pop
X = res.X
F = res.F
G = res.G


plot = Scatter()
plot.add(problem.pareto_front(), plot_type="line", color="black", alpha=0.7)
plot.add(F, facecolor="none", edgecolor="red")
plot.title = "Frente de Pareto"
plot.show()

print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))



plt.figure(figsize=(7, 5))
plt.scatter(F[:, 0], F[:, 1], s=30, facecolors='none', edgecolors='blue')
plt.title("Objective Space")
plt.show()

fl = F.min(axis=0)
fu = F.max(axis=0)
# print(f"Scale f1: [{fl[0]}, {fu[0]}]")
# print(f"Scale f2: [{fl[1]}, {fu[1]}]")

approx_ideal = F.min(axis=0)
approx_nadir = F.max(axis=0)

plt.figure(figsize=(7, 5))
plt.scatter(F[:, 0], F[:, 1], s=30, facecolors='none', edgecolors='blue')
plt.scatter(approx_ideal[0], approx_ideal[1], facecolors='none', edgecolors='red', marker="*", s=100, label="Ideal Point (Approx)")
plt.scatter(approx_nadir[0], approx_nadir[1], facecolors='none', edgecolors='black', marker="p", s=100, label="Nadir Point (Approx)")
plt.title("Puntos Nadir e Ideal (Approx)")
plt.legend()
plt.show()

nF = (F - approx_ideal) / (approx_nadir - approx_ideal)

fl = nF.min(axis=0)
fu = nF.max(axis=0)
# print(f"Scale f1: [{fl[0]}, {fu[0]}]")
# print(f"Scale f2: [{fl[1]}, {fu[1]}]")

plt.figure(figsize=(7, 5))
plt.scatter(nF[:, 0], nF[:, 1], s=30, facecolors='none', edgecolors='blue')
plt.title("Frente de Pareto (Normalizado)")
plt.show()

weights = np.array([0.5, 0.5])

from pymoo.decomposition.asf import ASF

decomp = ASF()

i = decomp.do(nF, 1/weights).argmin()

print("Best regarding ASF: Point \ni = %s\nF = %s \nX = %s" % (i, F[i], X[i]))

plt.figure(figsize=(7, 5))
plt.scatter(F[:, 0], F[:, 1], s=30, facecolors='none', edgecolors='blue')
plt.scatter(F[i, 0], F[i, 1], marker="x", color="red", s=200)
plt.title("Solución Subóptima Elegida por ASF")
plt.show()