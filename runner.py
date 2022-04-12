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
    driver.get(data["url"])
    search = driver.find_elements(by=By.XPATH, value=data["xpath"])
    if not search:
        return False
    mode = data.get("mode", "always")
    last_value = data.get("last_value", None)
    value = search[0].text
    if mode == "different" and value == last_value:
        return False
    data["last_value"] = value
    return re.sub(r"(\$\w+)", value, data["return"])


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


def next_timestamp(job):
    sch = job["schedule"]
    if "timestamp" in sch:
        return float(sch["timestamp"])

    target = datetime.now()
    year = target.year
    month = sch.get("month", target.month)
    day = sch.get("day", target.day)
    hour = sch.get("hour", target.hour)
    minute = sch.get("minute", target.minute)
    second = sch.get("second", int(random() * 60))

    target = datetime(year, month, day, hour, minute, second)
    if target > datetime.now():
        return target.timestamp()
    if "month" in sch:
        return datetime(year + 1, month, day, hour, minute, second).timestamp()
    elif "day" in sch:
        if month == 12:
            return datetime(year + 1, 1, day, hour, minute, second).timestamp()
        else:
            return datetime(year, month + 1, day, hour, minute, second).timestamp()
    elif "hour" in sch:
        return (target + timedelta(days=1)).timestamp()
    elif "minute" in sch:
        return (target + timedelta(hours=1)).timestamp()
    elif "second" in sch:
        return (target + timedelta(minutes=1)).timestamp()
    else:
        print("Error: no valid schedule set. Defaulting to tomorrow.")
        return (target + timedelta(days=1)).timestamp()


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
        runtime[next_timestamp(job)] = job
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
