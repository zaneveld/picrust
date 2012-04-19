#!/usr/bin/env python

from cogent.core.tree import PhyloNode

class PicrustNode(PhyloNode):
    def multifurcating(self, num, eps=None, constructor=None):
        """Return a new tree with every node having num or few children

        num : the number of children a node can have max
        eps : default branch length to set if self or constructor is of
            PhyloNode type
        constructor : a TreeNode or subclass constructor. If None, uses self
        """
        if num < 2: 
            raise TreeError, "Minimum number of children must be >= 2"

        if eps is None:
            eps = 0.0

        if constructor is None:
            constructor = self.__class__

        if hasattr(constructor, 'Length'):
            set_branchlength = True 
        else:
            set_branchlength = False

        new_tree = self.copy()

        for n in new_tree.preorder(include_self=True):
            while len(n.Children) > num: 
                new_node = constructor(Children=n.Children[-num:])

                if set_branchlength:
                    new_node.Length = eps

                n.append(new_node)

        return new_tree

    def bifurcating(self, eps=None, constructor=None):
        """Wrap multifurcating with a num of 2"""
        return self.multifurcating(2, eps, constructor)

    def getSubTree(self, name_list):
        """A new instance of a sub tree that contains all the otus that are
        listed in name_list.
        just a small change from that in cogent.core.tree.py so that the root
        node keeps its name
        
        Credit: Julia Goodrich
        """
        edge_names = self.getNodeNames(includeself=1, tipsonly=False)
        for name in name_list:
            if name not in edge_names:
                raise ValueError("edge %s not found in tree" % name)
        new_tree = self._getSubTree(name_list)
        if new_tree is None:
            raise SimTreeError, "no tree created in make sub tree"
        elif new_tree.istip():
            # don't keep name
            new_tree.params = self.params
            new_tree.Length = self.Length
            return new_tree
        else:
            new_tree.Name = self.Name
            new_tree.NameLoaded = self.NameLoaded
            new_tree.params = self.params
            new_tree.Length = self.Length
            # keep unrooted
            if len(self.Children) > 2:
                new_tree = new_tree.unrooted()
            return new_tree

    def _getSubTree(self, included_names, constructor=None):
        """An equivalent node with possibly fewer children, or None
            this is an iterative version of that in cogent.core.tree.py

        Credit: Julia Goodrich
        """
        nodes_stack = [[self, len(self.Children)]]
        result = [[]]

        # Renumber autonamed edges
        if constructor is None:
            constructor = self._default_tree_constructor()

        while nodes_stack:
            top = nodes_stack[-1]
            top_node, num_unvisited_children = top
            if top_node.Name in included_names:
                result[-1].append(top_node.deepcopy(constructor=constructor))
                nodes_stack.pop()
            else:
                #check the top node, any children left unvisited?
                if num_unvisited_children: #has any child unvisited
                    top[1] -= 1  #decrease the #of children unvisited
                    next_child = top_node.Children[-num_unvisited_children]
                    # - for order
                    #pre-visit
                    nodes_stack.append([next_child, len(next_child.Children)])
                    if len(next_child.Children) > 0:
                        result.append([])
                else:
                    node = nodes_stack.pop()[0]
                    children = result[-1]
                    children =[child for child in children if child is not None]
                    if len(top_node.Children) == 0:
                        new_node = None
                    elif len(children) == 0:
                        result.pop()
                        new_node = None
                    elif len(children) == 1:
                        result.pop()
                        # Merge parameter dictionaries by adding lengths and
                        # making weighted averages of other parameters.  This
                        # should probably be moved out of here into a
                        # ParameterSet class (Model?) or tree subclass.
                        params = {}
                        child = children[0]

                        if node.Length is not None and child.Length is not None:
                            shared_params = [n for (n,v) in node.params.items()
                                if v is not None
                                and child.params.get(n) is not None
                                and n is not "length"]
                            length = node.Length + child.Length
                            if length:
                                params = dict([(n,
                                        (node.params[n]*node.Length +
                                        child.params[n]*child.Length) / length)
                                    for n in shared_params])
                            params['length'] = length
                        new_node = child
                        new_node.params = params
                    else:
                        result.pop()
                        new_node = constructor(node, tuple(children))
                    if len(result)>0:
                        result[-1].append(new_node)
                    else:
                        return new_node