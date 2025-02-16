from django.http import HttpResponse

def home(request):
    html = """
    <html>
      <body>
        <h1>Hello from the root path!</h1>
        <p><a href="/api/parsing/upload-form/">Upload a PDF here</a></p>
      </body>
    </html>
    """
    return HttpResponse(html)