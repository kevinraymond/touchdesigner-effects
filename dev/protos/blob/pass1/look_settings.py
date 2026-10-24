TAG = 'pass1'
VARIANTS = {
    'dancer': {},
    'plaza': {'_clip': 'plaza'},
    'plaza_gpu_grid': {'_clip': 'plaza', 'Detector': 'grid'},
    'unwired': {'_unwired': True, '_audio': 'none'},
}
RATES = {'drop_count': 1 / 4.0, 'section_count': 1 / 5.0}
WHEN = ('dancer', 'flash_env', 0.8)
AT = (1.5, 2.5, 3.5, 4.5, 5.5)
EXTRA = {}
