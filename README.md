# 🔃 TaskRunner

[![GNU GPL License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/Confiqure/TaskRunner/blob/master/LICENSE)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/Confiqure)](https://github.com/Confiqure)

Task scheduler to queue and run various tasks through selenium. Runs on spare laptop during the day.

## TODO

* Record logs (similar to 99PartyPlanner)
* Send push to phone

## ⚙️ Install

First, install the latest version of Python 3.x.

Next, install required dependencies.

```shell
pip install -r requirements.txt
```

Next, save a chromedriver executable to your PATH. You may download the latest version here: <https://chromedriver.chromium.org/downloads>

Finally, build a proper `jobs.json` database for the runner using `jobs-example.json` as an example.

## 🐦 Usage

```shell
python runner.py
```

## 🤝 Contributing

Contributions, issues and, feature requests are welcome! Feel free to check the [issues page](https://github.com/Confiqure/TaskRunner/issues).

## 📝 License

Copyright © 2022 Dylan Wheeler.
This project is [GNU GPU](https://github.com/Confiqure/TaskRunner/blob/master/LICENSE) licensed.
