# Python port of mourner/flatbush

This is a port of https://github.com/mourner/flatbush

To test: `python test.py`

Example:
```python
from flatbush import FlatBush
fb = FlatBush()
# add two boxes
fb.add(30, 4, 32, 5) # x1,y1,x2,y2
fb.add(10, 60, 11, 63)
fb.finish();

# query
results = fb.search(minx, miny, maxx, maxy);
# results are an array of indices. The index starts at zero,
# and is the order in which you inserted elements into the tree.
```

## Performance

These results are from an i7-6700K @ 4GHz, Python 3.7.4

* Inserting 250,000 rectangles: 2.1 seconds
* 1000 queries that retrieve 9 results each: 35 milliseconds