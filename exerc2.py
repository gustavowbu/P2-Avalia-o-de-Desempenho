import exerc1

exerc1.change_parameters([
    [0.375, 0.105], # CPU
    [0.480, 0.090], # Disk 1
    [0.240, 0.090]  # Disk 2
])

print("MVA aproximado:")
print("")
exerc1.approximate_mva()

results = exerc1.exact_mva()[(1, 3)]

print("")
print("")
print("MVA exato:")
print("")

print(f"Tempo de resposta da classe update: {results['response_times'][0]}")
print(f"Vazão da classe update: {results['throughputs'][0]}")
print(f"Tempo de resposta da classe query: {results['response_times'][1]}")
print(f"Vazão da classe query: {results['throughputs'][1]}")
