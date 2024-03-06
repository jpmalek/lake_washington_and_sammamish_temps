# FILEPATH: /Users/jeffmalek/Documents/git/lake-washington-and-sammamish/Lake Washington Temps.ipynb
from collections import defaultdict
import csv
import json
import logging
import os
import re
import requests
import time
from datetime import datetime

import boto3
import pandas as pd
from botocore.exceptions import ClientError
from chromedriver_py import binary_path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
"""
    TODO: lock security
        DONE: create a new admin user
        Create a new user with only the necessary permissions
        test their credentials work with the script
        DONE: delete the root keys
        put their credentials in secrets manager
        update ecs policy to grant access to secrets manager
        test script in ecs
        create and test docker file on ec2 instance
        create repository : aws ecr create-repository --repository-name lake-washington-and-sammamish-temps --region us-west-2
        auth with default registry: aws ecr get-login-password --region us-west-2 | sudo docker login --username AWS --password-stdin 139626508613.dkr.ecr.us-west-2.amazonaws.com
        tag image: sudo docker tag lake-washington-and-sammamish-temps:latest 139626508613.dkr.ecr.us-west-2.amazonaws.com/lake-washington-and-sammamish-temps:latest
        push image to default registry: sudo docker push 139626508613.dkr.ecr.us-west-2.amazonaws.com/lake-washington-and-sammamish-temps:latest
        ~1.5G 
        https://docs.aws.amazon.com/AmazonECS/latest/developerguide/getting-started-fargate.html
        note: create all_cloudwatch_policy and attach to role https://us-east-1.console.aws.amazon.com/iam/home#/policies/details/arn%3Aaws%3Aiam%3A%3A139626508613%3Apolicy%2Fall_cloud_watch?section=entities_attached
    TODO: readme
    TODO: monitoring and alerting
    TODO: tests
    TODO: failover to backup files on error
    TODO: https://green2.kingcounty.gov/lake-buoy/GenerateMapData.aspx called from https://green2.kingcounty.gov/lake-buoy/default.aspx
    NOTE: python 3.11.5
    NOTE: https://d3bwuucxp9c0h3.cloudfront.net/WA/lake_wa_highs_and_lows.json
    NOTE: https://swimming.withelvis.com/WA/lake_wa_highs_and_lows.json
    NOTE : real-time data is updated by King County at approx 12AM, 8AM and 4PM
    NOTE: setup steps:
        pip install pipreqs; run pipreqs . in project directory to generate a requirements.txt file. pip freeze > requirements.txt outputs all installed packages.
        docker: 
            run source ./export_aws_credentials_to_env.sh to export AWS credentials to environment variables locally.
            docker init (creates .dockerignore,compose.yaml,Dockerfile,README.Docker.md)
            update compose.yaml with environment variables
            docker compose up --build
            TODO: install chromedriver in docker
"""         
class FileManager:
    """
    A class for managing file operations on either a local file system or AWS S3, including
    backing up, moving files, and ensuring an S3 bucket exists.
    """
    def __init__(self, use_s3=False, s3_bucket='lake-water-data', aws_region='us-west-2'):
        """
        Initializes the FileManager with optional S3 support. If S3 is used, checks for the
        existence of the specified S3 bucket and creates it if it doesn't exist.
        """
        self.logger = logging.getLogger()
        self.download_file_extension = '.csv'
        self.backup_file_extension = 'backup'
        self.downloads_folder = 'downloads'
        self.min_file_size = 5000

        self.header_written = False

        self.download_directory = os.path.join(os.getcwd(), self.downloads_folder)
        self.logger.info(f'Download directory: {self.download_directory}')
        self.clean_download_directory(self.download_directory)   

        self.use_s3 = use_s3
        self.s3_bucket = s3_bucket
        self.aws_region = aws_region
        self.s3_client = boto3.client('s3', region_name=self.aws_region) if use_s3 else ""

        self.new_file_base = self.download_directory if not self.use_s3 else "" 
        self.logger.info(f'New file base: {self.new_file_base }')
        # Check and create the S3 bucket if necessary
        if self.use_s3:
            self.ensure_bucket_exists()

    def backup_file(self, old_file, new_file):
            """
            Backs up a file either locally or on AWS S3.

            Args:
                old_file (str): The path to the file to back up.
                new_file (str): The path or key to the backup file.

            Raises:
                FileNotFoundError: If the old file does not exist.
                Exception: For errors encountered when using AWS S3.
            """
            if self.use_s3:
                try:
                    self.logger.info(f'Backing up file to S3: {old_file} -> {new_file}')
                    self.s3_client.copy_object(Bucket=self.s3_bucket, CopySource={'Bucket': self.s3_bucket, 'Key': old_file}, Key=new_file)
                    # Delete the original file
                    self.logger.info(f'Deleting old file in S3: {old_file}')
                    self.s3_client.delete_object(Bucket=self.s3_bucket, Key=old_file)
                    
                except FileNotFoundError:
                    self.logger.info(f"The file {old_file} does not exist.")
                except ClientError as e:
                    self.logger.info(f'Failed to back up file to S3: {e}')
            else:
                if os.path.isfile(old_file):
                    self.logger.info(f'Backing up old file locally: {old_file} -> {new_file}')
                    os.rename(old_file, new_file)

    def move_file(self, source, destination,remove_source=True):
        """
        Moves a file either locally or on AWS S3.

        Args:
            source (str): The path or key of the source file.
            destination (str): The path or key of the destination file.

        Raises:
            FileNotFoundError: If the source file does not exist (for local moves).
            Exception: For errors encountered when using AWS S3.
        """
        if self.use_s3:
            try:
                self.logger.info(f'Moving file from local to S3: {source} -> {destination}')
                # Upload the file to the new location on S3
                content_type = 'application/json' if source.endswith('.json') else 'text/csv'
                self.s3_client.upload_file(source, self.s3_bucket, destination, ExtraArgs={'ContentType': content_type})
                # If upload was successful, delete the local file
                if remove_source == True:
                    os.remove(source)
                self.logger.info(f'Successfully moved {source} to {destination} on S3.')
            except ClientError as e:
                self.logger.error(f'Failed to move file to S3: {e}')
            except FileNotFoundError:
                self.logger.error(f'Local file not found: {source}')
        else:
            if os.path.isfile(source):
                self.logger.info(f'Moving file locally: {source} -> {destination}')
                os.rename(source, destination)
            else:
                self.logger.error(f'File not found: {source}')
                raise FileNotFoundError(f'File not found: {source}')

    def ensure_bucket_exists(self):
        """
        Checks for the existence of the S3 bucket by name and creates it if it doesn't exist.
        """
        if not self.s3_bucket:
            self.logger.error("No S3 bucket name provided.")
            return

        try:
            # Check if the bucket exists and create it if not
            existing_buckets = self.s3_client.list_buckets().get('Buckets', [])
            bucket_names = [bucket['Name'] for bucket in existing_buckets]
            if self.s3_bucket in bucket_names:
                self.logger.info(f"S3 bucket '{self.s3_bucket}' already exists.")
            else:
                # Create the bucket
                self.s3_client.create_bucket(Bucket=self.s3_bucket,CreateBucketConfiguration={'LocationConstraint': self.aws_region})
                self.logger.info(f"S3 bucket '{self.s3_bucket}' created successfully.")
        except Exception as e:
            self.logger.error(f"Failed to check or create S3 bucket: {e}")
            raise
    
    def clean_download_directory(self,download_directory):
        if os.path.isdir(download_directory):
            for f in os.listdir(download_directory):
                if f.endswith('.crdownload') or f.endswith('.csv') or f.endswith('.txt'):
                    path = os.path.join(download_directory, f)
                    self.logger.info(f'Removing file for cleanup:{path}')
                    os.remove(path)
    
    def wait_for_download_to_complete(self,timeout=300):
        end_time = time.time() + timeout
        while True:
            # Check for any files not ending in '.crdownload'
            if not any(f.endswith('.crdownload') for f in os.listdir(self.download_directory)):
                # Assuming there's only one file being downloaded or you know the filename
                files = [f for f in os.listdir(self.download_directory) if (f.endswith(self.download_file_extension) or f.endswith('.txt'))]
                if files:
                    # Check if file size has stabilized indicating download completion
                    filepath = os.path.join(self.download_directory, files[0])
                    size = os.path.getsize(filepath)
                    self.logger.info(f'Size of {filepath} : {size}')
                    time.sleep(2)  # Wait for 2 seconds to see if the file size changes
                    if size == os.path.getsize(filepath) and size > self.min_file_size:
                        self.logger.info(f'Size of {filepath} : {size}')
                        self.logger.info(f'Download completed: {filepath}')
                        return filepath
            if time.time() > end_time:
                raise Exception("Timeout: File download did not complete in the allotted time.")
            time.sleep(1)  # Polling interval

    def mkdirs(self, path):
        """
        Creates a folder structure either in S3 or locally, based on the use_s3 flag.
        
        Parameters:
            path (str): The path or key to create. For S3, it should be the key structure.
                        For local, it's the directory path.
        """
        if self.use_s3:
            self._create_s3_directory_structure(path)
        else:
            self._create_local_directory_structure(path)
    
    def delete_first_n_lines(self,file_path, lines_to_delete=12, output_file_path=None):
        """Delete the first n lines from a file.

        Args:
        - file_path: Path to the input file.
        - n: Number of lines to delete from the beginning of the file.
        - output_file_path: Path to the output file. If None, the input file is overwritten.

        This function reads the input file, skips the first n lines, and writes the rest
        to the output file. If an output file is not specified, it overwrites the input file.
        """
        self.logger.info(f'Deleting first {lines_to_delete} lines from {file_path}')    
        if lines_to_delete < 2:
            return
        
        # If no output file path is provided, overwrite the input file
        if output_file_path is None:
            output_file_path = file_path
        
        with open(file_path, 'r', encoding='ISO-8859-1') as file:
            lines = file.readlines()

        with open(output_file_path, 'w', encoding='ISO-8859-1') as file:
            file.writelines(lines[lines_to_delete:])

    def _create_s3_directory_structure(self, path):
        """
        Simulates creating a directory structure in S3 by creating an empty object with a key
        that ends in a slash (/).
        
        Parameters:
            path (str): The S3 key structure to create.
        """
        # Ensure the path ends with a slash
        if not path.endswith('/'):
            path += '/'
        try:
            self.s3_client.put_object(Bucket=self.s3_bucket, Key=path)
            self.logger.info(f"Created S3 directory structure: {path} in bucket: {self.s3_bucket}")
        except Exception as e:
            self.logger.error(f"Error creating S3 directory structure: {e}")
            raise

    def _create_local_directory_structure(self, path):
        """
        Creates a directory structure locally using os.makedirs.
        
        Parameters:
            path (str): The local directory path to create.
        """
        try:
            os.makedirs(path, exist_ok=True)
            self.logger.info(f"Created local directory structure: {path}")
        except Exception as e:
            self.logger.error(f"Error creating local directory structure: {e}")
            raise
    
    def combine_csv(self, input_file,output_file):
        """
        Processes an input CSV file, discarding the first 12 lines of non-CSV data, and appends
        the remaining data to the output file. Prepends lake name and monitoring site name to each row.

        Parameters:
        - input_file (str): The path to the input CSV file.
        - output_file (str): The path to the output CSV file.
        """
        try:
            # Extract lake name and monitoring site name from the file name
            lake_name, monitoring_site = os.path.basename(input_file).split('.')[0].split('-')
            self.logger.info(f"Processing {input_file} for lake {lake_name} and monitoring site {monitoring_site} to output file {output_file}")
            with open(input_file, 'r', encoding='ISO-8859-1') as infile:
                # Skip the first 12 lines of non-CSV data
                for _ in range(12):
                    next(infile)
                csv_reader = csv.reader(infile)
                header = next(csv_reader)  # Read the header

                with open(output_file, 'a', newline='', encoding='ISO-8859-1') as outfile:
                    csv_writer = csv.writer(outfile)
                    
                    # Write the header if it hasn't been written yet
                    if not self.header_written:
                        csv_writer.writerow(['LakeName', 'MonitoringSite'] + header)
                        self.header_written = True
                    
                    # Write each row of data, prepending lake name and monitoring site
                    for row in csv_reader:
                        csv_writer.writerow([lake_name, monitoring_site] + row)
                        
            self.logger.info(f"Processed and combined CSV file: {input_file} > {output_file}")
        
        except Exception as e:
            self.logger.error(f"Error processing file {input_file}: {e}")
    
