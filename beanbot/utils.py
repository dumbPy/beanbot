
def format_transaction(transaction:dict[str,str])->str:
    return '```beancount\n{}\n```'.format(transaction['content'])