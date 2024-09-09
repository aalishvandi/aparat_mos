from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time,csv,click
import os,requests,json,re,urllib,subprocess
from datetime import datetime
from browsermobproxy import Server
from itu_p1203 import extractor
from itu_p1203 import p1203_standalone
from webdriver_manager.firefox import GeckoDriverManager
from concurrent.futures import ThreadPoolExecutor

from selenium.webdriver import ActionChains
import statistics
class SeleniumError(Exception):
    pass

class Driver:
    def __init__(self):
        self.file_names = []
        pass
    
    def startDriver(self):
        # firefox_driver = GeckoDriverManager().install()
        firefox_driver = "./driver/geckodriver_amd"
        os.popen("java -jar ./libs/browsermob-proxy-2.1.4/lib/browsermob-dist-2.1.4.jar --port 9090")
        self.server = Server("./libs/browsermob-proxy-2.1.4/bin/browsermob-proxy", options={'port': 9090})
        self.server.start()
        self.proxy = self.server.create_proxy()
        options = webdriver.FirefoxOptions()
        options.proxy = self.proxy.selenium_proxy()
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--proxy-bypass-list=aparat.com')
        options.add_argument('--headless')
        # options.headless = True
        # options.add_argument('--mute-audio')
        options.set_preference("media.volume_scale", "0.0")
        self.driver = webdriver.Firefox(service=Service(firefox_driver), options=options)     
        self.proxy.new_har("aparat.ir/")
    

    def openPage(self,url):
        vast_button=None
        
        # Open a web page
        self.driver.get(url)

        try:
            WebDriverWait(self.driver, timeout=15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "romeo-player-tooltip"))
            )
        except:
            raise SeleniumError("can not find romeo-player-tooltip")

        check_vast_counter=True        
        check_vast_button = True
        try:
            play_button = WebDriverWait(self.driver, timeout=5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'romeo-play-toggle'))
            )
            print("click on play")
            play_button.click()
            time.sleep(3)
        except:
            check_vast_counter=False        
            try:
                self.driver.find_element(By.CLASS_NAME, 'vast-skip-counter')
                print("video is played automatically but vast-skip-counter exists")
            except:
                check_vast_button=False
                try:
                    self.driver.find_element(By.CLASS_NAME, 'vast-skip-button')
                    vast_button = WebDriverWait(self.driver, timeout=15).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'vast-skip-button')))
                    print("video is played automatically but vast-skip-button exists")
                except:
                    # raise SeleniumError("can not find romeo-player-toggle")
                    print("vast is crossed")
                    pass
                
        if check_vast_counter:
            try:
                self.driver.find_element(By.CLASS_NAME, 'vast-skip-counter')
            except:
                print("vast skip counter not found")
                check_vast_button = False

        if check_vast_button:
            try:
                vast_button = WebDriverWait(self.driver, timeout=15).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'vast-skip-button'))
                )
            except:
                vast_button = None
                pass
        if vast_button:
            print("click on vast")
            vast_button.click()
        cur_time=datetime.now()
        self.start_video_time=f"{cur_time.hour:02d}:{cur_time.minute:02d}:{cur_time.second:02d}"
        self.start_video_date=f"{cur_time.year}-{cur_time.month}-{cur_time.day}"
        print("started video")

        headers = {'Accept': 'application/json'}
        video_hash=url.split("/")[-1]
        print(f"get hash of video {video_hash}")
        r = requests.get('https://www.aparat.com/etc/api/video/videohash/'+video_hash, headers=headers).json()
        video_duration=r["video"]["duration"]
        print(f"sleep for {video_duration} video duration")
        time.sleep(video_duration)
        cur_time=datetime.now()
        self.end_video_time=f"{cur_time.hour:02d}:{cur_time.minute:02d}:{cur_time.second:02d}"
        print("end of video")
        # self.driver.close()

    def createlogs(self):
        # with open("./logs/network_log.har", "w", encoding="utf-8") as f:
        #     f.write(json.dumps(self.proxy.har))
        #     print("wrote network logs to logs/network_log.har")
        with open("./logs/network_log.har", "r") as file:
            # Load the JSON data into a Python dictionary
            data = json.load(file)
        # data=json.loads(self.proxy.har)
        self.ts_urls=[]
        for log in data['log']['entries']:
            try:
                # URL is present inside the following keys
                url = log['request']['url']

                is_ts = re.search(r'.*/aparat-video/.*\.ts', url)
                """
                Every .ts file contains 10 seconds of aparat video; 
                we want to pass these files to the ITU-T P1203 Input.
                """

                if is_ts: self.ts_urls.append(url)
            except Exception as error:
                print(error)
                pass
        
    def downloadAndConvertTSFiles(self,url):
        print(url)
        file_name = f"{url.split('.ts')[0].split('/')[-1]}-{datetime.timestamp(datetime.now())}"
        print(f"Download {url}")
        urllib.request.urlretrieve(url, f"./logs/ts_files/{file_name}.ts")
        # convert ts file to mp4
        print(f"Convert {file_name} to mp4...")
        convert_command = ['ffmpeg', '-i', f'./logs/ts_files/{file_name}.ts', '-c', 'copy', '-bsf:a', 'aac_adtstoasc', '-f', 'mp4', f'./logs/mp4_files/{file_name}.mp4']
        subprocess.run(convert_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.file_names.append(file_name)
    
    def calculateVideoMos(self,mp4_files):
        print(f"Calculating mos {mp4_files}...")
        list_file=[]
        list_file.append(mp4_files)
        input_data = extractor.Extractor(list_file, 3)  # input .ts files, mode
        report = input_data.extract()
        # Use p1203_standalone to calculate parameters and send it to output
        output_calculated = p1203_standalone.P1203Standalone(report)
        result = output_calculated.calculate_complete()
        return result['O46']
    
    def removeTSFiles(self):
        os.system("rm -rf logs/mp4_files/* logs/ts_files/*")

    def restartProxy(self):
        self.proxy.new_har("aparat.ir/")
    
    def endOfProcess(self):
        self.server.stop()
        self.driver.quit()
                

@click.command()
@click.option('--file', prompt='Enter file path', type=click.Path(exists=True, dir_okay=False))
def main(file):
    try:
        os.system("pkill -f 'java -jar ./libs/browsermob-proxy-2.1.4/lib/browsermob-dist-2.1.4.jar'")
    except:
        pass
    
    output_file = open("output.csv", 'w')
    writer = csv.writer(output_file)
    writer.writerow(["","url","date","start_time","mos","end_time"])
    
    chrome_driver=Driver()
    # chrome_driver.startDriver()
    counter=1
    with open(file) as urls_file:
        # try:
        # chrome_driver.createlogs()
        
        # with ThreadPoolExecutor(max_workers=7) as executor:
        #     # Submit tasks to the executor, passing each object to the process_object function
        #     executor.map(chrome_driver.downloadAndConvertTSFiles,chrome_driver.ts_urls)
        
        # chrome_driver.downloadAndConvertTSFiles() 
        chrome_driver.file_names = sorted(os.listdir("logs/mp4_files/"))
        
        mp4_files = []
        for file_name in chrome_driver.file_names:
            mp4_files.append(f'./logs/mp4_files/{file_name}')
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = [executor.submit(chrome_driver.calculateVideoMos, value) for value in mp4_files]
            results = [future.result() for future in futures]
            # executor.map(chrome_driver.calculateVideoMos,mp4_files)
            
        # video_mos=chrome_driver.calculateVideoMos()
        video_mos = statistics.mean(results)
        print(f"MOS of : {video_mos}")
        counter+=1
        # except Exception as e:
        #     print(f"error in get mos of url . {e}")
    # chrome_driver.endOfProcess()
    
    output_file.close()


if __name__ == '__main__':
    main()

