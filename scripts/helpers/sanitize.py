import arcpy
import string

def sanitize(text):
    """provide a list of messages to this method"""
    return str(text).translate(str.maketrans('', '', string.punctuation))
