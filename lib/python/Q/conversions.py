import re

def html2markdown(html):
    text = "<br>".join(html.split("\n"))

    text = text.replace("<ul>", "\n\n")
    text = re.sub('<li>(.*?)</li>', '* \\1\n', text)
    text = text.replace("</ul>", "\n")

    text = text.replace("</div>", "\n")

    tags = '(span|b|div)'
    text = re.sub('<' + tags + '[^>]*>', '', text)
    text = re.sub('</' + tags + '>', '', text)

    text = text.replace("&quot;", '"')
    text = text.replace("&lt;", '<')
    text = text.replace("&gt;", '>')
    text = text.replace("&amp;", '&')

    text = text.replace("<br>", "\n")
    return text