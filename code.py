import web  
import os
import sys
from twython import Twython
import time
import Image
app_path = os.path.dirname(__file__) 
sys.path.append(app_path)  
if app_path: # Apache 
  os.chdir(app_path) 
else: # CherryPy 
  app_path = os.getcwd()  

urls = ( '/', 'index' ,
         '/login', 'get_auth_tokens',
         '/callback', 'auth',
         '/upload', 'upload',
         '/tag/(.+)', 'tag',
         '/user/(.+)', 'user',
         '/logout', 'logout')

render = web.template.render('templates/')

APP_KEY = '###############################'
APP_SECRET = '#############################'

twitter = Twython(APP_KEY, APP_SECRET)
db = web.database(dbn='mysql', user='root', pw='placeholder', db='robogram')

# WARNING
# web.debug = True and autoreload = True
# can mess up your session: I've personally experienced it
#web.debug = False # You may wish to place this in a config file
app = web.application(urls, globals(), autoreload=True)
application = app.wsgifunc() # needed for running with apache as wsgi

class index: 
  def GET(self): 
    username = web.cookies(username = None)
    code = ' '
    posts = list(db.select("posts", order="timestamp desc"))
    for p in posts:
      code = code + '<img src=' + p.url + '></img><br />' + p.description + '<br /> posted by: ' + p.username + '<br /> under tag: <a href=/robogram/tag/' + p.tags + '>' + p.tags + '</a><br /><br /><hr><br /><br />'
    if username.username:
      return render.index("Welcome, " + username.username, "<a href=/robogram/upload><img id=plus src=/robogram/static/plus.png></img></a><a href=logout id=logout>Logout?</a>", code)
    else:
      return render.index("<a href=/robogram/login><img id=twitter src=https://dev.twitter.com/sites/default/files/images_documentation/sign-in-with-twitter-gray.png></img></a>", "", code)

class tag:
  def GET(self, tag):
    username = web.cookies(username = None)
    query = 'tags = \"' + tag + '\"'
    code = ' '
    posts = list(db.select("posts", order="timestamp desc", where=query))
    for p in posts:
      code = code + '<img src=' + p.url + '></img><br />' + p.description + '<br /> posted by: ' + p.username + '<br /> under tag: ' + p.tags + '<br ><br /><br />'
    if username.username:
      return render.index("Welcome, " + username.username, "<a href=/robogram/upload><img id=plus src=/robogram/static/plus.png></img></a><a href=logout id=logout>Logout?</a>", code)
    else:
      return render.index("<a href=/robogram/login><img id=twitter src=https://dev.twitter.com/sites/default/files/images_documentation/sign-in-with-twitter-gray.png></img></a>", "", code)
class user:
  def GET(self, user):
    username = web.cookies(username = None)
    query = 'username = \"' + user + '\"'
    code = ' '
    posts = list(db.select("posts", order="timestamp desc", where=query))
    userdb = list(db.select("users", where=query))
    userdb = userdb[0]
    for p in posts:
      code = code + '<img src=' + p.url + '></img><br />' + p.description + '<br /> posted by: ' + p.username + '<br /> under tag: ' + p.tags + '<br /><br /><br /> <br />'
    if username.username:
      return render.user("Welcome, " + username.username, "<a href=/robogram/upload><img id=plus src=/robogram/static/plus.png></img></a><a href=logout id=logout>Logout?</a>", code, userdb.profile_picture, userdb.username, userdb.bio )
    else:
      return render.user("<a href=/robogram/login><img id=twitter src=https://dev.twitter.com/sites/default/files/images_documentation/sign-in-with-twitter-gray.png></img></a>", "", code, userdb[0].profile_picture, userdb.username, userdb.bio )

