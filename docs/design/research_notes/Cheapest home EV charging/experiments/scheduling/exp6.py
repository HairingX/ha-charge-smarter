"""Exp 6: pure-Python min-cost flow (networkx network_simplex) on the constant-power model.

Transportation form: slots supply up to u_t (cost p_t), targets demand their increment;
arc slot->target when the slot precedes the target's deadline. Integer units of 0.1 kWh."""
import time, random, networkx as nx
def build(T, K, u, seed=1):
    rng = random.Random(seed)
    G = nx.DiGraph()
    ds = sorted(rng.sample(range(T // (K + 1), T), K))
    inc = [rng.choice([50, 100, 150]) for _ in ds]  # 5-15 kWh in 0.1 kWh units
    total = sum(inc)
    G.add_node("s", demand=-total)
    for t in range(T):
        G.add_edge("s", ("t", t), capacity=u, weight=int(rng.uniform(0, 300) * 100))
        for k, d in enumerate(ds):
            if t < d:
                G.add_edge(("t", t), ("k", k), weight=0)
    for k, d in enumerate(ds):
        G.add_node(("k", k), demand=inc[k])
    return G
for T, u in [(168, 110), (672, 28)]:
    for K in (6, 20):
        G = build(T, K, u)
        best = 1e9
        for _ in range(3):
            t0 = time.perf_counter(); cost, flow = nx.network_simplex(G); best = min(best, time.perf_counter() - t0)
        print("network_simplex T=%d K=%d arcs=%d: %.0f ms" % (T, K, G.number_of_edges(), best * 1000))
