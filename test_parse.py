import requests
import re
from bs4 import BeautifulSoup
import csv
import json
import logging
from selenium import webdriver

def write_to_excel(list,filename):
    with open('%s'%filename, 'a', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for dict in list:
            spamwriter.writerow([dict['bank'],dict['otdelenie'],dict['uslugi'],dict['region'],dict['city'],dict['address'],dict['telephone'],dict['add_telephone'],dict['work_time']])
#BinBank
def new_office(html,city_name):
    result_list = []
    soap = BeautifulSoup(html,'lxml')
    for num in range(1,150):
        telephone_list = []
        bankomat = str(soap.findAll("div",{"class": "office_list", "rel": "%s" % num}))

        if len(bankomat)==2:
            if num==1 : logging.warning(city_name,"ALARM")
            break

        soap_bankomat = BeautifulSoup(bankomat,'lxml')

        dict = {"bank": "БинБанк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                "address": "",
                "telephone": "", "add_telephone": "", "work_time": "work_time"}
        #Otdelenie
        try:
            pre_otdelenie = soap_bankomat.find("div",{"class" : "office_list_name", "itemprop":"name"})
            if pre_otdelenie!= None:
                pre_otdelenie = pre_otdelenie.text
            else : pre_otdelenie=''
            if len(pre_otdelenie[0:pre_otdelenie.find('»') + 1]) != 0:
                dict['otdelenie'] = pre_otdelenie[0:pre_otdelenie.find('»') + 1].replace("ПАО «БИНБАНК»",'')
            else:
                dict['otdelenie'] = pre_otdelenie
        except:
            logging.warning('Otdelenie Error')
        #Work_Time
        try:
            dict['work_time'] = soap_bankomat.find("td", {"itemprop": "openingHours"}).text
        except:
            logging.warning("work_time failed at num:",num)
            pass
        #Address
        pre_address = soap_bankomat.find("td",{"itemprop":"streetAddress"}).text.replace(" проложить маршрут",'')
        dict['address'] = re.sub('[0-9,]{7,7}|[0-9]{6,6}|<br>.*\.', '', pre_address).replace('Россия, ', '')
        #Telephone
        try:
            telephone = soap_bankomat.find("td", {"itemprop": "telephone"}).text
            pre_telephone = re.findall('\d{1}\(\d{3}\)\d{3}\-\d{2}\-\d{2}|'
                                       '\d{7}\-\d{2}\-\d{2}|\d\(\d{4}\)\d{3}\-\d{3}|'
                                       '\(\d{5}\)\d\-\d{2}\-\d{2}|'
                                       '\(\d{4}\)\d{2}\-\d{2}\-\d{2}|'
                                       '\d\(\d{4}\)\d{6}|'
                                       '\d{1}\(\d{3}\)\d{3}\d{2}\d{2}|'
                                       '\d\(\d{5}\)\d{5}|'
                                       '\d\(\d{3}\)\d{7}', telephone.replace(' ',''))
            for item in pre_telephone:
                if item not in telephone_list:
                    telephone_list.append(item)
        except:
            logging.warning("Telephone error",num)

        try:
            dict['telephone'] = telephone_list[0]
            dict['add_telephone'] = telephone_list[1]
        except:
            pass
        result_list.append(dict)

    return(result_list)
def bankomat_info(html,city_name):
    return_list=[]
    soap = BeautifulSoup(html,"html.parser")
    for num in range(1,1000):
        dict = {"bank": "БинБанк", "otdelenie": "Банкомат", "uslugi": "", "region":'',"city":city_name, "address": "",
                    "telephone": "", "work_time": "work_time"}
        bankomat = soap.findAll("div",{"class":"office_list","rel":"%s"%num,"id":re.compile('branch[0-9]')})
        try:
            if len(re.findall('class="alpha_bank_ico"',str(bankomat)))!=0:
                print("StartOtherBanks")
                break

            dict['work_time'] = re.findall('<td width="588">(.*)</td>',str(bankomat))[0]
            dict['address'] = re.findall('<td itemprop="streetAddress" width="588">(.*)<br>',str(bankomat))[0]
            if len(re.findall("Cash-in",str(bankomat)))!=0:
                dict['uslugi'] = "Внесение наличных"
            return_list.append(dict)
        except:
            print("Over")
            break
    return return_list
def binbank():
    with open('BinBankDict.txt','r') as dict:
        a = dict.read().replace("'",'"').replace('True','"True"')
        result = re.sub('}, {','}; {',a)
        result = result.split(';')
        for item in result:
            dict = json.loads(item)
            city_id = dict['data']['ID']
            city_name = dict['data']['NAME']
            r = requests.get('https://www.binbank.ru/ajax/binbankCities/setCity/?id=%s' % city_id)
            cookie = r.cookies
            r_new = requests.get('https://binbank.ru/branches/atms/list/', cookies=cookie)
            offices = requests.get('https://www.binbank.ru/branches/offices/list/',cookies=cookie)
            list = new_office(offices.text, city_name)
            write_to_excel(list)
#Alfa
def alpha_bankomats():
    r = requests.get('https://alfabank.ru/ext-json/0.2/office/city?limit=500&mode=array')
    list_of_city_id = []
    result_list = []
    for item in r.json()['response']['data']:
        list_of_city_id.append({"title":item['title'],"id":item['id']})

    for item in list_of_city_id:
        for offset in range(0,100):
            print(offset)
            all_bankomats = requests.get('https://alfabank.ru/ext-json/0.2/atm/list?city=%d&limit=100&offset=%d&mode=array'%(item['id'],offset*100))
            all_bankomats = all_bankomats.json()['response']['data']
            if(len(all_bankomats))<3:
                break
            for bankomat in all_bankomats:
                dict = {"bank": "АльфаБанк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '', "address": "",
                        "telephone": "", "work_time": "", "add_telephone": ""}
                try:
                    bankomat['bank']
                except:
                    dict['city'] = item['title']
                    dict['address'] = bankomat['address']
                    dict['work_time'] = bankomat['processing']
                    if len(bankomat['in'])>0:
                        dict['uslugi'] += "Внесение наличных "
                    if len(bankomat['out'])>0:
                        dict['uslugi'] += "Выдача наличных "
                    result_list.append(dict)


    return result_list
def alpha_otdelenie():
    r = requests.get('https://alfabank.ru/ext-json/0.2/office/city?limit=500&mode=array')
    list_of_city_id = []
    result_list = []
    for item in r.json()['response']['data']:
        list_of_city_id.append({"title": item['title'], "id": item['id']})

    for item in list_of_city_id:
        for offset in range(0, 100):
            all_offices = requests.get('https://alfabank.ru/ext-json/0.2/office/list?city=%d&limit=100&offset=%d&mode=array'%(item['id'],offset*100))
            all_offices = all_offices.json()['response']['data']
            if (len(all_offices))==0:
                break
            for office in all_offices:
                dict = {"bank": "АльфаБанк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '', "address": "",
                        "telephone": "", "work_time": "", "add_telephone": ""}
                dict['city'] = item['title']
                try:
                    dict['address'] = str(office['address']).replace('&laquo;','«').replace('&ndash;','-').replace('&raquo;','»').replace('&ndash;','-').replace('&nbsp;',' ').replace('&mdash;','-')
                except:
                    print("Adress")
                try:
                    dict['otdelenie'] = str(office['title']).replace('&laquo;','«').replace('&ndash;','-').replace('&raquo;','»').replace('&mdash;','-').replace('&nbsp;',' ')
                except:
                    print("Otdelenie failed")
                try:
                    dict['work_time'] = re.sub('<!--.*','',json.loads(str(office['processing']).replace("'",'"'))['retail'].replace('&ndash;','-').replace('&nbsp;',' ').replace('&mdash;','-').replace('\n',' '))
                    dict['uslugi'] += 'Общее отделение'
                except:
                    pass

                try:
                    dict['work_time'] = re.sub('<!--.*', '',
                                               json.loads(str(office['processing']).replace("'", '"'))['corporate'].replace(
                                                   '&ndash;', '-').replace('&nbsp;', ' ').replace('&mdash;', '-').replace(
                                                   '\n', ' '))
                    dict['uslugi'] += 'Отделение работы с корп. клиентами'
                except:
                    pass

                try:
                    dict['work_time'] = re.sub('<!--.*', '',
                                               json.loads(str(office['processing']).replace("'", '"'))['vip'].replace(
                                                   '&ndash;', '-').replace('&nbsp;', ' ').replace('&mdash;', '-').replace(
                                                   '\n', ' '))
                    dict['uslugi'] += 'Отделение работы с VIP клиентами'
                except:
                    pass

                if len(dict['work_time'])<5:
                    print(office["processing"])

                result_list.append(dict)

    return result_list
#VTB24
def vtb_bankomati():
    region_list = []
    city_list = []
    result_list = []
    r = requests.get('https://www.bm.ru/common/ajax_server/n_service_point_ajax_server.php?s=1&p=25661&mode=3&region=01')
    soap = BeautifulSoup(r.text,'lxml')
    regions = soap.find_all('a',{"class":"b-regions-region","href":"javascript:;"})
    for item in regions:
        try:
            region_id = re.findall('region(\d{2})',str(item))[0]
        except:
            print("regionID failed")
        region_list.append({"region_id":region_id})

    for item in region_list:
        r = requests.get("http://www.bm.ru/common/ajax_server/n_service_point_ajax_server.php?t=102&s=1&p=25661&mode=3&region=%d"%int(item['region_id']))
        city_soap = BeautifulSoup(r.text,'lxml')
        cities = city_soap.find_all('a',{"class":"b-regions-city","href":"javascript:;"})
        for city in cities:
            try:
                city_id = re.findall("setCity\('\d{2}'..'(\d{1,15})'",str(city))[0]
            except:
                print(city)
                print('cityFindError')
                city_id = ''
                break
            city_list.append({"region_id":item['region_id'],"city_id":city_id,"city_name":city.text})


    for city in city_list:
        for num_from in range(0,100):
            r = requests.get(
                'http://www.bm.ru/common/ajax_server/n_service_point_ajax_server.php?t=102&s=1&p=25661&mode=4&atmtype1=1&query=&quantity=50&from=%d&region=%d&city=%d'%(num_from,int(city['region_id']),int(city['city_id'])))
            soap = BeautifulSoup(r.text, 'lxml')
            all_bankomats = soap.find_all('tr', {"class": "atm-single"})
            if len(all_bankomats)==0: break
            for bankomat in all_bankomats:
                dict = {"bank": "ВТБ Банк Москвы", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                        "address": "",
                        "telephone": "", "work_time": "", "add_telephone": ""}
                bankomat_soap = BeautifulSoup(str(bankomat), 'lxml')
                dict['city'] = city['city_name']
                dict['address'] = str(bankomat_soap.find('div').text).replace('&nbsp;','').replace('\xa0',' ').replace('\r', '')

                if dict['address'] == 'г. Москва':
                    try:
                        dict['address'] = 'г. Москва, станция метро '+str(bankomat_soap.find('div',{'style':re.compile('color:.{7}')}).text)
                    except:
                        print("another try")
                    try:
                        dict['address'] = 'г. Москва, '+str(bankomat_soap.find('a',{'href':'javascript:;'}).text)
                    except:
                        print(bankomat_soap)

                if len(dict['address']) < 20:
                    try:
                        dict['address'] += ' ' +str((bankomat_soap.find('a',{'href':'javascript:;'}).text))
                    except:
                        pass
                try:
                    dict['work_time'] = str(bankomat_soap.find_all('td')[2]).replace(' ', '').replace('\n', '').replace(
                        '\t', '').replace('\r', '').replace('\xa0',' ').replace('</td>','').replace('<td>','').replace('<spanclass="atm-single-statusatm-single-status__24">','').replace('</span>','')
                except:
                    print("WorkTime error")
                try:
                    if len(bankomat_soap.find_all('td')[3]) == 1:
                        dict['uslugi'] = 'Выдача наличных '
                    else:
                        dict['uslugi'] = 'Выдача наличных Внесение наличных'
                except:
                    print("uslugi Error")
                result_list.append(dict)

    return result_list
def vtb_offices():
    region_list = []
    city_list = []
    result_list = []
    r = requests.get('https://www.bm.ru/common/ajax_server/n_service_point_ajax_server.php?s=1&p=25661&mode=3&region=01')
    soap = BeautifulSoup(r.text,'lxml')
    regions = soap.find_all('a',{"class":"b-regions-region","href":"javascript:;"})
    for item in regions:
        try:
            region_id = re.findall('region(\d{2})',str(item))[0]
        except:
            print("regionID failed")
        region_list.append({"region_id":region_id})

    for item in region_list:
        r = requests.get("http://www.bm.ru/common/ajax_server/n_service_point_ajax_server.php?t=102&s=1&p=25661&mode=3&region=%d"%int(item['region_id']))
        city_soap = BeautifulSoup(r.text,'lxml')
        cities = city_soap.find_all('a',{"class":"b-regions-city","href":"javascript:;"})
        for city in cities:
            try:
                city_id = re.findall("setCity\('\d{2}'..'(\d{1,15})'",str(city))[0]
            except:
                print(city)
                print('cityFindError')
                city_id = ''
                break
            city_list.append({"region_id":item['region_id'],"city_id":city_id,"city_name":city.text})

    for city in city_list:
        for num_from in range(0,1):
            r = requests.get(
                'http://www.bm.ru/common/ajax_server/bm_office_ajax_server.php?cltypeid=1&longitude=&latitude=&e=list&region_code=%d&city_code=%d'%(int(city['region_id']),int(city['city_id'])))
            soap = BeautifulSoup(r.text, 'lxml')
            all_offices = soap.find_all('tr', {"class": "pnt-single"})
            for office in all_offices:
                dict = {"bank": "ВТБ Банк Москвы", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                        "address": "",
                        "telephone": "", "work_time": "", "add_telephone": ""}

                office_soap = BeautifulSoup(str(office), 'lxml')
                dict['city'] = city['city_name']
                dict['otdelenie'] = re.sub('Филиала «[а-яА-Я]*»','',str(office_soap.find('a', {
                    'class': 'pnt-table-point-link pnt-single-name pnt-single-search'}).text).replace('Банка ВТБ (ПАО)',
                                                                                                      ''))
                dict['telephone'] = str(office_soap.find_all('div')[1].text).replace(' — call-центр', '')
                dict['address'] = re.sub('[0-9,]{7,7}|[0-9]{6,6}|<br>.*\.','',str(office.div.text))
                try:
                    dict['work_time'] = str(office_soap.find_all('p')).replace(',','')
                except:
                    print(office_soap)

                result_list.append(dict)
    return result_list
#Bank Rossiya
def ros_bankomati():
    result_list = []
    with open('ros_city_list.txt', 'r') as city_list:
        city_list = city_list.readlines()
        for item in city_list:
            num = item.replace('\n', '')
            get_city = requests.get('http://abr.ru/include/block_city.php?ID=%d'%int(num))
            soap = BeautifulSoup(get_city.text, 'lxml')
            city = str(soap.find('span', {'class': 'current_city'}).text)
            for num in range(1,100):
                get_bankomats = requests.get('http://abr.ru/include/ajax/show_atms_list.php?page=%d'%num,cookies = get_city.cookies)
                soap_ross = BeautifulSoup(get_bankomats.text,'lxml')
                all_bankomats = (soap_ross.find_all('tr'))
                if(len(all_bankomats))==0:break
                for bankomat in all_bankomats:
                    dict = {"bank": "Банк Россия", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                            "address": "",
                            "telephone": "", "work_time": "", "add_telephone": ""}
                    soap_bankomat = BeautifulSoup(str(bankomat),'lxml')
                    try:
                        dict['work_time'] = re.sub('[\t\n\r]','',str(soap_bankomat.find_all('td')[2].text))
                    except:
                        break
                    dict['uslugi'] = re.sub('<li>|</li>|[\]\[]','',str(soap_bankomat.find_all('li')))
                    dict['address'] = re.sub('[\t\n\r]','',str(soap_bankomat.find('a').text))
                    dict['city'] = city
                    result_list.append(dict)
    return result_list
def ros_offices():
    result_list = []
    with open('ros_city_list.txt', 'r') as city_list:
        city_list = city_list.readlines()
        for item in city_list:
            num = item.replace('\n', '')
            get_city = requests.get('http://abr.ru/include/block_city.php?ID=%d' % int(num))
            soap = BeautifulSoup(get_city.text, 'lxml')
            city = str(soap.find('span', {'class': 'current_city'}).text)
            r = requests.post('http://abr.ru/include/ajax/show_officies_list.php',data = {"PAGEN_1":"1"},cookies = get_city.cookies)
            office_soap = BeautifulSoup(r.text,'lxml')
            all_offices = office_soap.find_all('tr')
            for office in all_offices:
                dict = {"bank": "Банк Россия", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                        "address": "",
                        "telephone": "", "work_time": "", "add_telephone": ""}
                ross_soap = BeautifulSoup(str(office),'lxml')
                try:
                    dict['otdelenie'] = re.sub('[\t\r\n]|«АБ «РОССИЯ»','',ross_soap.find('a',{'title':'Открыть на карте'}).text).replace(";",",")
                except:
                    break
                dict['address'] = re.sub('[0-9, ]{6,8}|[\t\r\n]','',ross_soap.find('p',{'class':'add-info'}).text).replace(";",",")
                dict['telephone'] = re.sub('[\t\r\n]','',str(office.find_all('td')[1].text)).replace(";",",")
                test = str(re.sub('Доступ к сейфовым ячейкам:.*|[\n\r\t]|<td>','',str(office.find_all('td')[2])))
                dict['work_time'] = test.replace(";",",")
                dict['city'] = city
                #print(test)
                result_list.append(dict)
                break

    return result_list
#Bank Rs Standart
def rs_bankomati():
    result_list = []
    city_list = []
    r = requests.get('https://www.rsb.ru/about/atms/')
    soap = BeautifulSoup(r.text, 'lxml')
    cities = soap.find_all('li', {'class': 'cr_geo_menu-city'}) + soap.find_all('li', {'class': 'cr_geo_menu-region'})
    for city in cities:
        city_soap = BeautifulSoup(str(city), 'lxml')
        try:
            city_href = city_soap.find('a').get('href')
            city_name = city_soap.find('a').text
            if [city_href,city_name] not in city_list: city_list.append([city_href,city_name])
        except:
            pass

    for city in city_list:
        r = requests.get('https://www.rsb.ru%s'%city[0])
        bankomat_soap = BeautifulSoup(r.text, 'lxml')
        all_bankomats = bankomat_soap.find_all('ul', {'data-coords0': re.compile('.*')})
        for bankomat in all_bankomats:
            dict = {"bank": "Банк Русский Стандарт", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                    "address": "",
                    "telephone": "", "work_time": "", "add_telephone": ""}
            rsb_soap = BeautifulSoup(str(bankomat), 'lxml').find('ul')

            dict['address'] = str(rsb_soap.get('data-address')).replace('\xa0','')
            dict['work_time'] = rsb_soap.get('data-work_time')
            if rsb_soap.get('data-rur_out') == '1':
                dict['uslugi'] += "Выдача наличных "
            if rsb_soap.get('data-rur_in') == '1':
                dict['uslugi'] += "Прием наличных "
            dict['city']=city[1]

            if rsb_soap.get('data-company_code') == "rs":
                result_list.append(dict)
                print(city[1],"Added")
    return result_list
def rs_offices():
    result_list = []
    city_list = []
    r = requests.get('https://www.rsb.ru/about/branch/')
    soap = BeautifulSoup(r.text, 'lxml')
    cities = soap.find_all('li', {'class': 'cr_geo_menu-city'}) + soap.find_all('li', {'class': 'cr_geo_menu-region'})
    for city in cities:
        city_soap = BeautifulSoup(str(city), 'lxml')
        try:
            city_href = city_soap.find('a').get('href')
            city_name = city_soap.find('a').text
            if [city_href,city_name] not in city_list: city_list.append([city_href,city_name])
        except:
            pass

    for city in city_list:
        r = requests.get('https://www.rsb.ru%s'%city[0])
        office_soap = BeautifulSoup(r.text, 'lxml')
        all_offices = office_soap.find_all('ul', {'data-coords0': re.compile('.*')})
        for office in all_offices:
            dict = {"bank": "Банк Русский Стандарт", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                    "address": "",
                    "telephone": "", "work_time": "", "add_telephone": ""}
            rsb_soap = BeautifulSoup(str(office), 'lxml').find('ul')
            dict['address'] = rsb_soap.get('data-address')
            dict['work_time'] = rsb_soap.get('data-work_time')
            dict['otdelenie'] = rsb_soap.get('data-name1')
            dict['city'] = city[1]
            result_list.append(dict)
    return result_list
#Bank Jugra
def jugra_bankomati():
    result_list=[]

    r = requests.get('http://jugra.ru/msk/offices-and-atms/')
    soap = BeautifulSoup(r.text, 'lxml')
    alls = soap.find_all('tr', {'id': re.compile('mapItem[0-9]{1,3}')})
    for item in alls:
        dict = {"bank": "Банк Югра", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                    "address": "",
                    "telephone": "", "work_time": "", "add_telephone": ""}
        new_item = BeautifulSoup(str(item), 'lxml')
        dict['address'] = re.sub('\d{6,7}', '', str(new_item.find_all('td')[0].text))
        if len(str(new_item.find_all('td')[2])) > 150:
                dict['otdelenie'] = new_item.find_all('td')[1].text
        else:
                dict['otdelenie'] = 'Банкомат'
        dict['work_time'] = str(new_item.find_all('td')[2]).replace(';',',')
        dict['city'] = 'Москва'
        result_list.append(dict)

    return result_list
#Bank Vostochnii
def vost_bankomati():
    result_list = []
    with open('vostok-dict.txt','r') as city_list:
        city_list = city_list.readlines()
        for item in city_list:
            num = item.replace('\n', '')
            get_city = requests.post('https://www.vostbank.ru/local/ajax/change_city.php',data={'city_id':num})
            try:
                get_city.json()['city']['city_name']
            except:
                continue
            print(get_city.text)
            r = requests.get('https://www.vostbank.ru/office/',cookies = get_city.cookies)
            soap = BeautifulSoup(r.text,'lxml')
            all_bankomats = soap.find_all('tr',{'data-type-item':re.compile('atm|terminal')})
            for bankomat in all_bankomats:
                dict = {"bank": "Банк Восточный", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                        "address": "",
                        "telephone": "", "work_time": "", "add_telephone": ""}
                soap_bankomat = BeautifulSoup(str(bankomat),'lxml')
                dict['city'] = get_city.json()['city']['city_name']
                dict['address'] = soap_bankomat.find('p',{'class':'head-text'}).text
                try:
                    dict['work_time'] = re.sub('[\t\r\n]','',str(bankomat.find('div',{'class':'time-wrap'}).text))
                except:
                    dict['work_time'] = "Круглосуточно"
                dict['uslugi'] = re.sub("[\t\r\n]","",soap_bankomat.find('td',{'class':'accordeon'}).text).replace('    ','</br>')
                result_list.append(dict)

    return result_list
def vost_offices():
    result_list = []
    with open('vostok-dict.txt', 'r') as city_list:
        city_list = city_list.readlines()
        for item in city_list:
            num = item.replace('\n', '')
            get_city = requests.post('https://www.vostbank.ru/local/ajax/change_city.php', data={'city_id': num})
            try:
                test = get_city.json()['city']['city_name']
            except:
                continue
            r = requests.get('https://www.vostbank.ru/office/', cookies=get_city.cookies)
            soap = BeautifulSoup(r.text, 'lxml')
            all_offices = soap.find_all('tr', {'data-type-item': re.compile('office')})
            for office in all_offices:
                dict = {"bank": "Банк Восточный", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                        "address": "",
                        "telephone": "", "work_time": "", "add_telephone": ""}

                soap_bankomat = BeautifulSoup(str(office), 'lxml')
                dict['city'] = get_city.json()['city']['city_name']
                dict['address'] = soap_bankomat.find('p', {'class': 'head-text'}).text
                dict['otdelenie'] = soap_bankomat.find('p', {'class': 'office-name'}).text
                try:
                    dict['work_time'] = re.sub('[\t\r\n]', '',
                                               str(soap_bankomat.find('div', {'class': 'time-wrap'}).text))
                except:
                    dict['work_time'] = "Круглосуточно"

                dict['uslugi'] = re.sub("[\t\r\n]", "", soap_bankomat.find('td', {'class': 'accordeon'}).text).replace(
                    '    ', '</br>')
                print(dict['city'])
                result_list.append(dict)

        return result_list
#Bank vbbr
def offices():
    offices = requests.get('https://www.vbrr.ru/contacts')
    new_soap = BeautifulSoup(offices.text,'lxml')
    test = new_soap.find_all('a',{'onclick':re.compile('showcity4map\(\'[a-zA-Z]*\'\);')})
    for item in test:
        dict = {"bank": "Всероссийский банк развития регионов", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                "address": "",
                "telephone": "", "work_time": "", "add_telephone": ""}
        city = item.get('href').replace('#','')
        city_offices = requests.get('https://www.vbrr.ru/contacts/index.php?ajax=y&city=%s&bxajaxid=d234fa1e015c1bf530a3e12b529f1d62'%city)
        city_soap = BeautifulSoup(str(city_offices.text),'lxml')
        try:
            dict['city'] = city_soap.find('div',{'class':'news-detail'}).h3.text
            test = city_soap.find_all('td')
            print(test[1])
        except:
            print(city, 'Fail')
        break
#VTB24()
def vtb_bankomats():
    result_list = []
    r = requests.get('http://www.vtb.ru/geography/russia/')
    new_soap = BeautifulSoup(r.text,'lxml')
    list_of_cities = new_soap.find_all('a',{'class':'dot'})
    print(len(list_of_cities))
    count = 0
    list_of_cities = list_of_cities[0:550]
    for item in list_of_cities:
        count +=1
        print(count)
        city = item.get('href')
        all_items = requests.get('http://www.vtb.ru/group/contacts/geography/russia/moscow/')
        items_soap = BeautifulSoup(str(all_items.text),'lxml')
        try:
            city_name = items_soap.find('span',{'class':'dash jSwitcher'}).text
        except:
            city_name = ''
        pre_all_bankomats = items_soap.find('tbody',{'class':'adr-list atms'})
        all_bankomats = BeautifulSoup(str(pre_all_bankomats),'lxml').find_all('tr', {'class': 'item'})
        for bankomat in all_bankomats:
            dict = {"bank": "Банк ВТБ24", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                    "address": "",
                    "telephone": "", "work_time": "", "add_telephone": ""}
            one_bankomat = bankomat.find_all('td')
            if one_bankomat[0].img.get('src') != '/local/templates/vtb2016_ru/images/mapPoints/bVTB24.png':
                continue
            dict['address'] = re.sub('[\n\r\t]|.*]', '', str(one_bankomat[1].text))
            pre_work_time = one_bankomat[2].text.replace(';', '')

            if pre_work_time.count('\n') > 8:
                try:
                    dict['work_time'] = one_bankomat[3].text.replace(';', '')
                except:
                    pass
                    dict['work_time'] = pre_work_time
            dict['city'] = city_name
            if(str(one_bankomat[3]).count('Выдача'))>1:dict['uslugi'] += 'Внесение наличных '
            if(str(one_bankomat[3]).count('Приём'))>1:dict['uslugi'] += 'Выдача наличных '
            result_list.append(dict)
        break
    return result_list
def vtb_offices_2():
    result_list = []
    data = {"action": "{\"action\":\"OfficeBusyService\"}",
            "scopeData": "{\"method\":\"GetOffices\",\"query\":{\"Bounds\":{\"LeftBottomLatitide\":0,\"LeftBottomLongitude\":0,\"RightTopLatitide\":170,\"RightTopLongitude\":170},\"WorkOnWeekends\":false,\"Services\":[],\"OfficeId\":null}}",
            "pageUrl": "/map/"}
    r = requests.post('https://www.vtb24.ru/services/ExecuteAction', data=data)
    all_bankomats = r.json()['getOfficesResult']

    for bankomat in all_bankomats:
        dict = {"bank": "ВТБ24", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                "address": "",
                "telephone": "", "add_telephone": "", "work_time": "work_time"}
        json_bankomat = json.loads(bankomat['properties'])
        dict['work_time'] = re.sub('<li>|</li>|\r','',json_bankomat['Office_NaturalPersonSchedule']).replace('\n','<br>')
        dict['address'] = re.sub('[0-9,]{6,7}|\/','',json_bankomat['ServicePoint_Address'])
        dict['otdelenie'] = json_bankomat['Office_ShortName']
        result_list.append(dict)

    return result_list
#Minbank
def minbank_bankomati():
    result_list = []
    r = requests.get('https://telebank.minbank.ru/geoapi/getTerminals?count=10000&max_dist=1000000000')
    data = r.json()
    all_bankomats = data['list']
    for bankomat in all_bankomats:
        dict = {"bank": "Банк Минбанк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                "address": "",
                "telephone": "", "work_time": "", "add_telephone": ""}

        dict['address'] = bankomat['address']
        dict['city'] = bankomat['city']
        dict['region'] = bankomat['region']
        try:
            dict['work_time'] = bankomat['workhours'].replace(';','')
        except:
            dict['work_time'] = ''
        result_list.append(dict)

    return result_list
def minbank_offices():
    headers = {"User-Agent" : "Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0"}
    r = requests.get('http://www.minbank.ru',headers=headers)
    r = requests.get('https://www.minbank.ru/map/',cookies = r.cookies,headers=headers)
    new_soap = BeautifulSoup(r.text,'lxml')
    all_offices = new_soap.find_all('div',{'class':'bank-item'})
    for item in all_offices:
        print(item)
#MosOblBank
def mosoblbank_offices():
    result_list = []
    r = requests.get('http://mosoblbank.ru')
    city_coap = BeautifulSoup(r.text,'lxml')
    all_regions = city_coap.find_all('a',{"class":"region_link"})
    count = 0
    for region in all_regions:
        count += 1
        region_id = int(region.get('id'))
        webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.Cookie'] = 'REGION=%d'%region_id
        driver = webdriver.PhantomJS('/Users/orange13/Documents/phantomjs/bin/phantomjs')
        driver.get("http://mosoblbank.ru/offices/atms/")
        region_soap = BeautifulSoup(driver.page_source,'lxml')
        all_offices = region_soap.find_all('td',{'class':'office'})
        for office in all_offices:
            dict = {"bank": "Банк Мособлбанк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                "address": "",
                "telephone": "", "work_time": "", "add_telephone": ""}
            href = office.a.get('href')
            r = requests.get('http://mosoblbank.ru/%s' % href)
            office_soap = BeautifulSoup(r.text, 'lxml')

            dict['otdelenie'] = office_soap.find_all('h1')[1].text.replace(';','')
            pre_tel_work = office_soap.find_all('p')[15].text.replace(';','').replace('+','').replace(' ', '')
            try:
                dict['telephone'] = re.findall('\d{1}\(\d{3}\)\d{3}\-\d{2}\-\d{2}|'
                                               '\d{7}\-\d{2}\-\d{2}|\d\(\d{4}\)\d{3}\-\d{3}|'
                                               '\(\d{5}\)\d\-\d{2}\-\d{2}|'
                                               '\(\d{3,4}\)\d{2,3}\-\d{2}\-\d{2}|'
                                               '\d\(\d{4}\)\d{6}|'
                                               '\d{1}\(\d{3}\)\d{3}\d{2}\d{2}|'
                                               '\d\(\d{5}\)\d{5}|'
                                               '\d\(\d{3}\)\d{7}',str(pre_tel_work))[0]
                dict['add_telephone'] = re.findall('\d{1}\(\d{3}\)\d{3}\-\d{2}\-\d{2}|'
                                               '\d{7}\-\d{2}\-\d{2}|\d\(\d{4}\)\d{3}\-\d{3}|'
                                               '\(\d{5}\)\d\-\d{2}\-\d{2}|'
                                               '\(\d{3,4}\)\d{2,3}\-\d{2}\-\d{2}|'
                                               '\d\(\d{4}\)\d{6}|'
                                               '\d{1}\(\d{3}\)\d{3}\d{2}\d{2}|'
                                               '\d\(\d{5}\)\d{5}|'
                                               '\d\(\d{3}\)\d{7}', str(pre_tel_work))[1:]
            except:
                print(pre_tel_work)
                continue

            dict['address'] = re.sub('Адрес:.[\d\,]{6,7}','',office_soap.find_all('p')[14].text)
            dict['work_time'] = re.sub('[\t\r\n\;]|<p><strong>Режим работы:</strong>|</p>','',str(office_soap.find_all('p')[16]))
            result_list.append(dict)

    return result_list
#MTS BANK
def mts_offices():
    result_list = []
    r = requests.get('http://www.mtsbank.ru/cities.php?')
    with open('test.html', 'w') as test:
        test.write(r.text)
    soap = BeautifulSoup(r.text, 'lxml')
    new_soap = soap.find('table')
    all_cities = new_soap.find_all('li')
    for city in all_cities:
        href = city.a.get('href')
        city_name = city.a.text
        r = requests.get('http://www.mtsbank.ru%s' % href)
        city_soap = BeautifulSoup(r.text, 'lxml')
        all_offices = city_soap.find_all('div', {'id': re.compile('item.*')})
        print(len(all_offices))
        for office in all_offices:
            dict = {"bank": "Банк Мособлбанк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                    "address": "",
                    "telephone": "", "work_time": "", "add_telephone": ""}
            dict['otdelenie'] = office.a.text
            dict['address'] = office.p.text
            dict['work_time'] = re.sub(
                '[\r\n\t]|<p>|Обслуживание физических лиц:|<span class="small">|без перерыва|</span>|</p>', '',
                str(office.find_all('p')[1]))
            dict['city'] = city_name
            result_list.append(dict)

    return result_list
def mts_bankomats():
    result_list = []
    r = requests.get('http://www.mtsbank.ru/cities.php?')
    with open('test.html','w') as test:
        test.write(r.text)
    soap = BeautifulSoup(r.text,'lxml')
    new_soap = soap.find('table')
    all_cities = new_soap.find_all('li')
    for city in all_cities:
        href = city.a.get('href').replace('branches','atms')
        city_name = city.a.text
        r = requests.get('http://www.mtsbank.ru%s'%href)
        city_soap = BeautifulSoup(r.text,'lxml')
        all_offices = city_soap.find_all('div',{'id':re.compile('item.*')})
        print(len(all_offices))
        print(href)
        for bankomat in all_offices:
            dict = {"bank": "МТС Банк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                    "address": "",
                    "telephone": "", "work_time": "", "add_telephone": ""}
            dict['address'] = bankomat.a.text
            dict['work_time'] = re.sub('&lt;|p&gt;|<p>|<p/>]','',str(bankomat.find_all('p')[1])).replace(';','')
            if str(bankomat).count('Выдача') > 0:
                dict['uslugi'] += "Выдача наличных"
            if str(bankomat).count('Прием') > 0 :
                dict['uslugi'] += "Внесение наличных"

            result_list.append(dict)
    return result_list
#Trast Bank
def trast_bankomats():
    result_list = []
    r = requests.get('http://www.trust.ru/address/')
    soap = BeautifulSoup(r.text, 'lxml')
    pre_find = soap.find_all('select')[0]
    cities = pre_find.find_all('option')
    for city in cities:
        href = city.get('value')
        city_name = city.text
        r = requests.get('http://www.trust.ru/address/?regions=%s' % href)
        soap = BeautifulSoup(r.text, 'lxml')
        find = soap.find_all('script')
        a = str(find[14])
        try:
            test = re.findall('\[\{.*', a)[0][:-2]
        except:
            print(city_name+"error")
            continue

        data = json.loads(test)

        for item in data:
            if item['DETAIL_TEXT'] == 'Банк ТРАСТ (ПАО)':
                pass
            else:
                continue

            dict = {"bank": "Траст Банк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                    "address": "",
                    "telephone": "", "work_time": "", "add_telephone": ""}
            dict['city'] = city_name
            dict["work_time"] = re.sub('&quot;|&nbsp;','',item['PROPERTY_OPERATING_TIME_VALUE'])
            dict["address"] = re.sub('&quot;|&nbsp;','',item['PROPERTY_ADRESS_VALUE'])
            dict["uslugi"] = re.sub('[\[\'\]]|RUR|USD|EUR|\,}','',str(item['BENEFITS'])).replace(',','')
            result_list.append(dict)

    return result_list
def trast_offices():
    result_list = []
    r = requests.get('http://www.trust.ru/address/')
    soap = BeautifulSoup(r.text, 'lxml')
    pre_find = soap.find_all('select')[0]
    cities = pre_find.find_all('option')
    for city in cities:
        href = city.get('value')
        city_name = city.text
        r = requests.get('http://www.trust.ru/address/?regions=%s' % href)
        soap = BeautifulSoup(r.text, 'lxml')
        find = soap.find_all('script')
        a = str(find[14])
        try:
            test = re.findall('\[\{.*', a)[0][:-2]
        except:
            print(city_name+"error")
            continue

        data = json.loads(test)

        for item in data:
            if item['DETAIL_TEXT'] == '':
                pass
            else:
                continue

            dict = {"bank": "Траст Банк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                    "address": "",
                    "telephone": "", "work_time": "", "add_telephone": ""}
            dict['city'] = city_name
            dict["work_time"] = re.sub('&quot;|&nbsp;','',item['PROPERTY_OPERATING_TIME_VALUE'])
            dict["address"] = re.sub('&quot;|&nbsp;','',item['PROPERTY_ADRESS_VALUE'])
            dict['telephone'] = item['PROPERTY_PHONE_VALUE']
            dict['otdelenie'] = re.sub('&quot;','',item['NAME'])
            result_list.append(dict)

    return result_list
#Novibank
def novikom_bankomats():
    result_list = []
    r = requests.get('http://novikom.ru/ru/contacts/bankomats/')
    soap = BeautifulSoup(r.text,'lxml')
    pre_all_bankomats = BeautifulSoup(str(soap.find_all('table',{'class':'bankomat'})),'lxml')

    all_bankomats = pre_all_bankomats.find_all('tr')
    for bankomat in all_bankomats:
        dict = {"bank": "Траст Банк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                "address": "",
                "telephone": "", "work_time": "", "add_telephone": ""}
        fields = bankomat.find_all('td')
        try:
            dict['otdelenie'] = re.sub('<td>|<br/>|</td>','',str(fields[0]))
        except:
            continue
        dict['address'] = re.sub('<td>|<br/>|</td>','',str(fields[1]))
        dict['uslugi'] = re.sub('RUB|USD|EUR|\/|<td>|<br/>|</td>','',str(fields[2]))
        dict['work_time'] = re.sub('<td>|</td>','',str(fields[3]))
        result_list.append(dict)

    return result_list
#OTP Bank
def otp_bankomats():
    result_list = []
    r = requests.get('https://www.otpbank.ru/retail/branches/')
    cities_soap = BeautifulSoup(r.text, 'lxml')
    cities = cities_soap.find_all('li', {'class': 'city-list__item'})
    for city in cities:
        city_name = re.sub('[\r\n\t]', '', city.text)
        href = city.a.get('href')
        r = requests.get('https://www.otpbank.ru/%s'%href)
        soap = BeautifulSoup(r.text,'lxml')
        all_bankomats = soap.find_all('div',{'class':re.compile('offices-list__item offices-list__item_visible-hide category-[94,96]')})
        for bankomat in all_bankomats:
            dict = {"bank": "ОТП Банк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                    "address": "",
                    "telephone": "", "work_time": "", "add_telephone": ""}
            href = bankomat.a.get('href')
            new_r = requests.get('https://www.otpbank.ru%s'%href)
            bankomat_soap = BeautifulSoup(new_r.text,'lxml')
            fields = bankomat_soap.find('div',{'class':'content-block text'}).find_all('p')
            dict['address'] = re.sub('<p>|<b>|Адрес|\:|</b>|</p>|[0-9,]{6,7}','',str(fields[0])).replace(';','')
            try:
                dict['work_time'] = re.sub('[\r\t\n]|<p>|</p>|<strong>|</strong>|\|','',str(fields[1])).replace(';','')
            except:
                pass
            if new_r.text.count('выдача')>0:
                dict['uslugi'] += " Выдача наличных"
            if new_r.text.count('прием')>0:
                dict['uslugi'] += " Внесение наличных"
            dict['city']=city_name
            result_list.append(dict)
    return result_list
def otp_offices():
    result_list = []
    r = requests.get('https://www.otpbank.ru/retail/branches/')
    cities_soap = BeautifulSoup(r.text, 'lxml')
    cities = cities_soap.find_all('li', {'class': 'city-list__item'})
    count = 0
    for city in cities:
        count += 1
        city_name = re.sub('[\r\n\t]', '', city.text)
        href = city.a.get('href')
        r = requests.get('https://www.otpbank.ru/%s'%href)
        soap = BeautifulSoup(r.text,'lxml')
        all_bankomats = soap.find_all('div',{'class':re.compile('offices-list__item offices-list__item_visible-hide category-87')})
        for bankomat in all_bankomats:

            href = bankomat.a.get('href')
            new_r = requests.get('https://www.otpbank.ru%s'%href)
            bankomat_soap = BeautifulSoup(new_r.text,'lxml')
            otdelenie = re.sub('[\n\t\r]','',bankomat_soap.h2.text)
            fields = bankomat_soap.find('div',{'class':'content-block text'}).find_all('p')
            with open('otp-banks','a') as out:
                out.write(str(fields)+str(otdelenie)+"\n\n\n")

    return result_list
#ПромСвязьБанк
def promsvaz_bankomats():
    result_list = []
    r = requests.get('http://www.psbank.ru/psbservices/SearchService.svc/GetAllATMsAndOfficesInBounds?firstLatitude=0&firstLongitude=0&secondLatitude=170&secondLongitude=170&atmStatuses=null&officeOperations=null&textFilter=null&recordsOffset=0&recordsCount=1')
    all_bankomats = r.json()['Atms']
    print(len(all_bankomats))
    for bankomat in all_bankomats:
        dict = {"bank": "Промсвязьбанк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                "address": "",
                "telephone": "", "work_time": "", "add_telephone": ""}
        if bankomat['Owner']=='Промсвязьбанк':
            pass
        else:
            continue
        dict['city'] = bankomat['City']
        dict['address'] = bankomat['Address']

        if bankomat['HourseOfService']==[]:
            dict['work_time'] = "В режиме работы организации"
        else:
            for item in bankomat['HourseOfService']:
                dict['work_time'] += ' '+item['Key']+item['Value']

        try:
            if 6 in bankomat['Operations'] : dict['uslugi'] += ' Внесение наличных'
            if 2 in bankomat['Operations'] : dict['uslugi'] += ' Выдача наличных'
        except:
            pass
        result_list.append(dict)
    return result_list
def promsvaz_offices():
    result_list = []
    r = requests.get('http://www.psbank.ru/psbservices/SearchService.svc/GetAllATMsAndOfficesInBounds?firstLatitude=0&firstLongitude=0&secondLatitude=170&secondLongitude=170&atmStatuses=null&officeOperations=null&textFilter=null&recordsOffset=0&recordsCount=1')
    all_bankomats = r.json()['Offices']
    print(len(all_bankomats))
    for bankomat in all_bankomats:
        dict = {"bank": "Промсвязьбанк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                "address": "",
                "telephone": "", "work_time": "", "add_telephone": ""}
        print(bankomat)
        dict['otdelenie'] = bankomat['Name']
        dict['city'] = bankomat['City']
        dict['address'] = bankomat['Address']
        dict['telephone'] = '8 800 333 03 03'
        if bankomat['HourseOfService']==[]:
            dict['work_time'] = "В режиме работы организации"
        else:
            for item in bankomat['HourseOfService']:
                dict['work_time'] += ' '+item['Key']+item['Value']

        result_list.append(dict)
    return result_list
#РенесансКредит
def rencred():
    result_list = []
    r = requests.get('https://rencredit.ru')
    soap = BeautifulSoup(r.text,'lxml')
    all_cities = soap.find_all('a',{'class':'change-location-window__list-link js-change-location-link'})
    for city in all_cities:
        city_id = re.findall('[0-9]{1,3}',city.get('href'))[0]
        name = city.text
        r = requests.get('https://rencredit.ru/addresses/?VIEW=list&CITY=%s'%city_id)
        otdelenie = BeautifulSoup(r.text,'lxml')
        all_offices = otdelenie.find_all('tr',{'class':'location-table__row'})
        for office in all_offices:
            dict = {"bank": "Ренессанс Кредит Банк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                    "address": "",
                    "telephone": "", "add_telephone": "", "work_time": "work_time"}
            try:
                dict['otdelenie'] = office.find('div',{'class':'location-table__title'}).text
            except:
                continue

            dict['address'] = re.sub('.*[0-9,]{6,8}','',office.find('div',{'class':'location-table__address'}).text)
            telephone_list = office.find_all('span',{'class':'phones-block__row'})
            try:
                dict['telephone'] = telephone_list[0].text
                dict['add_telephone'] = telephone_list[1].text
            except:
                pass
            dict['work_time'] = office.find('div',{'class':'schedule'}).text.replace('\n','<br>')
            try:
                dict['uslugi'] = office.find('div',{'class':'location-table__services'}).text
            except:
                pass
            result_list.append(dict)
    return result_list
#РосБанк
def rosbank_bankomats():
    result_list = []
    headers={'Accept-Encoding': 'identity'}
    cities_request = requests.get('http://www.rosbank.ru/ru',headers=headers)
    cities_pre_soap = BeautifulSoup(cities_request.text,'lxml')
    cities_soap = cities_pre_soap.find_all('ul',{'class':'city-block__section_list'})
    for city_soap in cities_soap:
        city_soap_1 = city_soap.find_all('li')
        for item in city_soap_1:
            href = item.a.get('href')
            href2 = re.findall('[0-9]{1,3}',item.a.get('href'))[0]
            region_name = item.text
            print(region_name,href)
            new_r = requests.get('https://www.rosbank.ru/ru/atms/%s'%href,headers=headers)
            bankomats_soap = BeautifulSoup(new_r.text,'lxml')
            all_cities = bankomats_soap.find_all('option', {'value': re.compile('.*')})

            for city in all_cities:
                headers = {'Accept-Encoding': 'identity',
                           'Cookie':'regionrb=%s'%href2}
                print(headers)
                city_id = city.get('value')
                city_name = city.text
                list_for_check = [0]
                for i in range(0,14):
                    url = 'http://www.rosbank.ru/ru/atms/list.php?&p_f_2_11=%s&page_13=%s&p_f_2_all=0'%(city_id,str(i))
                    new_r_2 = requests.get(url, headers=headers)
                    print(len(new_r_2.content))
                    list_for_check.append(len(new_r_2.text))
                    bankomats_soap = BeautifulSoup(new_r_2.text, 'lxml')
                    all_bankomats = bankomats_soap.find_all('div',{'class':'page-atm__table_row'})
                    print(len(all_bankomats))

                    for bankomat in all_bankomats:
                        dict = {"bank": "Рос Банк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                                "address": "",
                                "telephone": "", "add_telephone": "", "work_time": "work_time"}

                        dict['region'] = region_name
                        dict['city'] = city_name
                        dict['address'] = bankomat.find('div',{'class':'address-title'}).text
                        dict['work_time'] = re.sub('[\r\n\t]','',bankomat.find('div',{'class':'page-atm__table_col page-atm__table_col--time'}).text).replace(' ','')
                        if str(bankomat).count('Выдача')>0:
                            dict['uslugi'] += " Выдача наличных"
                        if str(bankomat).count('Внесение')>0:
                            dict['uslugi'] += " Внесение наличных"
                        result_list.append(dict)
                        print(dict)

                    if len(all_bankomats)<12 and i!=0:
                        break

    return result_list

def rosbank_offices():
    result_list = []
    headers={'Accept-Encoding': 'identity'}
    cities_request = requests.get('http://www.rosbank.ru/ru',headers=headers)
    cities_pre_soap = BeautifulSoup(cities_request.text,'lxml')
    cities_soap = cities_pre_soap.find_all('ul',{'class':'city-block__section_list'})
    for city_soap in cities_soap:
        city_soap_1 = city_soap.find_all('li')
        for item in city_soap_1:
            href = item.a.get('href')
            href2 = re.findall('[0-9]{1,3}',item.a.get('href'))[0]
            region_name = item.text
            print(region_name,href)
            new_r = requests.get('https://www.rosbank.ru/ru/atms/%s'%href,headers=headers)
            bankomats_soap = BeautifulSoup(new_r.text,'lxml')
            all_cities = bankomats_soap.find_all('option', {'value': re.compile('.*')})

            for city in all_cities:
                headers = {'Accept-Encoding': 'identity',
                           'Cookie':'regionrb=%s'%href2}
                print(headers)
                city_id = city.get('value')
                city_name = city.text
                list_for_check = [0]
                for i in range(0,14):
                    url = 'http://www.rosbank.ru/ru/offices/list.php?p_f_1_12=%s&page_13=%s'%(city_id,str(i))
                    print(url)
                    new_r_2 = requests.get(url, headers=headers)
                    print(len(new_r_2.content))
                    list_for_check.append(len(new_r_2.text))
                    bankomats_soap = BeautifulSoup(new_r_2.text, 'lxml')
                    all_bankomats = bankomats_soap.find_all('div',{'class':'page-atm__table_row'})
                    print(len(all_bankomats))

                    for bankomat in all_bankomats:
                        dict = {"bank": "Рос Банк", "otdelenie": "Банкомат", "uslugi": "", "region": '', "city": '',
                                "address": "",
                                "telephone": "", "add_telephone": "", "work_time": "work_time"}

                        dict['otdelenie'] = bankomat.find('div',{'itemprop':'name'}).text
                        dict['address'] = re.sub('[\n\r\t]','',bankomat.find('div',{'class':'address-title'}).text).replace('  ','').replace(';','')
                        dict['region'] = region_name
                        dict['city'] = city_name
                        result_list.append(dict)

                    if len(all_bankomats) < 12 and i != 0:
                        break

    return result_list

list = novikom_bankomats()
write_to_excel(list,'novikom-bankomats.csv')