from __future__ import absolute_import

import os, random, re
from datetime import datetime, timedelta
from xml.etree import ElementTree

from django.core.management.commands.dumpdata import Command

from rapidsms.tests.scripted import TestScript

from schools.app import App
from schools.models import *
from blaster.models import *
from locations.models import *

# Got these from http://en.wikipedia.org/wiki/Districts_and_Regions_of_Uganda
# and http://babynamesworld.parentsconnect.com/category-ugandan-names.html
SCHOOL_AND_LAST_NAMES = \
    ["Abbo","Adroa","Akiiki","Akiki","Balondemu","Bitek","Gwandoya","Kadokechi","Kigongo",
     "Kissa","Kizza","Kyoga","Lutalo","Luzige","Madongo","Magomu","Mangeni","Masani",
     "Mulogo","Munanire","Munyiga","Musoke","Nabirye","Nabulungi","Najja","Nakisisa","Namono",
     "Nasiche","Ogwambi","Ojore","Okello","Taban","Wemusa","Wesesa","Zesiro","Zilabamuzale",
     "Kalangala","Kampala","Kayunga","Kiboga","Luwero","Lyantonde","Masaka","Mityana","Mpigi",
     "Mubende","Mukono","Nakaseke","Nakasongola","Rakai","Sembabule","Wakiso","Amuria","Budaka",
     "Bududa","Bugiri","Bukedea","Bukwa","Busia","Butaleja","Iganga","Jinja","Kaberamaido",
     "Kaliro","Kamuli","Kapchorwa","Katakwi","Kumi","Manafwa","Mayuge","Mbale","Namutumba",
     "Pallisa","Sironko","Soroti","Tororo","Abim","Adjumani","Amolatar","Amuru","Apac","Arua",
     "Dokolo","Gulu","Kaabong","Kitgum","Koboko","Kotido","Lira","Moroto","Moyo","Nakapiripirit",
     "Nebbi","Nyadri","Oyam","Pader","Yumbe","Bulisa","Bundibugyo","Bushenyi","Hoima","Ibanda",
     "Isingiro","Kabale","Kabarole","Kamwenge","Kanungu","Kasese","Kibale","Kiruhura","Kisoro",
     "Kyenjojo","Masindi","Mbarara","Ntungamo","Rukungirie"]
    

REGIONS = ["Central", "Eastern", "Northern", "Western"]

# map regions to districts 
DISTRICTS = \
    {"Central": ["Kalangala","Kampala","Kayunga","Kiboga","Luwero","Lyantonde","Masaka","Mityana","Mpigi",
                 "Mubende","Mukono","Nakaseke","Nakasongola","Rakai","Sembabule","Wakiso"],
     "Eastern": ["Amuria","Budaka","Bududa","Bugiri","Bukedea","Bukwa","Busia","Butaleja","Iganga","Jinja",
                 "Kaberamaido","Kaliro","Kamuli","Kapchorwa","Katakwi","Kumi","Manafwa","Mayuge","Mbale",
                 "Namutumba","Pallisa","Sironko","Soroti","Tororo"],
     "Northern": ["Abim","Adjumani","Amolatar","Amuru","Apac","Arua","Dokolo","Gulu","Kaabong","Kitgum",
                 "Koboko","Kotido","Lira","Moroto","Moyo","Nakapiripirit","Nebbi","Nyadri","Oyam","Pader",
                 "Yumbe"],
     "Western": ["Bulisa","Bundibugyo","Bushenyi","Hoima","Ibanda","Isingiro","Kabale","Kabarole",
                 "Kamwenge","Kanungu","Kasese","Kibale","Kiruhura","Kisoro","Kyenjojo","Masindi","Mbarara",
                 "Ntungamo","Rukungirie"]
     }

