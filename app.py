######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Mona Jalal (jalal@bu.edu), Baichuan Zhou (baichuan@bu.edu) and Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for, session
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
from flask.ext.login import current_user
from flask import Flask, request
import datetime

# for image uploading
# from werkzeug import secure_filename
import os, base64


mysql = MySQL()
app = Flask(__name__, static_folder = "upload")
app.secret_key = 'super secret string'  # Change this!

# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '123698745'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email FROM Users;")
users = cursor.fetchall()

# the provided code somehow uses the email as user_id, hence the need for this variable
currentUserID = None

def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM Users;")
    return cursor.fetchall()

def getUsersPhotos(uid):
    cursor = conn.cursor()

    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = (%s)", (uid))
    return cursor.fetchall()  # NOTE list of tuples, [(imgdata, pid), ...]


def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT userID  FROM Users WHERE email = (%s)", (email))
    return cursor.fetchone()[0]

def getUserInfoFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT fname,lname,userID  FROM Users WHERE email = (%s)",(email))
    return cursor.fetchall()

def isEmailUnique(email):
    # use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email FROM Users WHERE email = (%s)", (email)):
        # this means there are greater than zero entries with that email
        return False
    else:
        return True

def getUsersFriends(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT *  FROM Befriends WHERE userID1 = (%s) ", (uid))
    return cursor.fetchall()
def getUsersFriendsOfFriends(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT userID,fname,lname  FROM Befriends,Users WHERE userID2 = userID AND userID1=(%s) ", (uid))
    return cursor.fetchall()

def getUserByUid(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT fname,lname  FROM Users WHERE userID = (%s)", (uid))
    return cursor.fetchall()

def addFriendByUid(uid1, uid2):
    cursor = conn.cursor()
    if cursor.execute("INSERT INTO Befriends VALUES (%s,%s)", (uid1, uid2)) \
        and cursor.execute("INSERT INTO Befriends VALUES (%s,%s)", (uid2, uid1)):
        conn.commit()
        return True
    else:
        return False

def getTop5UsedTagByUser(uid):
    cursor = conn.cursor()
    query = "SELECT tag FROM (SELECT tag AS tag,COUNT(tag)AS tagCount FROM Tagged NATURAL JOIN "+\
        "Photo NATURAL JOIN Album WHERE userID="+str(uid)+" GROUP BY tag) AS Temp ORDER BY tagCount DESC LIMIT 5"
    query2 = str(query)
    cursor.execute(query2)
    return cursor.fetchall()

def getPhotoIDByTag(tag):
    cursor = conn.cursor()
    cursor.execute("SELECT photoID,CONVERT(data USING utf8) FROM Photo NATURAL JOIN Tagged WHERE tag=(%s)",(tag))
    return cursor.fetchall()

def getPhotoTagCountByPid(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Tagged WHERE photoID=(%s)", (pid))
    return cursor.fetchone()[0]
def getPhotoByPid(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT CONVERT(data USING utf8) FROM Photo WHERE photoID=(%s)", (pid))
    return cursor.fetchone()[0]

def getUserByComment(text):
    cursor = conn.cursor()
    query =" SELECT userID,COUNT(*) AS ccount FROM Comment WHERE text='"+str(text)+"' GROUP BY userID ORDER BY ccount DESC"
    cursor.execute(query)
    return cursor.fetchall()

def getPhotoByTagSearch(text,flag=1):
    input_str = str(text).split(" ")
    cursor = conn.cursor()
    queryStr = "SELECT photoID,CONVERT(data USING utf8),tag FROM Photo NATURAL JOIN Tagged WHERE tag= '"+str(input_str[0])+"'"
    if len(input_str) >1:
        for i in range(1,len(input_str)):
            if flag == 1:
                queryStr += " AND tag = '"
            elif flag == 0:
                queryStr += " OR tag = '"
            queryStr += str(input_str[i])
            queryStr += "'"

    cursor.execute(queryStr)
    return cursor.fetchall()

def getUserContribution():
    cursor = conn.cursor()
    query1 = "(SELECT userID,COUNT(*)AS photoUpdate FROM Album NATURAL JOIN Photo GROUP BY userID)AS Temp1"
    query2 = "(SELECT userID,COUNT(*)AS commentUpdate FROM Comment GROUP BY userID)AS Temp2"
    query3 = "(SELECT userID,COUNT(*)AS photoUpdate FROM Album NATURAL JOIN Photo GROUP BY userID)AS Temp3"
    query4 = "(SELECT userID,COUNT(*)AS commentUpdate FROM Comment GROUP BY userID)AS Temp4"
    query5 = "SELECT userID,photoUpdate,commentUpdate FROM "+str(query1)+" NATURAL LEFT OUTER JOIN "+str(query2)+" UNION "
    query6 = "SELECT userID,photoUpdate,commentUpdate FROM "+str(query3)+" NATURAL RIGHT OUTER JOIN "+str(query4)
    query = query5+query6
    cursor.execute(query)
    return cursor.fetchall()
def getMostPopularUsedTag(limit):
    cursor = conn.cursor()
    query = "SELECT tag,COUNT(*) AS tagCount FROM Tagged GROUP BY tag ORDER BY tagCOUNT DESC LIMIT "+str(limit)
    cursor.execute(query)
    return cursor.fetchall()

class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()

    cursor.execute("SELECT password FROM Users WHERE email = (%s);", (email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
    # The request method is POST (page is recieving data)
    email = flask.request.form['email']
    if email:
        email = str(email).strip()
    cursor = conn.cursor()
    # check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = (%s)", (email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user)  # okay login in user
            session["currentUserID"] = getUserIdFromEmail(flask_login.current_user.id)
            return flask.redirect(flask.url_for('protected'))  # protected is a function defined in this file

    # information did not match
    return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
def logout():
    session.pop("currentAlbumID", None)
    session.pop("albumOwnerID", None)
    session.pop("currentUserID", None)
    session.pop("switchMessage", None)
    flask_login.logout_user()
    return render_template('hello.html', message='Logged out')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')


# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    data = request.args.get('supress')
    if data:
        return render_template('register.html', supress=False)
    else:
        return render_template('register.html', supress=True)

@app.route("/register", methods=['POST'])
def register_user():
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            firstName = request.form.get('fname')
            lastName = request.form.get('lname')
        except:
            print("couldn't find all tokens")  # this prints to shell, end users will not see this (all print statements go to shell)
            return flask.redirect(flask.url_for('register'))

        if email:
            email = str(email).strip()
        gender = request.form.get('gender')
        month = request.form.get('month')
        day = request.form.get('day')
        year = request.form.get('year')

        DOB = str(year)+'-'+str(month)+'-'+str(day)

        hometown = request.form.get('hometown')
        if not gender:
            gender = 'U'
        if not hometown:
            hometown = 'unknown'
        cursor = conn.cursor()
        test = isEmailUnique(email)

        if test:
            #print(cursor.execute("INSERT INTO Users (email, password) VALUES ('email', 'password')"))

            #cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption) VALUES (%s, %s, %s)",
            #               (photo_data, uid, caption))
            print(cursor.execute("INSERT INTO Users (email, password,gender,fname,lname,DOB,hometown) VALUES (%s , %s,%s,%s,%s,%s,%s)",(email, password,gender,firstName,lastName,DOB,hometown)))
            conn.commit()
            # log user in
            user = User()
            user.id = email
            flask_login.login_user(user)
            session["currentUserID"] = getUserIdFromEmail(flask_login.current_user.id)
            cursor = conn.cursor()
            query = "SELECT fname, lname FROM Users WHERE email = (%s)"
            cursor.execute(query, (flask_login.current_user.id))
            userName = cursor.fetchone()
            return render_template('hello.html', name = str(userName[0]) + " " + str(userName[1]),\
                                    message='Account Created!')
        else:
            print("couldn't find all tokens")
            return flask.redirect(flask.url_for('register',supress=False))


# begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

#add a friend here
@app.route('/add_friendList', methods=['GET', 'POST'])
@flask_login.login_required
def add_friends():
    if request.method == 'GET':

        uid = getUserIdFromEmail(flask_login.current_user.id)
        currentFriendList = getUsersFriends(uid)
        friendNum = len(currentFriendList)
        friendName = []
        if currentFriendList:
            for i in range(friendNum):
                data = getUserByUid(currentFriendList[i][1])
                friendName.append(data[0][0] + " " + data[0][1])

            friendOfFriendList = []

            for i in range(friendNum):
                friendOfFriendData = getUsersFriendsOfFriends(currentFriendList[i][1])
                flag_notAdd = 0
                for j in range(len(friendOfFriendData)):
                    if i == 0 and j == 0 and friendOfFriendData[j][0] != uid:
                        for h in range(friendNum):
                            if friendOfFriendData[j][0] == currentFriendList[h][1]:
                                flag_notAdd = 1
                        if flag_notAdd != 1:
                            friendOfFriendList.append(dict(id=friendOfFriendData[j][0],
                                                           name=str(friendOfFriendData[j][1]) + " " + str(
                                                               friendOfFriendData[j][2]), value=1))
                    else:
                        flag_added = 0
                        for k in range(len(friendOfFriendList)):
                            if friendOfFriendList[k]['id'] == friendOfFriendData[j][0]:
                                friendOfFriendList[k]['value'] += 1
                                flag_added = 1
                                break
                        if flag_added == 0:
                            flag_notAdd = 0
                            for h in range(friendNum):
                                if friendOfFriendData[j][0] == currentFriendList[h][1]:
                                    flag_notAdd = 1
                            if flag_notAdd != 1 and friendOfFriendData[j][0] != uid:
                                friendOfFriendList.append(dict(id=friendOfFriendData[j][0],
                                                               name=str(friendOfFriendData[j][1]) + " " + str(
                                                                   friendOfFriendData[j][2]), value=1))

            # sort based on number of common friends:
            for i in range(len(friendOfFriendList)):
                for j in range(i, len(friendOfFriendList)):
                    if friendOfFriendList[i]['value'] < friendOfFriendList[j]['value']:
                        temp = friendOfFriendList[i]
                        friendOfFriendList[i] = friendOfFriendList[j]
                        friendOfFriendList[j] = temp

            if len(friendOfFriendList) == 0:
                friendOfFriendList = None

            return render_template('add_friendList.html', friendNum=friendNum,
                                   friendNames=friendName, recommends=friendOfFriendList, searchResult=None)
        else:
            return render_template('add_friendList.html', friendNum=0,
                                   friendNames=None, recommends=None, searchResult=None)
    else:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        data = request.form.getlist('recommends[]')
        dataAdd = request.form.get('addFriend')
        searchEmail = request.form.get('searchByEmail')
        searchID = []
        if searchEmail:
            searchName = getUserInfoFromEmail(searchEmail)
            if searchName:
                searchResult = searchName[0][0] + " " + searchName[0][1]
                searchID.append(dict(searchedName=searchResult, searchedID=searchName[0][2]))
            else:
                searchID = 0
        else:
            searchID = None

        n = 0
        flag_friend = 0

        if dataAdd:
            dataAdd = str(dataAdd).split('/')[0]
            dataAdd = int(dataAdd)
            currentFriendList = getUsersFriends(uid)
            if dataAdd != uid:
                for i in range(len(currentFriendList)):
                    if dataAdd == currentFriendList[i][1]:
                        flag_friend = 1
                        break
                if flag_friend == 0:
                    addFriendByUid(uid, dataAdd)
                    n += 1
            else:
                flag_friend = 2

        Num = len(data)

        if data:
            for i in range(Num):
                if addFriendByUid(uid, data[i]):
                    n += 1

        currentFriendList = getUsersFriends(uid)
        friendName = []
        friendNum = len(currentFriendList)
        for i in range(friendNum):
            data2 = getUserByUid(currentFriendList[i][1])

            friendName.append(data2[0][0] + " " + data2[0][1])

        if n != 0:
            message = "You have successfully added " + str(n) + " users!"
        elif n == 0 and flag_friend == 1:
            message = "This user is your friend already."
        elif n == 0 and flag_friend == 2:
            message = "You cannot add yourself as a friend."
        else:
            message = None

        # find out recommend friends
        friendOfFriendList = []

        for i in range(friendNum):
            friendOfFriendData = getUsersFriendsOfFriends(currentFriendList[i][1])
            flag_notAdd = 0
            for j in range(len(friendOfFriendData)):
                if i == 0 and j == 0 and friendOfFriendData[j][0] != uid:
                    for h in range(friendNum):
                        if friendOfFriendData[j][0] == currentFriendList[h][1]:
                            flag_notAdd = 1
                    if flag_notAdd != 1:
                        friendOfFriendList.append(dict(id=friendOfFriendData[j][0],
                                                       name=str(friendOfFriendData[j][1]) + " " + str(
                                                           friendOfFriendData[j][2]), value=1))
                else:
                    flag_added = 0
                    for k in range(len(friendOfFriendList)):
                        if friendOfFriendList[k]['id'] == friendOfFriendData[j][0]:
                            friendOfFriendList[k]['value'] += 1
                            flag_added = 1
                            break
                    if flag_added == 0:
                        flag_notAdd = 0
                        for h in range(friendNum):
                            if friendOfFriendData[j][0] == currentFriendList[h][1]:
                                flag_notAdd = 1
                        if flag_notAdd != 1 and friendOfFriendData[j][0] != uid:
                            friendOfFriendList.append(dict(id=friendOfFriendData[j][0],
                                                           name=str(friendOfFriendData[j][1]) + " " + str(
                                                               friendOfFriendData[j][2]), value=1))
        if len(friendOfFriendList) == 0:
            friendOfFriendList = None
        else:
            # sort based on number of common friends:
            for i in range(len(friendOfFriendList)):
                for j in range(i, len(friendOfFriendList)):
                    if friendOfFriendList[i]['value'] < friendOfFriendList[j]['value']:
                        temp = friendOfFriendList[i]
                        friendOfFriendList[i] = friendOfFriendList[j]
                        friendOfFriendList[j] = temp

        return render_template('add_friendList.html', friendNum=friendNum, friendNames=friendName, message=message,
                               recommends=friendOfFriendList, searchID=searchID)


## photo search/comment search/user contribution score calculation
@app.route('/photo_recommend', methods=['GET', 'POST'])
@flask_login.login_required
def photo_recommend():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':

        inputText_tag = request.form.get('searchByTag')
        inputText = request.form.get('searchByComment')
        inputFlag = request.form.get('searchByTagAnd')
        inputFlag2 = request.form.get('searchByTagOr')

        if inputText:
            inputText = str(inputText).strip()
        if inputText_tag:
            inputText_tag = str(inputText_tag).strip()

        if inputFlag2:
            inputFlag = inputFlag2
        if uid:
            messageCS = None
            # Photo search:
            photoSearchResult = []
            if inputText_tag:

                if inputFlag:
                    photoSearchData = getPhotoByTagSearch(inputText_tag, int(inputFlag))
                else:
                    photoSearchData = getPhotoByTagSearch(inputText_tag)
                flag = 0
                leng = len(photoSearchData)
                if leng != 0:
                    label = [0] * leng
                    for j in range(leng - 1):
                        if label[j] == 0:
                            tagAdd = dict(pid=photoSearchData[j][0], data=photoSearchData[j][1])
                            tagAdd2 = []
                            for k in range(j + 1, leng):
                                if (label[k] == 0 and photoSearchData[j][0] == photoSearchData[k][0]):
                                    label[k] = 1
                                    if k == leng - 1:
                                        flag = 1
                                    tagAdd2.append(photoSearchData[k][2])

                            tagAdd2.append(photoSearchData[j][2])
                            tagAdd.update(tag=tagAdd2)
                            photoSearchResult.append(tagAdd)
                    if flag == 0:
                        photoSearchResult.append(
                            dict(pid=photoSearchData[leng - 1][0], data=photoSearchData[leng - 1][1],
                                 tag=photoSearchData[leng - 1][2]))
                else:
                    photoSearchResult = None
                    messageCS = "No matched result!"

                # photoSearchResult is for photo search
                # It stores photoID('pid') and photo data or path('data')


                # comment search:

            formattedResult = []

            if inputText:
                result = getUserByComment(inputText)
                if len(result) == 0:
                    formattedResult = None
                    messageCS = "No user make such comment."
                else:
                    for i in range(len(result)):
                        userName = getUserByUid(result[i][0])
                        userName = userName[0][0] + " " + userName[0][1]
                        formattedResult.append(dict(userName=userName, matchCount=result[i][1]))
            else:
                formattedResult = None

            # formattedResult is for comment search
            # It stores userName and a count number of matching
            # messgeCS indicates empty result

            return render_template('photo_recommend.html', formattedResult=formattedResult, message=messageCS,photos=photoSearchResult)
    else:
        if uid:
            tagCounts = [0] * 300
            photoRec = []
            tagData = getTop5UsedTagByUser(uid)
            tagListLen = len(tagData)
            messageCS = None
            if tagListLen == 0:
                messageCS = "No recommend available."
            for i in range(tagListLen):
                tagID = getPhotoIDByTag(tagData[i])
                tagLen = len(tagID)
                for j in range(tagLen):
                    tagCounts[tagID[j][0]] += 1

            for i in range(len(tagCounts)):
                if tagCounts[i] != 0:
                    tagID = getPhotoByPid(i)

                    photoRec.append({'pid': i,'data':str(tagID), 'value': tagCounts[i]})
            for i in range(len(photoRec) - 1):
                for j in range(i + 1, len(photoRec)):
                    if photoRec[i]['value'] < photoRec[j]['value']:
                        temp = photoRec[i]
                        photoRec[i] = photoRec[j]
                        photoRec[j] = temp

            for i in range(len(photoRec) - 1):
                for j in range(i + 1, len(photoRec)):
                    if photoRec[i]['value'] == photoRec[j]['value']:
                        p1 = getPhotoTagCountByPid(photoRec[i]['pid'])
                        p2 = getPhotoTagCountByPid(photoRec[j]['pid'])
                        if p1 > p2:
                            temp = photoRec[i]
                            photoRec[i] = photoRec[j]
                            photoRec[j] = temp
            return render_template("photo_recommend.html",photoRec=photoRec,top5Tag=tagData,formattedResult=None,message=messageCS,photos=None)
                            #   photoRec is a dictionary list.
                            # It stores recommended photo id('pid') and the amount it matches with your frequently used tags('value')
                            # It is sorted
                            #   tagData stores the "5" most frequently used tags,tagListLen is its size, can be accessed by tagData[i]



@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        
        if "submitNewPhoto" in request.form:
            # uid = getUserIdFromEmail(flask_login.current_user.id)
            imgfile = request.files['photo']
            if allowed_file(imgfile.filename):
                save = open('upload/' + imgfile.filename, 'wb')
                save.write(imgfile.read())
                caption = request.form.get('caption')
                albumID = request.form["album"]
                # photo_data = base64.standard_b64encode(imgfile.read())
                cursor = conn.cursor()
                #cursor.execute(
                #    "INSERT INTO Pictures (imgdata, user_id, caption) VALUES ('photo_data', 'uid', 'caption')")
                cursor.execute("INSERT INTO Photo (albumID, caption, data) VALUES (%s, %s, %s)",
                               (albumID, caption, imgfile.filename))
                #cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption) VALUES (?, ?, ?)", (photo_data, uid, caption))
                conn.commit()

                query = "SELECT fname, lname FROM Users WHERE email = (%s)"
                cursor.execute(query, (flask_login.current_user.id))
                userName = cursor.fetchone()
                return render_template('hello.html', name = str(userName[0]) + " " + str(userName[1]), message='Photo uploaded!',login_state=True,viewOthers=True)
            else:
                return render_template('hello.html', name=None,
                                       errorMessage='File extension not allowed!', login_state=True, viewOthers=True)
        else:
            albumName = request.form["newAlbumName"]
            cursor = conn.cursor()
            query = "INSERT INTO Album (name, userID, DOC) VALUES (%s, %s, DATE %s)"
            cursor.execute(query, (albumName, uid, str(datetime.date.today())))
            conn.commit()
            
            # get the album info
            query = "SELECT albumID, name FROM Album WHERE userID = (%s)"
            cursor = conn.cursor()
            cursor.execute(query, (uid))
            return render_template("upload.html", albums = cursor.fetchall())
    # The method is GET so we return a  HTML form to upload the a photo.
    else:
        # get the album info
        query = "SELECT albumID, name FROM Album WHERE userID = (%s)"
        cursor = conn.cursor()
        cursor.execute(query, (uid))
        return render_template('upload.html', albums = cursor.fetchall())


# end photo uploading code


# the following two methods are similar, they differ in the current user identity

# displays the user's own profile
@app.route('/profile', methods = ['POST', 'GET'])
@flask_login.login_required
def protected():
    cursor = conn.cursor()
    session["albumOwnerID"] = session["currentUserID"]
    if request.method == "POST":
        if "albumName" in request.form:
            currentAlbumID = request.form["albumName"]
            session["currentAlbumID"] = currentAlbumID
            query = "SELECT photoID, caption, CONVERT(data USING utf8) FROM Photo WHERE albumID = (%s)"
            photoAll = getPhotos(query, (currentAlbumID))
            session["switchMessage"] = None
            return redirect(url_for(".showPhotos"))


    query = "SELECT fname, lname FROM Users WHERE email = (%s)"
    cursor.execute(query, (flask_login.current_user.id))
    userName = cursor.fetchone()

    query = "SELECT albumID, name FROM Album WHERE userID = (%s)"
    cursor.execute(query, (session["albumOwnerID"]))
    albums = cursor.fetchall()

    cursor.execute("SELECT *  FROM Users WHERE userID = (%s)", (session["albumOwnerID"]))
    data = cursor.fetchall()

    gender = str(data[0][1])
    email = str(data[0][2])
    DOB = str(data[0][4])
    hometown= str(data[0][5])

    uid = getUserIdFromEmail(flask_login.current_user.id)
    tagData = getTop5UsedTagByUser(uid)

    return render_template('hello.html', name = str(userName[0]) + " " + str(userName[1]),\
                            albums = albums, message="Here's your profile", allowSearching = False,\
                           email=email,DOB=DOB,hometown=hometown,gender=gender,viewOthers=False,login_state=True,topTags=tagData)

# displays the targeted user's profile
@app.route('/userProfile', methods = ['POST', 'GET'])
def browseProfile():
    cursor = conn.cursor()
    session["albumOwnerID"] = session["targetUserID"]
    viewOthers = False
    loginState = False
    if flask_login.current_user.is_authenticated :
        loginState = True
        if session["targetUserID"]!= getUserIdFromEmail(flask_login.current_user.id):
            viewOthers = True
    else:
        viewOthers = True


    if request.method == "POST" and "albumName" in request.form:
        currentAlbumID = request.form["albumName"]
        session["currentAlbumID"] = currentAlbumID
        query = "SELECT photoID, caption, CONVERT(data USING utf8) FROM Photo WHERE albumID = (%s)"
        photoAll = getPhotos(query, (currentAlbumID))
        session["switchMessage"] = None
        return redirect(url_for(".showPhotos"))
        
    query = "SELECT fname, lname FROM Users WHERE userID = (%s)"
    cursor.execute(query, (session["albumOwnerID"]))
    userName = cursor.fetchone()

    query = "SELECT albumID, name FROM Album WHERE userID = (%s)"
    cursor.execute(query, (session["albumOwnerID"]))
    albums = cursor.fetchall()

    return render_template('hello.html', name = str(userName[0]) + " " + str(userName[1]),\
                            albums = albums, allowSearching = False,viewOthers=viewOthers,login_state=loginState)

# default page
# offering the options to search photos either by user email or photo tag
@app.route("/", methods=['GET', 'POST'])
def hello():
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM Users WHERE userID = -1"
    cursor.execute(query)
    if cursor.fetchone()[0] == 0:
        query = "INSERT INTO Users (userID, password, fname, lname) VALUES (-1, \"anon\", \"anon\", \"anon\")"
        cursor.execute(query)
        conn.commit()

    #check privilege

    viewOthers = False
    loginState = False
    if flask_login.current_user.is_authenticated :
        loginState = True
        if "targetUserID" in session and session["targetUserID"]!= getUserIdFromEmail(flask_login.current_user.id):
            viewOthers = True
        else:
            viewOthers = True
    else:
        viewOthers = True

    #top 10 popular tags
    popularTagData= getMostPopularUsedTag(10)
    popularTagList = []
    for i in range(len(popularTagData)):
        oneTag = dict(tag=popularTagData[i][0],count=popularTagData[i][1])
        popularTagList.append(oneTag)
    if len(popularTagData)==0:
        popularTagList = None

    # top 10 users:
    userScoreData = getUserContribution()
    userScore = []
    userScoreTop10 = []
    for i in range(len(userScoreData)):
        if userScoreData[i][1] is None:
            photoScore = 0
        else:
            photoScore = int(userScoreData[i][1])
        if userScoreData[i][2] is None:
            commentScore = 0
        else:
            commentScore = int(userScoreData[i][2])
        scoreSum = commentScore + photoScore

        if userScoreData[i][0] != -1:
            userName = getUserByUid(userScoreData[i][0])
            userScore.append(dict(userID=userScoreData[i][0], userName=userName[0][0]+" "+userName[0][1], scoreSum=scoreSum))

    length = len(userScore)
    for i in range(length):
        for j in range(i, len(userScore)):
            if userScore[i]['scoreSum'] < userScore[j]['scoreSum']:
                temp = userScore[i]
                userScore[i] = userScore[j]
                userScore[j] = temp
    if length > 10:
        length = 10
    for i in range(length):
        userScoreTop10.append(userScore[i])
        # userScoreTop10 list stores 'userID' and 'scoreSum'
    if length == 0:
        userScoreTop10 = None

    if request.method == 'POST' and "search" in request.form:
        method = request.form["method"]
        cursor = conn.cursor()
        if method == "byEmail":
            query = "SELECT userID FROM Users WHERE email = (%s)"
            cursor.execute(query, (request.form["keyword"]))
            result = cursor.fetchone()
            if result == None:
                return render_template('hello.html', message='Welecome to Photoshare',\
                                        errorMessage = "0 result", allowSearching = True,viewOthers=viewOthers,login_state=loginState,\
                                       tags=popularTagList,contribution=userScoreTop10)
            else:
                session["targetUserID"] = result[0]
                return redirect(url_for(".browseProfile"))
        else:
            query = "SELECT P.photoID, P.caption, CONVERT(P.data USING utf8) FROM Photo P, Tagged T WHERE T.tag = (%s) AND T.photoID = P.photoID"
            cursor.execute(query, (request.form["keyword"]))
            photos = cursor.fetchall()
            
            if len(photos) == 0:
                return render_template('hello.html', message='Welecome to Photoshare',\
                                        errorMessage = "0 result", allowSearching = True,viewOthers=viewOthers,login_state=loginState,tags=popularTagList,contribution=userScoreTop10)
            else:
                photoAll = []
                for i in range(len(photos)):
                    tuple = photos[i]
                    if i % 4 == 0:
                        photoAll.append([tuple])
                    else:
                        photoAll[-1].append(tuple)
                session["photoAll"] = photoAll
                return redirect(url_for(".showPhotosByTag", tag = request.form["keyword"]))

    return render_template('hello.html', message='Welecome to Photoshare', allowSearching=True,viewOthers=viewOthers,login_state=loginState,tags=popularTagList,contribution=userScoreTop10)

@app.route("/showPhotos", methods = ['GET', 'POST'])
def showPhotos():
    if request.method == "POST":
        cursor = conn.cursor()
        if "image" in request.form:
            selectedPhotoID = request.form['image']
            query = "SELECT userID FROM Album A, Photo P WHERE A.albumID = P.albumID AND P.photoID = (%s)"
            cursor.execute(query, (selectedPhotoID))
            session["albumOwnerID"] = cursor.fetchone()[0]
            return redirect(url_for('.TLC', selectedPhotoID = selectedPhotoID))
        else:
            query = "DELETE FROM Album WHERE albumID = (%s)"
            cursor.execute(query, session["currentAlbumID"])
            conn.commit()
            return redirect(url_for(".protected"))
    canDelete = current_user.is_authenticated and session["currentUserID"] == session["albumOwnerID"]
    return render_template('showPhotos.html', photoAll = session["photoAll"],\
                            switchMessage = session["switchMessage"], canDelete = canDelete)

@app.route("/showPhotos/<tag>", methods = ['GET', 'POST'])
def showPhotosByTag(tag):
    cursor = conn.cursor()
    if request.method == 'POST':
        if "filter" in request.form:
            if session["switchMessage"] == "Only show my photos":
                session["switchMessage"] = "Show all photos"
                query = "SELECT P.photoID, P.caption, CONVERT(P.data USING utf8) FROM Photo P, Tagged T, Album A " +\
                        "WHERE T.tag = (%s) AND T.photoID = P.photoID AND A.albumID = P.albumID AND A.userID = (%s)"
                photoAll = getPhotos(query, (tag, session["currentUserID"]))
                return render_template("showPhotos.html", switchMessage = session["switchMessage"], photoAll = photoAll)
            else:
                session["switchMessage"] = "Only show my photos"
                query = "SELECT P.photoID, P.caption, CONVERT(P.data USING utf8) FROM Photo P, Tagged T " +\
                        "WHERE T.tag = (%s) AND T.photoID = P.photoID"
                photoAll = getPhotos(query, (tag))
                return render_template("showPhotos.html", switchMessage = session["switchMessage"], photoAll = photoAll)
        else:
            selectedPhotoID = request.form['image']
            query = "SELECT userID FROM Album A, Photo P WHERE A.albumID = P.albumID"
            cursor.execute(query)
            session["albumOwnerID"] = cursor.fetchone()[0]
            session["switchMessage"] = None
            return redirect(url_for('.TLC', selectedPhotoID = selectedPhotoID))
    query = "SELECT P.photoID, P.caption, CONVERT(P.data USING utf8) FROM Photo P, Tagged T " +\
            "WHERE T.tag = (%s) AND T.photoID = P.photoID"
    photoAll = getPhotos(query, (tag))
    if flask_login.current_user.is_authenticated:
        if not "switchMessage" in session or session["switchMessage"] == None:
            session["switchMessage"] = "Only show my photos"
        return render_template("showPhotos.html", switchMessage = session["switchMessage"], photoAll = photoAll)
    return render_template("showPhotos.html", photoAll=photoAll)

@app.route("/showSinglePhoto/<selectedPhotoID>", methods = ['GET', 'POST'])
def TLC(selectedPhotoID): # tag like comment
    currentUserID = None
    currentPhotoID = selectedPhotoID
    if current_user.is_authenticated:
        currentUserID = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    query = "SELECT U.userID FROM Users U, Album A, Photo P WHERE A.albumID = P.albumID AND A.userID = U.userID AND P.photoID = (%s)"
    cursor.execute(query, (currentPhotoID))
    photoOwnerID = cursor.fetchone()[0]
    session["photoOwnerID"] = photoOwnerID
    if request.method == 'POST':
        if "submitTag" in request.form:
            newTag = request.form["tag"]
            # query = "INSERT INTO Tag VALUES (%s)"
            # cursor.execute(query, (newTag))
            # conn.commit()
            query = "SELECT photoID, tag FROM Tagged WHERE photoID = (%s) and tag = (%s)"
            if not cursor.execute(query, (currentPhotoID, newTag)):
                query = "INSERT INTO Tagged VALUES (%s, %s)"
                cursor.execute(query, (currentPhotoID, newTag))
                conn.commit()
        elif "like" in request.form:
            query = "INSERT INTO LikeTable VALUES (%s, %s, Date %s)"
            cursor.execute(query, (currentUserID, currentPhotoID, datetime.date.today()))
            conn.commit()
        elif "submitComment" in request.form:
            newComment = request.form["comment"]
            query = "INSERT INTO Comment (userID, text, photoID, DOC) VALUES (%s, %s, %s, DATE (%s))"
            if currentUserID == None:
                cursor.execute(query, (-1, newComment, currentPhotoID, datetime.date.today()))
            else:
                cursor.execute(query, (currentUserID, newComment, currentPhotoID, datetime.date.today()))
            conn.commit()
        elif "delete" in request.form:
            query = "DELETE FROM Photo WHERE photoID = (%s)"
            cursor.execute(query, (currentPhotoID))
            conn.commit()
            query = query = "SELECT P.photoID, P.caption, CONVERT(P.data USING utf8) FROM Photo P, Album A WHERE A.albumID = P.albumID AND A.userID = (%s)"
            photoAll = getPhotos(query, (currentUserID))
            session["switchMessage"] = None
            return redirect(url_for(".showPhotos"))
    query = "SELECT caption, CONVERT(data USING utf8) FROM Photo WHERE photoID = (%s)"
    cursor.execute(query, (currentPhotoID))
    (caption, image) = cursor.fetchone()
    query = "SELECT tag FROM Tagged WHERE photoID = (%s)"
    cursor.execute(query, (currentPhotoID))
    tags = cursor.fetchall()
    query = "SELECT text FROM Comment WHERE photoID = (%s)"
    cursor.execute(query, (currentPhotoID))
    comments = cursor.fetchall()

    query = "SELECT COUNT(*)AS likeCount FROM LikeTable WHERE pid = (%s)"
    cursor.execute(query, (currentPhotoID))
    likeCount = cursor.fetchall()
    query = "SELECT fname,lname FROM LikeTable,Users WHERE uid=userID AND pid = (%s)"
    cursor.execute(query, (currentPhotoID))
    likeUsers = cursor.fetchall()
    likeUserList = []
    for i in range(len(likeUsers)):
        likeUserList.append(str(likeUsers[i][0])+" "+str(likeUsers[i][1]))

    # a registered user cannot like the same photo multiple times/unregister user cannot 'like'
    canLike = True
    if currentUserID != None:
        query = "SELECT * FROM LikeTable WHERE uid = (%s) AND pid = (%s)"
        cursor.execute(query, (currentUserID, currentPhotoID))
        if len(cursor.fetchall()) > 0:
            canLike = False
    else:
        canLike = False
    
    # the user themselves cannot comment their own photo
    canComment = False
    if currentUserID == None or currentUserID != photoOwnerID:
        canComment = True
        '''
        query = "SELECT * FROM Users U, Album A, Photo P WHERE (%s) = U.userId AND U.userId = A.userID AND A.albumID = (%s)"
        cursor.execute(query, (currentUserID, currentPhotoID))
        if len(cursor.fetchall()) == 0:
            canComment = True
        '''
    return render_template('showSinglePhoto.html',\
            tags = tags, comments = comments, image = image, caption = caption,\
            canLike = canLike, canComment = canComment,likeCount=likeCount,likeUsers=likeUserList)


#============================= Helper Functions ==============================#

def getPhotos(query, values):
    photoAll = []
    if values is None:
        cursor.execute(query)
    else:
        cursor.execute(query, values)
    photos = cursor.fetchall()
    for i in range(len(photos)):
        tuple = photos[i]
        if i % 4 == 0:
            photoAll.append([tuple])
        else:
            photoAll[-1].append(tuple)
    session["photoAll"] = photoAll
    return photoAll

#============================== End of Section= ==============================#

if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)
    conn.close()
