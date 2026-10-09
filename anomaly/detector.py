import statistics
from sample_data.historical_invoices import historical_invoices

STD_DEV_THRESHOLD = 2.0


def check_anomaly_statistical(amount, category, historical_invoices):
    category_amounts = [
        invoice["amount"]
        for invoice in historical_invoices
        if invoice["category"] == category
    ]

    if len(category_amounts) < 3:
        return {
            "is_anomaly": False,
            "score": 0.0,
            "reason": "Insufficient historical data"
        }

    mean = statistics.mean(category_amounts)
    std_dev = statistics.stdev(category_amounts)

    if std_dev == 0:
        return {
            "is_anomaly": False,
            "score": 0.0,
            "reason": "No variation in historical amounts"
        }

    z_score = abs((amount - mean) / std_dev)

    if z_score >= STD_DEV_THRESHOLD:
        return {
            "is_anomaly": True,
            "score": round(z_score, 2),
            "reason": f"Amount is {round(z_score, 2)} standard deviations from the category average"
        }

    return {
        "is_anomaly": False,
        "score": round(z_score, 2),
        "reason": "Amount is within the normal range"
    }

if __name__ == "__main__":

    normal_result = check_anomaly_statistical(
        13000,
        "Software Subscription",
        historical_invoices
    )

    anomaly_result = check_anomaly_statistical(
        50000,
        "Software Subscription",
        historical_invoices
    )

    print("Normal invoice:")
    print(normal_result)

    print("\nSuspicious invoice:")
    print(anomaly_result)