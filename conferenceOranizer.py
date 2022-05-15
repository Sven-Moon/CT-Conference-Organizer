# get data 
# write to dicts by country

# create date order obj:
# create an ordered dict with key format: mm-dd for min-max date


# for members in group,
# count dates available (05-02: 3, 05-03:6, 05-04:6)

# cycle through the dates,
# add availability for day + next day
    #choose date with highest availability total as start
    # if the count is less than 2x name count
        # find person(s) unable to make it, & remove name from invite list
        
    #post format:
    # { 'attendeeCount': int,
    #  'attendees': [<email>],
    #  'name': str (country),
    #  'startDate': date}
    
DAYS_IN_MONTH = {
    "01": 31, "02": 28, "03": 31, "04": 30, 
    "05": 31, "06": 30, "07": 31, "08":31,
    "09": 30, "10": 31, "11": 30, "12": 31
}
 
import json, re
import requests as r
from collections import OrderedDict

class Member:
    def __init__(self, first_name, last_name, country, available_dates, email) -> None:
        self.name = f'{first_name} {last_name}'
        self.country = country
        self.available_dates = available_dates
        self.email = email

class Conf_Organizer:

    def run(self, url):
        self.get_partners(url)
        self.run_analysis()
        self.compile_results()
        # self.post_results()
        
    def get_partners(self,url):
        data = self.get_data(url)
        for p in data:
            # add country to attributes if not already there
            if not p['country'] in vars(self):
                setattr(self, p['country'], Country(p['country']))
            # add member to country
            member = Member(p['firstName'],p['lastName'], 
                        p['country'], p['availableDates'], p['email'])
            getattr(self,p['country']).add_member(member)
            
        print(getattr(self, 'United States').name)
        print(getattr(self, 'United States').emails)
            
    def get_data(self, url):
        data = r.get(url)
        if data.status_code == 200:
            data = data.json()
        else:
            print('Error retrieving data')
        return data['partners']
        
    def run_analysis(self):
        for country in vars(self):
            getattr(self, country).find_best_date()
        
    def compile_results(self):
        results = []
        for country_name in vars(self):
            country = getattr(self, country_name)
            results.append( {
                "attendeeCount": len(country.attending_members),
                "attendees": country.attending_members,
                "name": country.name,
                "startDate": country.best_day
            })
        return results
    
    def post_results(self):
        url = ''
        data = self.compile_results()
        self.display_results()
        # x = r.post(url, data=data)
     
    def display_results(self):
        partners = self.compile_results()
        for partner in partners:
            print(f'{partner["name"]}')
            print(f'{partner["attendeeCount"]}')
            print(f'{partner["startDate"]}')
            print(f'{partner["attendees"]}')
            print('\n')
     
     
class Country:
    def __init__(self, name) -> None:
        self.name = name
        self.emails = []
        self.members = []
        self.available_dates = OrderedDict()
        self.min_date = '2019-01-01'
        self.max_date = '2016-01-01'
        self.date_map = OrderedDict()
        self.date_count_available = []
        self.best_day = ''
        self.second_day = ''
        self.attending_members = []

        
    def add_member(self, member):
        self.members.append(member)
        self.emails.append(member.email)
        self.add_dates_to_available_dates(member.available_dates,member)
        
    def add_dates_to_available_dates(self,dates,member):
        for date in dates:
            if date not in self.available_dates:
                self.available_dates[date] = []            
            self.available_dates[date].append(member.email)
            self.adjust_max_min_date(date)
                
    def adjust_max_min_date(self, date):
        # print("date",date)
        # print("minDate: ", self.min_date,"maxDate:",self.max_date)
        # print("self.min_date > date:",self.min_date > date,"self.max_date < date:", self.max_date < date)
        if self.min_date > date:
            self.min_date = date
        if self.max_date < date:
            self.max_date = date
                
    def create_date_map(self):
        min_month =str( re.search(r'-(\d{2})-',self.min_date).group(1)).zfill(2)
        min_month_min_day = str(re.search(r'-(\d{2})$',self.min_date).group(1)).zfill(2)
        max_month = str(re.search(r'-(\d{2})-',self.max_date).group(1)).zfill(2)
        max_month_max_day = str(re.search(r'-(\d{2})$',self.max_date).group(1)).zfill(2)
        
        if min_month < max_month:
            # create date entries for min month, min day - end
            self.add_partial_month(min_month,min_month_min_day,DAYS_IN_MONTH[min_month])
            # create date entries for months between (if any)
            self.add_full_month(min_month,max_month)
            
            # create date entires for max month day 1 - max day
            self.add_partial_month(max_month,1,max_month_max_day)
        else: # all dates are in same month
            self.add_partial_month(min_month,min_month_min_day,max_month_max_day)            
            
    def add_partial_month(self, month, start, end):
        for int_day in range(int(start), int(end)+1):
            day = str(int_day).zfill(2)
            self.date_map[f'2017-{month}-{day}'] = 0
            
    def add_full_month(self, min_month, max_month):
         for int_month in range(int(min_month)+1, int(max_month)+1):
            month = str(int_month).zfill(2)
            for day in range(1, DAYS_IN_MONTH[month]+1):
                self.date_map[f'2017-{month}-{day}'] = 0 
    
    def create_date_map_counts(self):
        print("self.date_map:")
        for date in self.date_map:
            print(date)
        # return array of tuples (date, count_of_members_available)
        for map_date in self.date_map:
            if self.available_dates.get(map_date) is None:
                self.date_count_available.append((map_date,0))
            else:
                self.date_count_available.append((map_date, len(self.available_dates[map_date])))
    
    def find_best_date(self):
        self.create_date_map()
        self.create_date_map_counts()
        print(self.date_count_available)
        best_date = ''
        best_count = 0
        for i in range(len(self.date_count_available)-1):
            if self.date_count_available[i][1] + self.date_count_available[i+1][1] > best_count:
                best_count = self.date_count_available[i][1] + self.date_count_available[i+1][1]
                best_date = self.date_count_available[i][0]
                second_day = self.date_count_available[i+1][0]
                
        # Also check if best date includes all members (count == 2x number of members)
        self.best_day = best_date        
        print(f'Best day for {self.name} is {best_date}')
        print(f'Second day for {self.name} is {second_day}')
        if best_count == 2*len(self.members):
            self.attending_members = [email for email in self.members.email]
        else:
            self.find_attending_members(best_date,second_day)
    
    def find_attending_members(self, first_day, second_day):
        for member in self.members:
            if first_day in member.available_dates and second_day in member.available_dates:
                self.attending_members.append(member.email)
    
    def print_dates(self):
        print(self.name)
        print(self.best_day)
        print(self.date_count_available)
        print(self.attending_members)


def run():
    taco_conference = Conf_Organizer()
    taco_conference.run('https://ct-mock-tech-assessment.herokuapp.com/')
    
    
run()