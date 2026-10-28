# Scheduling experiments

The experiments behind `../../scheduling_algorithm.md`: the planned two-pass greedy, corrected
greedy variants and an exact dynamic programme, compared on random and real instances.

`model.py` holds the model and the algorithms; each `exp*.py` starts with a docstring saying what
it tests. Run them from this folder with Python 3.13 or later:

```bash
python3 exp1.py
```

`exp3.py` and `exp5.py` take a JSON file of DK1 day-ahead prices from Energi Data Service's API,
with a `records` list whose rows hold `HourDK` and `SpotPriceEUR`, as their first argument.
`exp6.py` needs networkx. Timings in `exp4.py` depend on the machine.