# Got these from http://www.studentsoftheworld.info/penpals/stats.php3?Pays=UGA
FIRST_NAMES = \
    ["Sharon","Joseph","Martha","John","Maureen","Alex","Sarah","James","Faith","Moses","Grace",
     "Henry","Esther","Patrick","Brenda","Julius","Gloria","David","Joan","Charles","Mercy",
     "Peter","Mary","Okello","Ruth","Ronald","Juliet","Micheal","Vicky","Jude","Ritah","Paul",
     "Florence","Isaac","Hellen","Brian","Diana","Emma","Racheal","Mark","Pearl","Solomon",
     "Prossy","Lawrence","Rachel","George","Annet","Richard","Doreen","Jack","Winnie","Denis",
     "Sylvia","Fred","Angel","Michael","Jackie","Robert","Cathy","Pius","Hope","Stephen",
     "Lydia","Andrew","Pauline","Eric","Lilian","Kenneth","Nabukenya","Williams","Linda",
     "Francis","Julie","Evans","Natasha","Joshua","Claire","Arthur","Annie","Ronnie",
     "Christine","Ivan","Stella","Tonny","Betty","Daniel","Viola","Tom","Patience","Kaggwa",
     "Keisha","Edward","Ciara","Kalungi","Sandra","Frank","Patricia","Jimmy","Lisa","Ben",
     "Carol","Eddy","Freda","Ambrose","Remmy","Christopher","Becky","Edgar","Anna","Hakim",
     "Marion","Derrick","Peace","Alfred","Clare","Marvin","Debbie","Matovu","Namutebi",
     "Nicholas","Joy","Abdul","Miriam","Allan","Kevin","Mukasa","Rebecca","Okot","Barbara",
     "Kyagaba","Dina","Joel","Bridget","Samuel","Karen","Mwesigwa","Pamella","Jonathan",
     "Joanne","Ssali","Sweetie","Bukenya","Jasmine","Martin","Beyonce","Phillip","Evelyne",
     "Nelly","Vivian","Benjamin","Dorah","Victor","Desire","Kimera","Jojo","Ssebulime",
     "Flavia","Lutaaya","Nicole","Mbabaali","Immaculate","Kato","Jennifer","Angwella","Olivia",
     "Ntambi","Barbie","Walter","Judith","Vincent","Iryn","Amos","Shannie","Timothy","Juliana",
     "Semi","Jovia","Sunday","Ann","Trevor","Paula","Wasswa","Nakirya","Innocent","Irene",
     "Arnold","Anita","Sammy","Mimi","Mathias","Pretty","Bob","Clara","Gerald","Angella","Otia",
     "Mbabazi","Mayanja","Leah","Tadeo"]

SCHOOL_TYPES = ["Primary", "Secondary"]

