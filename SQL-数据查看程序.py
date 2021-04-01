import sqlite3
import getpass
import sys


def main(argv):
    # main function glued every functions together to perform whole functionality of this app
    db = sqlite3.connect(argv[1])  # connect to the database by  command line argument
    sql = db.execute
    success = (1, None)  # tuple used in later code to decide the flow of code
    while True:
        try:
            print("-------------------welcome----------------------------------\n")  # print out the initial interface
            choice = input(
                "sign up a new account press 1, log in with an account press 2, exit press 99: ")  # prompt the user for the action
            if int(choice) == 99:
                print("Thank you for using, Bye !!!\n")  # if user chose to exit, then terminate and close the db
                db.close()
                return

            if int(choice) == 1:  # if user wanna create a new account, call signup
                signup(sql)
                db.commit()  # commit the change to db
                continue
            if int(choice) == 2:  # if user wanna log in, call login function and save the return value back into sucess
                success = login(sql)
            if success[0] == 0:
                # successfully logged in and now user can exhibit other behaviours
                uid = success[1]  # obtain the uid of current user
                privilege = sql("select count(*) from privileged where uid = ?;",
                                [uid]).fetchall()  # check the privilege of the current user
                if privilege[0][0] == 1:
                    privilege = 1
                else:
                    privilege = 0
                sign_out = False
                while not sign_out:  # if the sign_out is not turned on, keep staying current menue
                    menu(sql, privilege)  # print menue by calling this menu function
                    try:  # catch all possible errors and handle
                        action = int(input("Enter the number of action you want to conduct : "))
                        if action == 99:  # if user choose to terminate, close the db and return
                            db.close()
                            return
                        if action in range(1, 9):  # if user wanna perform the action, map to correspondent function
                            if action in range(1, 5):  # action for all users
                                fun_dic[action](sql, uid)
                                db.commit()
                            else:
                                if privilege == 1:  # action for privileged user
                                    fun_dic[action](sql, uid)
                                    db.commit()
                        if action == 0:
                            sign_out = True  # if user choose to sign out, go back to original interface
                    except Exception as e :
                        print("!!!!!!!!!!!!!!!!!invalid input!!!!!!!!!!!!!!!!!!!!!!!\n\n")
                        continue

        except:
            continue


def menu(sql, privilege):
    # print user interface
    print("------------------------MENU-----------------------------")
    print("1 : post a question\n")
    print("2 : Search for post\n")
    print("3 : answer\n ")
    print("4 : vote\n")
    if privilege == 1:
        print("5 : mark as accepted\n")
        print("6 : give badge \n")
        print("7 : add a tag\n")
        print("8 : Edit\n")
    print("0 : logout\n")
    print("99: Exit\n")


def check_unique(sql, uid):
    # check if given uid is registered or not to make sure it is unique
    query = sql('Select count(*) from users where uid = ?;', [uid])
    count = query.fetchall()
    return count[0][0] == 0  # return 0 if there is no registered uid


def signup(sql):
    # sign a new account up

    uid = str(input("Please enter your user id (only first 4 characters will be valid) : "))[
          0:4]  # take user input as uid and store the first 4 chars
    while check_unique(sql, uid) is False:  # make sure the uid is unique
        print("This id has been used by other users\n")
        uid = str(input("Please enter your user id (only first 4 character will be valid): "))[0: 4]
    name = input("Please Enter your name: ")  # obtain other infos from user
    city = input("Please Enter your city: ")
    pwd = str(input("Please Enter your password: "))
    print("You are all set and you can log in with this account now!\n ")
    sql("insert into users values (?,?,?,?,date('now'));", (uid, name, pwd, city))  # store the value back into database


def login(sql):
    # log in a user
    uid = str(input("uid: "))  # get the user input uid
    pwd = str(getpass.getpass("Enter your password: "))  # get the user input password
    query = sql("select count(*) from users where uid = ? and pwd = ? ;", (uid, pwd))  # check with the data in database
    result = query.fetchall()
    while result[0][0] == 0:  # if not consistent ask for the following action
        quit = input("incorrect uid or password!!, press q to quit, or press any other button to keep trying: ")
        if quit == "q":
            return (1, null)  # return 1 if login failed
        uid = input("uid: ")
        pwd = getpass.getpass("Enter your password: ")
        query = sql("select count(*) from users where uid = ? and pwd = ? ;", (str(uid), pwd))
        result = query.fetchall()
    return (0, str(uid))  # return 0 and the uid if login successfully


