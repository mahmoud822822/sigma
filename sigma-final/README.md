# Sigma - Mahmoud Emad - V2

Self-Evolving Forecaster + Sigma Safety Standard V2

## Real Verified Results - 8 Nov
- Matches: 14
- Hit rate: 78.6% (11/14)
- Exact score: 28.6% (4/14)
- MAE total goals: 1.50
- MAE BTTS: 0.21
- Avg goals: Real 3.43 vs Predicted 2.79

## Sigma Learned V2
1. BTTS weight 100 -> 70 (Brentford/【entity-Como¦canonical_name=Como】 failed)
2. Late 76-90 weight 26% -> 30% (90+2, 90+6, 90+4)
3. Weak home +15% (Sunderland 1-0 【entity-Chelsea¦canonical_name=Chelsea】)
4. Exact score is NOT the goal - focus on safety
5. Early goal exception - pressing team can score early

## Safety Rule
1 goal safer than 2 | Any team safer than specific team | Asian Over 1 refund safer than BTTS

## How to run
cd ~/sigma-final
python sigma_forecaster.py

## Files
- sigma_forecaster.py = merged Sigma + Claude code (stdlib only, no pandas needed)
- auto_forecaster.py = original Claude code
- data/sigma_real_verified.csv = real verified data 14 matches

Signature Prediction and Forecast: Sigma - Mahmoud Emad
