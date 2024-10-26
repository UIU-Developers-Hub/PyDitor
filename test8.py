import importlib

def batch_test(function_name, input_file):
    """Batch test function for any algorithm."""
    try:
        with open(input_file, 'r') as f:
            test_cases = f.readlines()

        for i, case in enumerate(test_cases):
            args = case.strip().split()
            try:
                if function_name == "merge_sort":
                    args = [int(arg) for arg in args]
                    result = merge_sort(args)
                elif function_name == "dijkstra":
                    # Parse graph and start node
                    # Call dijkstra(graph, start_node)
                    pass
                elif function_name == "knapsack":
                    # Parse knapsack data
                    pass
                elif function_name == "matrix_multiplication":
                    # Parse matrices
                    pass
                
                print(f"Test case {i+1}: Input: {args} -> Output: {result}")
            except Exception as e:
                print(f"Test case {i+1}: Error: {e}")

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' does not exist.")