class upload:
    def GET(self):
        cookies = web.cookies(OAUTH_TOKEN = None)
        if cookies.OAUTH_TOKEN:
            return render.upload("Welcome, " + cookies.username, "<a href=/robogram/upload><img id=plus src=/robogram/static/plus.png></img></a><a href=logout id=logout>Logout?</a>")
        else:
            raise web.seeother('/login')
    def POST(self):
        x = web.input(myfile={}, share = None)
        filedir = '/home/ubuntu/uploads' # change this to the directory you want to store the file in.
        if 'myfile' in x: # to check if the file-object is created
            filepath=x.myfile.filename.replace('\\','/') # replaces the windows-style slashes with linux ones.
            filename=filepath.split('/')[-1]
            filename = str(time.time()) + filename
            im = Image.open(x.myfile.file) # writes the uploaded file to the newly created file.
            size = 700, 700
            im.thumbnail(size, Image.ANTIALIAS)
            im.save(filedir +'/'+ filename, "JPEG")
            cookies = web.cookies()
            OAUTH_TOKEN = cookies.OAUTH_TOKEN
            OAUTH_TOKEN_SECRET = cookies.OAUTH_TOKEN_SECRET
            twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
            names = twitter.verify_credentials()
            print names
            db.insert('posts', description=x.description, url='/robogram/static/uploads/' + filename, tags=x.tags, username=names['screen_name'])
            if x.share:
              photo = open(filedir +'/'+ filename, 'rb')
              twitter.update_status_with_media(status='Hey, just posted a pic at Robogram! ' + x.description, media=photo)
        raise web.seeother('/upload')

class logout:
  def GET(self):
    web.setcookie("OAUTH_TOKEN", "", expires=-1, domain='.phckopper.org')
    web.setcookie("OAUTH_TOKEN_SECRET", "", expires=-1, domain='.phckopper.org')
    web.setcookie("username", "", expires=-1, domain='.phckopper.org')
    raise web.seeother('/')
class get_auth_tokens:
    def GET(self):
        web.header('Cache-Control', 'no-cache, no-store, must-revalidate')
        web.header('Pragma', 'no-cache')
        web.header('Expires', '0') 
        auth = twitter.get_authentication_tokens()
        OAUTH_TOKEN = auth['oauth_token']
        OAUTH_TOKEN_SECRET = auth['oauth_token_secret']
        url = auth['auth_url']
        print url
        print web.setcookie("OAUTH_TOKEN", OAUTH_TOKEN, domain='.phckopper.org')
        print web.setcookie("OAUTH_TOKEN_SECRET", OAUTH_TOKEN_SECRET, domain='.phckopper.org')
        web.redirect(url)
class auth:
    def GET(self):
        data = web.input()
        OAUTH_TOKEN = data.oauth_token
        OAUTH_TOKEN_SECRET = web.cookies().get("OAUTH_TOKEN_SECRET")
        APP_KEY = '9QCAfAHTEPYHRa4IKhy4Vw'
        APP_SECRET = 'VhswLQnRdp9550CqIxYsvszdv5odNd55GmSahtK9j1M'
        print OAUTH_TOKEN
        print OAUTH_TOKEN_SECRET
        heeey = Twython(APP_KEY, APP_SECRET,
                  OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
        final_step = heeey.get_authorized_tokens(data.oauth_verifier)
        OAUTH_TOKEN = final_step['oauth_token']
        print final_step
        print "Ponto 1"
        print OAUTH_TOKEN
        print final_step['screen_name']
        OAUTH_TOKEN_SECRET = str(final_step).split('\'')[3]
        print OAUTH_TOKEN_SECRET
        twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
        print "Ponto 1.5"
        web.setcookie("OAUTH_TOKEN", OAUTH_TOKEN, domain='.phckopper.org')
        web.setcookie("OAUTH_TOKEN_SECRET", OAUTH_TOKEN_SECRET, domain='.phckopper.org')
        web.setcookie("username", final_step['screen_name'], domain='.phckopper.org')
        db.insert('users', username = final_step['screen_name'], access_token = OAUTH_TOKEN, access_token_secret = OAUTH_TOKEN_SECRET, bio = 'Heeeey new user here!', profile_picture = '/robogram/gear.png')
        raise web.seeother('/')

if __name__ == "__main__": 
  app.run()
