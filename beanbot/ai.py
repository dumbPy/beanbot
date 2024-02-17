import os
import logging
from beanbot.utils import get_date_in_locale
from langchain_openai.chat_models import ChatOpenAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

TRANSACTION_PROMPT="""
Below are the accounts in the user's beancount file.
* Given a message from the user, you are expected to return either
    1. one or more beancount transactions or directives
    2. note eg. `<today's date> note <account> <message>`
    3. answer a question related to a given query.
    4. echo the user's message if it is already a beancount transaction or directive.
which can then be appended to the user's transactions.beancount file if needed.

Instructions:
* Today's date is {date} in YYYY-MM-DD format.
* Make sure you use account names from the user's beancount file if they appear even slightly similar.
* You shall open a new account only if the user's message contains a completely new name,
    but make sure you conserve the account naming pattern from the accounts.beancount, and use 2020-01-01 as the account open date for all new accounts,
* Use todays date for all transactions unless the transaction mentions some day eg. yesterday, then use the date accordingly for it.
* Your output should be strictly beancount compatible. If the user asks for some information that cannot be in beancount format, write it in form of a note.
* If adding pad directive, use date atleast 1 day before balance directive date.
* For padding, use format `<date> pad <AccountToPad> <PadFrom>`
    AccountToPad is always an Asset or a Liability account while PadFrom is always an Equity or Expense account.
    Do not include amount or currency in the pad directive.
* The values in postings of a transaction MUST sum to zero. A posting without a value would be considered to take value such that it balances the other postings to zero. eg. If postingA has value -100 INR while postingB has value 500 INR, and postingC has no value, it means postingC will be equal to -400 INR to balance the transaction to zero (-100 + 500 - 400 = 0)
* Payees are optional and are strictly names of a person or a company. If the name exists in accounts in any form, use that instead of from the message. eg. If the instruction includes John Doa while accounts include John Doe, use "John Doe" instead of John Doa.

Beancount Format for Transaction:
YYYY-MM-DD * "<optional payee>" "<description>"       
	<account 1>	<value 1>  <optional currency>             // these are called postings
	<account 2>	<value 2>  <optional currency>
	...

Format for account opening:
YYYY-MM-DD open <account>

Format for Note:
YYYY-MM-DD note <account to attach note to> "<Note>"

Format for balance entry:
YYYY-MM-DD balance <account> <amount>


```accounts.beancount
{accounts}
```

User Instruction: {message}
```beancount
"""


def get_model():
    provider = os.environ.get('PROVIDER', '')
    if provider not in ['openai', 'google']:
        provider = 'google'
    if provider == 'openai':
        return ChatOpenAI(model='gpt-3.5-turbo-0125')
    else:
        return ChatGoogleGenerativeAI(model='gemini-pro')



logger = logging.getLogger(__name__)


def generate_transactions(userMessage:str, accounts:str) -> list[str]:
    logger.info(f"Generating transaction for {userMessage}")
    prompt = ChatPromptTemplate.from_template(TRANSACTION_PROMPT)
    # PROMPT = TRANSACTION_PROMPT.format(get_date_in_locale(), accounts, userMessage)
    logger.debug(f"Prompt: {prompt.invoke({'date': get_date_in_locale(), 'accounts': accounts, 'message': userMessage})}")
    model = (prompt | get_model())
    chat_completion = model.invoke({'message': userMessage, 'accounts': accounts, 'date': get_date_in_locale()})

    outputs = chat_completion.content.strip('```\n')
    if not outputs:
        raise ValueError("No Transactions were generated for the given input")
    return [outputs]

if __name__ == "__main__":
    print(generate_transactions("I bought a coffee", "2020-01-01 open Assets:Bank:Checking"))
