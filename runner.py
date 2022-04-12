import json
import re
from datetime import datetime, timedelta
from random import random
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from time import sleep

DEBUG = True

driver = webdriver.Chrome()
with open("jobs.json", "r") as data:
    jobs = json.load(data)


# SELENIUM


def selenium(data):
    if not DEBUG:
        random_sleep(20, 0.5)  # Avoid hitting the exact second
    alert_mode = str(data.get("alert_mode", "always"))
    last_values = list(data.get("last_values", []))
    new_values = list()
    result = str(data["return"])

    driver.get(data["url"])
    wait_for_element(data["xpath"][0])
    random_sleep(1)

    for xpath in data["xpath"]:
        search = driver.find_elements(by=By.XPATH, value=xpath)
        if not search:
            result = re.sub(r"(\$\w+)", "NaN", result)
            continue
        value = search[0].text.replace("\n", " ").strip()
        new_values.append(value)
        result = re.sub(r"(\$\w+)", value, result, 1)

    data['last_values'] = new_values
    if DEBUG:
        print(new_values)
    if alert_mode == "always" or not last_values:
        return result
    for i in range(len(last_values)):
        if new_values[i] != last_values[i]:
            return result


def wait_for_element(xpath, timeout=10):
    try:
        random_sleep(0.2)
        WebDriverWait(driver, timeout, poll_frequency=0.2).until(
            expected_conditions.presence_of_element_located((By.XPATH, xpath))
        )
        return driver.find_elements(by=By.XPATH, value=xpath)
    except TimeoutException:
        return None


# SCHEDULER

def _next_time(data):
    target = datetime.now()
    year = target.year
    month = data.get("month", target.month)
    day = data.get("day", target.day)
    hour = data.get("hour", target.hour)
    minute = data.get("minute", target.minute)
    second = data.get("second", int(random() * 60))

    target = datetime(year, month, day, hour, minute, second)
    if target > datetime.now():
        return target.timestamp()
    if "month" in data:
        return datetime(year + 1, month, day, hour, minute, second).timestamp()
    elif "day" in data:
        if month == 12:
            return datetime(year + 1, 1, day, hour, minute, second).timestamp()
        else:
            return datetime(year, month + 1, day, hour, minute, second).timestamp()
    elif "hour" in data:
        return (target + timedelta(days=1)).timestamp()
    elif "minute" in data:
        return (target + timedelta(hours=1)).timestamp()
    elif "second" in data:
        return (target + timedelta(minutes=1)).timestamp()
    else:
        print("Error: no valid schedule set. Defaulting to tomorrow.")
        return (target + timedelta(days=1)).timestamp()

def _next_loop(data):
    offset = 0
    if "seconds" in data:
        offset += data["seconds"]
    if "minutes" in data:
        offset += 60 * data["minutes"]
    if "hours" in data:
        offset += 60 * 60 * data["hours"]
    if "days" in data:
        offset += 60 * 60 * 24 * data["days"]
    if "weeks" in data:
        offset += 60 * 60 * 24 * 7 * data["weeks"]
    if "months" in data:
        offset += 60 * 60 * 24 * (365.25 / 12) * data["months"]
    if "years" in data:
        offset += 60 * 60 * 24 * 365.25 * data["years"]
    return datetime.now().timestamp() + offset

def next_timestamp(job, first=False):
    def by_time():
        data = job["time"]
        if "timestamp" in data:
            return float(data["timestamp"])
        return _next_time(data)
    if not DEBUG and first and "time" in job:
        return by_time()
    elif "loop" in job:
        data = job["loop"]
        return _next_loop(data)
    elif "time" in job:
        return by_time()

def random_sleep(seconds, noise=0.1):
    sleep((random() * 2 * noise * seconds) + (seconds * (1 - noise)))


def wait_for_timestamp(goal):
    if goal < 0:
        return False
    while True:
        delta = goal - datetime.now().timestamp()
        half = int(delta / 2)
        if DEBUG:
            print(f"Seconds left: {round(delta, 1)}")
        if half > 1:
            sleep(half)
        elif delta > 0:
            sleep(delta)
            return True
        else:
            return True


if __name__ == "__main__":
    runtime = {}
    for job in jobs:
        runtime[next_timestamp(job, first=True)] = job
    while True:
        next = min(runtime.keys())
        job = runtime[next]
        remainder = round(next - datetime.now().timestamp(), 1)
        if DEBUG:
            print(
                f"Next in the queue: {job['name']} at {datetime.fromtimestamp(next)} ({remainder} seconds)"
            )

        wait_for_timestamp(next)

        if DEBUG:
            print(f"Triggered job: {job['name']} at {datetime.now()}")
        if job["type"] == "selenium":
            result = selenium(job["data"])
            if result:
                print(result + " - " + job["name"])

        runtime[next_timestamp(job)] = runtime.pop(next)
