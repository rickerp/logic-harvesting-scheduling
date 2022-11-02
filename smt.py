from common import parse_input, parse_output
from z3 import Optimize, Int, And, Implies, Sum, Bool, AtMost, Or, Not


# n:            number of units
# k:            number of periods
# areas:        areas of the units
# neighbours:   dim: n x neighbours
# profits:      dim: k x n
# amin:         min area of the natural reserve


def main():
    import sys
    n, k, areas, neighbours, profits, amin = parse_input(sys.stdin.read())
    # print(f"{n=}\n{k=}\n{areas=}\n{neighbours=}\n{profits=}\n{amin=}")  # debug

    solver = Optimize()

    periods = [[Bool(f"H{i}{j}") for j in range(1, k + 1)] for i in range(1, n + 1)]
    nr = [Bool(f"NR{i}") for i in range(1, n + 1)]
    depths = [Int(f'D{i}') for i in range(1, n + 1)]

    for idx, (i_periods, nri) in enumerate(zip(periods, nr)):
        # A unit of land can only be harvested once :
        solver.add(AtMost(*i_periods, 1))

        # Pi neighbours must not have the same value
        for i_n in neighbours[idx]:
            if idx + 1 > i_n:
                for pj_i, pj_in in zip(i_periods, periods[i_n-1]):
                    solver.add(Or(Not(pj_i), Not(pj_in)))

        # If natural reserve, cannot be harvested
        if amin > 0:
            solver.add(Implies(nri, And(*[Not(pj_i) for pj_i in i_periods])))

    if amin > 0:
        dmax = 0
        nr_min_area_sum = 0
        for i_area in sorted(areas):
            nr_min_area_sum += i_area
            dmax += 1
            if nr_min_area_sum >= amin:
                break

        for idx, (nri, di) in enumerate(zip(nr, depths)):
            solver.add(
                # 0 <= di,  # Di >= 0, Di = 0 : i does not belong to the tree, Di = d : i belongs to the tree a d level
                Implies(1 <= di, nri),  # Di >= 1 -> NR (Pi == k + 1)
                Implies(nri, 1 <= di),  # NR (Pi == k + 1) -> Di >= 1
                Implies(di > 1, Sum(*[di == depths[i_n - 1] + 1 for i_n in neighbours[idx]]) == 1),
                # i with depth d can only have 1 neighbour with depth d-1
            )

        # Must only have one root
        solver.add(Sum(*[di == 1 for di in depths]) == 1)

        # Area of natural reserve must be greater than Amin
        solver.add(Sum(*[areas[idx] * nri for idx, nri in enumerate(nr)]) >= amin)

    # Maximize profit
    solver.maximize(
        Sum(*[profits[j_idx][i_idx] * periods[i_idx][j_idx] for i_idx in range(n) for j_idx in range(k)]))

    if not solver.check():
        raise Exception("UNSAT")

    sol = solver.model()

    # Decoding
    total_profit = 0
    harvesting_periods: list[list[int]] = [[] for _ in range(k)]
    natural_reserve = []
    for i_idx, i_periods in enumerate(periods):
        for j_idx, pj_i in enumerate(i_periods):
            if sol[pj_i]:
                harvesting_periods[j_idx].append(i_idx + 1)
                total_profit += profits[j_idx][i_idx]

        if sol[nr[i_idx]]:
            natural_reserve.append(i_idx + 1)

    print(parse_output(total_profit, harvesting_periods, natural_reserve), end="")


if __name__ == '__main__':
    main()
