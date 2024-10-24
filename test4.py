# Test Code for Linting
import sys, os  # This will trigger a lint warning for multiple imports in one line

def bubble_sort(arr):  # Naming conventions issue: "bubble_sort" should be "BubbleSort"
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]  # No issue here

    print(arr)  # This will trigger a warning for using print in production code

arr = [64, 34, 25, 12, 22, 11, 90]
bubble_sort(arr)

# This will trigger a NameError
print(undefined_var)

# Indentation issue
def example():
   print("Incorrectly indented")  # This line has inconsistent indentation
