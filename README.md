# BEANBOT
A telegram bot that uses ChatGPT to generate transactions.

## Usage
* Upload an `<anyName>.beancount` file to save it as `accounts.beancount` to be used for predicting new transactions
* `/help` to get the available commands.
* `/cat [n] [transactions|archived|accounts]` to print the (optionally last n) transactions from current ledger or archived or from accounts
* `/download [transactions|archived|accounts]` to download current (default) or archived transactions or accounts.
* `/archive` to archive all the transactions in your current ledger
* `/edit [archived]` to enter interactive edit mode that allows you to delete transactions individually.

## Screenshots

## Build
* First clone the repo with
```
git clone https://github.com/dumbPy/beanbot.git
cd beanbot
```

* Create a telegram bot by going to [@BotFather](t.me/BotFather) and notedown the bot token
* Note down your username (you might want to set a new one if it isn't set already). This is used to filter received messages incase someone adds your bot.

* Signup on [openai](https://platform.openai.com/api-keys) and create api keys

* Signup on [filess.io](https://files.io) and create a free mongodb instance. get the mongo uri.

* Edit the `.env` file where we would add the required environment variables related to openai, telegram, and mongo.

## Deploy
* GCP
    You can deploy this to GCP using an always free `e2-micro` instance. 
    
    * Clone the project
    * Add [repository secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository) for each of the environment variables mentioned in [.env](./.env)
    * Create [credentials json](https://stackoverflow.com/a/46290808) for your gcp account and add its content to repository secrets as `GCP_CREDENTIALS`
    * Now you can deploy it using the `Deploy to GCP` Github Action included with the repository and it should deploy it to the e2 micro.

* Self Hosted / Manual
    * Clone the project
    * Edit the `.env` and add all the variables from above
    * Build the docker with
    ```
    docker build -t beanbot:latest .
    ``` 
    and it would have the .env copied inside while building.
    * Run the docker using
    ```
    docker run -d beanbot:latest
    ```
    It needs no port mapping or any new environment variables, since all the required environment variables were already added in `.env`

## Development
Improvements are welcome. 
You can setup the environment with a separate conda env as below
```bash
conda create -n beanbot -y python==3.11 && \
    conda activate beanbot && \
    pip3 install -r requirements.txt
```

And run the bot server in debug mode after editing the `.env` as above, using the `Debug Beanbot` debug config already added.