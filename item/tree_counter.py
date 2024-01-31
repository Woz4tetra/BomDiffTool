class TreeCounter:
    def __init__(self, min_level=0):
        self.tree_counter = {}
        self.prev_level = 0
        self.min_level = min_level

    def get_tree_num(self, level):
        level -= self.min_level
        assert level >= 0, level
        for i in range(level + 1):
            if i not in self.tree_counter:
                if i == level:
                    self.tree_counter[i] = 0
                else:
                    self.tree_counter[i] = 1

        if self.prev_level < level:
            self.tree_counter[level] = 0
        self.prev_level = level
        self.tree_counter[level] += 1
        split_num = [str(self.tree_counter[i]) for i in range(level + 1)]
        tree_num = ".".join(split_num)
        parent = ".".join(split_num[:-1])
        return tree_num, parent
