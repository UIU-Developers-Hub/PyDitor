# test_lint_code.py

import sys, os  # This will trigger a lint warning for an unused import

def BubbleSort(arr):  # This will trigger a naming convention warning
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]  # This line is fine

    print(arr)  # This will trigger a lint warning for using print() in production code

    # The following code has indentation errors to trigger lint errors
    if True:
      print("This is indented incorrectly")

# Running the function
bubble_sort([64, 34, 25, 12, 22, 11, 90])  # This will trigger a lint error for using an undefined variable