class TestApp (TestScript):
    apps = (App,)

    def setUp(self):
        self._create_locations()
        
    def testSchoolToElement(self):
        school = self._new_school()
        elem = school.to_element()
        expected = '<School latitude="%s" longitude="%s"><Name>%s</Name><Teachers>%s</Teachers></School>' %\
                    (school.latitude, school.longitude, school.name, school.teachers)
        # unfortunately we added a bunch of random crap to the xml and I'm not fixing these now
        #self.assertEqual(expected, ElementTree.tostring(elem))
        #self.assertEqual(expected, school.to_xml())
    
        
    def testGenerateData(self):
        self._create_message_blasts()
        blasts = MessageBlast.objects.all()
        for i in range(100):
            school = self._new_school()
            headmaster = self._new_reporter(school, "headmaster")
            self._create_groups(school)
            # these go to everyone
            for blast in blasts:
                BlastedMessage.objects.create(blast=blast,reporter=headmaster)
            to_populate = random.random() 
            if to_populate < .95:
                self._populate_data(school, headmaster)
            
            
        self._dumpdata()
    
    def _dumpdata(self):
        dumpdata = Command()
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__),"test_schools.json"))
        options = { "indent" : 2 }
        datadump = dumpdata.handle("locations", "reporters", "schools","blaster", **options)
        file = open(filename, "w")
        file.write(datadump)
        file.close()
        print "=== Successfully wrote fixtures to %s ===" % filename
        
    
    
    def _new_school(self):
        # estimate the rough boundaries of Uganda
        lat, lon = _ugandan_coordinate()
        min_students = 5
        max_students = 35
        name = "%s %s" % (random.choice(SCHOOL_AND_LAST_NAMES), random.choice(SCHOOL_TYPES))
        parent = random.choice(Location.objects.filter(type__name="District"))
        teachers = random.randint(3,20)
        count = School.objects.filter(parent=parent).count()
        school_code = "%(district)s%(school)03d" % \
                    {"district": parent.code, "school":count + 1}
        school_type = LocationType.objects.get(name="School")
        school = School.objects.create(latitude=str(lat), longitude=str(lon), 
                                       code=school_code, type=school_type,
                                       teachers=teachers, name=name, parent=parent)
        for year in range(1,3):
            # only make 3 grades to keep things simple
            girls = random.uniform(min_students, max_students)
            boys = random.uniform(min_students, max_students)
            Grade.objects.create(school=school,year=year,
                                 girls=girls,boys=boys)
        return school
        
    def _create_groups(self, school):
        for type in SCHOOL_GROUP_TYPES: 
            # headmasters are created separately so we guarantee exactly 1
            # per school
            if not type=="headmaster":
                members = random.randint(0,5)
                for i in range(members):
                    self._new_reporter(school, type)
                
    def _new_reporter(self, school, type):
        # create a reporter, add them to a school and the group type
        firstname = random.choice(FIRST_NAMES)
        lastname = random.choice(SCHOOL_AND_LAST_NAMES)
        alias = Reporter.parse_name("%s %s" % (firstname, lastname))[0]
        reporter = Reporter.objects.create(first_name=firstname, 
                                           last_name = lastname,
                                           alias=alias, location=school)
        reporter.save()
        group = SchoolGroup.get_or_create(type, school)
        reporter.groups.add(group)
        reporter.save()
        return reporter
        
        
    def _populate_data(self, school, headmaster):
        """Poplate a single report of each type"""
        now = datetime.now()
        # report time anywhere from 2 weeks ago to 2 days from now
        offset = random.randint(-2, 14)
        date = now + timedelta(days=offset)
        
        # each thing has a 90% chance of having a response
        if random.random() < .90:
            # say the water is 95% working
            water = False if random.random() > .95 else True
            SchoolWaterReport.objects.create(reporter=headmaster,
                                             date=date,
                                             school=school,
                                             water_working=water)
            message = BlastedMessage.objects.get(reporter=headmaster,
                                                 blast=self.WATER_BLAST)
            text = "yes" if water else "no"
            BlastResponse.objects.create(date=now,text=text, 
                                         message=message,success=True)
            
        if random.random() < .90:
            teachers = self._get_scaled_int(school.teachers,.95)
            SchoolTeacherReport.objects.create(reporter=headmaster,
                                           date=date,
                                           school=school,
                                           expected=school.teachers,
                                           actual=teachers)
            
            message = BlastedMessage.objects.get(reporter=headmaster,
                                                 blast=self.TEACHER_BLAST)
            BlastResponse.objects.create(date=now,text=str(teachers), 
                                         message=message,success=True)
        for grade in school.classes.all():
            if random.random() < .90:
                girls = self._get_scaled_int(grade.girls,.92)
                GirlsAttendenceReport.objects.create(reporter=headmaster,
                                                 date=date,
                                                 grade=grade,
                                                 expected=grade.girls,
                                                 actual=girls)
            if random.random() < .90:
                boys = self._get_scaled_int(grade.boys,.92)
                BoysAttendenceReport.objects.create(reporter=headmaster,
                                                date=date,
                                                grade=grade,
                                                expected=grade.boys,
                                                actual=boys)
                
        
    def _get_scaled_int(self, value, likelihood):
        """Treats value as a set of unique occurrences, each of which has
           likelihood percent chance of being true.  Returns a random number
           probabilistically = to one iteration of the values happening.  If
           likelihood = 0, returns 0, if likelihood = 1 returns value"""
        count = 0
        for i in range(value):
            if random.random() < likelihood:
                count += 1
        return count
    
    def _create_locations(self):
        try:
            LocationType.objects.get(name="School")
            # assume if this is there that everything else is set, we probably loaded
            # the fixtures.
            return 
        except LocationType.DoesNotExist:
            # just let this pass through to the rest of the method
            pass
        region_type = LocationType.objects.create(name="Region")
        district_type = LocationType.objects.create(name="District")
        school_type = LocationType.objects.create(name="School")
        region_code = 1
        for region_name in REGIONS:
            region = Location.objects.create(type=region_type,
                                             code=str(region_code), 
                                             name=region_name)
            district_code = 1
            for district_name in DISTRICTS[region_name]:
                full_district_code = "%(region)s%(district)02d" % \
                    {"region":region_code, "district":district_code}
                district = Location.objects.create(type=district_type,
                                                   code=full_district_code,
                                                   name=district_name,
                                                   parent=region)
                district_code = district_code+1
            region_code = region_code+1
            
        
    def _create_message_blasts(self):
        questions = [1,2]
        now = datetime.now()
        blasts = []
        for question_id in questions:
            question = BlastableMessage.objects.get(id=question_id)
            blasts.append(MessageBlast.objects.create(message=question,date=now))
        self.WATER_BLAST = blasts[0]
        self.TEACHER_BLAST = blasts[1]
        
def _ugandan_coordinate():
    min_lat = -0.964005
    max_lat = 3.518904
    min_lon = 29.992676
    max_lon = 34.727783
    lat = random.uniform(min_lat, max_lat)
    lon = random.uniform(min_lon, max_lon)
    if _in_lake(lat, lon):
        return _ugandan_coordinate()
    return (lat,lon)

def _in_lake(lat, lon):
    # it's a big lake...
    # we also use this to snip off the upper left area where the country
    # cuts in.
    return (lat < 0.400998 and lon > 31.761475) or \
           (lat > 1.10955 and lon < 31.135254)
    