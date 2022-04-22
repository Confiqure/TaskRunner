from datetime import datetime, timedelta
from random import random
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from time import sleep

import json
import re
import winsound

DEBUG = True
JOBS = "jobs.json"

driver = webdriver.Chrome()
with open(JOBS, "r") as data:
    jobs = json.load(data)


# SELENIUM


def selenium(data):
    if not DEBUG:
        random_sleep(10, 0.5)  # Avoid hitting the exact second
    result = str(data["return"])
    new_values = list()

    driver.get(data["url"])
    wait_for_element(data["vars"][0]["xpath"])
    random_sleep(1)

    alert = False
    for var in data["vars"]:
        search = driver.find_elements(by=By.XPATH, value=var["xpath"])
        if not search:
            result = re.sub(r"(\$\w+)", "NaN", result)
            continue
        value = search[0].text.replace("\n", " ").strip()
        new_values.append(value)
        result = re.sub(r"(\$\w+)", value, result, 1)
        test = var.get("alert")
        if test is None:
            alert = True
        elif test["type"] == "contains" and test["value"] in value:
            alert = True
        elif test["type"] == "eq" and test["value"] == value:
            alert = True
        elif test["type"] == "neq" and test["value"] != value:
            alert = True
            test["value"] = value
        elif test["type"] == "neq_num":
            value = float("".join(re.findall(r"[\d\.]+", value)))
            diff = value - float(test["value"])
            if diff == 0:
                continue
            elif diff > 0:
                diff = "+" + str(diff)
            else:
                diff = str(diff)
            if diff.endswith(".0"):
                diff = diff[:-2]
            result = result.replace("$diff", diff)
            alert = True
            test["value"] = str(value)
        elif test["type"] in ("gte", "gt", "lte", "lt"):
            value = float("".join(re.findall(r"[\d\.]+", value)))
            if test["type"] == "gte" and value >= test["value"]:
                alert = True
            elif test["type"] == "gt" and value > test["value"]:
                alert = True
            elif test["type"] == "lte" and value <= test["value"]:
                alert = True
            elif test["type"] == "lt" and value < test["value"]:
                alert = True
            if alert:
                test["value"] = value

    if DEBUG:
        print(alert, new_values)
    if alert:
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


def interval_secs(job):
    offset = 0
    data = job["interval"]
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
    return offset


def next_timestamp(job, first=False):
    def by_time():
        data = job["start_time"]
        if "timestamp" in data:
            return float(data["timestamp"])
        return _next_time(data)

    if not DEBUG and first and "start_time" in job:
        return by_time()
    elif "interval" in job:
        return datetime.now().timestamp() + interval_secs(job)
    elif "start_time" in job:
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
            print(f"{round(delta, 1)}s")
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
    for time in sorted(runtime.keys()):
        job = runtime[time]
        print(
            f"{job['name']} at {datetime.fromtimestamp(time)} and every {round(interval_secs(job) / 60, 1)}m"
        )
    while True:
        next = min(runtime.keys())
        job = runtime[next]
        mins = round((next - datetime.now().timestamp()) / 60, 1)

        print(f"Next in the queue: {job['name']} starting in {mins}m")
        wait_for_timestamp(next)
        if DEBUG:
            print(f"Triggered job: {job['name']} at {datetime.now()}")

        if job["type"] == "selenium":
            result = selenium(job["data"])
        if result:
            print(result + " - " + job["name"])
            winsound.Beep(500, 1000)

        with open(JOBS, "w") as save:
            json.dump(jobs, save)
        runtime[next_timestamp(job)] = runtime.pop(next)
