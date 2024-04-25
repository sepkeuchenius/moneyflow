from typing import List, Union
import plotly.graph_objects as go
import info_model


def increase_amount_for_category(category: Union[dict, list], target_category, amount):
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


def create_dataset_for_sankey(
    category: Union[dict, int, float],
    category_name: str,
    labels: list,
    source: list,
    target: list,
    value: list,
    inverse=False,
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
                category[subcategory],
                subcategory,
                labels,
                source,
                target,
                value,
                inverse=inverse,
            )

        elif isinstance(category[subcategory], (int, float)):
            amount = category[subcategory]

        if amount and amount > 0 and amount != "amount" and subcategory != "amount":
            if subcategory not in labels:
                labels.append(subcategory)
            if not inverse:
                source.append(labels.index(category_name))
                target.append(labels.index(subcategory))
            else:
                target.append(labels.index(category_name))
                source.append(labels.index(subcategory))
            value.append(amount)
    return labels, source, target, value


def sum_list(obj):
    if isinstance(obj, dict):
        for key in obj:
            if isinstance(obj[key], dict):
                sum_list(obj[key])
            elif isinstance(obj[key], list):
                obj[key] = round(sum(obj[key]))
            elif isinstance(obj[key], (float, int)):
                obj[key] = round(obj[key])


def create_chart(payments: List[dict], uid):
    [info_model_in, info_model_out] = info_model.get_user_model(uid).values()
    info_model_in["*"]["OTHER_IN"] = []
    info_model_out["*"]["OTHER_OUT"] = []
    categories_in = info_model.generate_list_of_categories(info_model_in, [])
    for payment in payments:
        amount = float(payment["features"]["amount"])
        
        if payment.get("annotation") not in info_model.SPECIAL_CATEGORIES:
            if (
                "annotation" in payment
            ):
                if payment["annotation"] in categories_in:
                    increase_amount_for_category(
                        info_model_in, payment["annotation"], amount
                    )
                else:
                    increase_amount_for_category(
                        info_model_out, payment["annotation"], amount * -1
                    )
            else:
                print(payment["features"])
                if amount < 0:
                    print('found')
                    increase_amount_for_category(info_model_out, "OTHER_OUT", amount * -1)
                else:
                    increase_amount_for_category(info_model_in, "OTHER_IN", amount)

    sum_list(info_model_out)
    sum_list(info_model_in)

    print(info_model_in)

    labels, source, target, value = create_dataset_for_sankey(
        info_model_out["*"], "*", [], [], [], []
    )

    labels, source, target, value = create_dataset_for_sankey(
        info_model_in["*"], "*", labels, source, target, value, inverse=True
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
