from copy import deepcopy
from itertools import product

service_demands = [
    [0.375, 0.105], # CPU
    [0.480, 0.180], # Disk 1
    [0.240, 0.000]  # Disk 2
]
num_devices = len(service_demands)
num_classes = len(service_demands[0])
mpls = [1, 3]

def change_parameters(new_service_demands: list[list[float]] = None, new_mpls: list[int] = [1, 3]) -> None:
    global service_demands, num_devices, num_classes, mpls, queue_lengths

    service_demands = new_service_demands if new_service_demands is not None else service_demands
    num_devices = len(service_demands)
    num_classes = len(service_demands[0])
    mpls = new_mpls

    queue_lengths = queue_length_estimates()

def queue_length_estimates():
    estimated_queue_lengths = []
    for i in range(num_classes):
        # Count the ammount of used devices

        used_devices = 0
        for j in range(num_devices):
            if i == 0:
                estimated_queue_lengths.append([])

            if service_demands[j][i] != 0:
                used_devices += 1

        estimate = mpls[i] / used_devices

        for j in range(num_devices):
            estimated_queue_lengths[j].append(0)
            if service_demands[j][i] != 0:
                estimated_queue_lengths[j][i] = estimate

    return estimated_queue_lengths

queue_lengths = queue_length_estimates()

def one_fewer_queue_length_multiplier(c: int) -> float:
    return (mpls[c] - 1) / mpls[c]

def queue_length(device: int, c: int = -1) -> float:
    if c == -1:
        return sum(queue_length(device, i) for i in range(2))

    return throughput(c) * response_time(device, c)

def response_time(device: int = -1, c: int = -1) -> float:
    if device == -1:
        return sum(response_time(i, c) for i in range(num_devices))

    return service_demands[device][c] * (1 + sum(queue_lengths[device][i] * (one_fewer_queue_length_multiplier(c) if i == c else 1) for i in range(num_classes)))

def throughput(c: int) -> float:
    return mpls[c] / response_time(c=c)

def approximate_mva(stopping_criterion: float = 0.001):
    global queue_lengths

    i = 0
    while True:
        print(f"Iteração: {i}")
        print("    Vazão da classe update:", throughput(0))
        print("    Vazão da classe query:", throughput(1))
        prev_queue_lengths = deepcopy(queue_lengths)
        queue_lengths = [[queue_length(device, c) for c in range(num_classes)] for device in range(num_devices)]
        max_change = max(abs(prev_queue_lengths[device][c] - queue_lengths[device][c]) for device in range(num_devices) for c in range(num_classes))
        i += 1
        if max_change < stopping_criterion:
            break
    print(f"Iteração: {i}")
    print("    Vazão da classe update:", throughput(0))
    print("    Vazão da classe query:", throughput(1))



def exact_mva():
    results = {}

    empty_population = tuple(0 for _ in range(num_classes))

    results[empty_population] = {
        "queue_lengths": [[0.0 for c in range(num_classes)] for device in range(num_devices)],
        "response_times": [0.0 for c in range(num_classes)],
        "throughputs": [0.0 for c in range(num_classes)]
    }

    populations = product(*(range(mpl + 1) for mpl in mpls))

    for population in populations:
        if population == empty_population:
            continue

        residence_times = [[0.0 for c in range(num_classes)] for device in range(num_devices)]
        response_times = [0.0 for c in range(num_classes)]
        throughputs = [0.0 for c in range(num_classes)]

        for c in range(num_classes):
            if population[c] == 0:
                continue

            # Remove one customer
            prev_population = list(population)
            prev_population[c] -= 1
            prev_population = tuple(prev_population)

            prev_queue_lengths = results[prev_population]["queue_lengths"]

            for device in range(num_devices):
                total_queue_length = sum(prev_queue_lengths[device])
                residence_times[device][c] = (service_demands[device][c] * (1 + total_queue_length))

            response_times[c] = sum(residence_times[device][c] for device in range(num_devices))
            throughputs[c] = (population[c] / response_times[c])

        queue_lengths = [[throughputs[c] * residence_times[device][c]for c in range(num_classes)] for device in range(num_devices)]

        results[population] = {
            "queue_lengths": queue_lengths,
            "response_times": response_times,
            "throughputs": throughputs
        }

    return results

if __name__ == "__main__":
    print("MVA aproximado:")
    print("")
    approximate_mva()

    results = exact_mva()[(1, 3)]

    print("")
    print("")
    print("MVA exato:")
    print("")

    print(f"Tempo de resposta da classe update: {results['response_times'][0]}")
    print(f"Vazão da classe update: {results['throughputs'][0]}")
    print(f"Tempo de resposta da classe query: {results['response_times'][1]}")
    print(f"Vazão da classe query: {results['throughputs'][1]}")



    print("\n\n\nNível de multiprogramação da classe update triplicado:\n")
    change_parameters(new_mpls=[3, 3])

    print("MVA aproximado:")
    print("")
    approximate_mva()

    results = exact_mva()[(3, 3)]

    print("")
    print("")
    print("MVA exato:")
    print("")

    print(f"Tempo de resposta da classe update: {results['response_times'][0]}")
    print(f"Vazão da classe update: {results['throughputs'][0]}")
    print(f"Tempo de resposta da classe query: {results['response_times'][1]}")
    print(f"Vazão da classe query: {results['throughputs'][1]}")
