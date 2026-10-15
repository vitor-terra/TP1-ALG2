def longest_common_prefix(str1, str2):
    count = 0
    for i in range(min(len(str1), len(str2))):
        if str1[i] == str2[i]:
            count += 1
        else:
            break
    return count


class Node():
    #__slots__ = ("geohash", "children", "drivers")
    
    def __init__(self, geohash = None, children = None, drivers = None):
        self.geohash = geohash                                      #the rest of the geohash on that node
        self.children = children if children is not None else {}    #each dict element is {"first letter of the rest of the geohash on that node" : Node()} ex: "a" : Node(geohash = "abcd")
        self.drivers = drivers if drivers is not None else []       #all drivers on that geohash square (their id)


class Trie():
    def __init__(self):
        self.root = Node(geohash="")

    def insert(self, current_node, geohash, driver_id):
        for key in current_node.children:
            if geohash[0] == key:
                if geohash != current_node.children[key].geohash:

                    lcp = longest_common_prefix(geohash, current_node.children[key].geohash)

                    if lcp == len(current_node.children[key].geohash):
                        return self.insert(current_node.children[key], geohash[lcp:], driver_id)

                    if lcp < len(current_node.children[key].geohash):
                        current_node.children[key].children = {
                            current_node.children[key].geohash[lcp] : Node(current_node.children[key].geohash[lcp:], current_node.children[key].children, current_node.children[key].drivers),
                            geohash[lcp] : Node(geohash[lcp:], {}, [driver_id])
                            }
                        current_node.children[key].geohash = geohash[:lcp]
                        current_node.children[key].drivers = []
                        return True
                else:
                    current_node.children[key].drivers.append(driver_id)
                    return True

        current_node.children[geohash[0]] = Node(geohash, {}, [driver_id])
        return True

    def get_drivers(self, geohash):
        node = self.root
        while geohash:
            child = node.children.get(geohash[0])
            if child is None or not geohash.startswith(child.geohash):
                return []
            geohash = geohash[len(child.geohash):]
            node = child
        return node.drivers

    def prefix_search(self, geohash, start = None):
        #breakpoint()

        if start is None:
            start = self.root

        #Name change for clarity
        node = start

        while geohash:
            child = node.children.get(geohash[0])
            if child is None or not longest_common_prefix(geohash, child.geohash) == min(len(geohash), len(child.geohash)):
                return []
            geohash = geohash[len(child.geohash):]
            node = child

        drivers = []
        if node.children:
            for c in node.children:
                drivers += (self.prefix_search("", node.children[c]))
        else:
            return node.drivers

        return drivers 

t = Trie()
t.insert(t.root, "7h2y8jsb", 0)
t.insert(t.root, "7h2y8jsc", 1)
t.insert(t.root, "7h2y8k01", 2)
t.insert(t.root, "7h2xrcsw", 3)
breakpoint()

print(t.prefix_search('7h2y8j'))
