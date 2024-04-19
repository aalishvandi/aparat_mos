from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time,csv,click
import os,requests,json,re,urllib,subprocess
from datetime import datetime
from browsermobproxy import Server
from itu_p1203 import extractor
from itu_p1203 import p1203_standalone


from selenium.webdriver import ActionChains

class SeleniumError(Exception):
    pass

class Driver:
    def __init__(self):
         pass
    
    def startDriver(self):
        os.popen("java -jar ./libs/browsermob-proxy-2.1.4/lib/browsermob-dist-2.1.4.jar --port 9090")
        time.sleep(10)
        self.server = Server("./libs/browsermob-proxy-2.1.4/bin/browsermob-proxy", options={'port': 9090})
        self.server.start()
        # Create a WebDriver instance (replace with the path to your WebDriver executable)
        service = Service(executable_path='/usr/bin/chromedriver')
        options = webdriver.ChromeOptions()
        self.proxy = self.server.create_proxy()
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--proxy-bypass-list=aparat.com"')
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--mute-audio')
        options.add_argument('--disable-gpu')
        options.add_argument('--proxy-server={host}:{port}'.format(host='localhost', port=self.proxy.port))
        # self.driver = webdriver.Chrome(options=options)
        self.driver = webdriver.Chrome(service=service, options=options)
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
        with open("./logs/network_log.har", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.proxy.har))
            print("wrote network logs to logs/network_log.har")
        # data=json.loads(self.proxy.har)
        self.ts_urls=[]
        for log in self.proxy.har['log']['entries']:
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
        
    def downloadAndConvertTSFiles(self):
        self.file_names = []
        for url in self.ts_urls:
            print(url)
            file_name = f"{url.split('.ts')[0].split('/')[-1]}-{datetime.timestamp(datetime.now())}"
            print(f"Download {url}")
            urllib.request.urlretrieve(url, f"./logs/ts_files/{file_name}.ts")
            # convert ts file to mp4
            print(f"Convert {file_name} to mp4...")
            convert_command = ['ffmpeg', '-i', f'./logs/ts_files/{file_name}.ts', '-c', 'copy', '-bsf:a', 'aac_adtstoasc', '-f', 'mp4', f'./logs/mp4_files/{file_name}.mp4']
            subprocess.run(convert_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.file_names.append(file_name)
    
    def calculateVideoMos(self):
        print(f"Calculating mos...")
        mp4_files = []
        for file_name in self.file_names:
            mp4_files.append(f'./logs/mp4_files/{file_name}.mp4')
        input_data = extractor.Extractor(mp4_files, 3)  # input .ts files, mode
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
    chrome_driver.startDriver()
    counter=1
    with open(file) as urls_file:
        aparat_urls = [line.strip() for line in urls_file]
        for x in range(24):
            for video_url in aparat_urls:
                try:
                    print(f"========== calculate mos of {video_url} ==========")
                    chrome_driver.openPage(video_url)
                    chrome_driver.createlogs()
                    chrome_driver.downloadAndConvertTSFiles()
                    video_mos=chrome_driver.calculateVideoMos()
                    print(f"MOS of {video_url} : {video_mos}")
                    video_result=[counter,video_url,chrome_driver.start_video_date,chrome_driver.start_video_time,video_mos,chrome_driver.end_video_time]
                    writer.writerow(video_result)
                    chrome_driver.removeTSFiles()
                    chrome_driver.restartProxy()
                    counter+=1
                except Exception as e:
                    print(f"error in get mos of url {video_url}. {e}")
                    continue
    chrome_driver.endOfProcess()
    
    output_file.close()


if __name__ == '__main__':
    main()
