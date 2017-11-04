"""This script finds all standard semester units and lecture videos in a given
    timeframe, is able to place lecture videos into individual unit html files
    following a given template, and generate a html file containing a list of
    all units that were found.
"""
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import re
import os.path

from tqdm import tqdm #pip3 install tqdm

BASE_URL = 'http://media.lcs.uwa.edu.au/echocontent/'


def get_hashes_from_dir(url):
    """Fetches all links in a directory that are in the right hash format
    """
    response = urllib.request.urlopen(url)
    data = response.read()
    text = data.decode('utf-8')

    links = text.split("<a href=\"")
    links = links[6:]
    links.reverse()

    hash_links = []
    for link in links:
        hash_links.append(link[0:36])
    return hash_links

def check_year_week_day(year, week, day):
    """Checks year, week and day ints are within valid ranges.
    Args:
        year (int): Two digit year abbreviation, valid range: 15 to current year
        week (int): ISO week number, valid range: 1 to 53
        day  (int): ISO weekda, valid range: 1 (Monday) to 7(Sunday)
    Returns:
        bool: True if valid, False otherwise.
    Raises:
        ValueError:    If input arguments are outside of the allowed ranges
    """
    if year < 15 or year > datetime.now().year:
        raise ValueError("Year argument out of range (valid:15-"+
                         str(datetime.now().year)[-2:])
    if week < 1 or week > 53:
        raise ValueError("Week argument out of range (valid:1-53")
    if day < 1 or day > 7:
        raise ValueError("Day argument out of range (valid:1-7)")

class UnitXML:
    """Class for holding the section.xml file and related info for a given unit

    Attributes:
        url (str): URL for the unit's section.xml file
        tree (ET.Element): XML tree of unit's section.xml file
    """

    sectionsURL = BASE_URL+'sections/'
    fileName = '/section.xml'

    def __init__(self, unitHash):
        self.url = self.sectionsURL+unitHash+self.fileName
        data = urllib.request.urlopen(self.url)
        data = data.read()
        self.tree = ET.fromstring(data)

    def get_year(self):
        year = self.tree.find('term').find('name')
        return year.text[2:]

    def get_sem(self):
        longName = self.tree.find('name')
        #Attempt to split the name at "Standard semester "
        semester = longName.text.split(sep='Standard semester ')
        if len(semester) < 2:
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

    def __init__(self, year, week, day, lectureHash):
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
        check_year_week_day(year, week, day)

        dirPath = str(year) + str(week) +'/'+ str(day) +'/'+ lectureHash +'/'
        self.url = BASE_URL + dirPath
        data = urllib.request.urlopen(self.url+'presentation.xml')
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

