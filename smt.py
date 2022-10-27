from common import parse_input
from z3 import Optimize, Bool, Int, And, If, Implies


# def define_encoding(n: int) -> Callable[[int, int], int]:


def get_hard_clauses(n: int, k: int, areas: list[int], neighbours: list[list[int]], amin: int)-> list:
    clauses = []
    u_period = [Int(f'P{i}') for i in range(1, n + 1)]
    u_depth = [Int(f'D{i}') for i in range(1, n + 1)]
    u_nr = [Bool(f'R{i}') for i in range(1, n + 1)]

    # A unit of land can only be harvested once :

    for idx, pi in enumerate(u_period):
        # Pi must have values between 0 and k
        clauses.append(And(0 <= pi, pi <= k))
        for i_n in neighbours[idx]:
            if idx + 1 > i_n:
                # Pi neighbours must not have the same value, except their value is 0
                clauses.append(If(And(pi != 0), pi != u_period[i_n-1], True))

    for pi, di in zip(u_period, u_depth):
        clauses += [0 <= di, Implies(1 <= di, pi == k + 1), Implies(pi == k + 1, 1 <= di)]
        # TODO: Must only have one root

    



    return clauses


def main():
    import sys
    n, k, areas, neighbours, profits, amin = parse_input(sys.stdin.read())

    solver = Optimize()
    solver.add(*get_hard_clauses(n, k))


if __name__ == '__main__':
    main()
