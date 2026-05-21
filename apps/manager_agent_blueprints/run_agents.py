import pandas as pd

signals = pd.read_csv('seed_data/market_signals.csv')

def risk_score(v):
    if v > 1.3:
        return 90
    if v > 1.2:
        return 70
    return 30

signals['risk_score'] = signals['value'].apply(risk_score)
print(signals[signals['risk_score'] >= 70])
