from __future__ import annotations
from typing import List, Tuple
import sys


class Box:
    def __init__(self, index: int, min_x: float, min_y: float, max_x: float, max_y: float):
        self.index = index
        self.min_x: float = min_x
        self.min_y: float = min_y
        self.max_x: float = max_x
        self.max_y: float = max_y

    @staticmethod
    def inverted() -> Box:
        return Box(-1, sys.float_info.max, sys.float_info.max, -sys.float_info.max, -sys.float_info.max)

    def positive_union(self, b: Box) -> bool:
        return b.max_x >= self.min_x and b.min_x <= self.max_x and b.max_y >= self.min_y and b.min_y <= self.max_y


class FlatBush:
    def __init__(self):
        self.boxes: List[Box] = []
        self.bounds: Box = Box.inverted()
        self.hilbert_values: List[int] = []
        self.level_bounds: List[int] = []
        self.num_items: int = 0
        self.node_size: int = 16

    def size(self) -> int:
        return self.num_items

    def add(self, rect: Tuple(float, float, float, float)) -> int:
        index = len(self.boxes)
        self.boxes.append(Box(index, rect[0], rect[1], rect[2], rect[3]))
        self.bounds.min_x = min(self.bounds.min_x, rect[0])
        self.bounds.min_y = min(self.bounds.min_y, rect[1])
        self.bounds.max_x = max(self.bounds.max_x, rect[2])
        self.bounds.max_y = max(self.bounds.max_y, rect[3])
        return index

    def finish(self):
        if len(self.boxes) == 0:
            return

        if self.node_size < 2:
            self.node_size = 2

        self.num_items = len(self.boxes)

        # calculate the total number of nodes in the R-tree to allocate space for
        # and the index of each tree level (used in search later)
        n = self.num_items
        numNodes = n
        self.level_bounds.append(n)
        while True:
            n = (n + self.node_size - 1) // self.node_size
            numNodes += n
            self.level_bounds.append(numNodes)
            if n == 1:
                break

        width = self.bounds.max_x - self.bounds.min_x
        height = self.bounds.max_y - self.bounds.min_y

        hilbertMax = (1 << 16) - 1

        # map item centers into Hilbert coordinate space and calculate Hilbert values
        for i in range(len(self.boxes)):
            b = self.boxes[i]
            x = hilbertMax * ((b.min_x + b.max_x) / 2 - self.bounds.min_x) / width
            y = hilbertMax * ((b.min_y + b.max_y) / 2 - self.bounds.min_y) / height
            self.hilbert_values.append(hilbert_xy_to_index(16, int(x), int(y)))

        # sort items by their Hilbert value (for packing later)
        sort_boxes(self.hilbert_values, self.boxes, 0, len(self.boxes) - 1)

        # generate nodes at each tree level, bottom-up
        pos = 0
        for i in range(len(self.level_bounds) - 1):
            end = self.level_bounds[i]

            # generate a parent node for each block of consecutive <nodeSize> nodes
            while pos < end:
                nodeBox = Box.inverted()
                nodeBox.index = pos

                # calculate bbox for the new node
                j = 0
                while j < self.node_size and pos < end:
                    box = self.boxes[pos]
                    pos += 1
                    nodeBox.min_x = min(nodeBox.min_x, box.min_x)
                    nodeBox.min_y = min(nodeBox.min_y, box.min_y)
                    nodeBox.max_x = max(nodeBox.max_x, box.max_x)
                    nodeBox.max_y = max(nodeBox.max_y, box.max_y)
                    j += 1

                # add the new node to the tree data
                self.boxes.append(nodeBox)

    def search(self, minX: float, minY: float, maxX: float, maxY: float) -> List[int]:
        if len(self.level_bounds) == 0:
            # Remember, you must call finish() before you can search
            return []

        results: List[int] = []

        queue: List[int] = []
        queue.append(len(self.boxes) - 1)  # nodeIndex
        queue.append(len(self.level_bounds) - 1)  # level

        while len(queue) != 0:
            nodeIndex = queue[len(queue) - 2]
            level = queue[len(queue) - 1]
            queue.pop()
            queue.pop()

            # find the end index of the node
            end = min(nodeIndex + self.node_size, self.level_bounds[level])

            # search through child nodes
            for pos in range(nodeIndex, end):
                # check if node bbox intersects with query bbox
                if maxX < self.boxes[pos].min_x or maxY < self.boxes[pos].min_y or minX > self.boxes[pos].max_x or minY > self.boxes[pos].max_y:
                    continue
                if nodeIndex < self.num_items:
                    # leaf item
                    results.append(self.boxes[pos].index)
                else:
                    # node; add it to the search queue
                    queue.append(self.boxes[pos].index)
                    queue.append(level - 1)

        return results


