import pywaves as pw
from resources.database import add_to_db

def create_transaction(name, surname, course_id, date, hashcode, private_key):
    try:
        myAddress = pw.Address(privateKey = private_key)
        data = [{'type': 'string', 'key': 'hashcode', 'value': hashcode}]
        transaction = myAddress.dataTransaction(data)
    except Exception as ex:
        raise ex

    add_to_db((hashcode, transaction['id'], date), 'transaction')
    transaction_id = transaction['id']
    return f'https://wavesexplorer.com/tx/{transaction_id}'