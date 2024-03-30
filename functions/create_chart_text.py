from typing import List
import plotly.graph_objects as go
import copy


def increase_amount_for_category(category: [dict, list], target_category, amount):
    if isinstance(category, dict) and (
        target_category in category
        or any(
            [
                increase_amount_for_category(
                    category[subcategory], target_category, amount
                )
                for subcategory in category.keys()
                if isinstance(category[subcategory], dict)
            ]
        )
    ):
        if "amount" in category:
            category["amount"] += amount
        else:
            category["amount"] = amount

        if target_category in category:
            category[target_category].append(amount)

        return True
    return False


def create_connecting_text(category, text, category_name):
    amount = None
    for subcategory in category:
        amount = None
        if (
            isinstance(category[subcategory], dict)
            and "amount" in category[subcategory]
        ):
            amount = category[subcategory]["amount"]
            text = create_connecting_text(category[subcategory], text, subcategory)

        elif isinstance(category[subcategory], (int, float)):
            amount = category[subcategory]

        if amount and amount > 0 and amount != "amount" and subcategory != "amount":
            text += f"\n{category_name} [{amount}] {subcategory}"
    return text


def create_dataset_for_sankey(
    category, category_name, labels: list, source, target, value
):
    if category_name not in labels:
        labels.append(category_name)
    for subcategory in category:
        amount = None
        if (
            isinstance(category[subcategory], dict)
            and "amount" in category[subcategory]
        ):
            amount = category[subcategory]["amount"]
            labels, source, target, value = create_dataset_for_sankey(
                category[subcategory], subcategory, labels, source, target, value
            )

        elif isinstance(category[subcategory], (int, float)):
            amount = category[subcategory]

        if amount and amount > 0 and amount != "amount" and subcategory != "amount":
            if subcategory not in labels:
                labels.append(subcategory)
            source.append(labels.index(category_name))
            target.append(labels.index(subcategory))
            value.append(amount)
    return labels, source, target, value


def sum_abs_lists(obj):
    if isinstance(obj, dict):
        for key in obj:
            if isinstance(obj[key], dict):
                sum_abs_lists(obj[key])
            elif isinstance(obj[key], list):
                obj[key] = round(abs(sum(obj[key])))
            elif isinstance(obj[key], (float, int)):
                obj[key] = round(abs(obj[key]))


def create_chart(payments: List[dict]):
    from info_model import OUTGOING_INFORMATION_MODEL, INCOME_INFORMATION_MODEL

    print("test")
    TEMP_INFO_MODEL = copy.deepcopy(OUTGOING_INFORMATION_MODEL)
    for payment in payments:
        info_model = INCOME_INFORMATION_MODEL
        amount = float(payment["features"]["amount"])
        if amount < 0 and "annotation" in payment:
            info_model = TEMP_INFO_MODEL["UIT"]
            increase_amount_for_category(info_model, payment["annotation"], amount)

    sum_abs_lists(TEMP_INFO_MODEL)
    create_connecting_text(TEMP_INFO_MODEL["UIT"], "", "UIT")

    labels, source, target, value = create_dataset_for_sankey(
        TEMP_INFO_MODEL["UIT"], "UIT", [], [], [], []
    )

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels,
                    color="blue",
                ),
                link=dict(
                    source=source,  # indices correspond to labels, eg A1, A2, A1, B1, ...
                    target=target,
                    value=value,
                ),
            )
        ]
    )

    fig.update_layout(font_size=10)
    return fig.to_html()
