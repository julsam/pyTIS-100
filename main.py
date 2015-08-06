from VM import VM

if __name__ == '__main__':
    vm = VM()
    vm.create_nodes()
    vm.split_sourcecode('scripts/port_test01.tis')
    vm.parse()
    vm.run()
    # symtable = SymbolTable()
    # parser = Parser(symtable)
    # parser.parse('scripts/test0.tis', 'file')