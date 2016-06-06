
def rstripText(basetext, striptext):
    if basetext.endswith(striptext):
        return basetext[:-len(striptext)]
    return basetext

def lstripText(basetext, striptext):
    if basetext.startswith(striptext):
        return basetext[len(striptext):]
    return basetext

def isTextYes(text):
    return text.lower() in ('yes', 'true', '1', 't', 'y')
