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
