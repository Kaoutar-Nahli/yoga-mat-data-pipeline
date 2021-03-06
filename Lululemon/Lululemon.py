#%%
from numpy import numarray
import pandas as pd
import csv , json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from datetime import date, datetime
from time import sleep, time

import urllib.request
from pathlib import Path
import tempfile
import pprint

#libraries to upload to aws
import psycopg2 as ps2
import pandas as pd
from sqlalchemy import create_engine 
from botocore.exceptions import ClientError
import logging
import boto3

import os
from webdriver_manager import chrome # ChromeDriverManager`
def chrome_driver():
        options = Options()
        options.add_argument("--log-level=3")  # disable Info/Error/Warning in Chrome Driver
        os.environ['WDM_LOG_LEVEL'] = '0'  # Disable the logging of ChromeDriverManager()
        WebDriver = webdriver.Chrome(chrome.ChromeDriverManager().install(), options=options)
        return WebDriver
# options = webdriver.ChromeOptions()
# options.headless = True
#options.add_argument
# options.add_argument("--window-size=1920,1080")
# options.add_argument('--ignore-certificate-errors')
# options.add_argument('--allow-running-insecure-content')
# options.add_argument("--disable-extensions")
# options.add_argument("--proxy-server='direct://'")
# options.add_argument("--proxy-bypass-list=*")
# options.add_argument("--start-maximized")
# options.add_argument('--disable-gpu')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--no-sandbox')
# driver = webdriver.Chrome( options=options)
BUCKET = 'webscraping-project-amazon-mats-pictures'
#to make it go faster
# options = webdriver.ChromeOptions()
# prefs = {"profile.managed_default_content_settings.images": 2}
# options.add_experimental_option("prefs", prefs)

#Creating class for each product which includes all features including url and s3 uri
class YogaMat:
    def __init__(self,id_mat='', provider='Lululemon', name='', price='', material=[], number_of_reviews='', rating ='', colours ='', image_url='',image_uri='', product_url=''):
        self.id_mat = id_mat
        self.provider = provider
        self.name = name
        self.price = price
        self.material = material
        self.rating = rating
        self.number_of_reviews = number_of_reviews
        self.colours = colours
        self.image_url = image_url
        self.image_uri = image_uri
        self.product_url = product_url

    def __repr__(self):
        return (f'{self.id_mat},{self.provider}, {self.name}, {self.price}, {self.material},{self.number_of_reviews}, {self.rating}, {self.colours}, {self.image_url}, {self.image_uri}, {self.product_url}\n')
    
