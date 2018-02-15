import pydxcc
import web
import os

urls = (
  '/callsign', 'index',
  '/lookup/json/(.+)', 'call_json',
  '/lookup/xml/(.+)', 'call_json'
)

class index:
    def GET(self):
        return "Hello, world!"

class call_json:
    def GET(self, callsign):
        return (pydxcc.dxcc2json(pydxcc.call2dxcc(callsign.upper(), None)))
class call_xml:
    def GET(self, callsign):
        return (pydxcc.dxcc2xml(pydxcc.call2dxcc(callsign.upper(), None)))

app = web.application(urls, globals())
application = app.wsgifunc()

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
