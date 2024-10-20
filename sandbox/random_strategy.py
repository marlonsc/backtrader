import random
import matplotlib.pyplot as plt

# Initialize parameters
initial_capital = 10000  # Starting capital in dollars
bet_amount = 100         # Amount risked per bet
days = 365               # Number of days (bets)
capital_list = [initial_capital]  # List to store capital evolution

# Simulate the betting over 365 days
for day in range(1, days + 1):
    # Simulate the outcome of the bet (1 for win, 0 for loss)
    bet_outcome = random.choice([1, 0])  # 50% chance of winning or losing

    # Update capital based on the outcome
    if bet_outcome == 1:
        # Win: add the bet amount
        current_capital = capital_list[-1] + bet_amount
    else:
        # Lose: subtract the bet amount
        current_capital = capital_list[-1] - bet_amount

    # Append the updated capital to the list
    capital_list.append(current_capital)

# Plot the evolution of capital over 365 days
plt.figure(figsize=(10, 6))
plt.plot(capital_list, label="Capital Over Time")
plt.title("Capital Evolution over 365 Days (Strategy 3)")
plt.xlabel("Day")
plt.ylabel("Capital ($)")
plt.axhline(y=initial_capital, color='gray', linestyle='--', label="Initial Capital")
plt.legend()
plt.grid(True)
plt.show()