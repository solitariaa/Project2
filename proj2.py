import datetime

from pymongo import *
import json
import string

table = str.maketrans(dict.fromkeys(string.punctuation))  # OR {key: None for key in string.punctuation}
import re


def main():
    # connect to the server and build the database and collections
    port = input("Enter a port number you are connecting to : ")  # obtain the port number from user
    client = MongoClient('localhost', int(port))  # connect to the local server
    db = client['291db']  # connect to database
    # following lines are used for the test
    '''
    if "Posts" in db.list_collection_names():
        db['Posts'].drop()
    if "Votes" in db.list_collection_names():
        db['Votes'].drop()
    if "Tags" in db.list_collection_names():
        db["Tags"].drop()
    '''

    posts = db["Posts"]  # connect to each collection
    votes = db["Votes"]
    tags = db["Tags"]
    '''
    print("Inserting data into database..............")
    with open('Posts.json') as f:
        file_data = json.load(f)

    posts.insert_many([terms(i) for i in file_data['posts']['row'] ])

    with open('Votes.json') as f:
        file_data = json.load(f)

    votes.insert_many(file_data['votes']['row'])
    
    with open('Tags.json') as f:
        file_data = json.load(f)

    tags.insert_many(file_data['tags']['row'])
    
    print("Creating the index for the terms ...................")


    posts.create_index("terms")

    '''
    a = input(
        "Do you want to provide a user id (type y to enter user id, type others to skip) : ")  # prompt the user for user id
    if a == 'y':  # if user want to input a id, then show the user information on his posts
        uid = user_show(posts, votes)
    else:
        uid = None  # other wise uid is none
    while True:  # forever loop unless return by the user when he choose to exit
        try:  # handle all the errors to make sure the program run non-stop
            action = menu()  # obtain the user action and show the current menue
            if action == '0':  # according to the action from the user, execute different funtions
                return 0
            if action == '1':
                post_qn(posts, uid, tags)
            if action == '2':
                search(posts, uid, votes)
            if action == '3':
                answer(posts, uid, None)
            if action == '4':
                list_answers(posts, None, uid, votes)
            if action == '5':
                vote(posts, uid, None, votes)
        except:
            continue


def search(posts, uid2, votes):
    # funtion to search the posts with user provided keywords
    key_words = input(
        "please enter the key words you want to search for, separated with space(eg. sql nosql mysql) : ")  # prompt the user for the keywords list
    keys = key_words.lower().split()  # put all keywords into a list
    all_posts = []  # track the post that already showed
    for each in keys:  # iterate through the keywords to search
        if len(each) >= 3:  # if provided keyword has length 3 or more, search through the terms
            result = posts.find({"terms": {'$in': [each.lower()]}})
            for every_post in result:  # result gives back all the post, for each post, show on the screen
                if every_post['Id'] not in all_posts:
                    all_posts.append(every_post["Id"])
                    print("Id  : ", every_post["Id"])
                    if every_post['PostTypeId'] == '1':  # if current post is a question, show details
                        print("      This is a question post: ")
                        print("      Title : ", every_post["Title"])
                        print("      creationDate : ", every_post["CreationDate"])
                        print("      score: ", every_post["Score"])
                        print("      answerCount: ", every_post["AnswerCount"])


        else:  # if keyword has length less than 3
            query = {
                '$or': [
                    {
                        'Title': {
                            '$regex': re.compile(r"(?i){}".format(each.lower()))
                        }
                    }, {
                        'Body': {
                            '$regex': re.compile(r"(?i){}".format(each.lower()))
                        }
                    }, {
                        'tags': {
                            '$regex': re.compile(r"(?i){}".format(each.lower()))
                        }
                    }
                ]
            }
            result = posts.find(query)  # perform above query to partially search the existance from all posts
            for every_post in result:  # print the result of search
                if every_post['Id'] not in all_posts:
                    all_posts.append(every_post["Id"])
                    print("Id  : ", every_post["Id"])
                    if every_post['PostTypeId'] == '1':
                        print("     Title : ", every_post["Title"])
                        print("     creationDate : ", every_post["CreationDate"])
                        print("      score: ", every_post["Score"])
                        print("      answerCount: ", every_post["AnswerCount"])

    choice = input(
        "Do you want to check the complete information of a question?(y/n): ")  # after the search, prompt the user to conduct further action
    if choice == 'y':
        check_id = input("please enter a post id : ")  # get the id that the user want to check
        result = list(posts.find({"Id": check_id}))  # find the post
        if result == []:  # check if this is a valid post
            print("No such a post!!!!!")
            return
        if result[0]["PostTypeId"] != '1':  # check if post is a question
            print("Not a question!!")
            return
        for each in result[0].keys():  # print all fields of the required post
            print("{0:20}: ".format(each), result[0][each])
        if 'ViewCount' in result[0].keys():  # increment the view count
            count = result[0]['ViewCount']
            count += 1
            posts.update_one({"Id": result[0]['Id']}, {"$set": {"ViewCount": count}})

        choice = input("do you want to answer this question? (y/n): ")  # prompt the user for answer action
        if choice == 'y':
            answer(posts, uid2, result[0]['Id'])
        choice = input(
            "do you want to see all the answers of this question? (y/n): ")  # prompt the user for list_answers action on current qn
        if choice == 'y':
            list_answers(posts, result[0]['Id'], uid2, votes)
        choice = input(
            "Do you want to vote on the question you selected? (y/n): ")  # user is able to vote under this question as well
        if choice == 'y':
            vote(posts, uid2, result[0]['Id'], votes)


