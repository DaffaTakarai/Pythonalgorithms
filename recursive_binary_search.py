def recursive_binary_search(list, target, start = None, end = None):
    start_index = 0 if start is None else start
    end_index = len(list) - 1 if end is None else end

    if start_index > end_index:
        return -1
    else:
        middle_index = (start_index + end_index) // 2

        if list[middle_index] == target:
            return middle_index
        elif list[middle_index] < target:
            return recursive_binary_search(list, target, middle_index + 1, end_index)
        else:
            return recursive_binary_search(list, target, start_index, middle_index - 1)