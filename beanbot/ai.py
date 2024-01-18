import openai
import logging
import datetime
import pytz


TRANSACTION_PROMPT="""
Below are the accounts in the user's beancount file.
* Given a message from the user, you are expected to return either
    1. one or more beancount transactions or directives
    2. note eg. `<today's date> note <account> <message>`
    3. answer a question related to a given query.
    4. echo the user's message if it is already a beancount transaction or directive.
which can then be appended to the user's transactions.beancount file if needed.

Instructions:
* Today's date is {} in YYYY-MM-DD format.
* You shall open a new account if the user's message contains a new account name, but use 2020-01-01 as the account open date for all new accounts,
* Use todays date for all other transactions.
* Your output should be strictly beancount compatible.
* If adding pad directive, use date atleast 1 day before balance directive date.
* For padding, use format `<date> pad <AccountToPad> <PadFrom>`
    AccountToPad is always an Asset or a Liability account while PadFrom is always an Equity or Expense account.
    Do not include amount or currency in the pad directive.

```accounts.beancount
{}
```

Message: {}
```beancount
"""

logger = logging.getLogger(__name__)

def get_date_in_locale(locale:str='Asia/Kolkata') -> str:
    locale = pytz.timezone('Asia/Kolkata')
    return datetime.datetime.now(locale).strftime('%Y-%m-%d')


def generate_transaction(userMessage:str, accounts:str) -> str:
    logger.info(f"Generating transaction for {userMessage}")
    PROMPT = TRANSACTION_PROMPT.format(get_date_in_locale(), accounts, userMessage)
    logger.info(f"Prompt: {PROMPT}")
    chat_completion = openai.chat.completions.create(
        messages=[
            {
                "role":"system", "content":"You are a beancount bot that accepts instructions from user and returns beancount transactions."
            },
            {
                "role": "user",
                "content": PROMPT
            }
        ],
        model="gpt-3.5-turbo-1106",
        temperature=0.1,
        stop=["```"],

    )
    output = chat_completion.choices[0].message.content
    logger.debug(f"Generated transaction: {output}")
    if output == '':
        return ';; The bot was unable to generate a transaction for this message.'
    return output
