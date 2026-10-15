import os


def rule_based_advice(bin_records):
    urgent = [
        item for item in bin_records
        if item["fill_level"] >= 90
    ]

    soon = [
        item for item in bin_records
        if 70 <= item["fill_level"] < 90
    ]

    lines = [
        "Demo fallback: rule-based recommendations",
        "",
        f"Urgent bins: {len(urgent)}",
        f"Bins to collect soon: {len(soon)}",
    ]

    for item in urgent:
        lines.append(
            f"Prioritize {item['id']} at "
            f"{item['location']} "
            f"({item['fill_level']}% full)."
        )

    for item in soon:
        lines.append(
            f"Monitor {item['id']} at "
            f"{item['location']} "
            f"({item['fill_level']}% full)."
        )

    lines.append(
        "Review segregation practices and verify "
        "local recycling guidelines."
    )

    return "\n".join(lines)


def generate_advice(bin_records):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return rule_based_advice(bin_records)

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    summary = [
        {
            "id": item["id"],
            "location": item["location"],
            "waste_type": item["waste_type"],
            "fill_level": item["fill_level"],
            "hours_since_collection":
                item["hours_since_collection"],
        }
        for item in bin_records
    ]

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        instructions=(
            "You are a waste-management planning assistant. "
            "Use only the supplied simulated data. "
            "Prioritize collection, explain your reasoning, "
            "and suggest segregation improvements. "
            "Never claim simulated values are real sensor data. "
            "Keep the response concise and practical."
        ),
        input=f"Analyze these simulated bin records: {summary}",
    )

    return response.output_text