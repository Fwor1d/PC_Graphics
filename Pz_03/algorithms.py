# Алгоритмы только изменяют данные и возвращают описание шага.
# Этот файл не зависит от PyGame.


def bubble_sort_steps(values):
    comparisons = 0
    swaps = 0
    passes = 0
    steps = 0
    n = len(values)
    sorted_from = n

    for end in range(n - 1, 0, -1):
        passes += 1
        made_swap = False

        for i in range(end):
            comparisons += 1
            steps += 1
            yield {
                "type": "compare", "indices": (i, i + 1),
                "comparisons": comparisons, "swaps": swaps,
                "pass": passes, "steps": steps,
                "sorted_from": sorted_from,
                "message": f"Comparing indices {i} and {i + 1}",
            }

            if values[i] > values[i + 1]:
                values[i], values[i + 1] = values[i + 1], values[i]
                made_swap = True
                swaps += 1
                steps += 1
                yield {
                    "type": "swap", "indices": (i, i + 1),
                    "comparisons": comparisons, "swaps": swaps,
                    "pass": passes, "steps": steps,
                    "sorted_from": sorted_from,
                    "message": f"Swapped indices {i} and {i + 1}",
                }

        sorted_from = end
        if not made_swap:
            sorted_from = 0

        steps += 1
        yield {
            "type": "pass_complete", "indices": (),
            "comparisons": comparisons, "swaps": swaps,
            "pass": passes, "steps": steps,
            "sorted_from": sorted_from,
            "message": (
                f"Pass {passes} complete: no swaps, early finish"
                if not made_swap else f"Pass {passes} complete"
            ),
        }

        if not made_swap:
            break

    steps += 1
    yield {
        "type": "done", "indices": (),
        "comparisons": comparisons, "swaps": swaps,
        "pass": passes, "steps": steps,
        "sorted_from": 0,
        "message": "Bubble Sort complete",
    }


def selection_sort_steps(values):
    comparisons = 0
    swaps = 0
    passes = 0
    steps = 0
    n = len(values)

    for start in range(n - 1):
        passes += 1
        min_index = start

        steps += 1
        yield {
            "type": "select_start", "indices": (start,),
            "start": start, "current": None, "min_index": min_index,
            "sorted_count": start,
            "comparisons": comparisons, "swaps": swaps,
            "pass": passes, "steps": steps,
            "message": f"Unsorted part begins at index {start}",
        }

        for j in range(start + 1, n):
            comparisons += 1
            steps += 1
            yield {
                "type": "compare", "indices": (j, min_index),
                "start": start, "current": j, "min_index": min_index,
                "sorted_count": start,
                "comparisons": comparisons, "swaps": swaps,
                "pass": passes, "steps": steps,
                "message": f"Comparing index {j} with minimum {min_index}",
            }

            if values[j] < values[min_index]:
                min_index = j
                steps += 1
                yield {
                    "type": "new_min", "indices": (min_index,),
                    "start": start, "current": j, "min_index": min_index,
                    "sorted_count": start,
                    "comparisons": comparisons, "swaps": swaps,
                    "pass": passes, "steps": steps,
                    "message": f"New minimum at index {min_index}",
                }

        if min_index != start:
            values[start], values[min_index] = values[min_index], values[start]
            swaps += 1
            steps += 1
            yield {
                "type": "swap", "indices": (start, min_index),
                "start": start, "current": None, "min_index": min_index,
                "sorted_count": start,
                "comparisons": comparisons, "swaps": swaps,
                "pass": passes, "steps": steps,
                "message": f"Swapped indices {start} and {min_index}",
            }

        steps += 1
        yield {
            "type": "pass_complete", "indices": (),
            "start": start, "current": None, "min_index": None,
            "sorted_count": start + 1,
            "comparisons": comparisons, "swaps": swaps,
            "pass": passes, "steps": steps,
            "message": f"Pass {passes} complete",
        }

    steps += 1
    yield {
        "type": "done", "indices": (),
        "start": None, "current": None, "min_index": None,
        "sorted_count": n,
        "comparisons": comparisons, "swaps": swaps,
        "pass": passes, "steps": steps,
        "message": "Selection Sort complete",
    }


def binary_search_steps(values, target):
    left = 0
    right = len(values) - 1
    comparisons = 0
    steps = 0

    while left <= right:
        mid = (left + right) // 2
        comparisons += 1
        steps += 1
        yield {
            "type": "check", "left": left, "mid": mid, "right": right,
            "target": target, "comparisons": comparisons,
            "steps": steps, "result": "Searching...",
            "message": f"Checking index {mid}: value {values[mid]}",
        }

        if values[mid] == target:
            steps += 1
            yield {
                "type": "done", "left": left, "mid": mid, "right": right,
                "target": target, "comparisons": comparisons,
                "steps": steps, "found_index": mid,
                "result": f"Element found: index {mid}",
                "message": f"Element found: index {mid}",
            }
            return

        if values[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

        steps += 1
        yield {
            "type": "range", "left": left, "mid": None, "right": right,
            "target": target, "comparisons": comparisons,
            "steps": steps, "result": "Searching...",
            "message": f"Remaining range: [{left}, {right}]" if left <= right
                       else "Search range is empty",
        }

    steps += 1
    yield {
        "type": "done", "left": left, "mid": None, "right": right,
        "target": target, "comparisons": comparisons,
        "steps": steps, "result": "Element not found",
        "message": "Element not found",
    }
