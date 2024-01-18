# BEANBOT
A telegram bot that uses ChatGPT to generate transactions.

## Functionality
* `/help` to get the available commands.
* `/cat` to print the transactions or `/cat <int>` to print last n transactions
* `/download` and `/download archived` to download current and archived transactions as `transactions.beancount`. This can then be copied to your ledgre
* `/archive` to archive all the transactions in your current ledgre
* `/edit` to enter interactive edit mode that allows you to delete transactions individually. You can also use `/edit archived` similarly.

## Screenshots

## Build and Deploy
* First clone the repo with
```
git clone https://github.com/dumbPy/beanbot.git
cd beanbot
```

* Create a telegram bot by going to t.me/BotFather and notedown the bot token and also notedown your username (you might want to set a new one if it isn't set already)

* Signup on [openai](https://platform.openai.com/api-keys) and create api keys

* Signup on filess.io and create a free mongodb instance. get the mongo uri.

* Edit the `.env` file where we would add the required variables related to openai, telegram, and mongo.
