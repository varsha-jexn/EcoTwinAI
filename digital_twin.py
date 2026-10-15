def get_status(fill_level):
    if fill_level >= 90:
        return "Urgent"
    if fill_level >= 70:
        return "Collect Soon"
    return "Normal"


def calculate_priority(fill_level, hours_since_collection):
    fill_score = fill_level * 0.7

    waiting_score = (
        min(hours_since_collection, 12) / 12 * 30
    )

    return round(fill_score + waiting_score, 1)


def update_bin(bin_data, new_fill_level):
    bin_data["fill_level"] = max(
        0, min(100, int(new_fill_level))
    )

    bin_data["status"] = get_status(
        bin_data["fill_level"]
    )

    bin_data["priority"] = calculate_priority(
        bin_data["fill_level"],
        bin_data["hours_since_collection"],
    )

    return bin_data


def get_priority_order(bin_records):
    return sorted(
        bin_records,
        key=lambda item: calculate_priority(
            item["fill_level"],
            item["hours_since_collection"],
        ),
        reverse=True,
    )


def simulate_collection(bin_records, threshold=90):
    """Simulate collecting bins at or above a threshold."""
    updated_records = []

    for item in bin_records:
        updated = dict(item)

        if updated["fill_level"] >= threshold:
            updated["fill_level"] = 20
            updated["hours_since_collection"] = 0

        updated["status"] = get_status(
            updated["fill_level"]
        )

        updated["priority"] = calculate_priority(
            updated["fill_level"],
            updated["hours_since_collection"],
        )

        updated_records.append(updated)

    return updated_records