def post_qn(sql, uid):
    # handle user action of posting a question
    if not hasattr(post_qn, "counter"):
        post_qn.counter = 0
    post_qn.counter += 1
    pid = '{0:04d}'.format(post_qn.counter)
    # in case pid already exist, just increament the counter

    query = sql('select * from posts where pid = ?;', [pid])
    while query.fetchall():
        post_qn.counter += 1
        pid = '{0:04d}'.format(post_qn.counter)
        query = sql('select * from posts where pid = ?;', [pid])

    print("-------------------post section-----------------------------")
    title = input("please enter a title for your question: ")
    body = input("please enter the body of your post question: ")
    sql("insert into posts values(?, date('now'), ?, ?, ?)", (pid, title, body, uid))
    sql("insert into questions values (?, ?)", (pid, None))
    print('you successfully posted an question !!!!!\n')


def search(sql, uid):
    # search for the post that contains the certain keywords provided by the user
    print("----------------------------search section-----------------------")
    matching = {}
    name = ['pid', 'pdate', 'title', 'body', 'poster']
    keyword = input("please enter all keywords you wanna search for in one line :")  # get the keywords
    words_lst = keyword.split()  # put those keywords into a list
    for key in words_lst:  # iterate over every keyword to find the posts related
        k = '%' + key + '%'  # put the key word in the format of searching
        query = sql(
            "select pid from posts left outer join tags using (pid) where title like ? or body like ? or tag like ? ; ",
            [k, k, k])
        result = query.fetchall()  # get the searching result
        for each in result:  # for each result, we use a dictionary to record frequency
            if each[0] not in matching.keys():  # if it has not been added into dic, add
                matching[each[0]] = 1
            else:  # else add one to this post
                matching[each[0]] += 1

    order = sorted(matching.items(), key=(lambda kv: (kv[1], kv[0])),
                   reverse=True)  # we sort the dictionary base on the values
    total = len(order)
    if total > 5:  # find out the number of post we can print at first time so that it will not outnumber 5
        printnum = 5
    else:
        printnum = total
    pre = 0;
    end_display = False;
    while total > 0 and end_display == False:  # if there is still posts left, we keep printing
        for i in range(pre, printnum):
            pid = order[i][0]
            query = sql("select * from posts where pid = ?;", [pid])
            result = query.fetchall()
            for s in range(0, 5):
                if s != 0:
                    print("--------", end='')
                print('{0:>10}'.format(name[s]), " : ", result[0][s], "\n")

            query = sql("select count(*) from votes where pid = ?;", [pid])  # find the votes number for certain post
            result = query.fetchall()
            print("--------   voteNum : ", result[0][0])
            print("\n")
            query = sql("select * from questions where pid = ? ;",
                        [pid])  # find out if this post is a question or not, if it is, we print answer numbers
            result = query.fetchall()
            if result:
                query = sql('select count(*) from answers where qid = ?;', [pid])
                result = query.fetchall()
                print("-------- this is a Question post and number of answers : ", result[0][0])  # print answer amount
                print("\n")

        total -= printnum  # update the print number in the next round
        pre = printnum
        if total > 5:  # make sure there will be 5 at most printed next round
            printnum += 5
        else:
            printnum += total
        if total > 0:  # if there is posts left to print, ask if user wanna to keep printing or not
            h = input(
                "Do you want to end the display? Press (n) to keep showing the posts, (y) to end the display here: ")
            if h.lower() == 'y':  # keep printing if answer is yes
                end_display = True
    posting = input(
        "Do you want to select a post to perform post action? (y/n) : ")  # end print and ask for the one user wanna reply to
    if posting.lower() == 'y':
        answer_post(sql, uid)