def list_answers(posts, pid, uid, votes):
    # given a pid from user, list all the answers of this question
    if pid == None:  # if there is no pid given, prompt the input of  pid
        pid = input("Please enter a post id of the question you want to list the answers of: ")
        result = list(posts.find({"Id": pid}))

        if result == []:  # check the validity of pid
            print("Not a valid pid!!!!!!!!!!!!!!!")
            return
        if result[0]["PostTypeId"] != '1':  # check if given pid is a question or not
            print("This is not a question!!!")
            return

    accept_id = None  # store the answer id which is accepted answer of current qn
    result = list(posts.find({"Id": pid}))  # perform query to find the current post
    if "AcceptedAnswerId" in result[0].keys():  # if there is a accepted answer, show at the top
        accept_id = result[0]["AcceptedAnswerId"]
        result = list(posts.find({"Id": accept_id}))
        print("{0:20}: ".format('*Id'), result[0]["Id"])  # show the id with a star
        if len(result[0]["Body"]) <= 80:  # show first 80 chars of the body
            print("  {0:20}: ".format('body'), result[0]["Body"])
        else:
            print("  {0:20}: ".format('body'), result[0]["Body"][0:80])
        print("  {0:20}: ".format('createDate'), result[0]["CreationDate"])
        print("  {0:20}: ".format('Score'), result[0]["Score"])

    result = posts.find({"ParentId": pid})  # query over all the answers of current qn
    for each in result:  # for each answer, print out the information
        if each["Id"] != accept_id:
            print("{0:20}: ".format('Id'), each["Id"])
            if len(each["Body"]) <= 80:
                print("  {0:20}: ".format('body'), each["Body"])
            else:
                print("  {0:20}: ".format('body'), each["Body"][0:80])
            print("  {0:20}: ".format('createDate'), each["CreationDate"])
            print("  {0:20}: ".format('Score'), each["Score"])
    choice = input(
        "Do you want to select one answer to see full info? (y/n): ")  # the user should be able to see more details about a selected question
    if choice == 'y':
        check_id = input("please enter a post id of the answer you want to see: ")
        result = list(posts.find({"Id": check_id}))
        if result == []:  # check the validity of the selected post
            print("No such a post!!!!!")
            return
        if result[0]["PostTypeId"] != '2':
            print("Not a Answer!!")
            return
        for each in result[0].keys():
            print("{0:20}: ".format(each), result[0][each])
        if 'ViewCount' in result[0].keys():  # if current answer has a viewCount field, increment it
            count = result[0]['ViewCount']
            count += 1
            posts.update_one({"Id": result[0]['Id']}, {"$set": {"ViewCount": count}})

        choice = input(
            "Do you want to vote oh this answer?(y/n) : ")  # the user should be able to vote under this answer
        if choice == 'y':
            vote(posts, uid, result[0]['Id'], votes)


def vote(posts, uid, pid, votes):
    # function for user to vote under a post
    if pid == None:  # if pid is not provided, prompt the user for a pid
        pid = input("Please enter a post id of the post you want to vote: ")
        result = list(posts.find({"Id": pid}))

        if result == []:  # check the validity of the post
            print("Not a valid pid!!!!!!!!!!!!!!!")
            return
    if uid != None:  # check if current user has already voted for this post
        result = list(votes.find({"PostId": pid, "UserId": uid}))
        if result != []:
            print("This user has voted for this post already, please dont vote again!!!")
            return

    dic = {}  # dictionary to store the vote information
    if not hasattr(vote, "counter"):  # system assigned id
        vote.counter = 0
    vote.counter += 1
    vid = 'v{0:04d}'.format(vote.counter)
    result = list(votes.find({"Id": vid}))
    while result != []:  # check the uniqueness  of the Id
        vote.counter += 1
        vid = 'v{0:04d}'.format(vote.counter)
        result = list(votes.find({"Id": vid}))

    dic['Id'] = vid         #set all the vote information
    dic['PostId'] = pid
    dic["VoteTypeId"] = '2'
    dic["CreationDate"] = str(datetime.datetime.now())
    if uid != None:         #if this user is logged in, set the uid to current user
        dic["UserId"] = uid
    votes.insert_one(dic)

    result = list(posts.find({"Id": pid}))      #for the post that has been voted, increment the score
    if 'Score' in result[0].keys():
        count = result[0]['Score']
        count += 1
        posts.update_one({"Id": result[0]['Id']}, {"$set": {"Score": count}})
    print("Vote successfully !!!")


