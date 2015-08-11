from VM import VM

if __name__ == '__main__':
    vm = VM()
    vm.load('scripts/test3.tis')
    # vm.load('scripts/signal_edge_detector.tis')
    # vm.load('scripts/mov_04.tis')
    vm.run()
    vm.compare_io()