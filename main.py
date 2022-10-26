#!/usr/bin/env python3
"""
[ALC] Algorithms for Computational Logic : Project
Author: @rickerp
"""
from pysat.card import CardEnc
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


def define_encoding(n: int = None, k: int = None):
    """
    Defines the encoding to map the problem variables i, j and d to SAT variables.
    The 'd' variable is also used to auxiliary variables
    @param n: the max of i
    @param k: the max of j
    @return: a function which receiving the i, j problem variables returns a number (the SAT variable) > 0
    """
    if not n or not k:
        def nil(i, j):
            raise NotImplemented()

        return nil, nil
    else:
        def encoding_func(i: int = None, j: int = None, d: int = None):
            """
            Maps the problem variables i, j and d to SAT variables
            * if j = 0, the i unit is not harvested (and it's not a natural reserve)
            * if j = k+1, the unit is a natural reserve
            (not harvested != natural reserve)
            @param i: the unit identifier
            @param j: the period number, 0 or natural reserve (k+1)
            @param d: (used for auxiliary variables) depth of the unit in the tree
            @return: the SAT variable
            """
            assert j != d and (j is None or d is None)

            if d is not None:
                j = k + d + 1

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
        for j_to_harvest in range(0, k + 1):
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

    # Natural reserve is contiguous, encoding: Tid tree, i unit, d depth
    # * Calculate a priori the max depth of the tree, the worst case would be for the units with less area
    # being the natural reserve (until it reaches the minimum area). This works because we always want
    # the optimal solution and if there are any conflicts in harvesting periods we can just simply consider
    # the conflict unit as non-harvested
    if amin > 0:
        max_depth = 0
        nr_min_area_sum = 0
        for i_area in sorted(areas):
            nr_min_area_sum += i_area
            max_depth += 1
            if nr_min_area_sum >= amin:
                break

        top_id = (k + max_depth + 2) * n

        # * There can only be one root: SUM(Ti1, i in U) <= 1
        cnf = CardEnc.atmost([E(i, d=1) for i in range(1, n + 1)], top_id=top_id)
        clauses += cnf.clauses
        top_id = cnf.nv

        if max_depth > 1:
            # * If a unit belongs to the tree at depth d, one and only one neighbour belongs to the tree at depth d-1 or
            # the unit it's a root: Tid -> Ti1 or SUM(Tnd-1, n in i_neighbours) = 1
            for i in range(1, n + 1):
                for d in range(2, max_depth + 1):
                    cnf = CardEnc.equals([E(i_n, d=d-1) for i_n in neighbours[i - 1]], top_id=top_id)
                    clauses += [[-E(i, d=d)] + cls for cls in cnf.clauses]
                    top_id = cnf.nv

            # * Each unit must either not belong to the tree or only be present in one level in the tree
            #   - for each unit i: SUM(Tid, d in D) <= 1
            # * If it belongs to the tree is a natural reserve
            for i in range(1, n + 1):
                cnf = CardEnc.atmost([E(i, d=d) for d in range(1, max_depth + 1)], top_id=top_id)
                clauses += cnf.clauses
                top_id = cnf.nv

        # * If a unit is a natural reserve it must be in the tree: (1)
        #   * 1R -> T11 or T12 or ... or T1m <=> ~1R or T11 or T12 or ... or T1m
        # * If a unit is in the tree it must be a natural reserve: (2)
        #   * T11 or T12 or ... or T1m -> 1R <=> (~T11 or 1R) and (~T12 or 1R) and ... and (~T1m or 1R)
        for i in range(1, n + 1):
            i_tree_vars = [E(i, d=d) for d in range(1, max_depth+1)]
            clauses.append([-E(i, j=k+1)] + i_tree_vars)  # (1)
            for i_tree_var in i_tree_vars:
                clauses.append([E(i, j=k+1), -i_tree_var])  # (2)

        # * The natural reserve area must be >= Amin >= 0
        cnf = PBEnc.atleast(
            lits=[E(i, k + 1) for i in range(1, n + 1)],
            weights=[areas[i - 1] for i in range(1, n + 1)],
            bound=amin,
            top_id=top_id
        )
        clauses += cnf.clauses

    return clauses


def main():
    import sys
    n, k, areas, neighbours, profits, amin = parse_input(sys.stdin.read())
    # print(f"{n=}\n{k=}\n{areas=}\n{neighbours=}\n{profits=}\n{amin=}")  # debug

    # Define the encoding/decoding with a static 'n', so that we don't have to pass it everytime
    global E, D
    E, D = define_encoding(n, k)

    cnf = WCNF()
    cnf.extend(get_hard_clauses(n, k, areas, neighbours, amin))

    # Add soft clauses for profit
    for i in range(1, n + 1):
        for j in range(1, k + 1):
            cnf.append([E(i, j)], weight=profits[j - 1][i - 1])

    solver = RC2(cnf, adapt=True)
    solution = solver.compute()

    if not solution:
        raise Exception("UNSAT")

    # Decoding
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