def answer_post(sql, uid):
    query = sql('select q.pid, p.title  from questions q, posts p where q.pid = p.pid ;')  # Get the id, title, and body from posts.
    result = query.fetchall()
    print("-----------all the Questions----------\n")
    for each in result:
        print("Qestion's title: ", '{0:10}'.format(each[1]) , "  pid: ", each[0])  # Print out the table.
    if not hasattr(answer_post, "counter"):  # If it is the first time to answer, then initialize the counter.
        answer_post.counter = 9999
    answer_post.counter -= 1  # Minus one to make pid as a unique number.
    pid = '{0:04d}'.format(answer_post.counter)

    query = sql('select * from posts where pid = ?;', [pid])  # Find the posts which pid is above.
    while query.fetchall():  # If there is an answer with the same pid, then keep minusing the counter until the pid is unique.
        answer_post.counter -= 1
        pid = '{0:04d}'.format(answer_post.counter)
        query = sql('select * from posts where pid = ?;', [pid])
    print("-----------------answer section----------------------")
    qid = input("Enter the pid of post you want to reply to : ")
    query = sql("select pid from questions where pid = ? ; ",
                [qid])  # Find the pid of questions which equals to the qid inputted above.
    result = query.fetchall()  # Return the post id of questions, which match the users' input.
    if not result:  # If there is no matches, ask for the input again.
        print("The pid you entered is not a Question !!!!!!\n")
        return

    title = input("Please enter a title for your answer: ")
    body = input("Pleas enter the context here : ")
    sql("insert into posts values(?, date('now'), ?, ?, ?);",
        (pid, title, body, uid))  # Add the title and body to the posts and record the time and its unique post id.
    sql("insert into answers values(?, ?) ;", (pid, qid))
    print("successfully answered !!!!!!!!!!!")


def vote(sql, uid):
    query = sql('select pid, title, body from posts;')  # Get the id, title, and body from posts.
    result = query.fetchall()
    print("-----------all the posts ---------\n")
    for each in result:
        print("Post's title: ", '{0:10}'.format(each[1]), "  pid: ", each[0], "  body: ", each[2])  # Print out the table.

    pid = input(
        "Enter the pid of the post you are about to vote for : ")  # Ask the poster id which the user wanted to vote for.
    query = sql("select * from posts where pid = ? ;", [pid])  # Find the post which post id is the user input above.
    if not query.fetchall():  # If the post id doesn't exist, then return an error.
        print("Vote failed, no such a post!!!!")
        return
    query = sql("select * from votes where pid = ? and uid = ? ;", [pid,
                                                                    uid])  # If the post id exists, then return the votes of the post which has been voted by the user.
    if query.fetchall():  # If the vote has been exist, then return an error.
        print("Vote failed, you have already voted for this post before !!!!!!!")
        return

    if not hasattr(vote, "counter"):  # If it is the first time to vote, then initialize the counter.
        vote.counter = 2931
    vote.counter += 1  # And plus one and try to make vno as a unique number.
    vno = vote.counter

    query = sql('select * from votes where vno = ?;', [vno])  # Check if there has been a vote with the same vno.
    while query.fetchall():  # If there is a vote with the same vno, then keep add the counter until the vno is unique.
        vote.counter += 1
        vno = vote.counter
        query = sql('select * from votes where vno = ?;', [vno])

    sql("insert into votes values (?, ?, date('now'), ?);", (pid, vno, uid))  # Record the vote into the table votes.
    print(
        "You successfully voted for this post! Thank you..............................\n")  # Notice the user that he or she has voted a vote successfully.


def mark_post(sql, uid):
    query = sql("select p.pid, p.title from answers a, posts p where a.pid = p.pid;")
    result = query.fetchall()  # Find the post id and title of the questions which are answered.
    print(
        "---------------------------------------------Here are all the answers existed: ------------------------------- \n")
    for each in result:
        print("aid : ", each[0], "                title: ", each[1])  # Print out the answers of each question posted.
    theaid = input("Choose the aid you want to mark as an accepted answer : ")
    query = sql("select * from answers where pid = ? ;", [theaid])
    result = query.fetchall()  # If the id of the answer exits, return its id.
    while not result:  # If there is no match, ask for the input again.
        print("Not a Valid aid !!!!!!")
        theaid = input("Choose the aid you want to mark as an accepted answer : ")
        query = sql("select * from answers where pid = ? ;", [theaid])
        result = query.fetchall()

    query = sql("select q.theaid, q.pid from questions q, answers a where a.qid = q.pid and a.pid = ?;", [theaid])
    result = query.fetchall()  # Get a list of two-dimension tuples which records the answer id and question id.
    pid = result[0][1]  # Get the question id which returned.
    print('\n')
    if result[0][0] == None:  # Check whether the id of the answer is already marked.
        print("You successfully marked an answer! \n")
        sql("update questions set theaid = ? where pid = ?;", [theaid, pid])
        return
    elif result[0][0] == theaid:
        print("This answer is already marked!\n")
        return
    else:  # If the question already get an accepted answer, ask for changing.
        change = input("The question of this answer has already gotten an accepted answer, do you wanna change ? (y/n)")
        if change.lower() == 'y':
            sql("update questions set theaid = ? where pid = ?;", [theaid, pid])    
            print("succeeded!\n")
        return


