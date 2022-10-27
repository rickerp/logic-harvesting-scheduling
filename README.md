# Harvesting Scheduling

Logical problem which involves restrictions such as contiguity, solved in two ways: using SAT solver (
pysat) [sat.py](./sat.py); SMT solver (z3-solver) [smt.py](./smt.py).  
Originally a project for my college, Instituto Superior Técnico, course, Algorithms for Computational Logic (ALC).  
The original statement of the project for SAT solving is [here](./docs/sat-statement.pdf) and for SMT solving
is [here](./docs/smt-statement.pdf) - essentially they are the same just the 'project goals' are different. Below, is a
summarized version of it.

## Run

```bash
pdm install

pdm run python sat.py < input.file > output.file  # using SAT
pdm run python smt.py < input.file > output.file  # using SMT

# test
./test/test.sh  # by default uses SMT, change inside file
```

## Summary

There are units of farming land which have different profits depending on the period which are harvested. There is also
natural reserve units which are units that cannot be harvested and must be contiguous. Each unit as a area associated
with, and there is a minimum area for the total area of the natural reserve units.

## Definitions:

* U = {1,...,n} : units of land
* Ai, i ∈ U : area of the unit of land i
* T = {1,...,k} : periods of harvesting
* Pij, i ∈ U, j ∈ T : Profit of harvesting the unit of land i

## Restrictions:

* A unit of land can only be harvested once
* Neighbour units cannot be harvested in the same time period
* Natural reserve must be contiguous with a minimum area size Amin >= 0

## Example:

```
______________________
| U1       | U2       |
|          ├----------|
├----------⏌U4 |     |
|____   |_______|___ _|
|U6 |        U5   |U7 |
|   ⎿------|------   |
|___________|_________|
```

A1 = 6 ; A2 = 3 ; A3 = 4 ; A4 = 3 ; A5 = 6 ; A6 = 4 ; A7 = 4  
U = { 1, ..., 7 };  
T = { 1, 2, 3 };

| Pi,j | U1  | U2  | U3  | U4  | U5  | U6  | U7  |
|------|-----|-----|-----|-----|-----|-----|-----|
| T1   | 5   | 1   | 4   | 5   | 5   | 1   | 1   |
| T2   | 5   | 1   | 3   | 3   | 3   | 2   | 1   |
| T3   | 4   | 1   | 3   | 4   | 3   | 2   | 1   |

Amin >= 7

### Solution:

* Total profit 18
* { U1, U2, U3, U4, U5, U6, U7 } = { 2, 1, 2, 3, 1, N, N }
    * Periods harvested (N: Natural reserve)

## Format:

### Input

* 1st line: n
* 2nd line: k
* 3rd line: Ai, i ∈ U (integers separated by a space)
* 4th line - (3+n)th line: number of neighbours of the ith unit followed by their identifiers
* (4+n)th line - (3+n+k)th line: profit of each area separated by a space of the jth period
* (4+n+k)th line: Amin

### Output

* 1st line: total profit
* 2nd line - (1+k)th line: The jth line contains the number of units harvested in the jth period
  followed by their identifiers
* (2+k)th line: The number of units that represent the natural reserve followed by their identifiers

#### Example input:

```
7
3
6 3 4 3 6 4 4
3 2 4 5
3 1 3 4
4 2 4 5 7
4 1 2 3 5
5 1 4 3 6 7
2 5 7
3 5 6 3
5 1 4 5 5 1 1
5 1 3 3 3 2 1
4 1 3 4 3 2 1
7
```

#### Example output

```
18
2 2 5
2 1 3
1 4
2 6 7
```
