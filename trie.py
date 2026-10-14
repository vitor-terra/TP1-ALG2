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
                return None
            geohash = geohash[len(child.geohash):]
            node = child
        return node.drivers

t = Trie()
t.insert(t.root, "abc", 0)
t.insert(t.root, "abd", 1)
t.insert(t.root, "abx", 2)
t.insert(t.root, "abd", 3)

print(t.get_drivers('abd'))
