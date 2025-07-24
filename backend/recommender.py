def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    sec = seconds % 60

    if hours > 0:
        if minutes > 0 and sec > 0:
            return f"{hours} h {minutes} min {sec} sec"
        elif minutes > 0:
            return f"{hours} h {minutes} min"
        elif sec > 0:
            return f"{hours} h {sec} sec"
        else:
            return f"{hours} h"
    elif minutes > 0:
        if sec > 0:
            return f"{minutes} min {sec} sec"
        else:
            return f"{minutes} min"
    else:
        return f"{sec} sec"

tests = [10, 59, 60, 79, 96, 3600, 3665]

for t in tests:
    print(f"{t} secondes → {format_duration(t)}")