class ChromeUtility:
    """
    A class for managing Chrome WebDriver operations, including setting up the WebDriver.
    """
    def __init__(self,headless=True,download_directory='downloads'):
        self.logger = logging.getLogger()
        self.binary_path = binary_path
        self.pacific_tz = pytz.timezone('America/Los_Angeles')
        self.historical_locations = '' 

        self.options = Options()
        self.options.add_argument("--headless") if headless else self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-gpu")  # Disables GPU hardware acceleration. If software renderer is not in place, then the GPU process won't launch.
        self.options.add_argument("--no-sandbox")  # Bypasses OS security model; recommended for running in Docker or CI/CD environments.
        self.options.add_argument("--disable-dev-shm-usage")  # Overcomes limited resource problems.
        self.options.add_experimental_option("prefs", {
            "download.default_directory": download_directory,
            "download.prompt_for_download": False,  # Disables prompt
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True  # Disables safebrowsing to allow automatic file downloads
            })
        self.service = Service(executable_path=binary_path)
        # Setup WebDriver
        self.driver = webdriver.Chrome(service=self.service,options=self.options)
    
    def get_historical_wa_lake_data_locations(self):
        """
        Get historical lake temperature locations from the Washington State Department of Ecology.
        """
        self.driver.get('https://green2.kingcounty.gov/lakes/Query.aspx')
        self.logger.info(f'Navigated to {self.driver.title}')
        # Find the dropdown element by its ID
        dropdown = Select(self.driver.find_element(By.ID, "ctl00_kcMasterPagePlaceHolder_LocatorDropDownList"))
        # List comprehension to get the text of each option
        locations = [option.text for option in dropdown.options[1:]]
        #json_config = json.dumps(locations,indent=4)
        self.historical_locations = locations
        return locations
    
    def get_historical_wa_lake_data(self,start_date='01/01/1983',end_date= datetime.now().strftime('%m/%d/%Y'),just_get_temps=True,location=None):
        """
        Get historical lake temperature data from the Washington State Department of Ecology.
        """
        end_date = datetime.now(self.pacific_tz).strftime('%m/%d/%Y')

        # Page reloads upon select. Re-locate the dropdown before interacting with it to avoid StaleElementReferenceException
        dropdown_element = self.driver.find_element(By.ID, "ctl00_kcMasterPagePlaceHolder_LocatorDropDownList")
        dropdown = Select(dropdown_element)
        # Now, select the next option
        dropdown.select_by_visible_text(location)
        self.logger.info(f'Option text: {location}')
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_kcMasterPagePlaceHolder_StartDateTextBox"))
        )
        # Fill out the form (update these selectors based on actual form structure)
        self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_StartDateTextBox').clear()
        self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_StartDateTextBox').send_keys(start_date)
        self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_EndDateTextBox').clear()
        self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_EndDateTextBox').send_keys(end_date)
        if just_get_temps:
            if not self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_TEMP').is_selected():
                self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_TEMP').click()
        else:
            self.driver.find_element(By.ID, 'Checkboxes').click()
        # Submit the form
        self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_DownLoadButton').click()
    
    def get_cached_realtime_wa_lake_data_locations(self):
        """
        Get realtime lake temperature locations from the Washington State Department of Ecology.
        """
        self.driver.get('https://green2.kingcounty.gov/lake-buoy/Data.aspx')
        self.logger.info(f'Navigated to {self.driver.title}')
        # Find the dropdown element by its ID
        data_type_dropdown = Select(self.driver.find_element(By.ID, "ctl00_kcMasterPagePlaceHolder_c_TypeDropDownList"))
        # List comprehension to get the text of each option
        data_types = [option.text for option in data_type_dropdown.options[1:]]
        data_type_dropdown.select_by_visible_text(data_types[0])
        current_year = datetime.now(self.pacific_tz).year.__str__()
        # Wait for the specific value to be available in the drop-down list
        WebDriverWait(self.driver, 10).until(
            EC.text_to_be_present_in_element_value((By.ID, 'ctl00_kcMasterPagePlaceHolder_c_YearDropDownList'), current_year)
        )
        # Find the dropdown element by its ID
        location_dropdown = Select(self.driver.find_element(By.ID, "ctl00_kcMasterPagePlaceHolder_c_BuoyDropDownList"))
        # List comprehension to get the text of each option
        locations = [option.text for option in location_dropdown.options if 'inactive' not in option.text.lower()]
        return locations

        
    
    def get_realtime_wa_lake_data(self,location=None):
        """
        Get historical lake temperature data from the Washington State Department of Ecology.
        """
        # Page reloads upon select. Re-locate the dropdown before interacting with it to avoid StaleElementReferenceException
        dropdown_element = self.driver.find_element(By.ID, "ctl00_kcMasterPagePlaceHolder_c_BuoyDropDownList")
        dropdown = Select(dropdown_element)
        # Now, select the next option
        dropdown.select_by_visible_text(location)
        self.logger.info(f'Option text: {location}')
        current_year = datetime.now(self.pacific_tz).year.__str__()
        current_month = datetime.now(self.pacific_tz).month.__str__()
        
        # Wait for the specific value to be available in the drop-down list
        WebDriverWait(self.driver, 10).until(
            EC.text_to_be_present_in_element_value((By.ID, 'ctl00_kcMasterPagePlaceHolder_c_YearDropDownList'), current_year)
        )
        
        # Fill out the form (update these selectors based on actual form structure)
        self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_c_YearDropDownList').send_keys(current_year)
        self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_c_MonthStartDropDownList').send_keys(current_month)
        self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_c_EndMonthDropDownList').send_keys(current_month)
        # Submit the form
        self.driver.find_element(By.ID, 'ctl00_kcMasterPagePlaceHolder_c_DownloadButton').click()
    
    def cleanup(self):
        self.driver.quit()
        self.logger.info('Chrome WebDriver quit successfully.')

