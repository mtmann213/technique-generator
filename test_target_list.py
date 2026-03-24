# Simulating the target list logic
targets = []
num_targets = 10
sticky = True

cf = 1000
bw = 5000

# Loop 1: Find target 1
if sticky:
    exists = False
    for t in targets:
        if abs(t['cf'] - cf) < 10000:
            exists = True
            break
    if not exists:
        targets.append({'cf': cf, 'bw': bw})
else:
    targets.append({'cf': cf, 'bw': bw})

if not sticky and len(targets) >= num_targets:
    pass

print(targets)
