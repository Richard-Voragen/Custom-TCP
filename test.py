from joblib import Parallel, delayed
import threading
import time

def process(i):
    print(threading.get_native_id())
    time.sleep(1)
    return i * i
    
results = Parallel(n_jobs=5)(delayed(process)(i) for i in range(10))
print(results)  # prints [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]