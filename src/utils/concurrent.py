import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)


def run_in_parallel(callables: list[Callable], args_list: list[tuple] = []):
    results = [None] * len(callables)

    args_list = args_list if args_list else [[] for _ in range(len(callables))]
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(callable, *args): i for i, (callable, args) in enumerate(zip(callables, args_list))}
        
        for future in futures:
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as e:
                logger.error(f"{e=}")
    
    return results


if __name__ == "__main__":
    import random
    from time import sleep
    def test_func(x: int = 1):
        sleep(random.random())
        if random.random() > 0.5:
            raise Exception()
        return x*x
    funcs = [test_func for _ in range(12)]
    args = [(x, ) for x in range(12)]
    result = run_in_parallel(funcs, args)