def bubble_sort(arr):
    # Outer loop to iterate through the list n times
    for n in range(len(arr) - 1, 0, -1):
        swapped = False  # Initialize swapped as False

        # Inner loop to compare adjacent elements
        for i in range(n):
            if arr[i] > arr[i + 1]:
                # Swap elements if they are in the wrong order
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                swapped = True  # Set swapped to True if a swap is made

        # If no elements were swapped, the list is sorted
        if not swapped:
            break

# Sample list to be sorted
arr = [39, 12, 18, 85, 72, 10, 2, 18]
print("Unsorted list is:")
print(arr)

bubble_sort(arr)

print("Sorted list is:")
print(arr)

# Intentional warning: Unused variable
unused_var = 42

# Intentional error: Undefined variable
print(undefined_var)