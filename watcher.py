from win10toast import ToastNotifier
import json
from time import sleep
import requests
from decimal import Decimal
from urllib import parse
from datetime import datetime
import re


toaster = ToastNotifier()

app_env = {"version": "0.1.1", "name": "CS:GO Market Watcher", "debug": False}

url_parts = {"host": "https://steamcommunity.com",
             "url": "/market/priceoverview/",
             "appid": 730}


def show_toast(msg):
    toaster.show_toast(
        app_env["name"], msg, icon_path="icon.ico")


print("Welcome to the CS:GO Market Watcher.")
show_toast("Welcome to the CS:GO Market Watcher.")


weapons = []
settings = {}
checks = []

# Read settings
try:
    with open('settings.json') as json_file:
        data = json.load(json_file)
        weapons = data["weapons"]
        settings = data["settings"]

except:
    show_toast("Error reading settings file. Please check settings.json")
    exit(1)


if settings["debug"]:
    app_env["debug"] = True

# Main loop
loop_num = 0
while True:
    loop_num += 1
    print(f"\nChecking Market ({loop_num})...")
    current_check = []

    weapon_num = 0
    for weapon in weapons:
        print(f'  > Checking weapon "{weapon}"')
        check = {"weapon": weapon, "date": str(datetime.now())}

        try:
            request_url = f'{url_parts["host"]}{url_parts["url"]}'
            request_params = {
                "country": settings["country"], "currency": settings["currency"], "appid": url_parts["appid"], "market_hash_name": weapon}
            r = requests.get(url=request_url, params=request_params)

            if app_env["debug"]:
                print("    -", r.url)

            request_data = r.json()

            if request_data["success"] == True:
                check["success"] = True
                lowest_price = float(
                    str(re.findall(r"[-+]?\d*[.,]\d+|\d+", request_data["lowest_price"])[0]).replace(",", "."))
                check["last_checked_price"] = lowest_price
                if app_env["debug"]:
                    print("    - Lowest Price:", lowest_price)

                if len(checks) > 0:
                    if checks[-1][weapon_num]["success"]:
                        if abs(checks[-1][weapon_num]["last_checked_price"]-lowest_price) > settings["notify_tolerance"]:
                            tolerance = round(Decimal(float(
                                checks[-1][weapon_num]["last_checked_price"]) - lowest_price), 2)

                            print("    -> Price has changed by", tolerance)
                            show_toast(
                                f'The value of the weapon "{weapon}" has changed by {str(tolerance)}!')
                            check["difference_notified"] = True
                        else:
                            check["difference_notified"] = False
                    checks.remove(checks[-1])
                else:
                    check["difference_notified"] = False

            else:
                check["success"] = False
                print("    -> Weapon not found.")
                show_toast(
                    f"Oh no! The weapon \"{weapon}\" was not found on steam!")

            if not check["success"]:
                check["last_checked_price"] = "--"
                check["difference_notified"] = False

            with open("checks.log", "a") as f:
                f.write(
                    f'\n{check["weapon"]} :: {check["last_checked_price"]} :: {check["date"]} :: {check["success"]} :: {check["difference_notified"]}')

            current_check.append(check)
            weapon_num += 1

        except requests.exceptions.RequestException as e:
            print("   -> Error checking weapon:", e)
            show_toast(
                f"Oh no! I was not able to check the weapon \"{weapon}\"!")

    checks.append(current_check)
    sleep(settings["request_interval"])


# Error
show_toast("Oh no! Something went wrong!")
exit(1)
