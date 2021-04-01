import datetime

from pymongo import *
import json
import string

table = str.maketrans(dict.fromkeys(string.punctuation))  # OR {key: None for key in string.punctuation}
import re


def main():
    # connect to the server and build the database and collections
    port = input("Enter a port number you are connecting to : ")  # prompt the user for the connection port number
    client = MongoClient('mongodb://localhost:{}'.format(port))  # connect to the server

    db = client['291db']  # open the database

    if "Posts" in db.list_collection_names():  # check if already exists the collection
        db['Posts'].drop()  # drop if does
    if "Votes" in db.list_collection_names():
        db['Votes'].drop()
    if "Tags" in db.list_collection_names():
        db["Tags"].drop()

    posts = db["Posts"]  # connect to each collection
    votes = db["Votes"]
    tags = db["Tags"]

    print("Inserting data into database..............")
    with open('Posts.json') as f:  # open the Posts file
        file_data = json.load(f)  # load in the json data

    posts.insert_many([terms(i) for i in file_data['posts']['row']])  # inseart into the collection
    f.close()  # close the file
    with open('Votes.json') as f:
        file_data = json.load(f)

    votes.insert_many(file_data['votes']['row'])
    f.close()
    with open('Tags.json') as f:
        file_data = json.load(f)

    tags.insert_many(file_data['tags']['row'])
    f.close()
    print("Creating the index for the terms ...................")  # create the index for terms

    posts.create_index("terms")
    print("you are all set !")


def terms(row):
    # build the terms of a post
    if "Body" in row:  # if post has a body, split the words by spaces and punctuations
        words = row["Body"].translate(table).split()
        new_words = [i.lower() for i in words if len(i) >= 3]   #select the words that have 3 or more chars
    else:
        new_words = list()          #if there is no such a field, create a empty list
    if "Title" in row:
        words2 = row["Title"].translate(table).split()      #collect terms from title
        new_words2 = [i.lower() for i in words2 if len(i) >= 3]
    else:
        new_words2 = list()

    if "Tags" in row:
        search_results = re.findall(r'\<.*?\>', row["Tags"])    #collect terms from Tags
        for each in search_results:
            word = each[1:len(each) - 1]           #split by < >
            if len(word) >= 3:
                new_words2.append(word.lower())

    result = new_words + new_words2
    row["terms"] = list(set(result))            #create term field
    return row


main()
