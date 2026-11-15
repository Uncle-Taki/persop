from pathlib import Path
root=Path(__file__).resolve().parents[1]
canonical=(root/'persob/docs/openapi.yaml').read_bytes()
assert canonical==(root/'persob/internal/api/openapi.yaml').read_bytes(), 'Run persob/scripts/sync-openapi.py'
print('Canonical and embedded API specifications match.')
