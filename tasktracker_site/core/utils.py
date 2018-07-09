def get_time_range(first, second, third):
    time_ranges = (first, second, third)
    time_ranges = sorted(time_ranges, key=lambda x: x if x is not None else -1)
    first, second, third = time_ranges

    print(time_ranges)
    if first is None:
        if second is None:
            if third is None:
                return None
            else:
                return (third, )
        return (second, third)
    else:
        return (first, third)