def answer(posts, uid, pid):
    #funtion to perform the answer action
    if pid == None:     #if pid is not provided, prompt the user for a pid
        pid = input("Please enter a post id of the question you want to answer under: ")
        result = list(posts.find({"Id": pid}))

        if result == []:    #check the validity of the pid
            print("Not a valid pid!!!!!!!!!!!!!!!")
            return
        if result[0]["PostTypeId"] != '1':
            print("This is not a question!!!")
            return

    body = input("please enter your answer text here : ")       #prompt the user for the answer body text
    if not hasattr(answer, "counter"):      #system assigned Id
        answer.counter = 0
    answer.counter += 1
    aid = 'a{0:04d}'.format(answer.counter)
    result = list(posts.find({"Id": aid}))
    while result != []:     #check the uniqueness of the Id
        answer.counter += 1
        aid = 'a{0:04d}'.format(answer.counter)
        result = list(posts.find({"Id": aid}))

    dic = {}        #dictionary used to store all the posts information
    dic['Id'] = aid
    dic["PostTypeId"] = '2'
    dic["ParentId"] = pid
    dic["CreationDate"] = str(datetime.datetime.now())
    if None != uid:         #set the current user as OwnerId
        dic['OwnerUserId'] = uid
    dic["Score"] = 0
    dic["Body"] = body
    dic["CommentCount"] = 0
    dic["ContentLicense"] = "CC BY-SA 2.5"
    terms(dic)              #build a term field for sake of searching
    posts.insert_one(dic)   #inseart data back to collection

    result = list(posts.find({"Id": pid}))
    if 'AnswerCount' in result[0].keys():       #if answerCount is in the field, increment it
        count = result[0]["AnswerCount"]
        count += 1
        posts.update_one({"Id": result[0]['Id']}, {"$set": {"AnswerCount": count}})

    print("successfully answered")


def menu():
    #function used to show the menu list
    print('\n----------------------------------main menu------------------------\n')
    print('1 : Post a question\n')
    print("2 : Search for question\n")
    print("3 : Answer a question \n")
    print("4 : List answers for a question\n")
    print("5 : Vote\n")
    print("0 : Exit the program\n")
    c = input("Select a action (0 - 5) : ") #prompt the user for the action
    return c #return the action to main function


def post_qn(posts, uid, tags_db):
    #function to perform a post question action
    if not hasattr(post_qn, "counter"): #system assigned Id
        post_qn.counter = 0
    post_qn.counter += 1
    pid = 'p{0:04d}'.format(post_qn.counter)
    tid = 'p{0:04d}'.format(post_qn.counter)
    result = list(posts.find({"Id": pid}))
    while result != []: #check the uniqueness of the Id
        post_qn.counter += 1
        pid = 'p{0:04d}'.format(post_qn.counter)
        result = list(posts.find({"Id": pid}))

    dic = {}    #dictionary to store all the post info
    dic["Id"] = pid
    title = input("Please provide a title for your post: ")
    body = input("Please provide a body for your post: ")
    if uid != None:     #if current Uid is not None, prompt if want to change the uid

        change = input("Do you want to post under current user id? (y: yes, n: change uid to post) : ")
        if change != 'y':
            uid = input("What uid do you want to post with? : ")
    else:
        change = input("you currently have no uid, do you want to provide one to post? : (y: provide uid, n: skip ):")
        if change == 'y':
            uid = input("Please enter the uid you want to post with: ")
    tags = []       #tags list
    choice = input(
        "Do you want to provide any tags for your post? (y/n, any input other than those 2 will be treated as no) : ")
    if choice == 'y':       #obtain the tags from the user
        tags_txt = input("Put all your tags in one line separated with space (eg. hardware sql noSql): ")
        tags = tags_txt.lower().split(' ')      #put all the tags into lower case
    tag_string = ""
    for each in tags:                       #put tags in right format to store into the tag field
        tag_string += '<' + each + '>'
    if tags != []:      #if there is at least one tag
        dic["Tags"] = tag_string            #store the tag field
    dic["CreationDate"] = str(datetime.datetime.now())      #initilize all the info
    dic["PostTypeId"] = '1'
    dic['Body'] = body
    dic["Title"] = title
    dic["Score"] = 0
    dic["ViewCount"] = 0
    dic["CommentCount"] = 0
    dic["AnswerCount"] = 0
    dic["FavoriteCount"] = 0
    dic["ContentLicense"] = "CC BY-SA 2.5"
    if None != uid:
        dic['OwnerUserId'] = uid
    terms(dic)      #extract all the terms from body and title
    posts.insert_one(dic)

    for each in tags:   #update the tag collection
        result = list(tags_db.find({"TagName": each}))  #query the existing tags
        if result != []:        #if there is already such a tag, update the count
            count = result[0]["Count"]
            count += 1
            tags_db.update_one({"TagName": each}, {"$set": {"Count": count}})
        else:   #else create a doc with the tag name
            result = list(tags_db.find({"Id": tid}))
            while result != []:
                post_qn.counter += 1
                tid = 't{0:04d}'.format(post_qn.counter)
                result = list(tags_db.find({"Id": tid}))
            dic2 = {}
            dic2["TagName"] = each
            dic2["Count"] = 1
            dic2["Id"] = tid
            post_qn.counter += 1
            tags_db.insert_one(dic2)