class ProcessData:
    """
    Processes temperature data from CSV files, maintaining all-time high and low temperatures,
    as well as high and low temperatures for each year and for each month, collected by lake name.
    """

    def __init__(self):
        """
        Initializes the ProcessData instance with empty structures for temperature tracking by lake name.
        """
        self.pacific_tz = pytz.timezone('America/Los_Angeles')

        self.highs_and_lows = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'high': None, 'low': None, 'high_meta': {}, 'low_meta': {}})))
        self.monthly_highs_and_lows = defaultdict(lambda: defaultdict(lambda: {'high': None, 'low': None, 'high_meta': {}, 'low_meta': {}}))
        self.all_time_high_low = defaultdict(lambda: {'high': None, 'low': None, 'high_meta': {}, 'low_meta': {}})
        self.logger = logging.getLogger(__name__)

    def high_and_low_temps(self, csv_file):
        """
        Processes a CSV file to update the temperature records for each year, each month, and all-time, by lake name.
        """
        try:
            with open(csv_file, mode='r', encoding='ISO-8859-1') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    #self.logger.info(f'Row: {row}')
                    if row['Depth (m)'] and row['Temperature (°C)'] and row['CollectDate']:
                        if row['Depth (m)'] != 'Composite' and float(row['Depth (m)']) == 1.0:
                            temp = float(row['Temperature (°C)'])
                            collect_date = row['CollectDate']
                            date_obj = datetime.strptime(collect_date, '%m/%d/%Y')
                            year = str(date_obj.year)
                            month = str(date_obj.month).zfill(2)  # Ensure month is two digits
                            lake_name = row['LakeName']
                            monitoring_site = row['MonitoringSite']
                            # Update records by lake
                            self._update_records(year, month, temp, monitoring_site, collect_date, lake_name)
        except FileNotFoundError:
            self.logger.error(f"CSV file {csv_file} not found.")
            raise
        except Exception as e:
            self.logger.error(f"Error processing CSV file {csv_file}: {e}")
            self.logger.error(f"Ros: {row}")
            raise

    def _update_records(self, year, month, temp, location_name, collect_date, lake_name):
        """
        Updates the temperature records for a specific year, month, and checks for all-time highs and lows, by lake name.
        """
        meta = {'location': location_name, 'lake': lake_name, 'CollectDate': collect_date, 'Year': year}
        # Update annual and monthly records by lake
        self._update_highs_and_lows(month, temp, meta, self.highs_and_lows[lake_name][year])
        # Update monthly records across all years by lake
        self._update_highs_and_lows(month, temp, meta, self.monthly_highs_and_lows[lake_name])
        # Update all-time high and low by lake
        self._update_all_time_high_low(temp, meta, lake_name)
    def _update_highs_and_lows(self, month, temp, meta, record):
        """
        Updates high and low temperature records for a specific month within a given record structure, by lake name.
        """
        if record[month]['high'] is None or temp > record[month]['high']:
            record[month]['high'] = temp
            record[month]['high_meta'] = meta
        if record[month]['low'] is None or temp < record[month]['low']:
            record[month]['low'] = temp
            record[month]['low_meta'] = meta

    def _update_all_time_high_low(self, temp, meta, lake_name):
        """
        Updates the all-time high and low temperature records by lake name.
        """
        record = self.all_time_high_low[lake_name]
        if record['high'] is None or temp > record['high']:
            record['high'] = temp
            record['high_meta'] = meta
        if record['low'] is None or temp < record['low']:
            record['low'] = temp
            record['low_meta'] = meta

    def print_records(self):
        """
        Prints the temperature records for each year, each month, and all-time, by lake name.
        """
        for lake, records in self.highs_and_lows.items():
            self.logger.info(f"Lake: {lake}")
            self.logger.info(f"All-time High: {self.all_time_high_low[lake]['high']} Location: {self.all_time_high_low[lake]['high_meta']['location']} Collect Date: {self.all_time_high_low[lake]['high_meta']['CollectDate']}")
            self.logger.info(f"All-time Low: {self.all_time_high_low[lake]['low']} Location: {self.all_time_high_low[lake]['low_meta']['location']} Collect Date: {self.all_time_high_low[lake]['low_meta']['CollectDate']}")
            self.logger.info(f"Monthly Highs and Lows:")
            for month, temps in self.monthly_highs_and_lows[lake].items():
                self.logger.info(f"Month: {month} - High: {temps['high']} - Low: {temps['low']} Location: {temps['high_meta']['location']} Collect Date: {temps['high_meta']['CollectDate']}")

    def celsius_to_fahrenheit(self, celsius):
        """
        Converts a temperature from Celsius to Fahrenheit.
        
        Parameters:
        - celsius (float): Temperature in Celsius.
        
        Returns:
        - float: Temperature in Fahrenheit.
        """
        return (celsius * 9/5) + 32

    def get_highs_and_lows_json(self):
        """
        Returns the temperature records in JSON format, including temperatures in Fahrenheit.
        
        Returns:
        - str: JSON string containing the high and low temperature records.
        """
        data = {}
        data['last_updated'] = datetime.now(self.pacific_tz).strftime('%Y-%m-%d %H:%M:%S')
        for lake, records in self.highs_and_lows.items():
            lake_data = {
                'all_time_high': self.all_time_high_low[lake]['high'],
                'all_time_low': self.all_time_high_low[lake]['low'],
                'all_time_high_fahrenheit': self.celsius_to_fahrenheit(self.all_time_high_low[lake]['high']) if self.all_time_high_low[lake]['high'] is not None else None,
                'all_time_low_fahrenheit': self.celsius_to_fahrenheit(self.all_time_high_low[lake]['low']) if self.all_time_high_low[lake]['low'] is not None else None,
                'all_time_high_meta': self.all_time_high_low[lake]['high_meta'],
                'all_time_low_meta': self.all_time_high_low[lake]['low_meta'],
                'monthly_highs_and_lows': {}
            }
            for month, temps in self.monthly_highs_and_lows[lake].items():
                lake_data['monthly_highs_and_lows'][month] = {
                    'high': temps['high'],
                    'low': temps['low'],
                    'high_fahrenheit': self.celsius_to_fahrenheit(temps['high']) if temps['high'] is not None else None,
                    'low_fahrenheit': self.celsius_to_fahrenheit(temps['low']) if temps['low'] is not None else None,
                    'high_meta': temps['high_meta'],
                    'low_meta': temps['low_meta']
                }
            data[lake] = lake_data
        
        # Convert the data dictionary to a JSON string
        return json.dumps(data, sort_keys=True,indent=4)

