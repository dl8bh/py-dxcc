import pydxcc
import web
import os

urls = (
  '/callsign', 'index',
  '/lookup/(.+)', 'findcall'
)

class index:
    def GET(self):
        return "Hello, world!"

class findcall:
    def GET(self, callsign):
        return pydxcc.call2dxcc(callsign.upper(), None)

app = web.application(urls, globals())
application = app.wsgifunc()

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
