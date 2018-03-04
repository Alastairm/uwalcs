"""This script finds all standard semester units and lecture videos in a given
    timeframe, is able to place lecture videos into individual unit html files
    following a given template, and generate a html file containing a list of
    all units that were found.
"""
import urllib.request as request
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta
import re
import os.path
#pip3 install tqdm
from tqdm import tqdm

#URL to UWA's echo lecture repository
BASE_URL = 'http://media.lcs.uwa.edu.au/echocontent/'

# def url_from_date(datetime):
#     return BASE_URL+datetime.strftime('%y%W/%w')

def url_today():
    today = datetime.now()
    return BASE_URL+today.strftime(f"%y%W/{today.weekday()+1}")


def check_date(year: int=None, week: int=None, day: int=None):
    """Checks year, week and day ints are within valid ranges.
    Args:
        year (int): Two digit year abbreviation, valid range: 15 to current year
        week (int): ISO week number, valid range: 1 to 53
        day  (int): ISO weekday, valid range: 1 (Monday) to 7(Sunday)
    Returns:
        bool: True if valid, False otherwise.
    Raises:
        ValueError: If input arguments are outside of the allowed ranges
    """
    current_year = str(datetime.now().year)[-2:]
    if year and (year < 15 or year > current_year):
        raise ValueError(f"Year argument out of range (valid:15-{current_year}")
    if week and (week < 1 or week > 53):
        raise ValueError("Week argument out of range (valid:1-53")
    if day and (day < 1 or day > 7):
        raise ValueError("Day argument out of range (valid:1-7)")
    return True


def get_hashes_from_dir(url: str):
    """Fetches all links in a directory that are in the correct unit hash format
    """
    response = request.urlopen(url)
    data = response.read()
    page_text = data.decode('utf-8')

    #A Very     ive way to select the correct links, regex would be more robust.
    links = page_text.split("<a href=\"")
    links = links[6:]
    links.reverse()

    hash_links = []
    for link in links:
        hash_links.append(link[0:36])
    return hash_links


def get_todays_hashes():
    URLToday = url_today()
    return get_hashes_from_dir(URLToday)



class UnitXML:
    """Class for holding the section.xml file and related info for a given unit

    Attributes:
        url (str): URL for the unit's section.xml file
        tree (ET.Element): XML tree of unit's section.xml file
    """

    url = BASE_URL
    fileName = '/presentation.xml'

    def __init__(self, unitHash: str):
    
        self.url = self.url+unitHash+self.fileName
        print(self.url)
        data = request.urlopen(self.url)
        data = data.read()
        self.tree = ET.fromstring(data)

    def get_year(self):
        year = self.tree.find('term').find('name')
        return year.text[2:]

    def get_sem(self):
        longName = self.tree.find('name')
        #Attempt to split the name at "Standard semester "
        semester = longName.text.split(sep='Standard semester ')
        if len(semester) == 1:
            #String does not contain "Standard semester "
            return None
        return semester[1][0]

    def get_unit_code(self):
        unitCode = self.tree.find('course').find('identifier')
        return unitCode.text

    def get_unit_url(self):
        unitURL = self.tree.find('portal').find('url')
        return unitURL.text

class LectureXML:
    """ class for holding the presentation.xml and
         related info for a given lecture

    Attributes:
        url (str): URL for the lecture's directory
        tree (ET.Element): XML tree of lecture's presentation.xml
    """

    fileName = 'presentation.xml'

    def __init__(self, year: int, week: int, day: int, lectureHash: str):
        """ Initialises lectureXML class by fetching presentation.xml from
        BASE_URL/year+week/dday/lectureHash'

        Parameters:
            year (int): Two digit year abbreviation,
                valid range: 15 to current year
            week (int): ISO week number, valid range: 1 to 53
            day  (int): ISO weekda, valid range: 1 (Monday) to 7(Sunday)
            lectureHash (str): Name of lecture's parent directory
                (e.g. 01234567-89ab-cdef-0123-456789abcdef)

        Raises:
            ValueError: If input arguments are outside of the allowed ranges
        """
        check_date(year, week, day)

        dirPath = str(year) + str(week) +'/'+ str(day) +'/'+ lectureHash +'/'
        self.url = BASE_URL + dirPath
        data = request.urlopen(self.url+'presentation.xml')
        data = data.read()
        self.tree = ET.fromstring(data)

    def get_lecture_unit(self):
        unitName = self.tree.find('presentation-properties').find('name')
        unitCode = unitName.text[0:8]
        return unitCode

    def get_lecture_video_url(self):
        return self.url + 'audio-vga.m4v'

    def get_lecture_time_date(self):
        """ Returns:
            A tuple (time,date) which is suitable for printing:
                time (str): time and day of video (e.g. "9AM Monday")
                date (str): day month year of video (e.g. "29 July 2015")
            e.g. ("9AM Monday", "29 July 2015")
        """
        time = self.tree.find('presentation-properties').find('start-timestamp')
        time = datetime.strptime(time.text, "%d-%b-%Y %H:%M:%S")
        #Lecture recordings start 2min prior to Lecture time:
        time = time + timedelta(minutes=2)
        date = time.strftime("%d %B %Y ")
        time = time.strftime("%I%p %A")
        if time[0] == '0':
            time = time[1:]
        return time, date

    def get_lecture_location(self):
        location = self.tree.find('presentation-properties').find('location')
        return location.text


def get_semester_units(year: int, semester: int):
    """Fetches all units in a given semester and returns a list of
    (unitcode, echo_lcs_url) tuples.

    Parameters:
        year (int): two digit abbreviation of Year in which the units ran
        semester (int): Semester in which the units ran (e.g. '1' or '2')
    """
    check_date(year=year)
    year = str(year)
    semester = str(semester)

    print('Fetching all unit URLs')
    unitHashes = get_hashes_from_dir(BASE_URL + 'sections/')
    #Regex to match with a valid unit code e.g. ABCD1234
    validUnit = re.compile('[a-zA-Z]{4}[0-9]{4}')

    sem_units = []
    print("Finding units from 20%s:"%( year))
    for _, unitHash in tqdm(enumerate(unitHashes),
                            total=len(unitHashes),
                            unit="units"):
        xml = UnitXML(unitHash)
        if xml.get_year() == year:
            unitCode = xml.get_unit_code()
            if not validUnit.match(unitCode):
                continue
            unitURL = xml.get_unit_url()
            unitInfo = unitCode, unitURL
            sem_units.append(unitInfo)
    return sem_units

def add_semester_units(year: int, semester: int):
    """Fetches all units in a given semester and adds them to JSON database.
    Parameters:
        year (int): two digit abbreviation of Year in which the units ran
        semester (int): Semester in which the units ran (e.g. '1' or '2')
    """

def get_days_lectures(year: int, week: int, day: int):
    """Fetches all units in a given semester and adds them to JSON database.
    Parameters:
        year (int): two digit abbreviation of Year of lecture
        week (int): Week of year of the lecture
        day (int): day of week lecture occured on
    """