class Bot():
    def __init__(self, headless=False):
        print('initializing bot') 
        options = Options() 
        if headless:
            options.add_argument('--headless')
            options.add_argument("--window-size=1920,1080")
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument("--disable-extensions")
            options.add_argument("--proxy-server='direct://'")
            #options.add_argument("--proxy-bypass-list=*")
            options.add_argument("--start-maximized")
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
        options.add_argument("--no-sandbox")   # without this, the chrome webdriver can't start (SECURITY RISK)
        self.driver = chrome_driver()			# create webdriver #options=options
    
    def upload(self,file_name, bucket, object_name=None):
        """
        Upload a file to an S3 bucket
        
        Parameters
        ----------
        file_name : stra
            Name of the file we want to upload
        bucket: str
            Name of the bucket
        object_name:
            Name of the object as we want it to appear in the bucket

        Returns
        -------
        bool
            False if the upload caused an error. True if the upload was successful
        """
        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        # Upload the file
        s3_client = boto3.client('s3')
        try:
            response = s3_client.upload_file(file_name, bucket, object_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True
            
    def get_all_links_to_each_mat(self): 
        """
        we are in the page where all products are listed and this function get all urls to each
        one or those products and appends into the list all_links

        """
        self.driver.get('https://www.lululemon.co.uk/en-gb/c/accessories?prefn1=styleNumber&prefv1=Yoga+Mats&sz=34')
        sleep(5)
        all_links = []
        for i in range(2,6): #(0,33)
            try:
                path_each = f'//*[@id="product-search-results"]/div[2]/div[2]/div[4]/div[{i}]/div/div/div[2]/div[2]/a'
                product_link = self.driver.find_element_by_xpath(path_each)
                link = product_link.get_attribute('href')
                print(link)
                all_links.append(link)
            except Exception as e:
                print('meassage',e)
                continue
        return(all_links)
    
    
    def get_materials(self):
        '''
        Feature materials, replacing commas by dash
        '''
        try:
            material_link = self.driver.find_element_by_xpath('//*[@id="collapseThree"]/ul/li')
            material_text = material_link.get_attribute("innerHTML")
        except Exception as e:
            material_text = 'error'
                    
    
        return (material_text.replace(',',' -'))


    def get_price (self):
        try:
            price_link = self.driver.find_element_by_class_name('markdown-prices')
            price = price_link.get_attribute('innerHTML')
        except Exception as e:
                price = 'error'

        return (price.replace('\n', ''))


    def get_name(self):
        try:
            name_link = self.driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[3]/div[3]/h1')
            name =  name_link.text
        except Exception as e:
            name = 'error'
        
        return (name)


    def get_number_of_reviews (self):
        try:
            number_of_reviews_xpath = self.driver.find_element_by_xpath('//*[@id="BVRRSearchContainer"]/div/div/div/div/div/div[1]/div/dl/dd[2]/a')
            number_of_reviews = number_of_reviews_xpath.text.split()[0]
        except Exception as e:
            number_of_reviews = 'error'
        
        return number_of_reviews
    
    def get_rating(self):
        try:
            
            rating_link = self.driver.find_element_by_class_name('bv-rating')
            rating = rating_link.text.split()[0]
            
        except Exception as e:
                rating = 'error'
        return rating

    def get_colours(self):
        try:
            colour_link = self.driver.find_element_by_class_name('selected-swatch-name')
            colour = colour_link.get_attribute("innerHTML")
        
        except Exception as e:
                colour = 'error'
        
        return colour

    def get_id(self, count):
        '''
        id used to identyfy each mat in s3 
        '''
        return f"mat_id_{count:04d}"


    def get_image(self, id):
        '''
        Uploading images to the bucket created in s3 using the function upload_file

        '''
        try:

            img_url = self.driver.find_element_by_xpath('//*[contains(@id,"pdpCarousel")]/div[1]/div[1]/a/img').get_attribute('src')


            with tempfile.TemporaryDirectory() as temp_dir:
                        #downloading the image
                        urllib.request.urlretrieve(img_url, f'{temp_dir}/webscarping_image{id}.png')
                        #uploading the image to s3
                        object_name=f'lululemon/{id}.png'
                        self.upload(f'{temp_dir}/webscarping_image{id}.png', 'webscraping-project-amazon-mats-pictures',object_name)
                        uri_s3 =f's3://webscraping-project-amazon-mats-pictures/{object_name}.png'
                        print(f'image with mat_id:{id} has been uploaded')

        except Exception as e:
            print('meassage',e)

        return(img_url,uri_s3)



        
    def fetch_all_data_for_one_mat(self,mat_url,count):
            self.driver.get(mat_url)
            sleep(5)
            id_product = self.get_id(count)
            url_img,uri_img = self.get_image(id_product) 
        
            mat_yoga = YogaMat(
                id_mat = id_product,
                material = self.get_materials(),
                price = self.get_price(),
                name = self.get_name (),
                rating = self.get_rating (),
                number_of_reviews = self.get_number_of_reviews(),
                colours = self.get_colours(),
                image_url = url_img,
                image_uri = uri_img,
                product_url = mat_url

            )
            return(mat_yoga)
if __name__ == '__main__':
   # Script to run all functions
    start_time =  time()
    # initializing class bot
    bot = Bot(headless=False)
    #first get all urls for the products
    links = bot.get_all_links_to_each_mat()
    print('urls for each product were obtained')
    print(links)

    #initialize list to append all instances created
    all_mats = []

    for url,count in zip(links, range(len(links))):
        try:
            single_mat = bot.fetch_all_data_for_one_mat(url,count)
            all_mats.append(single_mat) 
            print(f'all possible data for product number {count} was obtainded and appended')
        except Exception as e:
                    print('meassage',e)
                    continue
    end_time = time()
    elapsed_time = end_time - start_time
    print(f"Elapsed run time: {elapsed_time} seconds")
    print (all_mats)

    # # finding directory to save files csv and json

    # BASE_DIR = Path(__file__).resolve(strict=True).parent
    # output_timestamp = datetime.now().strftime("%Y%m%d%H")

    # #To csv
    # df = pd.DataFrame(links)
    # df.to_csv(f'{BASE_DIR}/data_lululemon/all_urls_lululemon{output_timestamp}.csv')
    # df = pd.DataFrame(all_mats)
    # df.to_csv(f'{BASE_DIR}/data_lululemon/mats_lululemon{output_timestamp}.csv')

    # #To json
    # output_timestamp = 'test'
    # import json
    # json_file= []
    # for i in all_mats:
    #     a = {
    #     'id_mat' : i.id_mat,
    #     'provider' : i.provider,
    #     'name' : i.name,
    #     'price' : i.price,
    #     'material' : i.material,
    #     'rating' : i.rating,
    #     'number_of_reviews' : i.number_of_reviews,
    #     'colours' : i.colours,
    #     'image_url' : i.image_url,
    #     'image_uri' : i.image_uri,
    #     'product_url' : i.product_url
    #     }
    #     json_file.append(a)

    # with open(f'{BASE_DIR}/data_lululemon/mats_lululemon{output_timestamp}.json', 'w') as f:
    #     json.dump(json_file,f, indent=4)

    # #connect to aws database and and visualize data through pgadmin
 
    # host = 'webscrape.ccdpsgqkc9sb.us-east-2.rds.amazonaws.com' # database is in aws
    # port = '5432'
    # dbname ='aicore'
    # user ='postgres'
    # password = 'postgres'

    # #cursor = conn.cursor()
    # db_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}" 
    # db = create_engine(db_string) 

    # # open json file
    # with open(f'{BASE_DIR}/data_lululemon/mats_lululemon{output_timestamp}.json') as f:
    #     df = pd.read_json(f, orient='records')

    # # insert data to db
    # df.to_sql(f'mats_lululemon{output_timestamp}', db)





# %%