def give_badge(sql, uid):
    query = sql('select poster, title from posts;')
    result = query.fetchall()  # return a tuple of two-dimension tuples which record all the poster and titles in the table posts.
    print("-----------all the posts and their poster----------")
    for each in result:
        print("Post's title: ", each[1], "                         poster: ",
              each[0])  # Show all of the titles and posters in the table posts.
    uid = input("Which poster(uid) you want to give a badge to? \n")  # Ask the user choose a poster to give a badge.
    query = sql('select * from posts where poster = ? ;', [uid])
    result = query.fetchall()  # Return all of the posts whose poster is the user input above.
    if not result:
        print("Such a poster does not exit!!!!!!!!!!!")  # If the inputted poster doesn't exist, then give an error.
        return
    bname = input("Provide a badge name: ")  # If the inputted poster exists, then give a badge name.
    type = 'silver'
    sql("insert into ubadges values (?, date('now'), ?);",
        [uid, bname])  # Record the badge's name which is added with its given time and given poster.
    query = sql("select * from badges where bname = ?;",
                [bname])  # Find all of the badges which have been existed in the current badges.
    result = query.fetchall()  # Check if the name of badge we give has existed.
    if result:
        pass
    else:  # If it is not existed before, then add it to the current badges.
        sql("insert into badges values (?, ? );", [bname, type])
    print("successfully gave the badge !\n")  # Tell user he or she has successfully given a badge.
    return


def give_tag(sql, uid):
    query = sql('select pid, title from posts;')
    result = query.fetchall()  # return a tuple of two-dimension tuples which record all the post id and titles in the table posts.
    print("-----------all the posts and their poster----------")
    for each in result:
        print("Post's title: ", '{0:10}'.format(each[1]), "    pid: ",
              each[0])  # Show all of the titles and post id in the table posts.
    pid = input("which posts do you wanna add a tag? Enter a pid: ")  # Ask the user choose a post to give a tag.
    query = sql('select * from posts where pid = ? ; ', [pid])
    result = query.fetchall()  # Return the post which post id is the user input above.
    if not result:
        print("not a valid pid !!!!!!!!\n")  # If the inputted post id doesn't exist, then give an error.
        return
    tag = input("WHat is the tag you want to put on? : ")  # If the inputted post id exists, then give a tag.
    query = sql('select * from posts p, tags t where p.pid = ? and t.tag = ? and t.pid = p.pid ;',
                [pid, tag.lower()])  # Record the tag which is added with its given post id.
    if query.fetchall():
        print("The post has already had the same tag !!!!!!!!!!!!!!!\n")
        return

    sql("insert into tags values (?, ?);", [pid, tag.lower()])
    print("successfully added a tag!!!!!!!!!!")  # Tell user he or she has successfully given a tag.
    return


def edit(sql, uid):
    query = sql('select pid, title, body from posts;')  # Get the id, title, and body from posts.
    result = query.fetchall()
    print("-----------all the posts ---------")
    for each in result:
        print("Post's title: ", '{0:10}'.format(each[1]), "     pid: ", each[0], "  body: ", each[2])  # Print out the table.
    pid = input("which posts do you wanna edit? Enter a pid: ")
    query = sql('select * from posts where pid = ? ; ', [pid])  # Select the post which the user wants to edit.
    result = query.fetchall()
    if not result:  # If match failed, return an error.
        print("not a valid pid !!!!!!!!\n")
        return
    change1 = input("Do you want to edit the body of this post? (y/n): ")  # Ask the part that user wants to edit.
    if change1.lower() == 'y':
        body = input("What is the new body of this post? :  ")
    else:
        query = sql('select body from posts where pid = ? ; ', [pid])
        result = query.fetchall()
        body = result[0][0]  # Remain the original body.

    change2 = input("Do you want to edit the title of this post? (y/n): ")  # Ask the part that user wants to edit.
    if change2.lower() == 'y':
        title = input("What is the new title of this post? :  ")
    else:
        query = sql('select title from posts where pid = ? ; ', [pid])
        result = query.fetchall()
        title = result[0][0]  # Remain the original title.

    sql('update posts set title = ? where pid = ?;', [title, pid])  # update the table.
    sql('update posts set body = ? where pid = ?;', [body, pid])

    print("successfully updated the post!!!!!!!!!!")


fun_dic = {1: post_qn, 2: search, 3: answer_post, 4: vote, 5: mark_post, 6: give_badge, 7: give_tag, 8: edit}
main(sys.argv)
