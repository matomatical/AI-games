"""
    A min-priority queue for a set of unique, hashable items with anything 
    comparable as priorities.

Note: Does NOT allow duplicate items.
Note: DOES allow fast change-priority operations.

These characteristics make this a suitable data-structure for implementing 
graph search algorithms such as Dijkstra's algorithm or A* search (where there 
is no use storing the same node/state multiple times in the queue). Python's 
built-in heapq module is inadequate for this task, so this is a rebuild.
Algorithms are fun!

Author: Matt Farrugia-Roberts, 2019

"""
class PriorityQueue:
    """
    Our priority queue consists three components:
    1. `items` - a binary-min-heap-ordered list of items
    2. `p_map` - a dictionary mapping items to their priorities
    3. `h_map` - a dictionary mapping items to their index in the `items` list
    The constructor establishes the heap invariant on `items` (based on 
    priorities from `p_map`), and the additional invariant that `h_map` 
    correctly maps items to locations in the heap, in O(n) time.
    All other methods maintain these invariants (each in O(log(n)) time).
    """
    def __init__(self, items_priorities=None):
        """
        create a priority queue, optionally with initial item/priority pairs
        from the list of tuples `items_priorities`.
        in case the list contains duplicate items, the last priority value for 
        each item is used.
        requires O(n) time to establish invariants (still faster than inserting 
        the first n items one by one).
        """
        self.items = []
        self.p_map = {}
        self.h_map = {}
        if items_priorities is not None:
            for item, priority in items_priorities:
                if item in self.p_map:
                    self.p_map[item] = priority
                else:
                    self.items.append(item)
                    self.p_map[item] = priority
                    self.h_map[item] = len(self.items) - 1
            self._heapify()
    
    def _heapify(self):
        """establish heap invariant on self.items/self.p_map in O(n) time"""
        for i in range(len(self.items)//2-1, -1, -1):
            self._sift_down(i)
    
    def update(self, item, new_priority):
        """
        insert a new item to the priority queue, or, if the item-to-be-inserted
        already exists in the priority queue, just update its priority value.
        requires O(logn) time to re-establish invariants.
        """
        if item in self.p_map:
            old_priority = self.p_map[item]
            self.p_map[item] = new_priority
            self._sift_up(self.h_map[item])
            self._sift_down(self.h_map[item])
        else:
            self.items.append(item)
            self.p_map[item] = new_priority
            self.h_map[item] = len(self.items)-1
            self._sift_up(len(self.items)-1)
    
    def extract_min(self):
        """
        remove and return the item with the lowest priority value (highest
        priority) amongst the items in this priority queue.
        requires O(logn) time to re-establish invariants.
        """
        item = self.items[0]
        del self.p_map[item]
        del self.h_map[item]
        if len(self.items) > 1:
            replacement = self.items.pop()
            self.items[0] = replacement
            self.h_map[replacement] = 0
            self._sift_down(0)
        else:
            self.items.pop()
        return item
    
    def _sift_down(self, i):
        """
        restore the heap invariant amongst the descendants of the heap node at 
        position i. O(logn) time.
        """
        parent = i
        child = self._min_child(parent)
        while child < len(self.items) and self._p(child) < self._p(parent):
            self._swap(child, parent)
            parent = child
            child = self._min_child(parent)
    
    def _min_child(self, parent):
        """
        of the (up to) two children of parent, calculate the child with a 
        smaller priority value (i.e. higher priority---this is a min heap)
        NOTE: in case parent has no children, still return the index that the 
        first child _would_ be at---caller should check this separately.
        """
        child = parent * 2 + 1
        if child + 1 < len(self.items) and self._p(child) > self._p(child+1):
            child += 1
        return child
    
    def _sift_up(self, i):
        """
        restore the heap invariant amongst the ancestors of the heap node at 
        position i. O(logn) time.
        """
        child  = i
        parent = (child - 1) // 2
        while child > 0 and self._p(child) < self._p(parent):
            self._swap(child, parent)
            child  = parent
            parent = (child - 1) // 2
    
    def _swap(self, i, j):
        """swap two items in the heap, maintaining correctness of h_map"""
        item_a = self.items[i]
        item_b = self.items[j]
        self.items[j] = item_a
        self.items[i] = item_b
        self.h_map[item_a] = j
        self.h_map[item_b] = i
    
    def _p(self, index):
        """helper method: get the priority of the item at a particular index"""
        return self.p_map[self.items[index]]

    
    # magic methods to ease working with a PriorityQueue instance:
    def __bool__(self):
        """bool(pq) is True iff pq is non-empty"""
        return bool(self.items)
    
    def __len__(self):
        """len(pq) gives the number of items in the pq"""
        return len(self.items)
        # (should equal len(self.p_map) and len(self.h_map))
    
    def __iter__(self):
        """
        allow iteration through this priority queue (e.g. with for loop)
        NOTES:
        1. Iteration is destructive: items are removed from the pq as they are
           produced
        2. Concurrent modification is allowed and will affect the items produced
        As such, iteration differs substantially from iteration through other
        Python data structures (such as lists and dictionaries).
        """
        while self:
            item = self.extract_min()
            yield item
    
    def __str__(self):
        """
        str(pq) gives a string representation of the items in pq and priorities
        """
        return "<PQ: "+", ".join(f"{i}/{self.p_map[i]}" for i in self.items)+">"
    
    def __repr__(self):
        """repr(pq) gives a constructor call that would recreate this pq"""
        return f"PriorityQueue({[(i, self.p_map[i]) for i in self.items]})"
        