# custom quicksort that sorts bbox data alongside the hilbert values
def sort_boxes(values: List[int], boxes: List[Box], left: int, right: int):
    if left >= right:
        return

    pivot = values[(left + right) >> 1]
    i = left - 1
    j = right + 1

    while True:
        while True:
            i += 1
            if values[i] >= pivot:
                break
        while True:
            j -= 1
            if values[j] <= pivot:
                break
        if i >= j:
            break
        values[i], values[j] = values[j], values[i]
        boxes[i], boxes[j] = boxes[j], boxes[i]

    sort_boxes(values, boxes, left, j)
    sort_boxes(values, boxes, j + 1, right)


# From https://github.com/rawrunprotected/hilbert_curves (public domain)
def interleave(x: int) -> int:
    x = (x | (x << 8)) & 0x00FF00FF
    x = (x | (x << 4)) & 0x0F0F0F0F
    x = (x | (x << 2)) & 0x33333333
    x = (x | (x << 1)) & 0x55555555
    return x


def hilbert_xy_to_index(n: int, x: int, y: int) -> int:
    x = x << (16 - n)
    y = y << (16 - n)

    A, B, C, D = 0, 0, 0, 0

    # Initial prefix scan round, prime with x and y
    a = x ^ y
    b = 0xFFFF ^ a
    c = 0xFFFF ^ (x | y)
    d = x & (y ^ 0xFFFF)

    A = a | (b >> 1)
    B = (a >> 1) ^ a

    C = ((c >> 1) ^ (b & (d >> 1))) ^ c
    D = ((a & (c >> 1)) ^ (d >> 1)) ^ d

    # phase 2
    a = A
    b = B
    c = C
    d = D

    A = ((a & (a >> 2)) ^ (b & (b >> 2)))
    B = ((a & (b >> 2)) ^ (b & ((a ^ b) >> 2)))

    C ^= ((a & (c >> 2)) ^ (b & (d >> 2)))
    D ^= ((b & (c >> 2)) ^ ((a ^ b) & (d >> 2)))

    # phase 3
    a = A
    b = B
    c = C
    d = D

    A = ((a & (a >> 4)) ^ (b & (b >> 4)))
    B = ((a & (b >> 4)) ^ (b & ((a ^ b) >> 4)))

    C ^= ((a & (c >> 4)) ^ (b & (d >> 4)))
    D ^= ((b & (c >> 4)) ^ ((a ^ b) & (d >> 4)))

    # Final round and projection
    a = A
    b = B
    c = C
    d = D

    C ^= ((a & (c >> 8)) ^ (b & (d >> 8)))
    D ^= ((b & (c >> 8)) ^ ((a ^ b) & (d >> 8)))

    # Undo transformation prefix scan
    a = C ^ (C >> 1)
    b = D ^ (D >> 1)

    # Recover index bits
    i0 = x ^ y
    i1 = b | (0xFFFF ^ (i0 | a))

    return ((interleave(i1) << 1) | interleave(i0)) >> (32 - 2 * n)