class KingCountyLakes():
    def __init__(self):
        self.pacific_tz = pytz.timezone('America/Los_Angeles')
        self.file_manager = FileManager(use_s3=False)
        self.s3_file_manager = FileManager(use_s3=True)
        self.chrome_helper = ChromeUtility(headless=True,download_directory=self.file_manager.download_directory)
        self.data_processor = ProcessData()
        self.lake_temps_json_file = f'lake_temps.json'
        self.highs_and_lows_json_file = f'lake_wa_highs_and_lows.json'
        self.king_county_real_time_url = 'https://green2.kingcounty.gov/lake-buoy/GenerateMapData.aspx'
        self.highs_and_lows_prod_url = 'https://swimming.withelvis.com/WA/lake_wa_highs_and_lows.json'
        self.lake_temps_prod_url = 'https://swimming.withelvis.com/WA/lake_temps.json'
        self.prod_url_dict = {
            'highs and lows': { 
                'url': self.highs_and_lows_prod_url,
                'hours_to_cache': 0, # 60 days = 1440
                'update': False
            },
            'lake temps': { 
                'url': self.lake_temps_prod_url,
                'hours_to_cache': 0,
                'update': False
            },
        }

    def get_all_historical_wa_lake_data(self):
        locations = self.chrome_helper.get_historical_wa_lake_data_locations()

        for location in locations:
            self.file_manager.logger.info(f'Location: {location}')
            new_file_directory = f'{location}' if self.file_manager.use_s3 else f'{self.file_manager.new_file_base}/{location}'
            self.file_manager.logger.info(f'New file directory: {new_file_directory}')
            self.file_manager.mkdirs(new_file_directory)
            new_file_path = f'{new_file_directory}/{location}.csv'
            backup_file_path = f'{new_file_path}.{self.file_manager.backup_file_extension}'
            self.file_manager.logger.info(f'new file path: {new_file_path}')
            self.file_manager.logger.info(f'backup_file_path: {backup_file_path}')
            self.chrome_helper.get_historical_wa_lake_data(location=location)
            file_path = self.file_manager.wait_for_download_to_complete(timeout=30)
            self.file_manager.logger.info(f'File path: {file_path}')
            self.file_manager.backup_file(new_file_path,backup_file_path)
            self.file_manager.move_file(file_path,new_file_path)

    def get_combined_csv_file_path(self):
        combined_csv_directory = f'{self.file_manager.new_file_base}/WA'
        self.file_manager.mkdirs(combined_csv_directory)
        new_combined_csv_file_path = f'{combined_csv_directory}/all_historical_wa_lake_data.csv'
        return new_combined_csv_file_path

    def combine_historical_csv(self):
        if self.chrome_helper.historical_locations == '':
            self.file_manager.logger.info('No historical locations found. Getting historical locations.')
            self.chrome_helper.get_historical_wa_lake_data_locations()
        new_combined_csv_file_path = self.get_combined_csv_file_path()
        backup_combined_csv_file_path = f'{new_combined_csv_file_path}.{self.file_manager.backup_file_extension}'
        self.file_manager.backup_file(new_combined_csv_file_path,backup_combined_csv_file_path)
        for location in self.chrome_helper.historical_locations:
            file_to_append = f'{self.file_manager.download_directory}/{location}/{location}.csv'
            self.file_manager.logger.info(f'Calling file_manager.combine_csv for {location} for file {file_to_append}' )
            self.file_manager.combine_csv(file_to_append,new_combined_csv_file_path)
        return new_combined_csv_file_path

    def get_highs_and_lows(self,combined_csv_file):
        self.data_processor.high_and_low_temps(combined_csv_file)
        return self.data_processor.get_highs_and_lows_json()

    def write_highs_and_lows_to_json_file(self):
        new_combined_csv_file_path = self.get_combined_csv_file_path()
        if not os.path.isfile(new_combined_csv_file_path):
            new_combined_csv_file_path = self.combine_historical_csv()    
        highs_and_lows_json_file_path = f'{self.file_manager.download_directory}/WA/{self.highs_and_lows_json_file}'
        highs_and_lows_backup_file_path = f'{highs_and_lows_json_file_path}.{self.file_manager.backup_file_extension}'
        highs_and_lows_json = self.get_highs_and_lows(new_combined_csv_file_path)
        # create a backup of the file if it already exists
        self.file_manager.backup_file(highs_and_lows_json_file_path,highs_and_lows_backup_file_path)
        # write the json object to the file
        with open(highs_and_lows_json_file_path, 'w') as file:
            file.write(highs_and_lows_json)
        return highs_and_lows_json_file_path

    def upload_highs_and_lows_to_s3(self,highs_and_lows_json_file_path):
        self.s3_file_manager.mkdirs('WA')
        s3_json_file_path = f'WA/{self.highs_and_lows_json_file}'
        s3_backup_json_file_path = f'{s3_json_file_path}.{self.file_manager.backup_file_extension}'
        self.s3_file_manager.backup_file(s3_json_file_path,s3_backup_json_file_path)
        self.s3_file_manager.move_file(highs_and_lows_json_file_path,f'WA/{self.highs_and_lows_json_file}',remove_source=False)

    def process_all_historical(self):
        self.get_all_historical_wa_lake_data()
        self.combine_historical_csv()
        highs_and_lows_json_file_path = self.write_highs_and_lows_to_json_file()
        self.upload_highs_and_lows_to_s3(highs_and_lows_json_file_path)

    def invalidate_cloudfront_cache(self):
        self.file_manager.logger.info('Invalidating CloudFront cache')
        client = boto3.client('cloudfront')
        response = client.create_invalidation(
        DistributionId='ESWMI6WOZH1YK',  # replace with your distribution ID
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': [
                    '/*',  # this will invalidate all objects
                ]
            },
            'CallerReference': str(time.time())  # unique identifier for this invalidation request
        }
        )
    
    def get_cached_realtime_lake_data(self):
        locations = self.chrome_helper.get_cached_realtime_wa_lake_data_locations()
        new_files = []
        for location in locations:
            lake_name = f"lake_{location.split(' ')[0].lower()}"
            self.file_manager.logger.info(f'Location: {lake_name}')
            new_file_directory = f'{lake_name}' if self.file_manager.use_s3 else f'{self.file_manager.new_file_base}/{lake_name}'
            self.file_manager.logger.info(f'New file directory: {new_file_directory}')
            self.file_manager.mkdirs(new_file_directory)
            new_file_path = f'{new_file_directory}/{lake_name}.txt'
            backup_file_path = f'{new_file_path}.{self.file_manager.backup_file_extension}'
            self.file_manager.logger.info(f'new file path: {new_file_path}')
            self.file_manager.logger.info(f'backup_file_path: {backup_file_path}')
            self.chrome_helper.get_realtime_wa_lake_data(location=location)
            file_path = self.file_manager.wait_for_download_to_complete(timeout=30)
            self.file_manager.logger.info(f'File path: {file_path}')
            self.file_manager.backup_file(new_file_path,backup_file_path)
            self.file_manager.move_file(file_path,new_file_path)
            new_files.append(new_file_path)
        return new_files
        
    def process_cached_realtime_lake_data(self,file):
        self.file_manager.logger.info(f'Processing file {file}')
        # Load the data
        df = pd.read_csv(file,delimiter='\t',)
        # Make sure column names are correctly identified
        df.columns = [col.strip() for col in df.columns]
        
        # Round the "Depth (m)" to the closest integer
        df['Depth (m)'] = df['Depth (m)'].round().astype(int)
        
        # Filter for depth of 1 and provisional column value is "no"
        filtered_df = df[(df['Depth (m)'] == 1)]
        
        # Find the most recent temperature
        df.loc[filtered_df.index, 'Date'] = pd.to_datetime(filtered_df['Date'],format='%m/%d/%Y %I:%M:%S %p')
        
        most_recent_row = filtered_df.sort_values('Date', ascending=False).iloc[0]
        
        # Convert temperature to Fahrenheit
        temp_celsius = most_recent_row['Temperature (°C)']
        temp_fahrenheit = self.data_processor.celsius_to_fahrenheit(celsius=temp_celsius)

        # Construct the JSON object
        
        json_object = {
            'most_recent_temperature_celsius': temp_celsius,
            'most_recent_temperature_fahrenheit': temp_fahrenheit,
            'date_of_collection': most_recent_row['Date'] #.strftime('%Y-%m-%d')  # Format the date
        }
        return json_object

    def save_cached_realtime_lake_data(self,files):
        data = {}
        data['last_updated'] = datetime.now(self.pacific_tz).strftime('%Y-%m-%d %H:%M:%S')
        lake_name = ''
        for f in files:
            lake_name = f.split('/')[-1].split('.')[0]  # Extract file prefix
            lake_data = self.process_cached_realtime_lake_data(f)
            data[lake_name] = lake_data
        self.write_realtime_lake_data(data)

    def write_realtime_lake_data(self,json_object):
        self.file_manager.logger.info(f'Real-time json temps object: {json.dumps(json_object,indent=4)}')
        file_name = self.lake_temps_json_file
        new_file_directory = f'{self.file_manager.new_file_base}/WA/'
        new_s3_file_directory = f'WA'
        self.file_manager.logger.info(f'New local file directory: {new_file_directory}')
        self.file_manager.mkdirs(new_file_directory)
        self.s3_file_manager.mkdirs(new_file_directory)
        new_file_path = f'{new_file_directory}/{file_name}'
        backup_file_path = f'{new_file_path}.{self.file_manager.backup_file_extension}'
        self.file_manager.logger.info(f'New file path: {new_file_path}')
        self.file_manager.logger.info(f'Backup file path: {backup_file_path}')
        self.file_manager.backup_file(new_file_path,backup_file_path)
        new_s3_file_path = f'{new_s3_file_directory}/{file_name}'
        backup_s3_file_path = f'{new_s3_file_path}.{self.file_manager.backup_file_extension}'
        self.file_manager.logger.info(f'New s3 file path: {new_s3_file_path}')
        self.file_manager.logger.info(f'Backup s3 file path: {backup_s3_file_path}')
        self.s3_file_manager.backup_file(new_s3_file_path,backup_s3_file_path)
        # write the json object to the file
        with open(new_file_path, 'w') as file:
            file.write(json.dumps(json_object,indent=4))
        self.file_manager.logger.info(f'wrote file: {new_file_path}')
        self.s3_file_manager.move_file(new_file_path,new_s3_file_path,remove_source=False)

    def get_realtime_lake_data(self):
        url = self.king_county_real_time_url 
        self.file_manager.logger.info(f'Getting realtime lake data from {url}')
        get_cached = False
        response = None
        try:
            response = requests.get(url)
        except Exception as e:
            self.file_manager.logger.info(f'Exception thrown accessing {url}.')
            get_cached = True
        # check if the response contains the expected keys
        if get_cached == False and response.text.find('|Washington|') == -1 and response.text.find('|Sammamish|') == -1:
            self.file_manager.logger.error(f'Failed to get data from {url} - keys not found.')
            get_cached = True
        if get_cached:
            self. file_manager.logger.error(f'Failed to get data from {url}. Retrieving cached data...')
            files = self.get_cached_realtime_lake_data()
            #files = ['/Users/jeffmalek/Documents/git/lake-washington-and-sammamish/downloads/lake_sammamish/lake_sammamish.txt','/Users/jeffmalek/Documents/git/lake-washington-and-sammamish/downloads/lake_washington/lake_washington.txt']
            self.save_cached_realtime_lake_data(files)  
            return
        self.file_manager.logger.info(f'Got realtime lake data from {url}')
        # Split the response into segments
        segments = re.split('N\^|Y\^', response.text)
        lake_segments = [next((segment for segment in segments if lake_name in segment), None) for lake_name in ['Washington', 'Sammamish']]
        data = {}
        data['last_updated'] = datetime.now(self.pacific_tz).strftime('%Y-%m-%d %H:%M:%S')
        for segment in lake_segments:
            # Split the segment into fields
            fields = segment.split('|')
            lake_name = f'lake_{fields[1].lower().strip()}'
            temperature_celsius = float(fields[6].strip())
            self.file_manager.logger.info(f'{segment} temp: {temperature_celsius}')
            temperature_fahrenheit = self.data_processor.celsius_to_fahrenheit(float(temperature_celsius))
            date_of_collection = fields[2].strip()
            # Create a JSON object with the required fields
            lake_data = {
                'most_recent_temperature_celsius': temperature_celsius,
                'most_recent_temperature_fahrenheit': temperature_fahrenheit,
                'date_of_collection': date_of_collection   
            }
            data[lake_name] = lake_data   
        self.write_realtime_lake_data(data)  

    def get_latest_production_json(self):
        keys = list(self.prod_url_dict.keys())
        for key in keys:
            url = self.prod_url_dict[key]["url"]
            hours_to_cache = self.prod_url_dict[key]["hours_to_cache"]
            self.file_manager.logger.info(f'Getting latest production json for {key} from {url} with {hours_to_cache} days to cache.')
            try:
                response = requests.get(url)
            except Exception as e:
                self.file_manager.logger.error(f'Failed to get latest production json from {url}')
                raise
            json_response = response.json()
            server_time = response.headers.get('Date', None)
            last_modified = response.headers.get('Last-Modified', None)
            age = response.headers.get('Age', None) 
            self.file_manager.logger.info(f'Response server time: {server_time} Last modified: {last_modified} Age in seconds: {age}')
            # calculate whether it's time to request new data
            last_updated = json_response.get('last_updated',None)
            formatted_last_updated = datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S")
            formatted_last_updated = self.pacific_tz.localize(formatted_last_updated)
            time_diff = datetime.now(self.pacific_tz) - formatted_last_updated
            hours_diff = time_diff.total_seconds() / 3600
            if hours_diff > hours_to_cache:
                self.prod_url_dict[key]["update"] = True
            self.file_manager.logger.info(f'Data for {key} Last updated: {last_updated} time diff: {time_diff} hours diff: {hours_diff} hours to cache: {hours_to_cache}')
        
    def go(self):
        self.get_latest_production_json()
        self.file_manager.logger.info(f'prod_url_dict: {json.dumps(self.prod_url_dict,indent=4)}')
        if self.prod_url_dict['highs and lows']["update"]:
            self.file_manager.logger.info(f'+++++++++ Processing all historical data...')
            self.process_all_historical()
            self.invalidate_cloudfront_cache()
        else:
            self.file_manager.logger.info(f'+++++++++ Not time to process all historical data.')

        if self.prod_url_dict['lake temps']["update"]:
            self.file_manager.logger.info(f'+++++++++ Processing real-time lake data...')
            self.get_realtime_lake_data()
            self.invalidate_cloudfront_cache()
        else:
            self.file_manager.logger.info(f'+++++++++ Not time to process real-time lake data.')
        
        
    def __del__(self):
        self.chrome_helper.cleanup()

king_county_lakes = KingCountyLakes()
king_county_lakes.go()
# uncomment the next line to gather Lake WA and Sammamish temps and push to S3.
#king_county_lakes.get_realtime_lake_data()

# uncomment the next line and run to process all lake historical data and upload the high-low temps to S3.
#king_county_lakes.process_all_historical()


    