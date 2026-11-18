from typing import List
import argparse
from uuid import uuid4
from google.cloud.firestore import Client
from google.cloud.firestore_v1.base_query import FieldFilter

db = Client()

def disable_user_token(token, hard_disable: bool = False):
    user_id = get_token_id(token)
    if hard_disable:
        db.collection('users').document(user_id).delete()
    else:
        db.collection('users').document(user_id).update({"valid": False})

def get_token_id(token: str):
    docs = db.collection('users').where(filter = FieldFilter('token', '==', token)).stream()
    for doc in docs:
        return doc.id
    raise RuntimeError("Token not found in the database")

def process_arguments():
    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description = "Token generator",
                                     formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f',
                        nargs = '?',
                        dest = "f",
                        help = "If set the token will be removed from the database",
                        type = bool,
                        default = False)
    
    parser.add_argument('-t',
                        nargs = '?',
                        dest = "t",
                        help = "Token to disable",
                        type = str)
    
    # Parse the commandline
    args = parser.parse_args()
    
    if args.t == None:
        raise RuntimeError("Must provide the token")
    
    return args

if __name__ == '__main__':
    args = process_arguments()
    disable_user_token(args.t, args.f)
    