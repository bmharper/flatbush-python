import unittest
import random
import time
from flatbush import FlatBush, Box


class TestFlatBush(unittest.TestCase):
    def test_validate(self):
        f = FlatBush()
        boxes = []
        dim = 100
        index = 0
        for x in range(dim):
            for y in range(dim):
                boxes.append(Box(index, x + 0.1, y + 0.1, x + 0.9, y + 0.9))  # Keep our own copy of the box for brute force validation
                checkIndex = f.add(x + 0.1, y + 0.1, x + 0.9, y + 0.9)
                assert checkIndex == index
                index += 1
        f.finish()

        n_checked = 0
        for _ in range(1000):
            maxQueryWindow = 5
            minx = random.uniform(0, dim)
            miny = random.uniform(0, dim)
            maxx = minx + random.uniform(0, maxQueryWindow)
            maxy = miny + random.uniform(0, maxQueryWindow)
            results = f.search(minx, miny, maxx, maxy)
            # brute force validation that there are no false negatives
            qbox = Box(0, minx, miny, maxx, maxy)
            for box in boxes:
                if box.positive_union(qbox):
                    # if object crosses the query rectangle, then it should be included in the result set
                    n_checked += 1
                    found = False
                    for b in results:
                        if b == box.index:
                            found = True
                            break
                    assert found, "Failed to find box in result set"
        assert n_checked != 0, "Unit test didn't actually check anything"

    def test_benchmark(self):
        f = FlatBush()
        dim = 500
        start = time.perf_counter()
        for x in range(dim):
            for y in range(dim):
                f.add(x + 0.1, y + 0.1, x + 0.9, y + 0.9)
        f.finish()
        print(f"Time to insert {dim * dim} elements: {1000 * (time.perf_counter() - start)} milliseconds")

        start = time.perf_counter()
        nquery = 100 * 1000
        results = []
        sx = 0
        sy = 0
        nresults = 0
        for _ in range(nquery):
            minx = sx % dim
            miny = sy % dim
            maxx = minx + 3.0
            maxy = miny + 3.0
            results = f.search(minx, miny, maxx, maxy)
            nresults += len(results)
            sx += 5
            sy += 7
        print(f"Time per query returning average of {round(nresults / nquery)} elements: {(1000000.0 / nquery) * (time.perf_counter() - start)} microseconds")


if __name__ == '__main__':
    unittest.main()
