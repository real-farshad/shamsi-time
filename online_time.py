import requests
import copy
from bs4 import BeautifulSoup
import jdatetime
from persian_converter import find_persian_month_name_in_text, find_persian_day_name_in_text

# Global cache variable
shamsi_time_cache = {
    'date': None,
    'data': None
}

def get_shamsi_time_info_online():
    try:
        shamsi_time_info = get_shamsi_time_info_online_impl()
        return shamsi_time_info
    except Exception as e:
        print(f"something went wrong in get_shamsi_time_info_online_impl: {e}")
        return None

def get_shamsi_time_info_online_impl():
    cached_data  = check_cache()
    if cached_data :
        return cached_data 

    soup = get_soup_from_url('https://time.ir')

    date_info = extract_shamsi_date_info(soup)
    month_occasions = extract_month_occasions(soup)
    date_info = add_occasions_to_date_info(date_info, month_occasions)

    date_info['year'] = convert_to_farsi_numbers(date_info['year'])
    date_info['month'] = convert_to_farsi_numbers(date_info['month'])
    date_info['day'] = convert_to_farsi_numbers(date_info['day'])
    
    add_date_info_to_cache(date_info)

    return date_info

def check_cache():
    current_date = jdatetime.date.today()
    if shamsi_time_cache['date'] == current_date:
        return shamsi_time_cache['data']
    
    return None

def get_soup_from_url(url):
    response = requests.get(url, timeout=5)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def extract_shamsi_date_info(soup):
    time_boxes_wrapper = soup.find('div', class_=lambda c: c and 'DateBoxResult' in c)
    time_boxes = time_boxes_wrapper.find_all('div', recursive=False)
    shamsi_time_box = time_boxes[0]

    shamsi_time_box_elements = shamsi_time_box.find_all('p', recursive=False)
    shamsi_time_date_string = shamsi_time_box_elements[1]

    date_text_elements = shamsi_time_date_string.text.split('/')
    year_index = date_text_elements[0]
    month_index = date_text_elements[1]
    day_index = date_text_elements[2]

    shamsi_time_descriptive_time_string = shamsi_time_box_elements[2]
    descriptive_date_text = shamsi_time_descriptive_time_string.text
    
    name_of_the_month = find_persian_month_name_in_text(descriptive_date_text)
    name_of_the_day = find_persian_day_name_in_text(descriptive_date_text)

    return {
        "year": year_index,
        "month": month_index,
        "day": day_index,
        "name_of_the_month": name_of_the_month,
        "name_of_the_day": name_of_the_day
    }

def extract_month_occasions(soup):
    occasions_wrapper = soup.find('div', class_=lambda c: c and 'events__container' in c)
    occasions = occasions_wrapper.find_all('div', recursive=False)

    month_occasions = {}
    for occasion in occasions:
        occasion_elements = occasion.find_all('span')

        occasion_date = occasion_elements[0]
        occasion_event = occasion_elements[1]

        occasion_date_text = occasion_date.text
        occasion_event_text = occasion_event.text

        day_index_in_date = occasion_date_text.split(' ')[0]
        day_index_in_date = day_index_in_date if len(day_index_in_date) != 1 else f"۰{day_index_in_date}"

        is_holiday = any('holiday' in cls for cls in occasion_date.get('class', [])) if occasion_date else False

        if day_index_in_date in list(month_occasions.keys()):
            previous_description = month_occasions[day_index_in_date]['occasion']
            month_occasions[day_index_in_date]['occasion'] = f"{occasion_event_text}, {previous_description}"
            if is_holiday:
                month_occasions[day_index_in_date]['is_holiday'] = is_holiday
        else:
            month_occasions[day_index_in_date] = {
                "occasion": occasion_event_text,
                "is_holiday": is_holiday
            }

    return month_occasions

def add_occasions_to_date_info(date_info, month_occasions):
    new_date_info = copy.deepcopy(date_info)
    if new_date_info['day'] in list(month_occasions.keys()):
        day_occasion = month_occasions[new_date_info['day']]
        new_date_info["occasion"] = day_occasion["occasion"]
        new_date_info["is_holiday"] = day_occasion["is_holiday"]

    return new_date_info

def convert_to_farsi_numbers(date_str):
    western_to_farsi = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    return date_str.translate(western_to_farsi)

def add_date_info_to_cache(date_info):
    shamsi_time_cache['date'] = jdatetime.date.today()
    shamsi_time_cache['data'] = date_info
