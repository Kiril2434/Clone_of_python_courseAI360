import queue
import threading
import time
import os
from multiprocessing import Pool

def very_slow_function(x: int) -> int:
    """Function which calculates square of given number really slowly
    :param x: given number
    :return: number ** 2
    """
    time.sleep(0.3)
    return x ** 2


def calc_squares_simple(bound: int) -> list[int]:
    """Function that calculates squares of numbers in range [0; bound)
    :param bound: positive upper bound for range
    :return: list of squared numbers
    """
    return [very_slow_function(x) for x in range(bound)]

def calc_squares_multithreading(bound: int) -> list[int]:
    """Function that calculates squares of numbers in range [0; bound)
    using threading.Thread
    :param bound: positive upper bound for range
    :return: list of squared numbers
    """
    q = queue.Queue()
    threadings = [threading.Thread(target=lambda q, x: q.put((x, very_slow_function(x))), args=(q, x))
                 for x in range(bound)]
    for thread in threadings:
        thread.start()
    result = [0] * bound
    for thread in threadings:
        thread.join()
    while not q.empty():
        ind, val = q.get()
        result[ind] = val
    return result

def calc_squares_multiprocessing(bound: int) -> list[int]:
    """Function that calculates squares of numbers in range [0; bound)
    using multiprocessing.Pool
    :param bound: positive upper bound for range
    :return: list of squared numbers
    """
    number_of_cpu_cores = os.cpu_count()
    if number_of_cpu_cores is None:
         number_of_cpu_cores = 2
    with Pool(processes=number_of_cpu_cores) as pool:
        return pool.map(very_slow_function, range(bound))
