def trigger_zero_division_error():
    try:
        result = 10 / 0  # This will raise ZeroDivisionError
    except ZeroDivisionError as e:
        print(f"Caught a ZeroDivisionError: {e}")

def trigger_index_error():
    try:
        lst = [1, 2, 3]
        print(lst[5])  # This will raise IndexError
    except IndexError as e:
        print(f"Caught an IndexError: {e}")

def trigger_file_not_found_error():
    try:
        with open("non_existent_file.txt", "r") as f:  # This will raise FileNotFoundError
            f.read()
    except FileNotFoundError as e:
        print(f"Caught a FileNotFoundError: {e}")

def trigger_type_error():
    try:
        result = "string" + 10  # This will raise TypeError
    except TypeError as e:
        print(f"Caught a TypeError: {e}")

def trigger_key_error():
    try:
        d = {"a": 1, "b": 2}
        print(d["c"])  # This will raise KeyError
    except KeyError as e:
        print(f"Caught a KeyError: {e}")

if __name__ == "__main__":
    trigger_zero_division_error()
    trigger_index_error()
    trigger_file_not_found_error()
    trigger_type_error()
    trigger_key_error()
