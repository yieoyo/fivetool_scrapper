import os
import sys
import requests
from bs4 import BeautifulSoup
import json
import time
import random
import threading

class ProfileScraper(threading.Thread):
    def __init__(self, session, href, page_dict,pagenumber,playernumber):
        threading.Thread.__init__(self)
        self.session = session
        self.href = href
        self.page_dict = page_dict
        self.pagenumber = pagenumber
        self.playernumber = playernumber

    def run(self):
        retry_counter = 3
        for _ in range(retry_counter):
            try:
                profile = self.session.get(self.href)
                soup = BeautifulSoup(profile.content, 'html.parser')
                playerheader = soup.find("div", class_="player-header")

                if playerheader:
                    row_element = playerheader.find("div", class_="row")
                    if row_element:
                        json_objects = {'URL': self.href}
                        profile_img_div = playerheader.find("div", class_="profile-img")
                        if profile_img_div:
                            h3_text = profile_img_div.find('h3').text.strip()
                            background_image_url = profile_img_div.find('div', class_='profile-img-display')['style'].split('url(')[-1].split(')')[0]
                            json_objects['Profile Picture'] = background_image_url
                            json_objects['Name'] = h3_text
                        allptagss = row_element.find_all('p')
                        for p_tag in allptagss:
                            text = p_tag.get_text().strip().split(":")
                            if text:
                                json_objects[text[0]] = text[1] if len(text) > 1 else 'no value'
                        playernumber = self.playernumber + 1
                        print('Page: ' + str(self.pagenumber) + ' : ' + 'Player: ' + str(playernumber) + ' : ' + self.href)
                        self.page_dict.append(json_objects)
                        break
                    else:
                        print("No 'row' element found within 'player-header'")
                else:
                    print("No 'player-header' class found")
            except Exception as e:
                print(f"Error occurred, retrying for player url: {self.href} {e}")

class FivetoolProfile:
    def __init__(self, login_url, target_url, username, password):
        self.login_url = login_url
        self.target_url = target_url
        self.username = username
        self.password = password
        self.session = requests.Session()

    def login(self):
        response = self.session.get(self.login_url)
        soup = BeautifulSoup(response.content, "html.parser")
        viewstate = soup.find("div", {"id": "loginform"})
        _token = viewstate.find("input", {"name": "_token"})["value"]
        redirect_to = viewstate.find("input", {"name": "redirect_to"})["value"]
        if _token:
            login_response = self.session.post(self.login_url,
                                                data={"_token": _token,
                                                      "formdata": "_token=" + str(_token) + "&email=" + str(
                                                          self.username) + "&password=" + str(
                                                          self.password) + "&redirect_to=" + str(redirect_to)
                                                      })
            login_response = json.loads(login_response.text)
            if 'msg' in login_response and 'success' in login_response['msg']:
                print("String 'success' found in the value associated with the key 'msg'")
                self.scrape()
            else:
                print("String 'success' not found in the value associated with the key 'msg'")
        return False

    def scrape(self):
        pagenumber = 95
        while True:
            pagenumber += 1
            redirected_url = self.target_url + str(pagenumber)
            page_retry_counter = 3
            for _ in range(page_retry_counter):
                try:
                    response = self.session.get(redirected_url)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    table = soup.find('table')
                    tbody = table.find('tbody')
                    if tbody.find_all():
                        page_dict = []
                        threads = []
                        for playernumber, tr in enumerate(tbody.find_all('tr')):
                            a_tag = tr.find('a')
                            if a_tag:
                                href = a_tag.get('href')
                                thread = ProfileScraper(self.session, href, page_dict, pagenumber,playernumber)
                                thread.start()
                                threads.append(thread)
                        for thread in threads:
                            thread.join()
                        
                        self.writefile(pagenumber, page_dict)
                        random_seconds = random.randint(1, 3)
                        time.sleep(random_seconds)
                        break
                    else:
                        print("No new page to scrape")
                        break
                except Exception as e:
                    print(f"Error occurred, retrying for url: {redirected_url} {e}")

    def writefile(self, pagenumber, my_dict):
        try:
            current_directory = os.getcwd()
            file_path = os.path.join(current_directory, 'data', f'{pagenumber}.txt')
            with open(file_path, 'w') as file:
                json.dump(my_dict, file, indent=4)
            print(f"File '{file_path}' created successfully.")
        except Exception as e:
            print(f"Error occurred: {e}")

if __name__ == "__main__":
    login_url = "https://fivetool.org/customer/login"
    target_url = "https://fivetool.org/players?address_state=&category=player&division=&grad_year=2025&keyword=&level=&page="
    username = "fivetool email address"
    password = "passsword"

    scraper = FivetoolProfile(login_url, target_url, username, password)
    scraper.login()
