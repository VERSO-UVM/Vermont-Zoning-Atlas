import json

with open('analysis/fgb_comparison/fgb_recovery_full.json', 'r') as f:
    data = json.load(f)

print('=== FGB DATA RECOVERY ANALYSIS RESULTS ===\n')
print('Summary:')
for key, val in data['summary'].items():
    print(f'  {key}: {val}')

print(f'\n=== TOP 20 RECOVERABLE FILES ===')
recovered = []
seen = set()
for r in data['recoverable_details']:
    if r['file'] not in seen:
        recovered.append(r)
        seen.add(r['file'])

for r in sorted(recovered, key=lambda x: x['gain'], reverse=True)[:20]:
    print(f"{r['file']}: +{r['gain']} props ({r['current']} -> {r['fgb']})")
    print(f"  District: {r['district']}")