def save_unit_semester_links(year, semester,
                             unitListFileName='unitList.html',
                             unitListTemplateFileName='unitListTemplate.html',
                             unitTemplateFileName='unitTemplate.html',
                             unitDirName='units'):
    """Fetches all units in a given semester and
        sets up unitCode.html files for each one.

    Parameters:
        year (str): two digit abbreviation of Year in which the units ran
        semester (str): Semester in which the units ran

        unitListFileName (optional[str]): Location of HTML file to add list of
             units to (default: 'unitList.html').
        unitListTemplateFileName (optional[str]): File containing template for
             unitListFileName (default: 'unitListTemplate.html').
        unitTemplateFileName (optional[str]): Location of HTML template for
             unitCode.html files (default: 'unitTemplate.html').
        unitDirName (optional[str]): Directory in which to place unitCode.html
             files (default: 'units').
    """

    # Use .format( [unitCode], [echoLink], [unitDir]) with unitHTML string
    unitHTML = """
        <div class="row">
            <div class="col-md-4"></div>
            <div class="col-md-1">{0}:</div>
            <div class="col-md-3">
                <div class="col-md-4"><a href="{2}/{0}.html">Downloads</a></div>
                <div class="col-md-4"><a href="{1}">Echo</a></div>
            </div>
            <div class="col-md-4"></div>
        </div>
        """

    validUnit = re.compile('[a-zA-Z]{4}[0-9]{4}')

    unitHashes = get_hashes_from_dir(BASE_URL + 'sections/')

    # Fetch unit info from retrieved hashes
    output = []
    print("Finding units from semester %s 20%s:"%(semester, year))
    for i, unitHash in tqdm(enumerate(unitHashes),
                            total=len(unitHashes),
                            unit="units"):
        xml = UnitXML(unitHash)
        if xml.get_year() == year:
            if xml.get_sem() == semester:
                unitCode = xml.get_unit_code()
                if not validUnit.match(unitCode):
                    continue
                unitURL = xml.get_unit_url()
                unitInfo = unitCode, unitURL
                output.append(unitInfo)
    output.sort()

    # Write out unit.html file links to unitListFile
    print("Fetched "+str(len(output))+" units, writing to file...")
    unitListTemplateFile = open(unitListTemplateFileName, 'r')
    unitListFileHTML = unitListTemplateFile.read()
    unitListFileHTML = unitListFileHTML.replace('{{semester}}', semester)
    unitListFileHTML = unitListFileHTML.replace('{{year}}', "20"+year)
    for unit in output:
        unitListFileHTML += unitHTML.format(unit[0], unit[1], unitDirName)
    unitListFile = open(unitListFileName, 'w')
    unitListFile.write(unitListFileHTML)
    unitListFile.close()

    # Write out individual unitCode.html files in unitDirName
    unitTemplateFile = open(unitTemplateFileName, 'r')
    template = unitTemplateFile.read()
    unitTemplateFile.close()
    for unit in output:
        unitPage = open(unitDirName+'/'+unit[0]+'.html', 'w')
        uTemplate = template
        uTemplate = uTemplate.replace('{{pageTitle}}', unit[0])
        uTemplate = uTemplate.replace('{{semester}}', semester)
        uTemplate = uTemplate.replace('{{year}}', year)
        unitPage.write(uTemplate)
        unitPage.close()

def fetch_days_units(year, week, day):
    check_year_week_day(year, week, day)
    print('fetching /%02d%02d/%01d'%(year, week, day))
    lectureHashes = get_hashes_from_dir('%s%02d%02d/%01d'%(BASE_URL,year,week,day))
    for lectureHash in lectureHashes:
        try:
            xml = LectureXML(year, week, day, lectureHash)
        except urllib.error.HTTPError:
            continue
        unitCode = xml.get_lecture_unit()
        if unit_has_page(unitCode):
            lectureURL = xml.get_lecture_video_url()
            lectureDayTime, lectureDate = xml.get_lecture_time_date()
            lectureLocation = xml.get_lecture_location()
            append_lecture(unitCode,
                           lectureURL,
                           lectureDayTime,
                           lectureDate,
                           lectureLocation)

def unit_has_page(unitCode):
    """Checks a html file exists for the given unitCode in /units/"""
    return os.path.isfile('units/'+unitCode+'.html')

def fetch_weeks_units(year, week):
    print('Fetching /%02d%02d/'%(year, week))
    for day in range(1, 8):
        try:
            fetch_days_units(year, week, day)
        except urllib.error.HTTPError:
            print('skipping day %01d, 404 returned'%day)
            continue

def add_unit(unitCode):
    pass

def append_lecture(unitCode,
                   lectureURL,
                   lectureDayTime,
                   lectureDate,
                   lectureLocation):
    lectureHTML = """

        <div class="row">
            <div class="col-sm-3"></div>
            <div class="col-sm-2">
                <div class="col-sm-12">{0}</div>
                <div class="col-sm-12">{1}</div>
            </div>
            <div class="col-sm-4">
                <div class="col-sm-12">{2}</div>
                </div>
            <div class="col-sm-2">
                <div class="col-sm-12"><a download="download.m4v" href="{3}">Download</a></div>
            </div>
            <div class="col-sm-1"></div>
        </div>

        <div class="row">
            <div class="col-sm-12">&nbsp</div>
        </div>

        """
    link = lectureHTML.format(lectureDayTime, lectureDate,
                              lectureLocation, lectureURL)
    unitPage = open('units/'+unitCode+'.html', 'a')
    unitPage.write(link)
    unitPage.close()