def user_show(posts, votes):
    #function used to show the info of current user
    uid = input("please enter a user id you want to perform on : ")     #prompt the user to enter a uid
    while True:     #check if the uid is valid or not
        try:
            int(uid)
            break
        except:
            uid = input("not a valid user id, please enter again: ")            #re-prompt the input of uid
    query = [
        {
            '$match': {
                'OwnerUserId': uid
            }
        }, {
            '$group': {
                '_id': '$PostTypeId',
                'count': {
                    '$sum': 1
                },
                'avg': {
                    '$avg': '$Score'
                }
            }
        }, {
            '$sort': {
                '_id': 1
            }
        }
    ]
    result = list(posts.aggregate(query))#seach for all posts from the user
    while result == []:     #if there is no post, throw a warning
        key = input("No posts for this user can be found, press r to re-enter a uid , press other keys to continue : ")
        if key == 'r':      #if the user want to re-enter id
            uid = input("please enter a user id you want to perform on : ")
            query = [
                {
                    '$match': {
                        'OwnerUserId': uid
                    }
                }, {
                    '$group': {
                        '_id': '$PostTypeId',
                        'count': {
                            '$sum': 1
                        },
                        'avg': {
                            '$avg': '$Score'
                        }
                    }
                }, {
                    '$sort': {
                        '_id': 1
                    }
                }
            ]
            result = list(posts.aggregate(query))
        else:
            return uid      #if not return the current uid
    if result[0]["_id"] == '1':       #
        print("number of question this user posted: {}\nAverage score of questions: {}\n".format(result[0]['count'],
                                                                                                 result[0]['avg']))
    else:   #if there is no questions posted, print the number of answers only
        print("there is no posted questions from this user yet\n")
        print("number of answers this user posted: {}\nAverage score of answers: {}\n".format(result[0]['count'],
                                                                                              result[0]['avg']))
    if len(result) == 2:    #if there is both qns and answers from the user, post both

        print("number of answers this user posted: {}\nAverage score of answers: {}\n".format(result[1]['count'],
                                                                                              result[1]['avg']))
    else:   #else post no answers
        if result[0]["_id"] == '2':
            print("there is no posted questions from this user yet\n ")
        else:
            print("there is no posted answers from this user yet\n ")


    query = [
        {
            '$match': {
                'OwnerUserId': uid
            }
        }, {
            '$lookup': {
                'from': 'Votes',
                'localField': 'Id',
                'foreignField': 'PostId',
                'as': 'search'
            }
        }, {
            '$project': {
                'size': {
                    '$size': '$search'
                }
            }
        }, {
            '$group': {
                '_id': 1,
                'count': {
                    '$sum': '$size'
                }
            }
        }
    ]
    # print("calculating the number of votes , this might take a while ......")
    # result = list(posts.aggregate(query))

    result = list(votes.find({'UserId': uid}))      #query over the votes to find how many votes from the user
    print("the number of votes registered for the user: ", len(result)) #print the votes number
    return uid


def terms(row):
    # build the terms of a post
    if "Body" in row:       #split out all the terms from the body
        words = row["Body"].translate(table).split()
        new_words = [i.lower() for i in words if len(i) >= 3]       #only store the words with len>= 3
    else:
        new_words = list()
    if "Title" in row:  #split out all the terms from the title
        words2 = row["Title"].translate(table).split()
        new_words2 = [i.lower() for i in words2 if len(i) >= 3]
    else:
        new_words2 = list()
    if "Tags" in row:           #store all the terms from the tags
        search_results = re.findall(r'\<.*?\>', row["Tags"])
        for each in search_results:
            word = each[1:len(each) - 1]
            if len(word) >= 3:
                new_words2.append(word.lower())

    result = set(new_words + new_words2 )
    row["terms"] = list(result)
    return row


main()
