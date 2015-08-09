from VM import VM

if __name__ == '__main__':
    vm = VM()
    vm.create_nodes()
    # vm.split_sourcecode('scripts/test3.tis')
    # vm.split_sourcecode('scripts/signal_edge_detector.tis')
    vm.split_sourcecode('scripts/mov_04.tis')
    vm.parse()
    vm.run()
    vm.compare_io()
    # symtable = SymbolTable()
    # parser = Parser(symtable)
    # parser.parse('scripts/test0.tis', 'file')