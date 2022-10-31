from common import parse_input, parse_output
from z3 import Optimize, Int, And, Implies, Sum, Bool


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

    u_period = [Int(f'P{i}') for i in range(1, n + 1)]
    u_depth = [Int(f'D{i}') for i in range(1, n + 1)]
    u_nr = [Bool(f'NR{i}') for i in range(1, n + 1)]

    # A unit of land can only be harvested once :
    for idx, (pi, nri) in enumerate(zip(u_period, u_nr)):
        # Pi must have values between 0 and k + 1
        solver.add(And(0 <= pi, pi <= k))
        solver.add(Implies(nri, pi == 0))
        for i_n in neighbours[idx]:
            if idx + 1 > i_n:
                # Pi neighbours must not have the same value, except their value is 0
                solver.add(Implies(pi != 0, pi != u_period[i_n - 1]))

    for idx, (nri, di) in enumerate(zip(u_nr, u_depth)):
        solver.add(
            0 <= di,  # Di >= 0, Di = 0 : i does not belong to the tree, Di = d : i belongs to the tree a d level
            Implies(1 <= di, nri),  # Di >= 1 -> NR (Pi == k + 1)
            Implies(nri, 1 <= di),  # NR (Pi == k + 1) -> Di >= 1
            Implies(di > 1, Sum(*[di == u_depth[i_n - 1] + 1 for i_n in neighbours[idx]]) == 1),
            # i with depth d can only have 1 neighbour with depth d-1
        )

    # Must only have one root
    solver.add(Sum(*[di == 1 for di in u_depth]) == 1)

    # Area of natural reserve must be greater than Amin
    solver.add(Sum(*[areas[idx] * nri for idx, nri in enumerate(u_nr)]) >= amin)

    # Maximize profit
    solver.maximize(
        Sum(*[profits[j - 1][i_idx] * (pi == j) for i_idx, pi in enumerate(u_period) for j in range(1, k + 1)]))

    if not solver.check():
        raise Exception("UNSAT")

    sol = solver.model()

    # Decoding
    total_profit = 0
    harvesting_periods: list[list[int]] = [[] for _ in range(k)]
    natural_reserve = []
    for i_idx, (pi, nri) in enumerate(zip(u_period, u_nr)):
        j = sol[pi].as_long()
        if 0 < j:
            harvesting_periods[j - 1].append(i_idx + 1)
            total_profit += profits[j - 1][i_idx]
        elif sol[nri]:
            natural_reserve.append(i_idx + 1)

    print(parse_output(total_profit, harvesting_periods, natural_reserve), end="")


if __name__ == '__main__':
    main()
