from line_solver import *
import matplotlib.pyplot as plt

def solve(method, query_rate=3.0, cpu_speed=1, d1_speed=1, terminals=50):
    model = Network("Transactions")

    source = Source(model, "Source")
    sink = Sink(model, "Sink")
    think = Delay(model, "Think")

    cpu = Queue(model, "CPU", SchedStrategy.PS)
    d1 = Queue(model, "Disk1", SchedStrategy.PS)
    d2 = Queue(model, "Disk2", SchedStrategy.PS)

    q = OpenClass(model, "Query")
    u = OpenClass(model, "Update")
    i = ClosedClass(model, "Interactive", terminals, think)

    source.set_arrival(q, Exp(query_rate))
    source.set_arrival(u, Exp(1.5))

    cpu.set_service(q, Exp(cpu_speed / 0.06))
    d1.set_service(q, Exp(d1_speed / 0.030))
    d2.set_service(q, Exp(1 / 0.06))

    cpu.set_service(u, Exp(cpu_speed / 0.10))
    d1.set_service(u, Exp(d1_speed / 0.030))
    d2.set_service(u, Exp(1 / 0.09))

    cpu.set_service(i, Exp(cpu_speed / 0.09))
    d1.set_service(i, Exp(d1_speed / 0.045))
    think.set_service(i, Exp(1 / 15))

    P = model.init_routing_matrix()

    for job in (q, u):
        P.set(job, job, source, cpu, 1.0)
        P.set(job, job, cpu, d1, 0.5)
        P.set(job, job, cpu, d2, 0.5)
        P.set(job, job, d1, sink, 1.0)
        P.set(job, job, d2, sink, 1.0)

    P.set(i, i, think, cpu, 1.0)
    P.set(i, i, cpu, d1, 1.0)
    P.set(i, i, d1, think, 1.0)

    model.link(P)
    return MVA(model, method=method, iter_tol=0.001, verbose=0).avg_table()


def response_times(table):
    if hasattr(table, "data"):
        table = table.data

    station_col = "Station" if "Station" in table.columns else "Node"

    def rt(station, job):
        return table.loc[
            (table[station_col] == station) &
            (table["JobClass"] == job), "RespT"
        ].iloc[0]

    return {
        "Query": rt("CPU", "Query")
                 + 0.5 * rt("Disk1", "Query")
                 + 0.5 * rt("Disk2", "Query"),
        "Update": rt("CPU", "Update")
                  + 0.5 * rt("Disk1", "Update")
                  + 0.5 * rt("Disk2", "Update"),
        "Interactive": rt("CPU", "Interactive")
                       + rt("Disk1", "Interactive")
    }


# (a) Baseline response times

print("Exato:")
print(solve("exact"))

print("Aproximado:")
print(solve("qd"))

base = response_times(solve("exact"))

print("\n(a) Tempo médio de resposta:")
for job, time in base.items():
    print(f"{job}: {time:.4f}s")


# (b) Increase Query arrival rate by 95%

high_load = response_times(solve("exact", query_rate=3 * 1.95))

print("\n(b) Tempos de resposta com taxa de chegada de queries aumentada em 95%:")
for job in base:
    change = (high_load[job] / base[job] - 1) * 100
    print(f"{job}: {base[job]:.4f} -> {high_load[job]:.4f}s ({change:+.1f}%)")


# (c) Hardware upgrades

disk_upgrade = response_times(solve("exact", query_rate=5.85, d1_speed=2))
cpu_upgrade = response_times(solve("exact", query_rate=5.85, cpu_speed=2))

print("\n(c) Tempos de resposta com melhorias de hardware:")
print("Disco1 2x mais rápido:")
for job in base:
    d1_gain = (high_load[job] - disk_upgrade[job]) / high_load[job] * 100

    print(f"  {job}: = {disk_upgrade[job]:.4f}s ({d1_gain:.1f}% mais rápido)")
print("CPU 2x mais rápida:")
for job in base:
    cpu_gain = (high_load[job] - cpu_upgrade[job]) / high_load[job] * 100

    print(f"  {job}: = {cpu_upgrade[job]:.4f}s ({cpu_gain:.1f}% mais rápido)")


# (d) Response time vs. number of terminals

print("\n(d) Número máximo de terminais:")

interactive_times = []

user_input = True
range_start = 50
while user_input:
    if interactive_times != [] and interactive_times[-1] >= 1.5:
        break
    else:
        terminal_range = range(range_start, range_start + 201)
        interactive_times = []
        for terminals in terminal_range:
            times = response_times(solve("exact", query_rate=5.85, cpu_speed=2, terminals=terminals))
            interactive_times.append(times["Interactive"])

        supported = [n for n, t in zip(terminal_range, interactive_times) if t < 1.5]

        n = max(supported)
        print(f"Entre {range_start} e {range_start + 200}:")
        print(f"{n} terminais")
        print(f"Tempo de resposta: {interactive_times[n - range_start]:.4f}s")

        plt.plot(list(terminal_range), interactive_times)
        plt.axhline(1.5, color="red", linestyle="--", label="limite de 1.5s")
        plt.xlabel("Número de terminais")
        plt.ylabel("Tempo de resposta da classe Interactive (segundos)")
        plt.title("Tempo de resposta da classe Interactive vs. Número de terminais")
        if range_start == 50:
            plt.yticks([i / 10 for i in range(0, 17, 1)])
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

        if interactive_times[-1] < 1.5:
            user_input = input("\nO número máximo de terminais está além dessa faixa de valores.\nContinuar procurando?\nPressione Enter para continuar ou digite 'n' para parar.\n")
            user_input = user_input != "n"
            range_start += 150
