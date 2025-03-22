import tkinter as tk
from tkinter import ttk
import requests
import time
import threading
from datetime import datetime, timedelta

# Function to fetch cryptocurrency prices with retries
def get_crypto_prices(retries=3, delay=2):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin,ethereum,ripple,litecoin,cardano,solana',
        'vs_currencies': 'usd',
        'include_24hr_change': 'true',
        'include_24hr_vol': 'true',
        'include_last_updated_at': 'true',
        'include_24hr_percent_change': 'true'
    }
    for attempt in range(retries):
        try:
            print(f"Fetching prices (Attempt {attempt + 1})...")
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            print("Prices fetched successfully!")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)  # Wait before retrying
    print("All attempts failed. Unable to fetch prices.")
    return None

# Function to calculate percentage change
def calculate_percentage_change(current_price, previous_price):
    if previous_price == 0:
        return 0  # Avoid division by zero
    return ((current_price - previous_price) / previous_price) * 100

# Function to format price as 1,000.00
def format_price(price):
    return f"{price:,.2f}"

# Function to reset percentage changes at midnight
def reset_percentage_at_midnight():
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_until_midnight = (midnight - now).total_seconds()
    threading.Timer(time_until_midnight, reset_percentage_changes).start()

# Function to reset percentage changes
def reset_percentage_changes():
    global previous_prices
    for crypto in cryptos:
        if crypto in previous_prices:
            previous_prices[crypto] = 0  # Reset to 0 to recalculate percentage change from the new price
    reset_percentage_at_midnight()  # Schedule the next reset

# Function to update the prices and percentage changes in the table
def update_prices(manual_refresh=False):
    global previous_prices  # Use global variable to store previous prices

    # Show progress bar and disable buttons while fetching data
    progress_bar.start()
    refresh_button.config(state="disabled")

    # Fetch new prices in a separate thread
    def fetch_data():
        prices = get_crypto_prices()
        if prices:
            for crypto in prices:
                current_price = prices[crypto]['usd']
                change_24h = prices[crypto].get('usd_24h_change', 0)

                # Update the price and percentage changes in the table
                price_labels[crypto].config(text=f"${format_price(current_price)}")

                # Update 24h change
                if change_24h > 0:
                    change_24h_labels[crypto].config(text=f"▲ {change_24h:.2f}%", foreground="green")
                elif change_24h < 0:
                    change_24h_labels[crypto].config(text=f"▼ {abs(change_24h):.2f}%", foreground="red")
                else:
                    change_24h_labels[crypto].config(text=f"{change_24h:.2f}%", foreground="white")

                # Store the current price for the next comparison
                previous_prices[crypto] = current_price
        else:
            # Handle API fetch failure
            for crypto in cryptos:
                price_labels[crypto].config(text="Error")
                change_24h_labels[crypto].config(text="—", foreground="white")

        # Hide progress bar and enable buttons after fetching data
        progress_bar.stop()
        refresh_button.config(state="normal")

    # Run the fetch_data function in a separate thread
    threading.Thread(target=fetch_data, daemon=True).start()

    # Schedule the function to run again after 10 seconds (if not a manual refresh)
    if not manual_refresh:
        root.after(10000, update_prices)

# Function to update the date and time display
def update_datetime():
    now = datetime.now()
    datetime_label.config(text=now.strftime("%Y-%m-%d %H:%M:%S"))
    root.after(1000, update_datetime)  # Update every second

# Create the main application window
root = tk.Tk()
root.title("Live Cryptocurrency Prices")
root.geometry("700x500")  # Adjusted window size for the table and date/time display
root.resizable(False, False)  # Disable resizing for a consistent layout

# Set black background and white text
root.configure(bg="black")

# Create a label for date and time
datetime_label = ttk.Label(root, font=("Arial", 12), anchor="center", background="black", foreground="white")
datetime_label.grid(row=0, column=0, columnspan=3, pady=10, padx=10, sticky="ew")

# Create headers for the table
headers = ["Crypto", "Price", "24h %"]
for col, header in enumerate(headers):
    header_label = ttk.Label(root, text=header, font=("Arial", 12, "bold"), background="black", foreground="white")
    header_label.grid(row=1, column=col, padx=10, pady=5, sticky="ew")

# Add rows for each cryptocurrency
cryptos = ["bitcoin", "ethereum", "ripple", "litecoin", "cardano", "solana"]
previous_prices = {}  # Initialize the previous_prices dictionary
price_labels = {}  # Dictionary to store price labels
change_24h_labels = {}  # Dictionary to store 24h change labels
for i, crypto in enumerate(cryptos):
    # Crypto name label
    crypto_label = ttk.Label(root, text=crypto.capitalize(), font=("Arial", 12), background="black", foreground="white")
    crypto_label.grid(row=i + 2, column=0, padx=10, pady=5, sticky="w")

    # Price label
    price_label = ttk.Label(root, text="—", font=("Arial", 12), background="black", foreground="white")
    price_label.grid(row=i + 2, column=1, padx=10, pady=5, sticky="e")
    price_labels[crypto] = price_label

    # 24h change label
    change_24h_label = ttk.Label(root, text="—", font=("Arial", 12), background="black", foreground="white")
    change_24h_label.grid(row=i + 2, column=2, padx=10, pady=5, sticky="e")
    change_24h_labels[crypto] = change_24h_label

# Progress bar for loading indicator
progress_bar = ttk.Progressbar(root, mode="indeterminate")
progress_bar.grid(row=len(cryptos) + 2, column=0, columnspan=3, pady=10, padx=10, sticky="ew")

# Add a manual refresh button
refresh_button = ttk.Button(root, text="Refresh Prices", command=lambda: update_prices(manual_refresh=True))
refresh_button.grid(row=len(cryptos) + 3, column=0, columnspan=3, pady=10, padx=10, sticky="ew")

# Start updating the prices
update_prices()

# Schedule percentage reset at midnight
reset_percentage_at_midnight()

# Start updating the date and time
update_datetime()

# Run the application
root.mainloop()