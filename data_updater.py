import requests
import io
import pandas as pd

YANDEX_PUBLIC_URL = "https://disk.yandex.com/i/40P6FT1VMg4jmg"

def get_direct_download_link(public_url):
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    params = {"public_key": public_url}
    response = requests.get(api_url, params=params)
    print("Ответ API Яндекс.Диска:", response.json())  # Отладочный вывод
    response.raise_for_status()
    data = response.json()
    direct_link = data.get("href")
    if not direct_link:
        raise Exception("Не удалось получить прямую ссылку для скачивания.")
    return direct_link

def download_xlsx_from_yadisk(public_url):
    direct_link = get_direct_download_link(public_url)
    response = requests.get(direct_link, verify=False)  # Отключение SSL для тестирования
    response.raise_for_status()
    df_remote = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
    df_remote.columns = [col.strip().strip('"') for col in df_remote.columns]
    return df_remote

if __name__ == "__main__":
    # Тестовый запуск обновления данных
    try:
        df = download_xlsx_from_yadisk(YANDEX_PUBLIC_URL)
        print(df.head())
    except Exception as e:
        print("Ошибка:", e)