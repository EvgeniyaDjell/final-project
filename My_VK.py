from my_VK_token import ACCESS_TOKEN_VK
from data_input import USER_ID, TOKEN_YANDEX, NUMBER_UPLOAD_PHOTO, FOLDER_NAME
import requests
import json
import time
from tqdm import tqdm
from datetime import datetime

class VkUser:
    def __init__(self, version='5.131'):
        self.token = ACCESS_TOKEN_VK
        self.user_id = USER_ID
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def get_photo_info(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.user_id,
                  'album_id': 'profile',
                  'photo_sizes': 1,
                  'extended': 1,
                  'rev': 1
                  }
        try:
            photo_info = requests.get(url, params={**self.params, **params}).json()['response']
            return photo_info['items']
        except:
            print(f"Не удалось получить данные о фотографиях из VK")
            return {}

    def get_photo_list(self, photo_info):
        if len(photo_info) == 0:
            print("Ошибка обработки информации о фотографиях. Подготовленные данные не получены")
            return {}
        else:
            photo_to_upload = {}
            for count in range(NUMBER_UPLOAD_PHOTO):
                photo = photo_info[count]
                likes_count = photo['likes']['count']
                photo_description = {'size': photo['sizes'][-1]['type'],
                                     'url': photo['sizes'][-1]['url'],
                                     'data': datetime.fromtimestamp(photo['date']).strftime('%Y_%m_%d')}
                if likes_count in photo_to_upload:
                    photo_to_upload[likes_count].append(photo_description)
                else:
                    photo_to_upload[likes_count] = [photo_description]
            return photo_to_upload


class YandexUser:
    def __init__(self):
        """Метод для получения основных параметров для загрузки фотографий на Я-диск"""
        self.token = TOKEN_YANDEX
        self.headers = {'Content-Type': 'application/json',
                        'Authorization': f"OAuth {self.token}"}

    def create_folder(self):
        """Метод для создания папки на Яндекс-диске"""
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': FOLDER_NAME}
        response = requests.put(url, headers=self.headers, params=params)
        if response.status_code == 201:
            print(f"\nПапка {FOLDER_NAME} на Яндекс диске успешно создана.\n")
        elif response.status_code == 409:
            print(f"\nПапка {FOLDER_NAME} уже существует.\n")
        else:
            print(f"\nПапку {FOLDER_NAME} создать не получилось.\n")
            return ''
        return FOLDER_NAME

    def write_file_result(self, json_file):
        try:
            file_name = 'photo_upload_results.json'
            with open(file_name, 'w') as outfile:
                json.dump(json_file, outfile)
            print(f"Результы загрузки фото из VK на Яндекс-диск записаны в файл {file_name}")
        except:
            print('Результы загрузки фото из VK на Яндекс-диск не удалось записать в json-файл')


    def photos_upload(self, photo_to_upload: dict):
        """Метод загружает фото из VK на яндекс диск в указанную папку"""
        if len(photo_to_upload) == 0:
            print("Список фотографий для загрузки пуст. Json-файл не будет создан. Работа программы прекращена.")
        else:
            upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            download_folder = self.create_folder()
            json_file_result = []
            if download_folder != '':
                try:
                    count = 1
                    for likes, photos in tqdm(photo_to_upload.items()):
                        time.sleep(2)
                        for description in photos:
                            if len(photos) == 1:
                                photo_name = f"disk:/{download_folder}/{str(likes)}.jpg"
                            else:
                                photo_name = f"disk:/{download_folder}/{str(likes)} {description['data']}.jpg"
                            params = {'path': photo_name, 'url': description['url']}
                            response_put = requests.put(upload_url, headers=self.headers, params=params)
                            if response_put.status_code == 202:
                                print(f"Фото {count} из {NUMBER_UPLOAD_PHOTO} успешно загружена на Яндекс диск в папку {download_folder}")
                                json_file_result.append({'file name': photo_name, 'size': description['size']})
                            else:
                                print(f"Ошибка загрузки фото {count} из {NUMBER_UPLOAD_PHOTO}, код ошибки {response_put.status_code}, имя файла: {photo_name}")
                            count = count + 1
                    if len(json_file_result) > 0:
                        self.write_file_result(json_file_result)
                    else:
                        print('Фотографии не удалось загрузить на Яндекс-диск, json-файл с результатами не будет записан')
                except:
                    print(f"Фотографии из VK не удалось загрузить на Яндекс-диск в папку {download_folder}")
            else:
                print("Фотографии из VK не удалось загрузить на Яндекс-диск, т.к. не указана папка для загрузки")


if __name__ == '__main__':
    vk = VkUser()
    photos_info = vk.get_photo_info()
    yd = YandexUser()
    yd.photos_upload(vk.get_photo_list(photos_info))
