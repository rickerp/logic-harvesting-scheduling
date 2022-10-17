"""
[ALC] Algorithms for Computational Logic : Project
Author: @rickerp
"""
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from pysat.pb import PBEnc


# n:            number of units
# k:            number of periods
# areas:        areas of the units
# neighbours:   dim: n x neighbours
# profits:      dim: k x n
# amin:         min area of the natural reserve


def parse_input(input_text):
    """
    @param input_text: Input text to parse
    @return: n, k, areas, neighbours, profits, amin
    """
    lines = input_text.split('\n')[:-1]  # last line is a \n
    n, k = [int(line) for line in lines[:2]]
    areas = [int(a) for a in lines[2].split(' ')]
    neighbours = [[int(i_neighbour) for i_neighbour in line.split(' ')[1:]] for line in lines[3:3 + n]]
    profits = [[int(j_pi) for j_pi in line.split(' ')] for line in lines[3 + n:3 + n + k]]
    amin = int(lines[3 + n + k])

    assert len(areas) == n
    assert len(neighbours) == n
    assert len(profits) == k and all([len(pj) == n for pj in profits])
    assert amin == int(lines[-1])

    return n, k, areas, neighbours, profits, amin


def parse_output(profit: int, harvest: list[list[int]], natural_reserve: list[int]) -> str:
    out = f"{profit}\n"

    for harvest_period in harvest:
        out += f"{len(harvest_period)}"
        if len(harvest_period) > 0:
            out += " " + " ".join(str(hp_unit) for hp_unit in harvest_period)
        out += "\n"

    out += f"{len(natural_reserve)}"
    if len(natural_reserve) > 0:
        out += " " + " ".join(str(nr_unit) for nr_unit in natural_reserve)
    out += "\n"

    return out


def define_encoding(n: int = None):
    """
    Defines the encoding to map the problem variables i, j to SAT variables
    @param n: the max of i
    @return: a function which receiving the i, j problem variables returns a number (the SAT variable) > 0
    """
    if not n:
        def nil(i, j):
            raise NotImplemented()

        return nil, nil
    else:
        def encoding_func(i, j):
            """
            Maps the problem variables i, j to SAT variables
            * if j = 0, the i unit is not harvested (and it's not a natural reserve)
            * if j = k+1, the unit is a natural reserve
            (not harvested !=
            @param i: the unit identifier
            @param j: the period number, 0 or natural reserve (k+1)
            @return: the SAT variable
            """
            return j * n + i

        def decoding_func(x: int):
            """
            Maps the SAT variable to the problem variables i, j
            @param x: SAT variable
            @return: i,j, the problem variables mapped
            """
            j = int((x - 1) / n)
            i = (x - 1) % n + 1
            return i, j

    return encoding_func, decoding_func


# Define encoding/decoding function variable globally to access it as a global variable
E, D = define_encoding()


def get_hard_clauses(n: int, k: int, areas: list[int], neighbours: list[list[int]], amin: int):
    clauses = []

    # A unit of land can only be harvested once :
    # * for each unit:
    #   * 11 -> ~12; 11 -> ~13; ...; 11 -> ~1kth (11 -> ~12 <=> ~11 V ~12)
    #   * 12 -> ~11; 12 -> ~13; ...; 12 -> ~1kth (12 -> ~11 <=> ~12 V ~11 <=> ~11 V ~12 - skip)
    #   (also include natural reserve: if natural reserve cannot be harvested - same behaviour as another period)
    for i in range(1, n + 1):
        for j_to_harvest in range(0, k + 2):
            for j_not_to_harvest in range(j_to_harvest + 1, k + 2):
                clauses.append([-E(i, j_to_harvest), -E(i, j_not_to_harvest)])

    # Neighbour units cannot be harvested in the same time period
    # * if U3 is neighbour of U1 and U4, then:
    #   * 31 -> ~11; 32 -> ~12; 33 -> ~13; ...; 3kth -> ~1kth (31 -> ~11 <=> ~31 V ~11)
    #   * 31 -> ~41; ...; 3kth -> ~4kth
    for i in range(1, n + 1):
        for i_neighbour in neighbours[i - 1]:
            if i_neighbour <= i: continue
            for j in range(1, k + 1):
                clauses.append([-E(i, j), -E(i_neighbour, j)])

    # Natural reserve must be contiguous with a minimum area size Amin >= 0

    # * Contiguous:
    # For each unit, it's grandchildren
    for i in range(1, n+1):
        i_neighbours = neighbours[i-1]
        for i_n in i_neighbours:
            i_n_neighbours = neighbours[i_n-1]
            for i_n_n in i_n_neighbours:
                i_n_n_neighbours = neighbours[i_n_n-1]
                if i not in i_n_n_neighbours:
                    clauses.append([
                        -E(i, k+1),
                        -E(i_n_n, k+1),
                        *[E(interception_i, k+1) for interception_i in set(i_neighbours).intersection(i_n_n_neighbours)]
                    ])

    # * The natural reserve area must be >= Amin
    cnf = PBEnc.atleast(
        lits=[E(i, k + 1) for i in range(1, n + 1)],
        weights=[areas[i - 1] for i in range(1, n + 1)],
        bound=amin,
        top_id=(k + 2) * n
    )
    clauses += cnf.clauses

    return clauses


def main():
    import sys
    n, k, areas, neighbours, profits, amin = parse_input(sys.stdin.read())
    # print(f"{n=}\n{k=}\n{areas=}\n{neighbours=}\n{profits=}\n{amin=}")  # debug

    # Define the encoding/decoding with a static 'n', so that we don't have to pass it everytime
    global E, D
    E, D = define_encoding(n)

    cnf = WCNF()
    cnf.extend(get_hard_clauses(n, k, areas, neighbours, amin))

    # Add soft clauses for profit
    for i in range(1, n + 1):
        for j in range(1, k + 1):
            cnf.append([E(i, j)], weight=profits[j - 1][i - 1])

    solver = RC2(cnf)
    solution = solver.compute()

    if not solution:
        raise Exception("UNSAT")

    total_profit = 0
    harvest = [[] for _ in range(0, k + 2)]
    for x in solution:
        if 0 < x <= (k + 2) * n:
            i, j = D(x)
            harvest[j].append(i)
            if 0 < j <= k:
                total_profit += profits[j - 1][i - 1]

    print(parse_output(total_profit, harvest[1:-1], harvest[-1]), end="")


if __name__ == "__main__":
    main()
