# DEV ONLY probe: proves dev/td.sh runs one at a time.
import time
print('lock probe ran at', time.strftime('%H:%M:%S'))
