import pydxcc
import web


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


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()