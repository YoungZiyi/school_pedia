#coding=utf-8

import requests
import MySQLdb
import csv
from bs4 import BeautifulSoup
from glob import glob

config = {}
config['host'] = 'localhost'
config['port'] = 3306
config['user'] = 'root'
config['passwd'] = ''
config['db'] = 'test'
config['use_unicode'] = True
config['charset'] = 'utf8'

file_name = 'school_info.csv'

def read(file_name):
    rows = []
    with open(file_name, 'r') as f:
        f_csv = csv.reader(f)
        for row in f_csv:
            rows.append(row)
    return rows


def save_school_info():
    conn = MySQLdb.connect( **config )
    cur = conn.cursor()

    rows = read(file_name)
    for row in rows:
        school_name = row[0].encode('utf-8')
        school_id = row[1].encode('utf-8')
        cur.execute('insert into school_info values(%s, %s)', (school_id, school_name))
    cur.close()
    conn.commit()
    conn.close()

def download_page():
    conn = MySQLdb.connect( **config )
    cur = conn.cursor()
    base_url = 'http://baike.baidu.com/item/'
    
    all = cur.execute('select * from school_info')
    rows = cur.fetchmany(all)

    for row in rows:
        school_id = (row[0]).strip()
        school_name = (row[1]).strip()
        page_file_name = school_name + '_' + school_id + '.html'
        url = base_url + school_name
    
        print('qurey ' + url)
        rsp = requests.get(url)
        content = rsp.content.decode('utf-8')
        with open('pages/' + page_file_name, 'w') as f:
            f.write(content)

    cur.close()
    conn.close()

if __name__ == '__main__':
    conn = MySQLdb.connect( **config )
    cur = conn.cursor()

    not_found_school_list = []
    
    for file in glob('pages/*.html'):
        # file = 'pages/齐鲁医药学院_200786220.html'
        school_id = file.split('_')[1].split('.')[0]
        school_name = file.split('_')[0].split('/')[1]
        soup = BeautifulSoup(open(file))
        basic_info = soup.find('div', {'class':'basic-info cmn-clearfix'})
        if basic_info == None:
            not_found_school_list.append(school_name)
            print(school_name + ' not found')
            continue

        info_dic = {'school_id':school_id}
        children = basic_info.findChildren()
        for item in children:
            if not item.name in ['dt', 'dd']: continue
            
            # 删除 sup 标签
            for sup in item.findChildren('sup'):
                sup.extract()
            
            if item.name == 'dt':
                info_dic['tag'] = item.text.replace('\xa0', '').strip()
            elif item.name == 'dd':
                info_dic['value'] = item.text.replace('\xa0', '').strip()
            if 'tag' in info_dic and 'value' in info_dic:
                try:
                    cur.execute('insert into school_basic_info (school_id, tag, value) values(%s, %s, %s)', (info_dic['school_id'], info_dic['tag'], info_dic['value']))
                    # print(info_dic)
                    info_dic.pop('tag')
                    info_dic.pop('value')
                except Exception as e:
                    print(school_name + ' data:' + str(info_dic) + 'msg:' + str(e))
        print(school_name + ' saved')
        
        # cur.close()
        # conn.commit()
        # conn.close()
        # exit()
    print('failed school counts:' + str(len(not_found_school_list)))
    print('done!')

    cur.close()
    conn.commit()
    conn.close()



