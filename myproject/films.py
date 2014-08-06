import cgi
import urllib

from google.appengine.api import users
# [START import_ndb]
from google.appengine.ext import ndb
# [END import_ndb]

import webapp2

MAIN_PAGE_FOOTER_TEMPLATE = """\
    <form action="/sign?%s" method="post">
      <div><textarea name="content" rows="3" cols="60"></textarea></div>
      <div><input type="submit" value="Sign filmbook"></div>
    </form>
    <hr>
    <form>filmbook name:
      <input value="%s" name="filmbook_name">
      <input type="submit" value="switch">
    </form>
    <a href="%s">%s</a>
  </body>
</html>
"""

DEFAULT_FILMBOOK_NAME = 'default_filmbook'

# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def filmbook_key(filmbook_name=DEFAULT_FILMBOOK_NAME):
    """Constructs a Datastore key for a filmbook entity with filmbook_name."""
    return ndb.Key('filmbook', filmbook_name)

# [START greeting]
class Greeting(ndb.Model):
    """Models an individual filmbook entry."""
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
# [END greeting]
class Film(ndb.Model):
    """ A individual film"""
    title = ndb.StringProperty(indexed=True)
    releaseYear = ndb.IntegerProperty()
    locations = ndb.StringProperty(repeated=True)
    funFact = ndb.StringProperty
    maker = ndb.StringProperty(indexed=True)
    distributor = ndb.StringProperty
    

# [START main_page]
class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write('<html><body>')
        filmbook_name = self.request.get('filmbook_name',
                                          DEFAULT_FILMBOOK_NAME)

        # Ancestor Queries, as shown here, are strongly consistent with the High
        # Replication Datastore. Queries that span entity groups are eventually
        # consistent. If we omitted the ancestor from this query there would be
        # a slight chance that Greeting that had just been written would not
        # show up in a query.
        # [START query]
        greetings_query = Greeting.query(
            ancestor=filmbook_key(filmbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)
        # [END query]

        for greeting in greetings:
            if greeting.author:
                self.response.write(
                        '<b>%s</b> wrote:' % greeting.author.nickname())
            else:
                self.response.write('An anonymous person wrote:')
            self.response.write('<blockquote>%s</blockquote>' %
                                cgi.escape(greeting.content))

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        # Write the submission form and the footer of the page
        sign_query_params = urllib.urlencode({'filmbook_name': filmbook_name})
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE %
                            (sign_query_params, cgi.escape(filmbook_name),
                             url, url_linktext))
# [END main_page]

# [START filmbook]
class filmbook(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each Greeting
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        filmbook_name = self.request.get('filmbook_name',
                                          DEFAULT_FILMBOOK_NAME)
        greeting = Greeting(parent=filmbook_key(filmbook_name))

        if users.get_current_user():
            greeting.author = users.get_current_user()

        greeting.content = self.request.get('content')
        greeting.put()

        query_params = {'filmbook_name': filmbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))
# [END filmbook]

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', filmbook),
], debug=True)

